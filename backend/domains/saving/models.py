from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from domains.common.types import Institution, TermUnit, unit_map

from .types import (SavingInterestType, SavingEarnMethod, SavingPreferentialRateType,
                    saving_interest_type_map, saving_earn_method_map)

import uuid


class PreferentialRateTier(BaseModel):
    """우대금리 내의 개별 조건과 금리

    Attributes:
        condition (str): 상세 조건
        interest_rate (float): 우대금리
    """

    condition: str
    interest_rate: float


class SavingPreferentialRate(BaseModel):
    """적금 상품의 개별 우대금리 조건

    Attributes:
        description (str): 조건 설명
        rate_type (SavingPreferentialRateType): 우대금리 유형
        tiers (List[PreferentialRateTier]): 조건에 따른 상세 금리 목록
    """

    description: str
    rate_type: SavingPreferentialRateType
    tiers: List[PreferentialRateTier]


class BaseInterestRateTier(BaseModel):
    """가입 기간 구간별 기본 금리

    Attributes:
        min_term (int): 구간의 최소값 (ge)
        max_term (Optional[int]): 구간의 최대값 (lt)
        interest_rate (float): 해당 구간에 적용되는 연 금리 (%p)
    """

    min_term: int
    max_term: Optional[int] = None

    # 아 시발
    # term_unit: TermUnit

    interest_rate: float


# 가입 기간 정책 유형
TermPolicyType = Literal["RANGE", "FIXED_DURATION", "CHOICES", "FIXED_DATE"]


class TermPolicy(BaseModel):
    """가입 기간 정책"""

    policy_type: TermPolicyType = Field(..., description="기간 정책 유형")

    # type: RANGE, FIXED_DURATION
    min_term: Optional[int] = None
    max_term: Optional[int] = None

    # type: CHOICES
    choices: Optional[List[int]] = None

    # type: RANGE, FIXED_DURATION, CHOICES
    term_unit: Optional[TermUnit] = None

    # type: FIXED_DATE
    maturity_date: Optional[datetime] = None


# 납입 금액 정책 유형 (Amount)
AmountPolicyType = Literal["RANGE", "CHOICES", "FIXED_AMOUNT"]


class AmountPolicy(BaseModel):
    """
    납입 금액 정책을 나타내는 데이터 모델
    """
    policy_type: AmountPolicyType = Field(..., description="금액 정책 유형")

    # 'RANGE' 유형에 사용
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None

    # 'CHOICES' 유형에 사용
    choices: Optional[List[int]] = None

    # 'FIXED_AMOUNT' 유형에 사용
    fixed_amount: Optional[int] = None

    # 납입 주기 ('월', '일', '년')
    amount_unit: TermUnit = "month"


class Saving(BaseModel):
    """금융 기관의 단일 적금 상품 정보

    Attributes:
        id (str): 상품의 고유 식별자.

        name (str): 상품명.
        institution (Institution): 상품을 제공하는 기관.
        targets (str): 상품 가입 대상.

        event (str | None): 특판


        term (TermPolicy): 상품 가입 기간 관련 정책
        amount (AmountPolicy): 상품 납입 금액 관련 정책

        interest_type (SavingInterestType): 금리 유형 ('fixed', 'variable').
        earn_method (SavingEarnMethod): 적립 방식 ('fixed', 'flexible').
        enroll_method (str | None): 가입 방법.

        base_interest_rate (float | List[BaseInterestRateTier]): 기본금리
        preferential_rates (List[SavingPreferentialRate]): 우대금리
    """

    id: str = Field(alias="_id",
                    default_factory=lambda _: str(uuid.uuid4()),
                    frozen=True)

    name: str
    institution: Institution
    targets: str

    event: Optional[str] = None

    term: TermPolicy
    amount: AmountPolicy

    interest_type: SavingInterestType = "fixed"
    earn_method: SavingEarnMethod = "fixed"
    enroll_method: Optional[str] = None

    base_interest_rate: float | List[BaseInterestRateTier]
    preferential_rates: List[SavingPreferentialRate]

    max_interest_rate: float

    def format_interest_rates(self):

        base_rate: float
        if isinstance(self.base_interest_rate, float):
            base_rate = self.base_interest_rate
        else:
            base_rate = max(tier.interest_rate for tier in self.base_interest_rate)
        """
        preferential_sum = 0.0
        for pref in self.preferential_rates:
            if len(pref.tiers) > 0:
                tier_max = max(tier.interest_rate for tier in pref.tiers)
                preferential_sum += tier_max

        max_rate = base_rate + preferential_sum
        """

        max_rate = self.max_interest_rate

        return [{
            "category": "기본",
            "value": f"연 {base_rate:.2f}%"
        }, {
            "category": "최대",
            "value": f"연 {max_rate:.2f}%"
        }]

    def __str__(self) -> str:

        def format_term_policy(p: TermPolicy) -> str:
            unit = unit_map(p.term_unit or "month")
            if p.policy_type == "RANGE":
                return f"{p.min_term}{unit}" + (f" ~ {p.max_term}{unit}"
                                                if p.max_term else "")
            if p.policy_type == "FIXED_DURATION":
                return f"{p.min_term}{unit} 고정"
            if p.policy_type == "CHOICES":
                choices = ", ".join(f"{c}{unit}" for c in p.choices or [])
                return f"선택 ({choices})"
            if p.policy_type == "FIXED_DATE":
                return f"{p.maturity_date:%Y년 %m월 %d일} 만기" if p.maturity_date else "-"
            return ""

        def format_amount_policy(p: AmountPolicy) -> str:
            unit = unit_map(p.amount_unit or "month")
            if p.policy_type == "RANGE":
                return f"{p.min_amount:,}원 이상" if p.min_amount else "" + (
                    f" ~ {p.max_amount:,}원 이하" if p.max_amount else "") + f" / {unit}"
            if p.policy_type == "CHOICES":
                choices = ", ".join(f"{c:,}원" for c in p.choices or [])
                return f"선택 ({choices}) / {unit}"
            if p.policy_type == "FIXED_AMOUNT":
                if not p.fixed_amount:
                    return "-"
                return f"{p.fixed_amount:,}원 고정 / {unit}"
            return ""

        def format_base_rate(rate) -> str:
            if isinstance(rate, float):
                return f"{rate:.2f}%"

            tiers = [
                f"  - {t.min_term}개월 이상: {t.interest_rate:.2f}%" if t.max_term is None
                else f"  - {t.min_term} ~ {t.max_term}개월: {t.interest_rate:.2f}%"
                for t in rate
            ]
            return "\n" + "\n".join(tiers)

        def format_pref_rates(prs: List[SavingPreferentialRate]) -> str:
            lines = []
            for pr in prs:
                tier_str = "\n".join(
                    f"    - {tier.condition}: +{tier.interest_rate:.2f}%"
                    for tier in pr.tiers)
                lines.append(f"  - {pr.description}\n{tier_str}")
            return "\n".join(lines)

        lines = [
            f"- **상품명**: {self.name}",
            f"- **기관**: {self.institution}",
            f"- **대상**: {self.targets}",
            f"- **특판**: {self.event or '없음'}",
            f"- **가입 기간**: {format_term_policy(self.term)}",
            f"- **납입 금액**: {format_amount_policy(self.amount)}",
            f"- **금리 유형**: {saving_interest_type_map[self.interest_type]}",
            f"- **적립 방식**: {saving_earn_method_map[self.earn_method]}",
            f"- **기본 금리**: {format_base_rate(self.base_interest_rate)}",
            "- **우대 금리**:",
            format_pref_rates(self.preferential_rates) or "없음",
        ]
        return "\n".join(lines)
