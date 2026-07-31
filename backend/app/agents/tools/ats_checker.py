"""ATS 兼容性检查工具"""

import re
from typing import Dict, List


def check_ats_compatibility(resume_text: str, jd_text: str = "") -> Dict:
    """检查简历的 ATS 兼容性：联系方式、分节、长度、JD 关键词覆盖"""
    text = resume_text or ""
    issues: List[str] = []
    suggestions: List[str] = []
    score = 100

    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))
    has_phone = bool(re.search(r"1[3-9]\d{9}", text)) or bool(re.search(r"\+?\d[\d\s-]{7,}\d", text))
    if not has_email:
        score -= 15
        issues.append("缺少邮箱联系方式")
    if not has_phone:
        score -= 10
        issues.append("缺少手机号联系方式")

    section_names = ["教育", "项目", "经验", "技能", "经历", "自我评价"]
    found_sections = [name for name in section_names if name in text]
    if not found_sections:
        score -= 20
        issues.append("未识别到常见简历分节（教育/项目/经验/技能）")
    elif len(found_sections) < 2:
        score -= 10
        issues.append("简历分节较少，建议补充教育、项目或技能模块")

    if len(text) < 200:
        score -= 15
        issues.append("内容过短，可能信息不足")

    long_lines = [line for line in text.splitlines() if len(line) > 200]
    if long_lines:
        score -= 10
        issues.append("存在超长段落，建议拆分为短句和项目符号")
        suggestions.append("将大段描述改为一句话要点 + 数据化成果")

    if jd_text:
        keywords = list(dict.fromkeys(
            kw for kw in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]*", jd_text.lower())
            if len(kw) >= 3
        ))[:50]
        if keywords:
            missing = [kw for kw in keywords if kw not in text.lower()]
            coverage = (len(keywords) - len(missing)) / len(keywords)
            if coverage < 0.5:
                score -= 20
                issues.append("JD 关键词覆盖率不足，ATS 可能无法识别相关技能")
                suggestions.append(f"补充 JD 中的关键词：{', '.join(missing[:8])}")

    if not suggestions and issues:
        suggestions.append("按 教育 → 技能 → 项目/实习 → 自我评价 的顺序整理简历")

    return {
        "score": max(0, min(100, score)),
        "issues": issues,
        "suggestions": suggestions,
    }


def extract_keywords(text: str) -> List[str]:
    """从文本中提取候选关键词"""
    return list(dict.fromkeys(
        kw for kw in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]*", (text or "").lower())
        if len(kw) >= 3
    ))
