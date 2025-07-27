from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    weighted_score: float
    maturity_details: Optional[dict] = None
    target_details: Optional[dict] = None

    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        super().__init__(product=Saving(**data), **data)


class SavingIn(BaseModel):
    """적금 상품 저장시 사용되는 DTO"""

    name: str
    institution: Institution

    min_term: int
    max_term: int
    term_unit: SavingTermUnit = "month"

    min_amount: int
    max_amount: int
    amount_unit: SavingAmountUnit = "month"

    interest_type: SavingInterestType = "fixed"
    earn_method: SavingEarnMethod = "fixed"

    base_interest_rate: float
    preferential_rates: List[SavingPreferentialRate]
