import json
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.core.llm import get_user_llm_or_raise
from app.models.user import User

logger = logging.getLogger(__name__)


def _clean_json_response(raw: str) -> str:
    """清洗 LLM 输出的 JSON 字符串"""
    import re
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"```$", "", raw)
    return raw.strip()


class JDState(TypedDict):
    raw_text: str
    parsed: dict
    error: str


def parse_jd_node(state: JDState, config: RunnableConfig | None) -> JDState:
    """Parse JD text into structured JSON"""
    user = (config or {}).get("configurable", {}).get("user")
    if user is None:
        raise ValueError("未找到当前用户")
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
        # 获取用户配置的 LLM
        llm = get_user_llm_or_raise(user)

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=raw_text),
        ])
        parsed = json.loads(_clean_json_response(response.content))
        return {"raw_text": state["raw_text"], "parsed": parsed, "error": ""}
    except ValueError as e:
        # 用户未配置 LLM
        logger.warning(f"JD 解析失败: {e}")
        return {"raw_text": state["raw_text"], "parsed": {}, "error": str(e)}
    except Exception as e:
        logger.error(f"JD 解析异常: {e}")
        return {"raw_text": state["raw_text"], "parsed": {}, "error": str(e)}


def create_jd_analysis_graph():
    workflow = StateGraph(JDState)
    workflow.add_node("parse", parse_jd_node)
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", END)
    return workflow.compile()


jd_analysis_graph = create_jd_analysis_graph()


async def analyze_jd(raw_text: str, user: User) -> dict:
    """Execute JD analysis with user-specific LLM config"""
    initial_state = {"raw_text": raw_text, "parsed": {}, "error": ""}
    # 将 user 作为配置传递
    result = await jd_analysis_graph.ainvoke(initial_state, config={"configurable": {"user": user}})
    return result
