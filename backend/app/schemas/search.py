from pydantic import BaseModel
from typing import List, Optional


class SearchItem(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchItem]