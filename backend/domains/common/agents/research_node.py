from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.config import get_stream_writer
from domains.common.agents.graph_state import GraphState

from langgraph.prebuilt import create_react_agent


def init_research_node(llm: BaseChatModel):

    tavily_tool = TavilySearchResults()
    research_agent = create_react_agent(
        llm,
        tools=[tavily_tool],
        prompt=
        "당신은 금융상품 추천을 위해 웹 검색과 리서치를 수행하는 에이전트입니다. 사용자의 질문에 답변하기 전에, 웹에서 필요한 정보를 사전에 탐색하고 정리요약하세요."
    )

    async def node(state: GraphState):
        writer = get_stream_writer()

        result = await research_agent.ainvoke({"messages": state["messages"]})
        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "웹에서 정보를 찾고 있습니다."
            }
        })
        return {
            "messages": [
                AIMessage(
                    content=result["messages"][-1].content,
                    name="researcher",
                )
            ]
        }

    return node
