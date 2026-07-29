"""面试准备 LangGraph 工作流"""

import json
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm


class InterviewState(TypedDict):
    resume_text: str
    jd_text: str
    articles: List[str]
    questions: list
    error: str


llm = get_llm()


def generate_questions_node(state: InterviewState) -> InterviewState:
    """基于简历+JD+面经生成面试题"""
    context = f"【简历】\n{state['resume_text']}\n【JD】\n{state['jd_text']}"
    if state.get("articles"):
        context += f"\n【相关面经】\n" + "\n---\n".join(state["articles"])

    system_prompt = """你是一个面试官。根据候选人的简历、目标JD和相关面经，生成可能被问到的面试题。
输出JSON数组：[{"question": "...", "category": "技术|项目|行为", "difficulty": "easy|medium|hard", "answer_hint": "..."}]"""
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context),
        ])
        questions = json.loads(response.content)
        return {**state, "questions": questions, "error": ""}
    except Exception as e:
        return {**state, "error": str(e)}


def create_interview_prep_graph():
    workflow = StateGraph(InterviewState)
    workflow.add_node("generate", generate_questions_node)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


interview_prep_graph = create_interview_prep_graph()


async def generate_questions(resume_text: str, jd_text: str, articles: List[str] = None) -> dict:
    """生成面试题"""
    initial = {"resume_text": resume_text, "jd_text": jd_text, "articles": articles or [], "questions": [], "error": ""}
    return await interview_prep_graph.ainvoke(initial)
