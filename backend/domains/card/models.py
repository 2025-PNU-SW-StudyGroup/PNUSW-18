from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import List
import uuid


class CardBenefitCategory(Enum):
    """카트 혜택 구분"""

    CONVENIENCE_STORE = "편의점"
    ONLINE_SHOPPING = "온라인 쇼핑몰"
    BILL_PAYMENT = "생활"
    SUPERMARKET = "대형마트"
    GAS_STATION = "주유/충전"
    HEALTHCARE = "병원/약국"
    LAUNDRY = "세탁소"
    TAXI = "택시"
    FOOD = "카페/간식"
    ETC = "기타"


class Card(BaseModel):

    id: uuid.UUID = Field(alias="_id", default_factory=uuid.uuid4, frozen=True)

    targets


class CardBenefitTargetBase(BaseModel):
    target: str


class CardBenefitTargetIn(CardBenefitTargetBase):
    pass


class CardBenefitTarget(CardBenefitTargetBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# CardBenefitRequirement schemas
class CardBenefitRequirementBase(BaseModel):
    requirement: str


class CardBenefitRequirementIn(CardBenefitRequirementBase):
    pass


class CardBenefitRequirement(CardBenefitRequirementBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# CardBenefitNote schemas
class CardBenefitNoteBase(BaseModel):
    note: str


class CardBenefitNoteIn(CardBenefitNoteBase):
    pass


class CardBenefitNote(CardBenefitNoteBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# CardBenefitLimit schemas
class CardBenefitLimitBase(BaseModel):
    per_day: int | None = None
    per_month: int | None = None
    per_year: int | None = None


class CardBenefitLimitIn(CardBenefitLimitBase):
    pass


class CardBenefitLimit(CardBenefitLimitBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# CardBenefit schemas
class CardBenefitBase(BaseModel):
    category: CardBenefitCategory
    description: str


class CardBenefitIn(CardBenefitBase):
    targets: List[CardBenefitTargetIn]
    requirements: List[CardBenefitRequirementIn]
    notes: List[CardBenefitNoteIn]
    limits: List[CardBenefitLimitIn]


class CardBenefit(CardBenefitBase):
    id: uuid.UUID
    targets: List[CardBenefitTarget]
    requirements: List[CardBenefitRequirement]
    notes: List[CardBenefitNote]
    limits: List[CardBenefitLimit]

    model_config = ConfigDict(from_attributes=True)


# Card schemas
class CardBase(BaseModel):
    name: str
    annual_fee: int | None = None
    monthy_requirement: int | None = None


class CardIn(CardBase):
    benefits: List[CardBenefitIn]


class Card(CardBase):
    id: int
    benefits: List[CardBenefit]

    model_config = ConfigDict(from_attributes=True)
