from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from domains.common.types import Institution, TermUnit
from domains.saving.types import SavingEarnMethod, SavingInterestType, SavingPreferentialRateType

from .models import Saving


class SavingRateWeights(BaseModel):
    """적금 검색에 사용되는 가중치.

    Attributes:
        base (float): 기본 금리
        max (float): 최대 금리 (기본 금리 + 우대 금리)
        intermediate (float): 중간 금리 (기본 금리 + user_choice 우대 금리)
    """

    base: float = Field(0, ge=0)
    max: float = Field(0, ge=0)
    intermediate: float = Field(0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def _normalize_and_validate(cls, data: dict) -> dict:

        base = data.get("base", 0)
        max = data.get("max", 0)
        intermediate = data.get("intermediate", 0)

        total = base + max + intermediate

        if total == 0:
            raise ValueError("가중치의 합은 0보다 커야합니다.")

        if abs(total - 1.0) > 1e-6:
            new_data = {
                "base": base / total,
                "max": max / total,
                "intermediate": intermediate / total,
            }

            return new_data

        return data


class SavingSearchResult(BaseModel):
    """메타데이터를 포함하는 적금 상품 검색 결과"""

    product: Saving
    score: float

    interest: Optional[int] = None  # 총 이자
    principal: Optional[int] = None  # 원금

    base_rate_rank: Optional[int] = None  # 기본금리 순위
    max_rate_rank: Optional[int] = None  # 최대 금리 순위

    model_config = ConfigDict(populate_by_name=True, strict=False)

    def __init__(self, **data):
        super().__init__(product=Saving(**data), **data)

    def __str__(self) -> str:

        info = "\n".join([
            f"총 이자: {format(self.interest or 0, ',') or '-'}",
            f"원금: {format(self.principal or 0, ',') or '-'}",
            f"기본금리 순위: {self.base_rate_rank or '-'}위",
            f"최대금리 순위: {self.max_rate_rank or '-'}위",
        ])

        result = ("### 상품 기본 정보\n"
                  f"{str(self.product)}\n\n"
                  "### 이율 정보\n"
                  f"{info}")

        print(result)

        return result


class TotalSavingSearchResult(BaseModel):

    savings: List[SavingSearchResult]
    offset: int


class SavingIn(BaseModel):
    """적금 상품 저장시 사용되는 DTO"""

    name: str
    institution: Institution

    min_term: int
    max_term: int
    term_unit: TermUnit = "month"

    min_amount: int
    max_amount: int
    amount_unit: TermUnit = "month"

    interest_type: SavingInterestType = "fixed"
    earn_method: SavingEarnMethod = "fixed"

    base_interest_rate: float
    preferential_rates: List[SavingPreferentialRateType]
