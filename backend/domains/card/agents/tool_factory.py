from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from domains.saving.repositories.retrieval import search_savings
from domains.saving.schemas import SavingRateWeights, SavingSearchResult


class MaturitySearchParams(BaseModel):
    """'만기 금액 계산' 도구의 입력 스키마"""
    monthly_deposit: int = Field(..., description="사용자가 매월 납입할 금액")
    total_term_months: int = Field(..., description="총 납입할 기간(개월 수)")
    weights: SavingRateWeights = Field(..., description="금리 유형별 랭킹 가중치")


class TargetSearchParams(BaseModel):
    """'목표 달성 기간 계산' 도구의 입력 스키마"""
    monthly_deposit: int = Field(..., description="사용자가 매월 납입할 금액")
    target_amount: int = Field(..., description="달성하고자 하는 목표 금액")
    weights: SavingRateWeights = Field(..., description="금리 유형별 랭킹 가중치")


class GeneralSearchParams(BaseModel):
    """'일반 상품 추천' 도구의 입력 스키마"""

    monthly_deposit: Optional[int] = Field(None, description="사용자가 매월 납입할 금액 (선택 사항)")
    weights: SavingRateWeights = Field(..., description="금리 유형별 랭킹 가중치")


def init_saving_retrieval_tools(collection: AsyncIOMotorCollection):
    """적금 검색 Tool 초기화 함수"""

    @tool("calculate_maturity_amount", args_schema=MaturitySearchParams)
    async def search_by_maturity_amount(
            params: MaturitySearchParams) -> List[SavingSearchResult]:
        """매월 일정 금액을 특정 기간 동안 납입했을 때 만기 시 받을 금액을 계산하고, 가장 유리한 적금 상품을 추천합니다.
        사용자가 '매달 ~원씩 ~개월(또는 ~년) 넣으면' 이라고 질문하는 경우에 사용해야 합니다."""

        results = await search_savings(collection=collection,
                                       monthly_deposit=params.monthly_deposit,
                                       total_term_months=params.total_term_months,
                                       weights=params.weights)

        return results

    @tool("calculate_time_to_target", args_schema=TargetSearchParams)
    async def search_by_target_amount(
            params: TargetSearchParams) -> List[SavingSearchResult]:
        """매월 특정 금액을 납입하여 목표 금액을 달성하는 데 걸리는 기간을 계산하고, 가장 빠르게 목표를 달성할 수 있는 상품을 추천합니다.
        사용자가 '매달 ~원씩 넣어서 ~원을 모으려면' 이라고 질문할 때 사용해야 합니다."""

        results = await search_savings(collection=collection,
                                       monthly_deposit=params.monthly_deposit,
                                       target_amount=params.target_amount,
                                       weights=params.weights)

        return results

    return [
        search_by_maturity_amount,
        search_by_target_amount,
    ]
