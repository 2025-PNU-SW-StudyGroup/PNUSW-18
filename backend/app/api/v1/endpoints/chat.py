import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Header
from langchain_upstage import ChatUpstage
from openai import AsyncOpenAI
from starlette.responses import StreamingResponse

from app.crud import get_history, list_chats, save_msg, update_chat_title, upsert_chat
from app.dependencies import get_workflow_stream
from app.schemas.chat import (ChatContentDTO, ChatDetailResponse, ChatHistoryDTO,
                              ChatListResponse, ChatPreviewDTO, ChatRequest,
                              ChatResponseDTO)

from fastapi.encoders import jsonable_encoder

from dotenv import load_dotenv

import os
import json

load_dotenv()

router = APIRouter(prefix="")

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")

openai_client = AsyncOpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1",
)


async def generate_chat_title(chat_id: str, question: str) -> str:
    system_prompt = ("다음 사용자 질문에서 짧고 요약된 대화 제목을 한 문장으로 만들어주세요. "
                     "20자 이내로 간결하게 작성해주세요.")

    response = await openai_client.chat.completions.create(
        model="solar-pro",
        messages=[{
            "role": "system",
            "content": system_prompt
        }, {
            "role": "user",
            "content": question
        }],
        temperature=0.3,
        max_tokens=30,
    )

    title = response.choices[0].message.content or "새로운 대화"
    update_chat_title(chat_id, title)

    print("- 질문: ", question, ", 제목: ", title)

    return title


async def chat_events(req: ChatRequest, run_stream) -> AsyncGenerator[str, None]:

    chat_id = upsert_chat(req.chat_id, "새로운 대화")

    title_task = None
    if not req.chat_id:
        title_task = asyncio.create_task(generate_chat_title(chat_id, req.message))

    user_content = ChatContentDTO(message=req.message)
    save_msg(chat_id, "user", jsonable_encoder(user_content))

    products = []
    reply_chunks = []

    initial_response = ChatResponseDTO(chat_id=chat_id,
                                       status="pending",
                                       content=ChatContentDTO(message="질문을 이해하고 있습니다."))

    data_json = json.dumps(jsonable_encoder(initial_response), ensure_ascii=False)
    yield f"data: {data_json}\n\n"

    title_yielded = False

    async for _, chunk in run_stream(req.message, chat_id):
        payload = ChatResponseDTO(**chunk)
        data_json = json.dumps(jsonable_encoder(payload), ensure_ascii=False)

        yield f"data: {data_json}\n\n"

        match payload:
            case ChatResponseDTO(status="response",
                                 content=ChatContentDTO(products=None,
                                                        message=reply_chunk)):
                reply_chunks.append(reply_chunk)

            case ChatResponseDTO(status="response",
                                 content=ChatContentDTO(products=_products)):
                products = _products

        if not title_yielded and title_task and title_task.done():
            try:
                title = title_task.result()
            except Exception:
                title = "새로운 대화"

            _send_title = ChatResponseDTO(chat_id=chat_id,
                                          status="title",
                                          content=ChatContentDTO(message=title))
            yield f"data: {json.dumps(jsonable_encoder(_send_title), ensure_ascii=False)}\n\n"

            title_yielded = True

    assistant_content = ChatContentDTO(message="".join(reply_chunks), products=products)
    save_msg(chat_id, "assistant", jsonable_encoder(assistant_content))

    yield "data: [DONE]\n\n"


@router.post("", response_class=StreamingResponse)
async def stream_chat(
        body: ChatRequest,
        last_event_id: str | None = Header(None, convert_underscores=False),
        run_stream=Depends(get_workflow_stream),
):
    headers = {"Cache-Control": "no-cache"}

    return StreamingResponse(
        chat_events(body, run_stream),
        media_type="text/event-stream",
        headers=headers,
    )


@router.get("", response_model=ChatListResponse)
async def get_chat_list(offset: int = 0, size: int = 20):
    rows = list_chats(offset, size)
    return ChatListResponse(size=len(rows),
                            offset=offset,
                            items=[ChatPreviewDTO(**r) for r in rows])


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat_detail(chat_id: str, offset: int = 0, size: int = 20):
    rows = get_history(chat_id, offset, size)
    if not rows:
        raise HTTPException(status_code=404, detail="chat not found")
    items = [
        ChatHistoryDTO(role=r["role"], content=json.loads(r["content"])) for r in rows
    ]
    return ChatDetailResponse(size=len(items), offset=offset, items=items)
