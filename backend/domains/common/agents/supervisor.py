import asyncio
from typing import AsyncIterator, List, TypedDict, cast
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_upstage import ChatUpstage
from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from motor.motor_asyncio import AsyncIOMotorDatabase
from common.database import init_mongodb_client
from domains.common.agents.graph_state import GraphState
from domains.common.agents.retrieval_subgraph.retrieval_node import init_retrieval_node, init_retrieval_subgraph
from domains.common.agents.types import Members
from domains.saving.agents.explain_node import init_explain_node
from domains.saving.agents.saving_subgraph import init_saving_subgraph
from domains.saving.agents.tool_factory import init_saving_retrieval_tools

SUPERVISOR_SYSTEM_PROMPT = """\
<Role>
당신은 Supervisor Node로서 ‘적금 추천’ 전체 워크플로우를 계획하고 실행까지 조율한다.
</Role>

<Goal>
1. 사용자의 요구·제약·데이터 부족 여부를 분석해 하위 노드 실행 순서를 3단계 이내로 결정
   • 외부 정보 필요 ➜ research_node 포함
   • 내부 DB만으로 충분 ➜ saving_node→explain_node
2. JSON 형태로 {"plan":[...], "next":"..."} 반환
</Goal>

<Output_Example>
{
  "plan": ["research_node", "saving_node", "explain_node"],
  "next": "research_node"
}
</Output_Example>"""


def init_supervisor_node(llm: BaseChatModel):

    class SupervisorResponse(TypedDict):
        plan: List[Members]
        next: Members

    async def supervisor_node(state: GraphState):
        print("============ Supervisor Node ============")

        writer = get_stream_writer()

        # 1) 이미 계획이 있으면 다음 단계만 실행
        if "plan" in state and state["current_step"] < len(state["plan"]):
            next_ = state["plan"][state["current_step"]]
            return {"next": next_, "current_step": state["current_step"] + 1}

        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "리서치 계획을 수립하고 있습니다."
            }
        })

        # 2) 최초 호출 → 계획 수립
        messages = [
            {
                "role": "system",
                "content": SUPERVISOR_SYSTEM_PROMPT
            },
            *state["messages"],
        ]
        result = cast(
            SupervisorResponse, await
            llm.with_structured_output(SupervisorResponse).ainvoke(messages))

        print(f"plan: {result['plan']}")
        print(f"next: {result['next']}")

        return {"next": result["next"], "plan": result["plan"], "current_step": 1}

    return supervisor_node


def init_graph(
    llm: BaseChatModel,
    db: AsyncIOMotorDatabase,
    target_count: int = 3,
):
    sg = StateGraph(GraphState)

    llm_with_reasoning = ChatUpstage(
        model="solar-pro2",
        reasoning_effort="medium",
        temperature=0.3,
    )
    """
    llm_with_reasoning = ChatUpstage(
        model="solar-pro2",
        temperature=0.3,
        reasoning_effort="high",
        max_tokens=16384,
    )
    """

    saving_tools = init_saving_retrieval_tools(db.get_collection("savings"))
    sg.add_node("saving_node", init_saving_subgraph(llm, saving_tools))

    _retrieval_subgraph = init_retrieval_subgraph()
    _retrieval_node = init_retrieval_node(_retrieval_subgraph)

    #sg.add_node("research_node", init_research_node(llm))
    sg.add_node("research_node", _retrieval_node)

    sg.add_node("explain_node", init_explain_node(llm))

    sg.add_node("supervisor", init_supervisor_node(llm_with_reasoning))

    sg.add_edge("research_node", "supervisor")
    sg.add_edge("saving_node", "supervisor")
    sg.add_edge("explain_node", END)

    sg.add_conditional_edges("supervisor", lambda s: s["next"])

    sg.set_entry_point("supervisor")

    graph = sg.compile()

    async def stream_graph(user_msg: str, chat_id: str) -> AsyncIterator[dict]:
        init_state: GraphState = {
            "chat_id": chat_id,
            "messages": [HumanMessage(content=user_msg)],
            "documents": [],
            "candidates": [],
            "selected": [],
            "offset": 0,
            "target_count": target_count,
            "next": None,
            "plan": [],
            "current_step": 0,
            "user_info": {
                "나이": "27세",
                "직업": "대학생",
                "월 소득": "50만원",
                "투자 성향": "안정적인 투자 선호",
                "결혼 여부": "미혼, 자녀없음"
            }
        }
        async for chunk in graph.astream(init_state,
                                         stream_mode="custom",
                                         subgraphs=True,
                                         config={"recursion_limit": 100}):
            yield chunk

    return stream_graph


import asyncio


async def run(query: str):
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
    )
    """

    llm = ChatUpstage(
        model="solar-pro2",
        temperature=0.3,
        reasoning_effort="low",
        max_tokens=16384,
    )
    _, db = init_mongodb_client()
    run = init_graph(llm, db)

    async for _, chunk in run(query, ""):
        if chunk["status"] == "response":
            print(chunk["content"]["message"], end="")
        else:
            print(chunk)


if __name__ == "__main__":
    asyncio.run(run("월 50씩 1년동안 모으려고 하는데 괜찮은 적금 추천좀 해주세요"))
