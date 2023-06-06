from enum import Enum
from typing import List
from typing import Optional

from pydantic import BaseModel


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"


class TwitterAPIRequest(BaseModel):
    method: HttpMethod
    url: str
    body: str | None = None


class SearchRequest(BaseModel):
    query: str
    sources: int
    source_max_words: int = 1000


class Source(BaseModel):
    link: str
    text: Optional[str] = None


class SearchResult(Source):
    title: str
    snippet: str


class SearchResponse(BaseModel):
    __root__: List[SearchResult]


class SourceReadRequest(BaseModel):
    link: str
    max_words: int = 1000
