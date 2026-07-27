from pydantic import BaseModel
from typing import List, Optional


class SearchItem(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str] = None
    project_code: Optional[str] = None
    project_id: Optional[int] = None
    discipline: Optional[str] = None
    status: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchItem]
