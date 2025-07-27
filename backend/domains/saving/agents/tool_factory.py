from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from domains.saving.repositories.retrieval import find_savings
from domains.saving.schemas import SavingRateWeights, SavingSearchResult


class TargetTermParams(BaseModel):

    top_k: int = Field(5, description="한 번에 가져올 최대 개수")
    offset: int = Field(0, description="limit 단위로 증가하며 페이지네이션에 사용")
    target_amount: int = Field(..., description="달성하고자 하는 목표 금액")
    total_term_months: int = Field(..., description="총 납입할 기간(개월 수)")


class MonthlyTermParams(BaseModel):

    top_k: int = Field(5, description="한 번에 가져올 최대 개수")
    offset: int = Field(0, description="limit 단위로 증가하며 페이지네이션에 사용")
    monthly_deposit: int = Field(..., description="사용자가 매월 납입할 금액")
    total_term_months: int = Field(..., description="총 납입할 기간(개월 수)")


class TargetMonthlyParams(BaseModel):

    top_k: int = Field(5, description="한 번에 가져올 최대 개수")
    offset: int = Field(0, description="limit 단위로 증가하며 페이지네이션에 사용")
    target_amount: int = Field(..., description="달성하고자 하는 목표 금액")
    monthly_deposit: Optional[int] = Field(None, description="사용자가 매월 납입할 금액 (선택 사항)")


def init_saving_retrieval_tools(collection: AsyncIOMotorCollection):
    """적금 검색 Tool 초기화 함수"""

    default_weights = SavingRateWeights(base=0.3, max=0.3, intermediate=0.4)

    @tool("find_savings_by_target_and_term",
          args_schema=TargetTermParams,
          return_direct=True)
    async def find_savings_by_target_and_term(**kwargs) -> List[SavingSearchResult]:
        """
        목표 금액과 가입 기간을 입력받아 필요한 월 납입액을 계산하고,
        해당 금액 정책을 만족하는 적금 상품을 score 기준으로 검색한다.
        """
        print("find_savings_by_target_and_term")

        results = await find_savings(collection=collection,
                                     weights=default_weights,
                                     **kwargs)

        return results

    @tool("find_savings_by_monthly_and_term",
          args_schema=MonthlyTermParams,
          return_direct=True)
    async def find_savings_by_monthly_and_term(**kwargs) -> List[SavingSearchResult]:
        """
        월 납입 4금액과 가입 기간을 입력받아 만기 원금/이자/총액을 계산한 뒤,
        score 기준으로 적금 상품을 검색한다.
        """
        print("find_savings_by_monthly_and_term")

        results = await find_savings(collection=collection,
                                     weights=default_weights,
                                     **kwargs)

        return results

    @tool("find_savings_by_target_and_monthly",
          args_schema=TargetMonthlyParams,
          return_direct=True)
    async def find_savings_by_target_and_monthly(**kwargs) -> List[SavingSearchResult]:
        """
        목표 금액과 월 납입액을 입력받아 필요한 가입 기간을 계산하고,
        해당 기간 정책을 만족하는 적금 상품을 score 기준으로 검색한다.
        """
        print("find_savings_by_target_and_monthly")

        results = await find_savings(collection=collection,
                                     weights=default_weights,
                                     **kwargs)
        return results

    return [
        find_savings_by_target_and_monthly,
        find_savings_by_monthly_and_term,
        find_savings_by_target_and_term,
    ]
