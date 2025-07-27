from typing import Optional, TypedDict


class TavilyDocument(TypedDict):

    title: str
    content: str
    raw_content: Optional[str]
