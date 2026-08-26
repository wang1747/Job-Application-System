"""简历结构化解析：把纯文本简历解析成「姓名/联系方式 + 分节」结构。

供导出排版使用。纯函数、确定性，不依赖 LLM。
"""

import re
from dataclasses import dataclass, field
from typing import List

from app.modules.resume.optimizer.sections import SECTION_HEADER


@dataclass
class ResumeSection:
    title: str
    lines: List[str] = field(default_factory=list)


@dataclass
class StructuredResume:
    name: str = ""
    contact: List[str] = field(default_factory=list)
    sections: List[ResumeSection] = field(default_factory=list)

    @property
    def has_content(self) -> bool:
        return bool(self.name or self.contact or self.sections)


def _clean_line(line: str) -> str:
    return line.strip()


def parse_resume_structure(text: str) -> StructuredResume:
    """把纯文本简历解析为结构化简历。"""
    result = StructuredResume()
    lines = [_clean_line(line) for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return result

    # 1. 找到第一个分节标题
    first_section_idx = None
    for idx, line in enumerate(lines):
        if SECTION_HEADER.match(line):
            first_section_idx = idx
            break

    # 2. 头部：分节标题之前的内容 = 姓名 + 联系方式
    if first_section_idx is None:
        # 没有识别到分节，整份当作一个「正文」节
        header_lines = []
        body_lines = lines
    else:
        header_lines = lines[:first_section_idx]
        body_lines = lines[first_section_idx:]

    if header_lines:
        # 约定：第一行是姓名，其余是联系方式
        result.name = header_lines[0]
        result.contact = header_lines[1:]
    else:
        # 没有头部，取正文第一行当姓名（多数简历第一行是名字）
        result.name = body_lines[0] if body_lines else ""
        body_lines = body_lines[1:]

    # 3. 分节
    current_title = "正文"
    current_lines: List[str] = []
    for line in body_lines:
        if SECTION_HEADER.match(line):
            if current_lines:
                result.sections.append(ResumeSection(title=current_title, lines=current_lines))
                current_lines = []
            current_title = re.sub(r"[:：]\s*$", "", line.strip())
        else:
            current_lines.append(line)
    if current_lines or (result.sections == [] and current_title != "正文"):
        result.sections.append(ResumeSection(title=current_title, lines=current_lines))

    # 兜底：没有分节且没有正文，至少给一个空节
    if not result.sections and not result.name:
        result.sections.append(ResumeSection(title="正文", lines=[]))

    return result
