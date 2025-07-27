import asyncio
from typing import TypedDict, cast

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from langgraph.types import Send
from langchain_tavily import TavilySearch

from domains.common.agents.retrieval_subgraph.states import ResearcherState, QueryState, RetrievalAgentState

QUERY_GENERATION_NODE_SYSTEM_PROMPT = """\
당신은 사용자가 적금으로 모으려는 **구체적 목표(구매 품목·경험·자금 용도)**와 관련된 외부 정보를 찾기 위한 검색 쿼리를 작성하는 에이전트다.

### 임무
1. 사용자 질문에서 ‘돈을 모으려는 대상·목적’(예: “맥북 Air M3”, “호주 워킹홀리데이 경비”)을 추출한다.  
2. 다양한 정보원을 겨냥한 **한국어 검색 쿼리 3개**를 작성한다.  
   - 제조사·공식 판매처, 가격 비교 사이트, 최신 리뷰·커뮤니티 글 등으로 분산  
   - 서로 유사하거나 중복된 표현을 피한다.

### 출력 규칙
- 쿼리만 한 줄씩 줄바꿈으로 나열한다.  
- 불릿, 번호, 해설, 추가 문구를 포함하지 않는다."""


def init_query_generation_node(llm: BaseChatModel):

    async def node(state: ResearcherState) -> dict[str, list[str]]:
        write = get_stream_writer()

        write({
            "chat_id": state.chat_id,
            "status": "pending",
            "content": {
                "message": "검색어를 생성 중입니다."
            }
        })

        class Response(TypedDict):
            queries: list[str]

        model = llm.with_structured_output(Response)
        messages = [
            {
                "role": "system",
                "content": QUERY_GENERATION_NODE_SYSTEM_PROMPT
            },
            {
                "role": "human",
                "content": state.question
            },
        ]

        response = cast(Response, await model.ainvoke(messages))
        return {"queries": response["queries"]}

    return node


def _tavily2document(data: dict):

    page_content = data.get("content") or data.get("raw_content") or data.get(
        "title", "")

    metadata = {
        "source": data.get("url"),
        "title": data.get("title"),
        "score": data.get("score"),
        **{
            k: v for k, v in data.items() if k not in {
                "raw_content", "content", "title", "url", "score"
            }
        }
    }

    return Document(page_content=page_content, metadata=metadata)


def init_document_retrieval_node():

    tool = TavilySearch(max_result=3)

    async def _fetch(query: str) -> Document:
        resp = await tool.ainvoke(query)
        return _tavily2document(resp)

    async def node(state: ResearcherState):
        documents = await asyncio.gather(*[_fetch(q) for q in state.queries])
        return {"documents": list(documents)}

    return node


def init_research_subgraph(llm: BaseChatModel):
    builder = StateGraph(ResearcherState)
    builder.add_node("generate_queries", init_query_generation_node(llm))
    builder.add_node("retrieve_documents",
                     init_document_retrieval_node())  # type: ignore

    builder.add_edge(START, "generate_queries")
    builder.add_edge("generate_queries", "retrieve_documents")
    builder.add_edge("retrieve_documents", END)
    graph = builder.compile()
    graph.name = "ResearcherGraph"

    return graph


def init_research_node(research_graph: CompiledStateGraph):

    async def node(state: RetrievalAgentState):
        result = await research_graph.ainvoke({
            "question": state.steps[0],
            "chat_id": state.chat_id
        })
        return {"documents": result["documents"], "steps": state.steps[1:]}

    return node
