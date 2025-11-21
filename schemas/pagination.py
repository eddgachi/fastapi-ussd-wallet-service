from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationMeta
