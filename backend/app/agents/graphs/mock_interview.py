"""模拟面试 LLM 调用函数"""

import logging
import re

from app.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

INTERVIEWER_PROMPT = """你是一个专业的面试官，正在面试一位求职者。

根据候选人的简历和岗位要求，提出专业的技术或行为问题。
面试风格：专业、友好、有洞察力。

只输出问题内容，不要有其他文字。"""

EVALUATOR_PROMPT = """你是资深面试官，请给出专业反馈。

要求：
1. 优点（20字以内）
2. 改进建议（30字以内）
3. 整体评价（一句话）

只输出反馈内容，不要有其他文字。"""

llm = get_llm()


def _clean_text(text: str) -> str:
    """清洗 LLM 输出"""
    if not text:
        return ""
    text = re.sub(r"^```json\s*", "", text.strip())
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


SUMMARIZER_PROMPT = """你是资深面试官，请根据整场模拟面试的题目、回答和逐题反馈，给出一份总结。

要求：
1. 总体表现评价（50字以内）
2. 突出优势（30字以内）
3. 改进建议（30字以内）

只输出总结内容，不要有其他文字。"""


def generate_interview_summary(
    questions: list,
    answers: list,
    feedbacks: list
) -> str:
    """生成整场面试总结"""
    if not questions or not answers:
        return ""

    conversation = []
    for i, question in enumerate(questions):
        conversation.append(f"Q{i + 1}: {question}")
        if i < len(answers):
            conversation.append(f"A{i + 1}: {answers[i]}")
        if i < len(feedbacks):
            conversation.append(f"F{i + 1}: {feedbacks[i]}")

    prompt = "整场模拟面试记录：\n" + "\n".join(conversation)

    try:
        response = llm.invoke([
            SystemMessage(content=SUMMARIZER_PROMPT),
            HumanMessage(content=prompt),
        ])
        return _clean_text(response.content)
    except Exception as e:
        logger.error(f"生成面试总结失败: {e}")
        return "面试已完成，请查看逐题反馈。"


def generate_question(
    resume_text: str,
    jd_text: str,
    previous_question: str = "",
    previous_answer: str = ""
) -> str:
    """生成面试问题"""
    prompt = f"""【简历】\n{resume_text}\n\n【岗位JD】\n{jd_text}"""

    if previous_question and previous_answer:
        prompt += f"\n\n【上一个问题】\n{previous_question}\n"
        prompt += f"【候选人回答】\n{previous_answer}\n"
        prompt += "\n请根据候选人的回答，生成下一个面试问题。"

    prompt += "\n\n只输出问题内容，不要有其他文字。"

    try:
        response = llm.invoke([
            SystemMessage(content=INTERVIEWER_PROMPT),
            HumanMessage(content=prompt),
        ])
        return _clean_text(response.content)
    except Exception as e:
        logger.error(f"生成问题失败: {e}")
        return "请介绍一下你最自豪的项目经历。"


def evaluate_answer(question: str, answer: str) -> str:
    """评估回答"""
    prompt = f"""面试问题：{question}

候选人回答：{answer}

请给出专业、简洁的反馈（50字以内），包括优点和改进建议。"""

    try:
        response = llm.invoke([
            SystemMessage(content=EVALUATOR_PROMPT),
            HumanMessage(content=prompt),
        ])
        return _clean_text(response.content)
    except Exception as e:
        logger.error(f"评估回答失败: {e}")
        return "回答不错，继续加油！"
