"""面试题生成 LangGraph 工作流"""

import json
import logging
import re
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm

logger = logging.getLogger(__name__)

# System Prompt 常量
SYSTEM_PROMPT = """你是一个面试题生成专家。根据候选人的简历、目标JD和面经知识库，生成可能被问到的面试题。

要求：
1. 题目要结合简历中的项目经验
2. 题目要覆盖JD中的技术要求
3. 参考面经中的真实问题
4. 区分技术题、项目题、行为题

输出格式（JSON）：
{
    "questions": [
        {"question": "题目内容", "category": "技术|项目|行为", "difficulty": "简单|中等|困难"}
    ]
}"""


class InterviewState(TypedDict):
    resume_text: str
    jd_text: str
    article_content: str
    limit: int
    questions: List[dict]
    error: str


def _clean_json_response(raw: str) -> str:
    """清洗 LLM 输出的 JSON 字符串"""
    # 移除 markdown 代码块标记
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"```$", "", raw)
    return raw.strip()


def _validate_question(item: dict) -> bool:
    """校验单个题目字段"""
    if not isinstance(item, dict):
        return False
    if not item.get("question") or not isinstance(item["question"], str):
        return False
    category = item.get("category", "")
    if category not in ["技术", "项目", "行为"]:
        return False
    difficulty = item.get("difficulty", "")
    if difficulty not in ["简单", "中等", "困难"]:
        return False
    return True


def generate_questions_node(state: InterviewState) -> InterviewState:
    """基于简历 + JD + 面经生成面试题（同步节点）"""
    logger.info("开始生成面试题")

    # 构建 prompt
    prompt = f"""【简历】\n{state['resume_text']}\n\n【目标JD】\n{state['jd_text']}"""

    if state.get("article_content"):
        prompt += f"\n\n【面经参考】\n{state['article_content']}"

    if state.get("limit", 0) > 0:
        prompt += f"\n\n请生成最多 {state['limit']} 道题目。"

    try:
        response = get_llm().invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        raw_content = response.content
        logger.debug(f"LLM 原始返回: {raw_content[:200]}...")

        cleaned = _clean_json_response(raw_content)
        parsed = json.loads(cleaned)

        questions = parsed.get("questions", [])
        # 校验并过滤有效题目
        valid_questions = [q for q in questions if _validate_question(q)]
        logger.info(f"生成 {len(valid_questions)} 道有效题目")

        return {**state, "questions": valid_questions, "error": ""}

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return {**state, "questions": [], "error": "面试题生成格式异常，请重试"}
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        return {**state, "questions": [], "error": f"生成失败: {str(e)}"}


def create_interview_prep_graph():
    """创建面试题生成工作流"""
    workflow = StateGraph(InterviewState)
    workflow.add_node("generate", generate_questions_node)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


# 全局 Graph 实例
interview_prep_graph = create_interview_prep_graph()


async def generate_interview_questions(
    resume_text: str,
    jd_text: str,
    article_content: str = "",
    limit: int = 10
) -> dict:
    """
    执行面试题生成（异步入口）

    Args:
        resume_text: 简历文本
        jd_text: JD 文本
        article_content: 面经参考内容（可选）
        limit: 生成题目数量上限

    Returns:
        dict: 包含 questions 和 error 字段
    """
    initial = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "article_content": article_content,
        "limit": limit,
        "questions": [],
        "error": ""
    }
    result = await interview_prep_graph.ainvoke(initial)
    return result
