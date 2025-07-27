from typing import List, TypedDict, cast
from langchain_core.language_models import BaseChatModel

from domains.common.agents.graph_state import GraphState
from domains.common.agents.types import Members

PLANNING_NODE_SYSTEM_PROMPT = """\
<ROLE>
당신은 ‘적금 상품 추천’을 위한 선행 계획 수립 담당자입니다.
</ROLE>

<GOAL>
1. 사용자 요구 분석 → 외부 조사 필요 여부 판단
2. 최대 3단계 이내로 ‘검색·분석·후속처리’ 계획 작성
3. 다음에 호출할 노드를 결정
    - 외부 정보 필수 ➜ "research_node"
    - 내부 DB만으로 충분 ➜ "saving_node"
</GOAL>

<OUTPUT_FORMAT>
```json
{
  "plan": ["...step1...", "...step2..."],
  "next": "research_node"
}
</OUTPUT_FORMAT>"""


def init_planning_node(llm: BaseChatModel):

    class Plan(TypedDict):
        steps: List[str]
        next: Members

    model = llm.with_structured_output(Plan)

    async def node(state: GraphState):

        messages = [
            {
                "role": "system",
                "content": ""
            },
            *state["messages"],
        ]

        result = cast(Plan, await model.ainvoke(messages))
        state["steps"] = result["steps"]

        return {"next": result["next"]}

    return node
