from typing import Dict, List
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer

from domains.common.agents.graph_state import GraphState

system_prompt = """\
당신은 사용자의 요청과 researcher의 리서치 결과를 바탕으로
상황에 맞는 적금 상품 검색 tool을 호출하는 에이전트다.

사용자가 어떤 질문을 하더라도, 상품 검색을 수행해야 한다.
올바른 파라미터와 함께 반드시 검색 도구를 호출하여라."""


def init_saving_tool_node(llm: BaseChatModel, tools: List[BaseTool]):

    agent_with_tools = llm.bind_tools(tools)
    tool_map: Dict[str, BaseTool] = {t.name: t for t in tools}

    async def node(state: GraphState):
        writer = get_stream_writer()

        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "상품을 검색하고 있습니다."
            }
        })

        research_context = ""
        if state.get("documents"):
            research_context = "\n\n## 외부 참고 정보\n" + "\n".join(
                f"- {getattr(d, 'page_content')}" for d in state["documents"][:5])

        messages = [{
            "role": "system",
            "content": system_prompt + research_context
        }] + state["messages"]

        res = await agent_with_tools.ainvoke(messages)
        tool_call = res.tool_calls[0]  # type: ignore
        tool = tool_map.get(tool_call.get("name"))
        tool_args = {**tool_call.get("args", {}), "offset": state["offset"]}

        if not tool:
            raise ValueError

        search_result = await tool.ainvoke(tool_args)
        #state["messages"].append(res)

        return {
            "candidates": search_result,
            "next": "filter_node",
        }

    return node
