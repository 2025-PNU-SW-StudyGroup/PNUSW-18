from typing import List, Literal, Optional
from pydantic import BaseModel


class ProductOptionDTO(BaseModel):
    category: str
    value: str


class ProductInfoDTO(BaseModel):
    name: str

    product_type: Literal["saving", "deposit", "card", "insurance"]
    description: str
    institution: str
    options: List[ProductOptionDTO]
    tags: List[str]
    details: str


class PartialProductInfoDTO(BaseModel):
    product_type: Literal["saving", "deposit", "card", "insurance"]
    description: Optional[str] = None
    institution: str

    options: Optional[List[ProductOptionDTO]] = None
    tags: Optional[List[str]] = None
    details: Optional[str] = None
