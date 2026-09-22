"""把用户提供的两篇简历（docx + pdf）提取文本，作为模板存进 resume_samples 表。

- docx：内容在文本框里，直接读 document.xml 提取 <w:t>，保序去重（文本框被 XML 引用两次导致重复）。
- pdf：PyPDF2 提取。
"""
import re
import sqlite3
import uuid
import zipfile
from datetime import datetime

from PyPDF2 import PdfReader

DB = "E:/vscode/ai/求职系统/offerflow.db"
DOCX = "E:/Desktop/王照涵_简历.docx"
PDF = "E:/xwechat_files/wxid_kcgh7op1srm122_50a4/msg/file/2026-08/姓名：申洪涛(1).pdf"


def extract_docx_text(path: str) -> str:
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8")
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.DOTALL)
    lines = []
    for p in paras:
        ts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)
        line = "".join(ts).strip()
        if line:
            lines.append(line)
    # 保序去重（文本框被引用两次导致整块重复）
    seen = set()
    dedup = []
    for l in lines:
        if l not in seen:
            seen.add(l)
            dedup.append(l)
    return "\n".join(dedup)


def extract_pdf_text(path: str) -> str:
    r = PdfReader(path)
    return "\n".join(p.extract_text() or "" for p in r.pages)


def main():
    docx_text = extract_docx_text(DOCX)
    pdf_text = extract_pdf_text(PDF)

    conn = sqlite3.connect(DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resume_samples (
            id TEXT PRIMARY KEY,
            direction TEXT NOT NULL,
            label TEXT NOT NULL,
            title TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            structure TEXT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    now = datetime.now().isoformat(timespec="seconds")
    templates = [
        ("tech", "技术研发", "王照涵 · 大模型应用开发/AI Agent/Python后端", docx_text),
        ("tech", "技术研发", "申洪涛 · 数据处理专员", pdf_text),
    ]
    for direction, label, title, raw in templates:
        rid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO resume_samples (id, direction, label, title, raw_text, structure, source, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (rid, direction, label, title, raw, None, "user_template", now),
        )
    conn.commit()

    # 统计
    total = conn.execute("SELECT COUNT(*) FROM resume_samples WHERE source='user_template'").fetchone()[0]
    print(f"用户模板入库 {total} 篇")
    for row in conn.execute("SELECT title, length(raw_text) FROM resume_samples WHERE source='user_template'"):
        print(f"  {row[0]}（{row[1]} 字符）")
    conn.close()


if __name__ == "__main__":
    main()
