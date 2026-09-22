"""简历生成服务：结构化生成、逐段重生成、评分与 JD 匹配。"""

import json
import logging
import re
import sqlite3
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.tools.ats_checker import check_ats_compatibility
from app.core.llm import get_user_llm_or_raise
from app.models.jd import JobDescription
from app.models.user import User
from app.modules.resume.optimizer.contracts import JDRequirement
from app.modules.resume.optimizer.gap import analyze_gap
from app.modules.resume.optimizer.service import (
    _condense_to_one_page,
    _estimate_too_long,
)
from app.observability.tracing import trace_operation

from .contracts import GenerationResult
from .prompts import (
    REGENERATE_SYSTEM_PROMPT,
    REGENERATE_VARIANTS_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_regenerate_user_prompt,
    build_user_prompt,
)
from .render import list_sections, render_resume_text
from .schemas import ResumeGenerateRequest

logger = logging.getLogger(__name__)

# 生成字数硬约束：目标 800 字，下限 700 字（绝不能低于），可略超 900。
MIN_RESUME_LENGTH = 700


def _load_reference_sample(direction: str) -> str:
    """从 resume_samples 表查同方向的参考范文（真实完整简历），用于 few-shot 参考。

    只参考结构与写法，内容仍以用户输入为准（prompt 里已约束）。
    """
    if not direction:
        return ""
    try:
        from app.config import get_settings

        url = get_settings().database_url
        if not url.startswith("sqlite:///"):
            return ""
        conn = sqlite3.connect(url[len("sqlite:///"):])
        row = conn.execute(
            "SELECT raw_text FROM resume_samples "
            "WHERE source IN ('web_resume_sample','user_template') AND direction=? "
            "ORDER BY length(raw_text) DESC LIMIT 1",
            (direction,),
        ).fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception:
        return ""


def _clean_json_response(raw: str) -> str:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


def _dict_list(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _str_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


async def _build_jd_requirement(
    jd: Optional[JobDescription],
    jd_text: str,
    user: User,
) -> JDRequirement:
    if jd is not None:
        tech_stack: List[str] = []
        ts = jd.tech_stack or {}
        if isinstance(ts, dict):
            for values in ts.values():
                if isinstance(values, list):
                    tech_stack.extend(str(item) for item in values)
        elif isinstance(ts, list):
            tech_stack = [str(item) for item in ts]
        return JDRequirement(
            raw_text=jd.raw_text or jd_text or "",
            company=jd.company or "",
            position=jd.position or "",
            must_have=jd.must_have or [],
            nice_to_have=jd.nice_to_have or [],
            tech_stack=tech_stack,
            hidden_signals=jd.hidden_signals or [],
        )

    # 没有结构化 JD，但有 jd_text：解析 JD 提取硬性/加分要求，让 gap 分析有据可依
    raw = (jd_text or "").strip()
    if not raw:
        return JDRequirement(raw_text="")
    try:
        from app.agents.graphs.jd_analysis import analyze_jd

        result = await analyze_jd(raw, user)
        parsed = result.get("parsed") or {}
        if parsed.get("must_have") or parsed.get("nice_to_have") or parsed.get("tech_stack"):
            tech_stack: List[str] = []
            ts = parsed.get("tech_stack") or {}
            if isinstance(ts, dict):
                for values in ts.values():
                    if isinstance(values, list):
                        tech_stack.extend(str(item) for item in values)
            elif isinstance(ts, list):
                tech_stack = [str(item) for item in ts]
            return JDRequirement(
                raw_text=raw,
                company=parsed.get("company") or "",
                position=parsed.get("position") or "",
                must_have=parsed.get("must_have") or [],
                nice_to_have=parsed.get("nice_to_have") or [],
                tech_stack=tech_stack,
                hidden_signals=parsed.get("hidden_signals") or [],
            )
    except Exception as e:
        logger.warning("简历生成时解析 JD 提取要求失败（gap 分析降级）: %s", e)
    return JDRequirement(raw_text=raw)


def _score(requirement: JDRequirement, resume_text: str) -> tuple:
    ats = check_ats_compatibility(resume_text, requirement.raw_text)
    gap = analyze_gap(resume_text, requirement)
    gap_dict = {
        "matched": gap.matched,
        "missing": gap.missing,
        "partial": gap.partial,
    }
    return ats, gap_dict


async def _build_result(
    payload: Any,
    fallback_position: str,
    jd: Optional[JobDescription],
    jd_text: str,
    user: User,
    edu_input: Optional[List[Dict[str, Any]]] = None,
    exp_input: Optional[List[Dict[str, str]]] = None,
) -> GenerationResult:
    if not isinstance(payload, dict):
        return GenerationResult(error="生成结果格式错误，请重试")

    name = (payload.get("name") or "").strip()
    position = (payload.get("position") or "").strip() or (fallback_position or "").strip()
    contact = payload.get("contact") if isinstance(payload.get("contact"), dict) else {}
    contact = {
        key: str(contact.get(key) or "").strip()
        for key in ("phone", "email", "github")
    }
    summary = (payload.get("summary") or "").strip()
    # 教育经历是纯事实：优先用用户输入原样回填，杜绝 LLM 编造学校/学历
    education = edu_input if edu_input is not None else _dict_list(payload.get("education"))
    experiences = _dict_list(payload.get("experiences"))
    # 经历的事实字段（公司/项目名、角色、时间）也用用户输入回填，只保留 LLM 优化的 bullets
    if exp_input is not None and len(exp_input) == len(experiences):
        for i, exp in enumerate(experiences):
            src = exp_input[i]
            exp["name"] = src.get("name", "")
            exp["role"] = src.get("role", "")
            exp["start"] = src.get("start", "")
            exp["end"] = src.get("end", "")
            exp["type"] = src.get("type") or exp.get("type") or "project"
    skills = _str_list(payload.get("skills"))
    certifications = _str_list(payload.get("certifications"))
    tips = _str_list(payload.get("tips"))
    risks = _dict_list(payload.get("risks"))
    jd_alignment = _dict_list(payload.get("jd_alignment"))

    if not name:
        return GenerationResult(error="生成结果缺少姓名，请重试")
    if not education and not experiences:
        return GenerationResult(error="生成结果缺少教育经历或项目/实习经历，请重试")

    structured: Dict[str, Any] = {
        "name": name,
        "position": position,
        "contact": contact,
        "summary": summary,
        "education": education,
        "experiences": experiences,
        "skills": skills,
        "certifications": certifications,
    }
    resume_text = render_resume_text(structured)
    if not resume_text:
        return GenerationResult(error="生成结果渲染为空，请重试")
    sections = list_sections(structured)

    if _estimate_too_long("", resume_text):
        try:
            with trace_operation("resume_generate_condense", getattr(user, "id", None)):
                condensed, removed = await _condense_to_one_page(resume_text, user)
            if condensed and condensed.strip():
                resume_text = condensed.strip()
                tips.append("内容较多，已自动精简到一页")
                if removed:
                    tips.append("精简内容：" + "、".join(removed))
        except Exception as exc:
            logger.warning("简历生成后精简失败: %s", exc)

    requirement = await _build_jd_requirement(jd, jd_text, user)
    ats, gap = _score(requirement, resume_text)

    return GenerationResult(
        name=name,
        position=position,
        contact=contact,
        summary=summary,
        education=education,
        experiences=experiences,
        skills=skills,
        certifications=certifications,
        tips=tips,
        risks=risks,
        jd_alignment=jd_alignment,
        resume_text=resume_text,
        sections=sections,
        ats=ats,
        gap=gap,
    )


def _normalize_fact(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").lower())


def _req_input_text(req: ResumeGenerateRequest) -> str:
    """把用户填写的所有信息拼成一段文本，作为「事实来源」基准（不含 JD）。"""
    parts = [req.name, req.position, req.summary or ""]
    parts.extend([req.phone or "", req.email or "", req.github or ""])
    for edu in req.education:
        parts.extend([
            edu.school, edu.major, edu.degree, edu.start, edu.end,
            getattr(edu, "courses", "") or "", getattr(edu, "gpa", "") or "",
            getattr(edu, "honors", "") or "",
        ])
    for exp in req.experiences:
        parts.extend([exp.name, exp.role, exp.start, exp.end])
        parts.extend(exp.bullets or [])
    parts.extend(req.skills or [])
    parts.extend(req.certifications or [])
    return "\n".join(p for p in parts if p)


def _edu_input_to_dict(edu) -> Dict[str, str]:
    """把用户填写的教育经历（EducationInput）转成渲染/存库用的标准 dict。

    教育经历是纯事实（学校/专业/学历/时间），没有任何「表达优化」空间，
    必须原样保留用户输入，绝不交给 LLM 改写或编造。
    """
    detail_parts = []
    if getattr(edu, "courses", "") and str(edu.courses).strip():
        detail_parts.append(f"主修课程：{edu.courses}")
    if getattr(edu, "gpa", "") and str(edu.gpa).strip():
        detail_parts.append(f"绩点：{edu.gpa}")
    if getattr(edu, "honors", "") and str(edu.honors).strip():
        detail_parts.append(f"荣誉：{edu.honors}")
    if getattr(edu, "detail", "") and str(edu.detail).strip():
        detail_parts.append(str(edu.detail).strip())
    return {
        "school": (edu.school or "").strip(),
        "major": (edu.major or "").strip(),
        "degree": (edu.degree or "").strip(),
        "start": (edu.start or "").strip(),
        "end": (edu.end or "").strip(),
        "detail": "；".join(detail_parts),
    }


def _exp_input_to_dict(exp) -> Dict[str, str]:
    """把用户填写的经历（ExperienceInput）的事实字段抽出来。

    经历里「name/role/start/end/type」是纯事实（公司/项目名、角色、时间），
    只有 bullets 是需要 LLM 优化的表达。事实字段必须原样保留用户输入。
    """
    return {
        "type": (exp.type or "project").strip(),
        "name": (exp.name or "").strip(),
        "role": (exp.role or "").strip(),
        "start": (exp.start or "").strip(),
        "end": (exp.end or "").strip(),
    }


def check_generation_fidelity(
    req: ResumeGenerateRequest,
    result: "GenerationResult",
) -> Dict[str, Any]:
    """校验生成结果是否编造事实：学校/学历/公司名/技能/证书/联系方式必须来自用户输入。

    返回 {passed, added_schools, added_companies, added_skills, added_certifications, added_contacts}。
    不在用户输入里出现过的学校/公司名/技能/证书，视为「疑似新增」（编造）。
    """
    input_text = _req_input_text(req)
    input_norm = _normalize_fact(input_text)
    input_skills = {_normalize_fact(s) for s in (req.skills or []) if s}
    input_certs = {_normalize_fact(c) for c in (req.certifications or []) if c}
    input_schools = {_normalize_fact(e.school) for e in req.education if e.school}
    input_exp_names = {_normalize_fact(e.name) for e in req.experiences if e.name}

    added_skills = []
    for s in (result.skills or []):
        sn = _normalize_fact(s)
        if not sn:
            continue
        if sn in input_skills or sn in input_norm:
            continue
        # 子串匹配：LLM 常把技能扩展成描述（如「Go」→「精通 Go，熟悉嵌入式…」），
        # 只要描述里包含用户填过的技能（长度 >= 2，避免单字符「C」误匹配），就不算编造
        if any(len(skill) >= 2 and skill in sn for skill in input_skills):
            continue
        added_skills.append(s)

    added_certs = []
    for c in (result.certifications or []):
        cn = _normalize_fact(c)
        if not cn:
            continue
        if cn in input_certs or cn in input_norm:
            continue
        added_certs.append(c)

    added_contacts = []
    for key in ("phone", "email", "github"):
        gen = (result.contact.get(key) or "").strip()
        inp = (getattr(req, key, None) or "").strip()
        if gen and gen != inp:
            added_contacts.append(gen)

    # 学校编造检测：生成的学校必须能匹配用户填写的某个学校（双向子串容错「XX大学XX学院」）
    added_schools = []
    for edu in (result.education or []):
        sn = _normalize_fact((edu.get("school") or "").strip() if isinstance(edu, dict) else "")
        if not sn:
            continue
        if not input_schools or not any(sn in s or s in sn for s in input_schools):
            added_schools.append(edu.get("school") if isinstance(edu, dict) else edu)

    # 公司/项目名编造检测：生成的公司/项目名必须能匹配用户填写的某个名称
    added_companies = []
    for exp in (result.experiences or []):
        nn = _normalize_fact((exp.get("name") or "").strip() if isinstance(exp, dict) else "")
        if not nn:
            continue
        if not input_exp_names or not any(nn in s or s in nn for s in input_exp_names):
            added_companies.append(exp.get("name") if isinstance(exp, dict) else exp)

    passed = (
        not added_skills
        and not added_certs
        and not added_contacts
        and not added_schools
        and not added_companies
    )
    return {
        "passed": passed,
        "added_skills": added_skills,
        "added_certifications": added_certs,
        "added_contacts": added_contacts,
        "added_schools": added_schools,
        "added_companies": added_companies,
    }


async def _generate_payload(
    req: ResumeGenerateRequest,
    user: User,
    jd_prompt: str,
    reference: str,
    extra_hint: str = "",
) -> dict:
    """调用 LLM 生成结构化简历 JSON。extra_hint 用于重试时追加补充约束。"""
    llm = get_user_llm_or_raise(user)
    content = build_user_prompt(
        name=req.name,
        position=req.position,
        phone=req.phone or "",
        email=req.email or "",
        github=req.github or "",
        summary=req.summary or "",
        education=req.education,
        experiences=req.experiences,
        skills=req.skills,
        certifications=req.certifications,
        jd_text=jd_prompt,
        reference=reference,
    )
    if extra_hint:
        content += "\n\n" + extra_hint
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content),
    ])
    return json.loads(_clean_json_response(response.content))


async def generate_resume(
    req: ResumeGenerateRequest,
    user: User,
    jd: Optional[JobDescription] = None,
) -> GenerationResult:
    jd_prompt = req.jd_text or (jd.raw_text if jd else "") or ""
    reference = _load_reference_sample(req.direction or "")

    # RAG：生成简历时，从语料库检索同方向优秀简历作为写法参考（语义检索，失败静默降级）
    try:
        from app.modules.corpus.services import retrieve_similar
        query = " ".join(filter(None, [req.position, req.direction or "", req.summary or ""]))
        similar = retrieve_similar(query, top_k=2, item_type="resume")
        if similar:
            corpus_ref = "\n\n".join(s["raw_text"][:800] for s in similar)
            reference = (reference + "\n\n" + corpus_ref) if reference else corpus_ref
    except Exception as e:  # noqa: BLE001
        logger.warning("语料检索失败（不影响生成）: %s", e)

    try:
        with trace_operation("resume_generate", getattr(user, "id", None)):
            payload = await _generate_payload(req, user, jd_prompt, reference)
    except ValueError as exc:
        logger.warning("简历生成失败: %s", exc)
        return GenerationResult(error=str(exc))
    except Exception as exc:
        logger.error("简历生成异常: %s", exc)
        return GenerationResult(error="简历生成失败，请稍后重试")

    # 教育经历用用户输入原样回填，杜绝 LLM 编造学校/学历（纯事实，不做表达优化）
    edu_input = [
        _edu_input_to_dict(e) for e in req.education
        if (e.school or e.major or e.degree or e.start or e.end)
    ]
    # 经历的事实字段（公司/项目名、角色、时间）同样回填，只让 LLM 优化 bullets
    exp_input = [_exp_input_to_dict(e) for e in req.experiences]
    result = await _build_result(payload, req.position, jd, req.jd_text or "", user, edu_input, exp_input)

    # 字数硬约束：低于 700 字则带明确反馈重新生成一次
    if not result.error and len(result.resume_text) < MIN_RESUME_LENGTH:
        logger.warning("简历生成字数不足(%s 字)，触发扩充重试", len(result.resume_text))
        try:
            with trace_operation("resume_generate_retry", getattr(user, "id", None)):
                hint = (
                    f"你上一版全文只有 {len(result.resume_text)} 字，未达到 700 字下限。"
                    "请重新生成，全文必须达到 800 字左右（绝不能少于 700 字）。"
                    "硬性要求：每段经历必须写满 5 条要点；每条要点不少于 40 字，"
                    "写足「动词+对象+方法/技术手段+量化结果」四要素；个人总结写 3~4 句、不少于 80 字。"
                    "可以充分展开技术细节、实现过程、优化手段，但不得编造不存在的数字、技能、项目。"
                )
                payload2 = await _generate_payload(req, user, jd_prompt, reference, extra_hint=hint)
            result2 = await _build_result(payload2, req.position, jd, req.jd_text or "", user, edu_input, exp_input)
            # 采纳更长的结果（即使仍未达标，也保留更接近 700 的一版）
            if not result2.error and len(result2.resume_text) > len(result.resume_text):
                result = result2
                result.tips.append("内容偏少，已自动扩充")
        except Exception as exc:
            logger.warning("字数不足扩充重试失败: %s", exc)

    # 事实保真校验：技能/证书/联系方式必须来自用户输入
    if not result.error:
        result.fidelity = check_generation_fidelity(req, result)
        # 标注范文参考（对标标书 materialSources）：让用户知道写法参考了同方向范文
        if reference:
            result.reference_source = f"{req.direction or '通用'}方向优秀简历范文"

    return result


async def regenerate_section(
    structured: Dict[str, Any],
    section: str,
    index: Optional[int],
    jd_text: str,
    user: User,
    jd: Optional[JobDescription] = None,
) -> GenerationResult:
    try:
        with trace_operation("resume_regenerate_section", getattr(user, "id", None)):
            llm = get_user_llm_or_raise(user)
            response = llm.invoke([
                SystemMessage(content=REGENERATE_SYSTEM_PROMPT),
                HumanMessage(
                    content=build_regenerate_user_prompt(
                        structured,
                        section,
                        index,
                        jd_text,
                    )
                ),
            ])
            payload = json.loads(_clean_json_response(response.content))
    except ValueError as exc:
        logger.warning("逐段重新生成失败: %s", exc)
        return GenerationResult(error=str(exc))
    except Exception as exc:
        logger.error("逐段重新生成异常: %s", exc)
        return GenerationResult(error="重新生成失败，请稍后重试")

    return await _build_result(
        payload,
        str(structured.get("position") or ""),
        jd,
        jd_text,
        user,
    )


async def regenerate_section_variants(
    structured: Dict[str, Any],
    section: str,
    index: Optional[int],
    jd_text: str,
    user: User,
    jd: Optional[JobDescription] = None,
) -> List[Any]:
    """为指定字段生成 3 个改写候选，供用户选择（而非覆盖式重写）。"""
    jd_prompt = jd_text or (jd.raw_text if jd else "") or ""
    try:
        with trace_operation("resume_regenerate_variants", getattr(user, "id", None)):
            llm = get_user_llm_or_raise(user)
            response = llm.invoke([
                SystemMessage(content=REGENERATE_VARIANTS_SYSTEM_PROMPT),
                HumanMessage(
                    content=build_regenerate_user_prompt(
                        structured, section, index, jd_prompt,
                    )
                ),
            ])
            payload = json.loads(_clean_json_response(response.content))
    except Exception as exc:
        logger.warning("生成改写候选失败: %s", exc)
        return []

    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(candidates, list):
        return []
    return [c for c in candidates if c is not None][:3]


async def save_structured(
    structured: Dict[str, Any],
    jd_text: str,
    user: User,
    jd: Optional[JobDescription] = None,
) -> GenerationResult:
    """把前端选定候选后的完整 structured 重新渲染 + 评分，用于落库（不重新调 LLM）。"""
    return await _build_result(
        structured,
        str(structured.get("position") or ""),
        jd,
        jd_text,
        user,
    )
