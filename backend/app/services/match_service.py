import re
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.jd import JobDescription
from app.models.match import MatchResult
from app.models.resume import Resume


SKILL_ALIASES: Dict[str, List[str]] = {
    "Python": ["python", "python3", "py"],
    "Java": ["java"],
    "Go": ["go", "golang"],
    "C++": ["c++", "cpp"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "React": ["react"],
    "Vue": ["vue", "vuejs"],
    "Node.js": ["node", "nodejs", "node.js"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "SQL": ["sql", "sqlite"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Redis": ["redis"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "亚马逊云"],
    "Git": ["git", "github", "gitlab"],
    "Linux": ["linux", "unix"],
    "Spring Boot": ["spring boot", "spring"],
    "Kafka": ["kafka"],
    "Nginx": ["nginx"],
    "CI/CD": ["ci/cd", "cicd", "jenkins"],
    "微服务": ["微服务", "microservice", "micro services"],
    "高并发": ["高并发", "high concurrency", "high-concurrency"],
    "分布式": ["分布式", "distributed"],
    "消息队列": ["消息队列", "message queue", "mq"],
    "RESTful API": ["restful", "rest api", "rest"],
    "算法": ["算法", "algorithm", "leetcode"],
    "机器学习": ["机器学习", "machine learning", "ml"],
    "深度学习": ["深度学习", "deep learning", "dl"],
    "数据分析": ["数据分析", "data analysis"],
    "测试": ["测试", "pytest", "单元测试", "unit test"],
    "安全": ["安全", "security"],
}


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[_\-\s]+", " ", text)
    return text


def _extract_skills(text: str) -> Set[str]:
    """从文本中识别已知技能"""
    normalized = _normalize(text)
    found: Set[str] = set()
    for skill, aliases in SKILL_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            found.add(skill)
    return found


def _skill_sources(jd: JobDescription, resume: Resume) -> tuple:
    jd_parts = [
        jd.raw_text or "",
        " ".join(jd.must_have or []),
        " ".join(jd.nice_to_have or []),
        " ".join(
            value
            for values in (jd.tech_stack or {}).values()
            if isinstance(values, list)
            for value in values
        ),
    ]
    resume_parsed = resume.parsed_json or {}
    resume_parts = [
        resume.raw_text or "",
        " ".join(resume_parsed.get("skills", []) if isinstance(resume_parsed.get("skills"), list) else []),
    ]
    return " ".join(jd_parts), " ".join(resume_parts)


def _persist_match(
    jd_id: str,
    resume_id: str,
    score: int,
    matched: List[str],
    missing: List[str],
    partial: List[str],
    suggestion: str,
    db: Session,
) -> MatchResult:
    existing = db.query(MatchResult).filter(
        MatchResult.jd_id == jd_id,
        MatchResult.resume_id == resume_id,
    ).first()
    if existing:
        existing.score = score
        existing.skill_match_detail = {"matched": matched, "missing": missing, "partial": partial}
        existing.gap_analysis = {"hard_gap": missing, "soft_gap": partial, "suggestion": suggestion}
        existing.suggestion = suggestion
        db.commit()
        db.refresh(existing)
        return existing
    match = MatchResult(
        jd_id=jd_id,
        resume_id=resume_id,
        score=score,
        skill_match_detail={"matched": matched, "missing": missing, "partial": partial},
        gap_analysis={"hard_gap": missing, "soft_gap": partial, "suggestion": suggestion},
        suggestion=suggestion,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def calculate_match(jd_id: str, resume_id: str, db: Session) -> dict:
    """计算 JD 与简历的技能匹配度并持久化结果"""
    settings = get_settings()
    jd = db.query(JobDescription).filter(
        JobDescription.id == jd_id,
        JobDescription.user_id == settings.default_user_id,
    ).first()
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == settings.default_user_id,
    ).first()
    if not jd:
        raise ValueError("JD 不存在")
    if not resume:
        raise ValueError("简历不存在")

    jd_text, resume_text = _skill_sources(jd, resume)
    jd_skills = _extract_skills(jd_text)
    resume_skills = _extract_skills(resume_text)

    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)
    partial = []
    for item in (jd.nice_to_have or []):
        if item and not any(alias in _normalize(resume_text) for alias in _extract_skill_aliases(item)):
            partial.append(item)

    hard_weight = 12
    nice_weight = 4
    score = max(0, min(100, 100 - len(missing) * hard_weight - len(partial) * nice_weight))
    suggestion = (
        "匹配度较高，可以直接投递。"
        if score >= 80
        else "建议补充缺失技能或相关项目经验后再投递。"
    )

    match = _persist_match(
        jd_id=jd_id,
        resume_id=resume_id,
        score=score,
        matched=matched,
        missing=missing,
        partial=partial,
        suggestion=suggestion,
        db=db,
    )
    return {
        "id": match.id,
        "jd_id": jd_id,
        "resume_id": resume_id,
        "company": jd.company,
        "position": jd.position,
        "score": match.score,
        "skill_match_detail": match.skill_match_detail,
        "gap_analysis": match.gap_analysis,
        "suggestion": match.suggestion,
        "created_at": match.created_at,
    }


def _extract_skill_aliases(term: str) -> List[str]:
    """返回某个技能词可能命中的别名，用于加分项判定"""
    normalized = _normalize(term)
    return [normalized] + [alias for aliases in SKILL_ALIASES.values() for alias in aliases if alias in normalized]


def get_match_detail(match_id: str, db: Session) -> Optional[dict]:
    """获取单条匹配结果详情"""
    settings = get_settings()
    match = db.query(MatchResult).join(
        JobDescription, MatchResult.jd_id == JobDescription.id
    ).filter(
        MatchResult.id == match_id,
        JobDescription.user_id == settings.default_user_id,
    ).first()
    if not match:
        return None
    return {
        "id": match.id,
        "jd_id": match.jd_id,
        "resume_id": match.resume_id,
        "score": match.score,
        "skill_match_detail": match.skill_match_detail,
        "gap_analysis": match.gap_analysis,
        "suggestion": match.suggestion,
        "created_at": match.created_at,
    }


def get_rankings(db: Session) -> List[dict]:
    """获取当前用户按匹配度排序的 JD 列表"""
    settings = get_settings()
    rows = db.query(MatchResult).join(
        JobDescription, MatchResult.jd_id == JobDescription.id
    ).filter(
        JobDescription.user_id == settings.default_user_id
    ).order_by(MatchResult.score.desc()).all()
    return [
        {
            "id": row.id,
            "jd_id": row.jd_id,
            "resume_id": row.resume_id,
            "company": row.jd.company,
            "position": row.jd.position,
            "score": row.score,
            "suggestion": row.suggestion,
            "created_at": row.created_at,
        }
        for row in rows
    ]
