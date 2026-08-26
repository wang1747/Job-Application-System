"""简历相对 JD 的差距分析。

纯函数、确定性、不依赖 LLM，用于：
1. 告诉 LLM 哪些 JD 关键词已经命中、哪些缺失（不要硬塞）；
2. 给前端展示「本次优化针对哪些关键词」。

技能识别复用 app.core.text_utils 的技能词典 + 别名映射。
"""

import re
from typing import List, Optional

from app.core.text_utils import SKILL_ALIASES, extract_skills, normalize_text

from .contracts import GapAnalysis, JDRequirement


def _canonical_skill(term: str) -> Optional[str]:
    """如果 term 是某个技能名或其别名，返回规范技能名。"""
    normalized = normalize_text(term)
    # 直接命中技能名
    for skill, aliases in SKILL_ALIASES.items():
        if normalized == normalize_text(skill):
            return skill
        for alias in aliases:
            if normalized == normalize_text(alias):
                return skill
    return None


def _aliases_of(term: str) -> List[str]:
    """返回 term 的所有别名（含自身），用于在简历文本里查。"""
    skill = _canonical_skill(term)
    result = [normalize_text(term)]
    if skill:
        result.append(normalize_text(skill))
        result.extend(normalize_text(a) for a in SKILL_ALIASES.get(skill, []))
    # 英文术语的连字符/空格变体
    extra: List[str] = []
    for r in list(result):
        if re.fullmatch(r"[a-z0-9+#./-]+", r):
            extra.append(r.replace("-", "").replace(" ", ""))
    return [x for x in result + extra if x]


def analyze_gap(resume_text: str, jd: JDRequirement) -> GapAnalysis:
    """计算简历相对 JD 的 matched / missing。"""
    resume_norm = normalize_text(resume_text)
    resume_skills = extract_skills(resume_text)

    requirements: List[str] = []
    seen = set()
    for item in list(jd.must_have or []) + list(jd.nice_to_have or []):
        item = (item or "").strip()
        if item and item not in seen:
            requirements.append(item)
            seen.add(item)

    matched: List[str] = []
    missing: List[str] = []

    for req in requirements:
        hit = False
        # 1. 术语（含别名）直接出现在简历文本中
        for alias in _aliases_of(req):
            if alias and alias in resume_norm:
                hit = True
                break
        # 2. 规范技能名在简历技能集中
        if not hit:
            canonical = _canonical_skill(req)
            if canonical and canonical in resume_skills:
                hit = True
        if hit:
            matched.append(req)
        else:
            missing.append(req)

    return GapAnalysis(matched=matched, missing=missing, partial=[])
