# -*- coding: utf-8 -*-
"""把桌面《面试题库.docx》导入系统 interview_questions 表（当前用户个人题库）。

解析规则：
- 章节标题（一、~六、）→ 映射 category（项目/技术/行为）
- "Q数字." 开头 → 题目，紧跟段落合并为答案
- 第六章 "**标题**：内容" 格式 → 标题作题目、内容作答案
"""
import re
import sys

from docx import Document

sys.path.insert(0, "E:/vscode/ai/求职系统/backend")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.interview import InterviewQuestion
from app.models.user import User

DOCX = "E:/Desktop/面试题库.docx"
DB = "E:/vscode/ai/求职系统/offerflow.db"


def parse_question_bank(path):
    paras = [p.text.strip() for p in Document(path).paragraphs if p.text.strip()]
    questions = []
    category = "项目"
    section = None
    current_q = None
    parts = []

    def flush():
        nonlocal current_q, parts
        if current_q:
            questions.append((current_q, "\n".join(parts).strip(), category))
        current_q = None
        parts = []

    for t in paras:
        # 章节标题
        if t.startswith(("一、", "二、", "三、", "四、", "五、", "六、")):
            flush()
            if t.startswith("六"):
                section, category = "six", "项目"
            elif "技术" in t:
                section, category = "tech", "技术"
            elif "行为" in t:
                section, category = "behave", "行为"
            else:
                section, category = "project", "项目"
            continue
        # Q 格式题目
        if re.match(r"^Q\d+\.", t):
            flush()
            current_q = t
            continue
        # 第六章的 **标题**：内容
        if section == "six" and t.startswith("**"):
            flush()
            m = re.match(r"^\*\*(.+?)\*\*\s*[:：]?\s*(.*)$", t)
            current_q = m.group(1).strip() if m else t
            parts = [m.group(2).strip()] if (m and m.group(2).strip()) else []
            continue
        # 答案段落
        if current_q:
            parts.append(t)

    flush()
    return questions


def main():
    questions = parse_question_bank(DOCX)
    print(f"解析出 {len(questions)} 道题")

    engine = create_engine(f"sqlite:///{DB}", connect_args={"check_same_thread": False})
    S = sessionmaker(bind=engine)
    db = S()

    user = db.query(User).filter(User.name == "王").first()
    if not user:
        print("未找到用户「王」，终止")
        return
    print(f"目标用户: {user.name} ({user.id[:8]})")

    inserted = 0
    skipped = 0
    for question, answer, category in questions:
        exists = db.query(InterviewQuestion).filter(
            InterviewQuestion.user_id == user.id,
            InterviewQuestion.question == question,
        ).first()
        if exists:
            skipped += 1
            continue
        db.add(InterviewQuestion(
            user_id=user.id,
            article_id=None,
            question=question,
            answer=answer or None,
            category=category,
            difficulty=None,
        ))
        inserted += 1
    db.commit()

    total = db.query(InterviewQuestion).filter(InterviewQuestion.user_id == user.id).count()
    print(f"新增 {inserted} 道，跳过重复 {skipped} 道，当前题库共 {total} 道")
    db.close()


if __name__ == "__main__":
    main()
