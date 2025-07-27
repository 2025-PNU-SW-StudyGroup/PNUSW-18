from operator import add
from typing import Annotated, Any, Dict, List, Optional, TypedDict, Union

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from domains.common.agents.types import Members
from domains.common.utils import reduce_docs
from domains.saving.schemas import SavingSearchResult

ProductSearchResults = Union[List[SavingSearchResult]] | None
ProductSearchResult = Union[SavingSearchResult]


class GraphState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]
    chat_id: str
    #tavily_results: Optional[dict]
    documents: Annotated[List[Document], reduce_docs]

    candidates: ProductSearchResults  # 추천 상품 후보
    selected: Annotated[ProductSearchResults, add]  # 실제 선택된 상품
    user_info: Dict[str, Any]  # 사용자 정보

    offset: int
    target_count: int  # 목표 상품 개수

    plan: List[Members]  # 예정된 하위 노드 실행 순서
    current_step: int  # 진행 중인 단계 인덱스

    next: Optional[str]
