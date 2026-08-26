"""简历导出服务：PDF / Word（中文排版 + 一页硬约束）。

核心规则（产品硬性要求）：
1. 简历必须控制在一页以内——导出时用实际渲染测页数，超一页则自动
   逐级缩小字号/行距/边距，直到塞进一页；内容完整不删减。
2. 注册系统中文字体，避免中文乱码。
3. 用 structure.parse_resume_structure 解析姓名/联系方式/分节，单栏 ATS 友好排版。
"""

import io
import os
import re
from typing import List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

from app.models.resume import Resume
from app.modules.resume.structure import StructuredResume, parse_resume_structure


# ============ 中文字体注册 ============

_FONT_CANDIDATES: List[Tuple[str, str, int]] = [
    # (字体名, 文件路径, TTC 子字体索引)
    ("CN", "C:/Windows/Fonts/simhei.ttf", 0),      # 本地开发 Windows
    ("CN", "C:/Windows/Fonts/msyh.ttc", 0),        # 微软雅黑
    ("CN", "C:/Windows/Fonts/simsun.ttc", 0),      # 宋体
    ("CN", "C:/Windows/Fonts/simkai.ttf", 0),      # 楷体
    # Docker 容器 Linux：文泉驿（TrueType outlines，reportlab 支持）
    ("CN", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
    ("CN", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
    # DejaVu（不含中文，仅兜底避免崩溃）
    ("CN", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0),
]

_font_name: Optional[str] = None


def _register_font() -> str:
    """注册中文字体，返回可用的字体名；找不到则回退内置字体。"""
    global _font_name
    if _font_name:
        return _font_name
    for name, path, subfont in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
                _font_name = name
                return name
            except Exception:
                continue
    _font_name = "Helvetica"
    return _font_name


def _bullet_line(line: str) -> str:
    """去掉行首的项目符号，返回纯文本。"""
    return re.sub(r"^\s*(?:[-•·▪◦●*]\s*)+", "", line).strip()


def _split_bullets(lines: List[str]) -> List[str]:
    """把可能含多个 `-` 分项的单行拆成多条。"""
    result: List[str] = []
    for line in lines:
        parts = re.split(r"\s{2,}(?=[-•·▪◦●*]\s)", line)
        result.extend(p for p in parts if p.strip())
    return result


def _escape(text: str) -> str:
    """转义 reportlab Paragraph 的特殊字符。"""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# 量化表达：百分比、带单位的数字（简历的「成果重点」），用于加色突出
_QUANT_PATTERN = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|万|千|亿|元|人|个|倍|条|项|次|ms|s|qps|k|w|月|日|年)",
    re.IGNORECASE,
)

# 重点强调色（深色，视觉上模拟「加粗」）
_ACCENT_COLOR = "#0F172A"


def _highlight_quantities(text: str) -> str:
    """给量化数字/百分比上色，突出简历的成果重点。

    需在 _escape 之后调用，这样插入的 <font> 标签不会被转义。
    用深色代替加粗，是因为文泉驿字体只有 Regular 字重、无 Bold。
    """
    return _QUANT_PATTERN.sub(
        lambda m: f'<font color="{_ACCENT_COLOR}">{m.group(0)}</font>',
        text,
    )


# ============ 一页自适应 ============

# 字号梯度：(正文, 行距, 标题, 联系方式, 姓名, 左右边距mm)。
# 越靠后越紧凑；导出时从第一档开始尝试，超一页就降一档，保证最终压进一页。
# 字号层级遵循成熟简历规范：姓名 18pt > 模块标题 12pt > 正文 10pt。
_SIZE_TIERS: List[Tuple[float, float, float, float, float, float]] = [
    (10.0, 15, 12.0, 9.5, 18, 18),
    (9.5, 14, 11.5, 9.0, 17, 16),
    (9.0, 13.5, 11.0, 9.0, 16, 15),
    (8.5, 13, 10.5, 8.5, 15, 14),
    (8.0, 12, 10.0, 8.5, 14, 12),
    (7.5, 11.5, 9.5, 8.0, 13, 10),
]

_WORD_SIZE_TIERS: List[float] = [10.5, 10.0, 9.5, 9.0, 8.5]


def _pdf_story(
    font: str,
    structured: StructuredResume,
    body: float,
    leading: float,
    heading: float,
    contact: float,
    title: float,
) -> List:
    title_style = ParagraphStyle(
        "CNTitle",
        fontName=font,
        fontSize=title,
        leading=title * 1.3,
        alignment=TA_CENTER,
        spaceAfter=3,
        textColor=colors.HexColor("#1f2937"),
    )
    contact_style = ParagraphStyle(
        "CNContact",
        fontName=font,
        fontSize=contact,
        leading=contact * 1.5,
        alignment=TA_CENTER,
        spaceAfter=2,
        textColor=colors.HexColor("#6b7280"),
    )
    heading_style = ParagraphStyle(
        "CNHeading",
        fontName=font,
        fontSize=heading,
        leading=heading * 1.3,
        spaceBefore=8,
        spaceAfter=2,
        textColor=colors.HexColor("#0F172A"),
    )
    body_style = ParagraphStyle(
        "CNBody",
        fontName=font,
        fontSize=body,
        leading=leading,
        leftIndent=8,
        spaceAfter=1.5,
        textColor=colors.HexColor("#475569"),
    )

    story: List = []
    if structured.name:
        story.append(Paragraph(_escape(structured.name), title_style))
    if structured.contact:
        story.append(Paragraph(_escape("  |  ".join(structured.contact)), contact_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#0F172A")))
    story.append(Spacer(1, 2 * mm))

    for section in structured.sections:
        story.append(Paragraph(_escape(section.title), heading_style))
        story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1")))
        for line in _split_bullets(section.lines):
            text = _bullet_line(line)
            if not text:
                continue
            # 先转义，再给量化数字上色，突出成果重点
            story.append(Paragraph(f"•&nbsp;{_highlight_quantities(_escape(text))}", body_style))

    return story


def _render_pdf(resume: Resume, tier: Tuple[float, ...]) -> Tuple[bytes, int]:
    font = _register_font()
    structured = parse_resume_structure(resume.raw_text)
    body, leading, heading, contact, title, margin = tier

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin * mm,
        rightMargin=margin * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
        title="简历",
    )
    story = _pdf_story(font, structured, body, leading, heading, contact, title)
    doc.build(story)
    return buffer.getvalue(), doc.page


def export_to_pdf(resume: Resume) -> bytes:
    """导出简历为 PDF，自动压缩到一页。"""
    last_data: Optional[bytes] = None
    for tier in _SIZE_TIERS:
        try:
            data, pages = _render_pdf(resume, tier)
        except Exception:
            continue
        last_data = data
        if pages <= 1:
            return data
    # 兜底：即使最小字号仍超一页，也返回最后一档（物理上已尽力压缩）
    return last_data if last_data is not None else b""


# ============ Word ============

def _estimate_word_size(char_count: int) -> float:
    """根据字符数估算 Word 字号，尽量压进一页。"""
    for threshold, size in [
        (700, 10.5),
        (900, 10.0),
        (1100, 9.5),
        (1400, 9.0),
    ]:
        if char_count <= threshold:
            return size
    return 8.5


def export_to_word(resume: Resume) -> bytes:
    structured = parse_resume_structure(resume.raw_text)
    char_count = len(resume.raw_text or "")
    body_size = _estimate_word_size(char_count)
    heading_size = body_size + 1.5
    name_size = body_size + 11

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(body_size)

    def _set_cn_font(run, size: float = body_size, bold: bool = False, color=None):
        run.font.name = "微软雅黑"
        run.font.size = Pt(size)
        run.font.bold = bold
        if color is not None:
            run.font.color.rgb = color

    if structured.name:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_cn_font(p.add_run(structured.name), size=name_size, bold=True, color=RGBColor(0x1F, 0x29, 0x37))

    if structured.contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_cn_font(p.add_run("  |  ".join(structured.contact)), size=body_size - 1, color=RGBColor(0x6B, 0x72, 0x80))

    for section in structured.sections:
        hp = doc.add_paragraph()
        _set_cn_font(hp.add_run(section.title), size=heading_size, bold=True, color=RGBColor(0x11, 0x18, 0x27))
        pPr = hp._p.get_or_add_pPr()
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "4")
        bottom.set(qn("w:space"), "2")
        bottom.set(qn("w:color"), "D1D5DB")
        pBdr.append(bottom)
        pPr.append(pBdr)

        for line in _split_bullets(section.lines):
            text = _bullet_line(line)
            if not text:
                continue
            bp = doc.add_paragraph(style="List Bullet")
            _set_cn_font(bp.add_run(text), size=body_size)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
