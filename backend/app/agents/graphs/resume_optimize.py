"""简历优化 LangGraph 工作流"""

import json
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm


class ResumeState(TypedDict):
    resume_text: str
    jd_text: str
    optimized: str
    changes: list
    error: str


def optimize_node(state: ResumeState) -> ResumeState:
    """针对 JD 优化简历"""
    system_prompt = """你是一个简历优化专家。根据目标 JD 的要求，优化简历内容。
保持所有事实不变，只优化表达方式和突出相关技能。
输出格式：{"optimized": "优化后的简历文本", "changes": ["改动1", "改动2"]}"""
    prompt = f"【原始简历】\n{state['resume_text']}\n\n【目标JD】\n{state['jd_text']}"
    try:
        response = get_llm().invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ])
        parsed = json.loads(response.content)
        return {**state, "optimized": parsed.get("optimized", ""), "changes": parsed.get("changes", []), "error": ""}
    except Exception as e:
        return {**state, "error": str(e)}


def create_resume_optimize_graph():
    workflow = StateGraph(ResumeState)
    workflow.add_node("optimize", optimize_node)
    workflow.set_entry_point("optimize")
    workflow.add_edge("optimize", END)
    return workflow.compile()


resume_optimize_graph = create_resume_optimize_graph()


async def optimize_resume(resume_text: str, jd_text: str) -> dict:
    """执行简历优化"""
    initial = {"resume_text": resume_text, "jd_text": jd_text, "optimized": "", "changes": [], "error": ""}
    return await resume_optimize_graph.ainvoke(initial)
