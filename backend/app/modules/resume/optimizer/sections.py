"""原始简历分块与内容保留校验。均为纯函数，不依赖 LLM、数据库或网络。

整份重写场景下，「保留校验」的核心目标是：关键事实（联系方式、时间、数字、
英文技术词、专有名词）不丢失、不新增，而不是逐字保留原文。
"""

import re
from typing import Dict, List, Set

from .contracts import PreservationResult


SECTION_HEADER = re.compile(
    r"^\s*(?:教育|教育背景|教育经历|项目|项目经历|实习|实习经历|工作|工作经历|"
    r"经历|技能|专业技能|自我评价|个人评价|荣誉|获奖|证书|个人信息|基本资料|求职意向|"
    r"个人总结|个人简介|专业技能|掌握技能)"
    r"[^：:]{0,12}[:：]?\s*$"
)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
# 手机号（11 位）或座机（区号 2-4 位 + 分隔符 + 号码 7-8 位），
# 避免把「2023-2027」这类年份区间误判为电话
_PHONE = re.compile(r"(?:1[3-9]\d{9})|(?:\+?\d{2,4}[\s-]\d{7,8})")
# URL 只匹配到空白/中文/中文标点为止，避免把后面紧跟的中文（如「个人信息」）粘连进来
_URL = re.compile(r"https?://[^\s\u4e00-\u9fff，。；：、（）【】《》]+")
# 明显年份：四位数字后跟「年/届/级/月」（如 2027届、2023年），
# 避免把「处理 2000 并发」这类量化数字误判为年份
_YEAR = re.compile(r"(?:19|20)\d{2}(?=\s*(?:年|届|级|月))")
# 英文技术词 / 专有名词（含大写开头、点、井号、加号、斜杠）
_EN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+#./-]{1,}")
_CJK = re.compile(r"[\u4e00-\u9fff]+")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def split_resume_blocks(text: str) -> List[str]:
    """按常见简历小节标题切块，未识别到标题时按行切块。"""
    lines = [line.rstrip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return []

    blocks: List[str] = []
    current: List[str] = []
    for line in lines:
        if SECTION_HEADER.match(line) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _extract_critical_facts(text: str) -> Set[str]:
    """提取「绝对不能丢」的硬事实：联系方式、链接、四位年份。

    这些表述稳定，不会因措辞优化而改变，丢了即视为篡改。注意：普通数字
    （如「3年」「500ms」）不在此列——LLM 整份重写时可能把「3年」改写成
    「三年」，属于合理措辞调整，不应硬拦截。
    """
    critical: Set[str] = set()
    for pattern in (_EMAIL, _PHONE, _URL, _YEAR):
        critical.update(_normalize(item) for item in pattern.findall(text or "") if item)
    return critical


def _extract_critical_categories(text: str) -> Dict[str, int]:
    """按类别统计硬事实数量（邮箱/电话/链接/时间），用于前端「事实保真」可视化。"""
    categories = {
        "邮箱": len(_EMAIL.findall(text or "")),
        "电话": len(_PHONE.findall(text or "")),
        "链接": len(_URL.findall(text or "")),
        "时间": len(_YEAR.findall(text or "")),
    }
    return {key: count for key, count in categories.items() if count > 0}


def _extract_key_terms(text: str) -> Set[str]:
    """提取用于保留度评分的词：英文技术词 + 中文二元组 + 数字。

    中文二元组能捕获「学校/公司/项目名被替换」这类关键变动；
    数字（不跨行）用于评估量化成果是否被大范围删改。
    """
    terms: Set[str] = set()
    for word in _EN_WORD.findall(text or ""):
        if len(word) >= 3:
            terms.add(_normalize(word))
    for cjk in _CJK.findall(text or ""):
        for index in range(len(cjk) - 1):
            terms.add(cjk[index : index + 2])
    # 数字：单独用行内正则，避免 \s* 跨行粘连
    for num in re.findall(r"\d+(?:\.\d+)?%?", text or ""):
        terms.add(_normalize(num))
    return terms


def preservation_result(original: str, rewritten: str) -> PreservationResult:
    """计算 rewritten 对 original 关键事实的保留情况。

    规则：
    - 硬事实（邮箱/电话/链接/四位年份）一个都不能丢，丢了直接不过；
    - 软保留度（英文词/中文二元组/数字）>= 0.60 即通过：允许措辞升级、
      数字表述微调、删除少量无关内容，但整体替换学校/公司或大范围删改
      会显著拉低该值而被拒绝。
    """
    critical_orig = _extract_critical_facts(original)
    critical_categories = _extract_critical_categories(original)
    rewritten_norm = _normalize(rewritten)

    missing_critical = [
        item for item in critical_orig if item not in rewritten_norm
    ]
    critical_ok = not missing_critical

    terms_orig = _extract_key_terms(original)
    missing_terms = [t for t in terms_orig if t not in rewritten_norm]
    term_score = (
        (len(terms_orig) - len(missing_terms)) / len(terms_orig) if terms_orig else 1.0
    )

    passed = critical_ok and term_score >= 0.60
    score = round(term_score, 4)

    return PreservationResult(
        score=score,
        passed=passed,
        missing_facts=(missing_critical + missing_terms[:10]),
        fallback=False,
        critical_facts=critical_categories,
    )


def block_preserved(original: str, rewritten: str) -> bool:
    if not rewritten.strip():
        return False
    return preservation_result(original, rewritten).passed
