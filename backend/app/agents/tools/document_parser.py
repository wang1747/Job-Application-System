"""文档解析工具：支持 PDF、图片 OCR、Markdown 等"""

from typing import Optional


def parse_pdf(file_path: str) -> Optional[str]:
    """解析 PDF 文件为纯文本（占位）"""
    # TODO: 接入 PyMuPDF
    return None


def parse_image(file_path: str) -> Optional[str]:
    """OCR 识别图片文字（占位）"""
    # TODO: 接入 OCR 引擎
    return None


def parse_markdown(file_path: str) -> Optional[str]:
    """读取 Markdown 文件（占位）"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None
