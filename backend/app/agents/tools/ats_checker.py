"""ATS 兼容性检查工具"""

from typing import List, Dict


def check_ats_compatibility(resume_text: str) -> Dict:
    """检查简历的 ATS 兼容性（占位）"""
    # TODO: 检查关键词密度、格式规范、可解析性
    return {
        "score": 0,
        "issues": [],
        "suggestions": [],
    }


def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词（占位）"""
    # TODO: 接入 NLP 关键词提取
    return []
