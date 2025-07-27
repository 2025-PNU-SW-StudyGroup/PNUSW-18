from typing import List, TypedDict, cast
from langchain_core.language_models import BaseChatModel
from langgraph.config import get_stream_writer
from langgraph.graph import END

from domains.common.agents.retrieval_subgraph.states import RetrievalAgentState

RESEARCH_PLANNING_NODE_SYSTEM_PROMPT = """\
당신은 **적금 상품을 추천하기 전에 필요한 외부 정보를 신속‧정확하게 수집하는 웹 리서치 에이전트**입니다. 사용자에게 직접 추천을 제공하는 것이 목적이 아니라, **추천에 앞서 알아봐야 할 핵심 데이터를 웹에서 찾아오기 위한 ‘검색 계획’을 세우는 것**이 주 임무입니다.

### 역할

1. 사용자가 제시한 상황·조건·목표를 분석해 **적금 추천에 꼭 필요한 추가 정보**를 식별합니다.
2. 공개 웹(금융감독원 금융상품통합비교공시, 각 은행/저축은행 공식 사이트, 뉴스·보도자료 등)에서 해당 정보를 **어떤 순서와 방식**으로 찾을지 **간결한 계획**을 만듭니다.
3. 계획은 사용자가 이해하기 쉽도록 **단계별 리스트**(최대 3단계)로 작성합니다.

### 출력 형식

* 오직 **검색 계획**만 제시합니다.
* **불필요한 서론·결론·해설을 포함하지 않습니다.**

### 추가 지침

* 계획 단계 수는 **1‧2‧3단계 중 필요한 만큼**만 사용합니다.
* 각 단계에는 **무엇을 찾을지**와 **어디서 찾을지**를 함께 명시합니다. (예: “최신 정기적금 금리 상위 5개 은행 확인 – 금융감독원 비교공시”)
* 동일 정보원을 중복 검색하지 않도록 합니다.
* 전문용어 대신 **명료한 한국어**를 사용하며, 사과·주저·불필요한 반복 표현은 피합니다.
* 출처 링크는 필요 시 괄호 안에 간단히 표기할 수 있으나, 계획 본문을 흐리지 않습니다."""


def check_finished(state: RetrievalAgentState):
    if len(state.steps or []) > 0:
        return "research_node"
    else:
        return END


def init_retrieval_planning_node(llm: BaseChatModel,
                                 prompt: str = RESEARCH_PLANNING_NODE_SYSTEM_PROMPT):

    class Plan(TypedDict):
        steps: List[str]

    model = llm.with_structured_output(Plan)

    async def node(state: RetrievalAgentState):
        writer = get_stream_writer()
        messages = [{"role": "system", "content": prompt}] + state.messages

        writer({
            "chat_id": state.chat_id,
            "status": "pending",
            "content": {
                "message": "웹 검색 계획을 세우고 있습니다."
            }
        })

        res = cast(Plan, await model.ainvoke(messages))
        return {
            "steps": res["steps"],
            "documents": "delete",
        }

    return node
