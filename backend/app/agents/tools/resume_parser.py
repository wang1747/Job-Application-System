import re
from typing import Optional, Union
from io import BytesIO

import PyPDF2
import markdown
from bs4 import BeautifulSoup


def parse_pdf(file_path: str) -> str:
    """解析 PDF 文件为纯文本"""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise ValueError(f"PDF 解析失败: {e}")


def parse_pdf_bytes(file_bytes: bytes) -> str:
    """解析 PDF 字节流为纯文本（支持前端上传）"""
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise ValueError(f"PDF 解析失败: {e}")


def parse_markdown(file_path: str) -> str:
    """解析 Markdown 文件为纯文本"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        return parse_markdown_text(md_content)
    except Exception as e:
        raise ValueError(f"Markdown 解析失败: {e}")


def parse_markdown_text(content: str) -> str:
    """解析 Markdown 文本为纯文本"""
    html = markdown.markdown(content)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text.strip()


def parse_text(raw_text: str) -> str:
    """清理纯文本"""
    text = re.sub(r"\n\s*\n", "\n\n", raw_text)
    return text.strip()


def parse_resume_file(file_path: str) -> str:
    """自动识别文件类型并解析简历"""
    if file_path.lower().endswith(".pdf"):
        return parse_pdf(file_path)
    elif file_path.lower().endswith(".md"):
        return parse_markdown(file_path)
    elif file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return parse_text(f.read())
    else:
        raise ValueError(f"不支持的文件类型: {file_path}")


def parse_resume_bytes(filename: str, file_bytes: bytes) -> str:
    """解析上传的字节流简历文件"""
    if filename.lower().endswith(".pdf"):
        return parse_pdf_bytes(file_bytes)
    elif filename.lower().endswith(".md"):
        return parse_markdown_text(file_bytes.decode("utf-8"))
    elif filename.lower().endswith(".txt"):
        return parse_text(file_bytes.decode("utf-8"))
    else:
        raise ValueError(f"不支持的文件类型: {filename}")