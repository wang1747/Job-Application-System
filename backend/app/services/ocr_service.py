"""
OCR 服务：图片文字识别
"""

import io
import re
from typing import Optional

import pytesseract
from PIL import Image


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    从图片中提取文字
    支持：PNG, JPG, JPEG, BMP, WEBP
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # 预处理：灰度化
        if image.mode != "L":
            image = image.convert("L")
        # 使用中文 + 英文语言包
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        # 清洗多余空白
        text = re.sub(r"\n\s*\n", "\n\n", text.strip())
        return text
    except Exception as e:
        raise ValueError(f"OCR 识别失败: {e}")


def extract_text_from_image_file(file_bytes: bytes, filename: str) -> str:
    """
    从上传的图片文件中提取文字
    支持常见图片格式
    """
    supported_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".webp"]
    ext = filename.lower()
    if not any(ext.endswith(suffix) for suffix in supported_extensions):
        raise ValueError(f"不支持的图片格式: {filename}，支持: {', '.join(supported_extensions)}")
    
    return extract_text_from_image(file_bytes)