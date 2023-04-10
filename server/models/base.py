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
    body: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    sources: int
    summarize: bool = True
    source_tokens: int = 600


class SearchResult(BaseModel):
    query: str
    answer: str
    source: str


class SearchResponse(BaseModel):
    __root__: List[SearchResult]
