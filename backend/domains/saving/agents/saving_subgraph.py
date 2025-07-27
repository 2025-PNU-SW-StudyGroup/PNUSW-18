from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph

from domains.common.agents.graph_state import GraphState

from domains.saving.agents.router_node import init_router_node
from domains.saving.agents.filter_node import init_filter_node
from domains.saving.agents.tool_node import init_saving_tool_node


def init_saving_subgraph(
    llm: BaseChatModel,
    saving_tools: List[BaseTool],
):
    """적금 서브그래프 초기화"""

    sg = StateGraph(GraphState)

    sg.add_node("tool_node", init_saving_tool_node(llm, saving_tools))
    #sg.add_node("tool_execution_node", init_saving_tool_execution_node(saving_tools))
    #sg.add_edge("tool_selection_node", "tool_execution_node")

    sg.add_node("filter_node", init_filter_node(llm))
    sg.add_node("router_node", init_router_node())

    sg.add_edge("tool_node", "filter_node")

    #sg.add_edge("tool_execution_node", "filter_node")
    sg.add_edge("filter_node", "router_node")

    sg.add_conditional_edges("router_node", lambda state: state["next"])

    sg.set_entry_point("tool_node")
    sg.set_finish_point("router_node")

    graph = sg.compile()

    return graph
