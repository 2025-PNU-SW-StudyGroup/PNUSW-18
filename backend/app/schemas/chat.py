from datetime import datetime
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

from pytz import timezone

from app.schemas.product import PartialProductInfoDTO, ProductInfoDTO


class ChatRequest(BaseModel):
    chat_id: Optional[str] = Field(None, description="현재 채팅 ID, 새 대화일 경우 null")
    message: str = Field(description="질문 또는 요청 텍스트")


class ChatContentDTO(BaseModel):
    message: Optional[str] = None
    products: Optional[Union[List[ProductInfoDTO], List[PartialProductInfoDTO]]] = None


ChatResponseStatus = Literal["pending", "title", "response", "failed", "stop"]


class ChatResponseDTO(BaseModel):
    chat_id: str
    status: ChatResponseStatus
    content: Optional[ChatContentDTO] = None


class ChatListRequest(BaseModel):

    offset: Optional[int] = None
    size: Optional[int] = None


class ChatHistoryDTO(BaseModel):

    role: Literal["user", "assistant"]
    content: ChatContentDTO


class ChatDetailResponse(BaseModel):

    size: int
    offset: int
    items: List[ChatHistoryDTO]


class ChatPreviewDTO(BaseModel):

    chat_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime:
                lambda v: v.astimezone(timezone('Asia/Seoul')).isoformat(
                    timespec='milliseconds').replace('+00:00', 'Z')
        }


class ChatListResponse(BaseModel):

    size: int
    offset: int
    items: List[ChatPreviewDTO]
