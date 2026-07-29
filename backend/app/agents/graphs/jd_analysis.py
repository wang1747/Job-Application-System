import json
from typing import TypedDict

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings

settings = get_settings()


# 定义状态
class JDState(TypedDict):
    raw_text: str
    parsed: dict
    error: str


# 初始化 LLM
llm = ChatOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    model=settings.llm_model,
    temperature=0.1,
)


def parse_jd_node(state: JDState) -> JDState:
    """解析 JD 文本为结构化 JSON"""
    raw_text = state["raw_text"]
    
    system_prompt = """你是一个专业的招聘JD解析专家。请从以下JD文本中提取结构化信息。

请严格按照以下JSON格式输出：
{
    "company": "公司名称",
    "position": "职位名称",
    "must_have": ["硬性要求列表"],
    "nice_to_have": ["加分项列表"],
    "tech_stack": {"backend": [], "frontend": [], "infra": [], "other": []},
    "hidden_signals": ["隐藏信号，如加班文化、团队规模等"]
}

如果某项信息无法提取，设置为空字符串或空列表。只输出JSON，不要有其他内容。"""
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=raw_text)
        ])
        parsed = json.loads(response.content)
        return {"raw_text": state["raw_text"], "parsed": parsed, "error": ""}
    except Exception as e:
        return {"raw_text": state["raw_text"], "parsed": {}, "error": str(e)}


# 构建工作流
def create_jd_analysis_graph():
    workflow = StateGraph(JDState)
    
    workflow.add_node("parse", parse_jd_node)
    
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", END)
    
    return workflow.compile()


# 全局实例
jd_analysis_graph = create_jd_analysis_graph()


async def analyze_jd(raw_text: str) -> dict:
    """执行 JD 分析"""
    initial_state = {"raw_text": raw_text, "parsed": {}, "error": ""}
    result = await jd_analysis_graph.ainvoke(initial_state)
    return result