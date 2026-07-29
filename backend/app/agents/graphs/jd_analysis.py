import json
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import get_llm


class JDState(TypedDict):
    raw_text: str
    parsed: dict
    error: str


_llm_instance = None


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm()
    return _llm_instance


def parse_jd_node(state: JDState) -> JDState:
    """Parse JD text into structured JSON"""
    raw_text = state["raw_text"]
    system_prompt = (
        "You are a professional JD parser. Extract structured info from the JD text.\n"
        "Output JSON strictly:\n"
        '{\n'
        '    "company": "...",\n'
        '    "position": "...",\n'
        '    "must_have": [...],\n'
        '    "nice_to_have": [...],\n'
        '    "tech_stack": {"backend": [], "frontend": [], "infra": [], "other": []},\n'
        '    "hidden_signals": [...]\n'
        '}\n'
        "If a field cannot be extracted, use empty string or empty list."
    )
    try:
        response = _get_llm().invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=raw_text),
        ])
        parsed = json.loads(response.content)
        return {"raw_text": state["raw_text"], "parsed": parsed, "error": ""}
    except Exception as e:
        return {"raw_text": state["raw_text"], "parsed": {}, "error": str(e)}


def create_jd_analysis_graph():
    workflow = StateGraph(JDState)
    workflow.add_node("parse", parse_jd_node)
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", END)
    return workflow.compile()


jd_analysis_graph = create_jd_analysis_graph()


async def analyze_jd(raw_text: str) -> dict:
    """Execute JD analysis"""
    initial_state = {"raw_text": raw_text, "parsed": {}, "error": ""}
    result = await jd_analysis_graph.ainvoke(initial_state)
    return result
