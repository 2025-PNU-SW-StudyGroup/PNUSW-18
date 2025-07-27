from langchain_openai.chat_models.base import ChatOpenAI
from langchain_upstage import ChatUpstage
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from domains.common.agents.graph_state import GraphState
from domains.common.agents.retrieval_subgraph.planning_node import check_finished, init_retrieval_planning_node
from domains.common.agents.retrieval_subgraph.research_subgraph import init_research_node, init_research_subgraph
from domains.common.agents.retrieval_subgraph.states import InputState, RetrievalAgentState


def init_retrieval_subgraph():

    llm = ChatUpstage(
        model="solar-pro2",
        temperature=0.3,
        reasoning_effort="low",
        max_tokens=16384,
    )

    builder = StateGraph(RetrievalAgentState, input_schema=InputState)

    research_graph = init_research_subgraph(llm)
    builder.add_node("research_node", init_research_node(research_graph))
    builder.add_node("planning_node", init_retrieval_planning_node(llm))
    builder.add_node("check_finished", check_finished)

    builder.add_edge(START, "planning_node")
    builder.add_edge("planning_node", "research_node")
    builder.add_conditional_edges("research_node", check_finished)
    builder.add_edge("research_node", END)

    graph = builder.compile()
    graph.name = "RetrievalGraph"

    return graph


def init_retrieval_node(graph: CompiledStateGraph):

    async def node(state: GraphState):

        write = get_stream_writer()

        write({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "검색어를 생성 중입니다."
            }
        })

        result = await graph.ainvoke({
            "documents": [],
            "messages": state["messages"],
            "chat_id": state["chat_id"]
        })
        documents = result.get("documents")

        return {"documents": documents}

    return node
