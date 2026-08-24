"""
简历导出服务：PDF / Word
"""

import io
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from docx import Document
from docx.shared import Inches

from app.models.resume import Resume


def export_to_pdf(resume: Resume) -> bytes:
    """导出简历为 PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=12
    )
    body_style = styles['Normal']
    
    story = []
    
    # 标题
    story.append(Paragraph(f"简历 - 版本 {resume.version}", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # 正文
    lines = resume.raw_text.split('\n')
    for line in lines:
        if line.strip():
            story.append(Paragraph(line.strip(), body_style))
            story.append(Spacer(1, 0.1 * inch))
    
    doc.build(story)
    return buffer.getvalue()


def export_to_word(resume: Resume) -> bytes:
    """导出简历为 Word"""
    doc = Document()
    
    # 标题
    doc.add_heading(f'简历 - 版本 {resume.version}', 0)
    
    # 正文
    lines = resume.raw_text.split('\n')
    for line in lines:
        if line.strip():
            doc.add_paragraph(line.strip())
    
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()