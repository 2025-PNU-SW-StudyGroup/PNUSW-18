from langgraph.graph import END
from domains.common.agents.graph_state import GraphState


def init_router_node():

    async def node(state: GraphState):
        print("============ Saving Router Node ============")

        selected = state.get("selected", [])

        if selected and len(selected) >= state["target_count"]:
            print(len(selected))
            return {"next": END}
        else:
            return {
                "next": "tool_node",
                "offset": state["offset"] + 5,
            }

    return node
