"""简历解析工具"""

from typing import Optional


def parse_resume_text(raw_text: str) -> dict:
    """从纯文本中提取简历结构化信息（占位）"""
    # TODO: 接入 LLM 进行结构化解析
    return {
        "personal_info": {},
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
    }


def parse_resume_pdf(file_path: str) -> Optional[str]:
    """解析 PDF 简历文件为纯文本（占位）"""
    # TODO: 接入 PyMuPDF
    return None
