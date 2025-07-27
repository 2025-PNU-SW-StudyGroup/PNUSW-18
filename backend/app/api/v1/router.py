from fastapi import APIRouter
from app.api.v1.endpoints import chat

router = APIRouter()

router.include_router(chat.router, prefix="/chats", tags=["chats"])
#router.include_router(user.router, prefix="/users", tags=["users"])
#router.include_router(auth.router, prefix="/auth", tags=["auth"])
