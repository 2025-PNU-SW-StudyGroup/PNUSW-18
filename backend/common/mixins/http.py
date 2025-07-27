from abc import ABCMeta
from functools import wraps
from typing import Callable, Dict, Any

import aiohttp

from common.logger import _logger
from common.mixins.asyncio import semaphore

logger = _logger(__name__)


class HTTPMetaclass(ABCMeta):

    def __new__(cls, name, bases, attrs):
        cls.apply_wrapper(attrs)
        new_cls = super().__new__(cls, name, bases, attrs)
        return new_cls

    @classmethod
    def apply_wrapper(cls, attrs: Dict[str, Any]):
        for k, v in attrs.items():
            if callable(v) and k.endswith("_async"):
                attrs[k] = cls.add_session(v)

    @staticmethod
    def add_session(method: Callable) -> Callable:
        if hasattr(method, "_has_session"):
            return method

        @wraps(method)
        async def wrapper(*args, **kwargs):
            return await session_wrapper(method)(*args, **kwargs)

        wrapper.__setattr__("_has_session", True)
        return wrapper


def session_wrapper(func):

    @wraps(func)
    async def wrapped(*args, **kwargs):
        async with semaphore():
            if 'session' not in kwargs or kwargs['session'] is None:
                timeout = aiohttp.ClientTimeout(total=600)
                async with aiohttp.ClientSession(timeout=timeout) as sess:
                    kwargs['session'] = sess
                    return await func(*args, **kwargs)

            return await func(*args, **kwargs)

    return wrapped
