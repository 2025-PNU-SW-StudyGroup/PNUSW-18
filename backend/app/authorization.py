from typing import Iterable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from datetime import datetime, timedelta

from dotenv import load_dotenv

import os

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = "HS256"
TTL_HOURS = 120


def create_temp_token(subject: str) -> str:
    """임시 토큰 발급"""

    now = datetime.utcnow()
    expire = now + timedelta(hours=TTL_HOURS)
    claims = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


class JWTAuthMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app,
        exempt_paths: Iterable[str] | None = None,
    ):
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or ["/docs", "/openapi.json", "/token"])

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in self.exempt_paths:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Authorization: Bearer <token> 헤더가 필요합니다")

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(401, "유효하지 않거나 만료된 토큰입니다")

        request.state.user = payload  # 이후 핸들러에서 활용
        return await call_next(request)


if __name__ == "__main__":
    token = create_temp_token("temporary")

    print(token)  # app/auth/middleware.py
