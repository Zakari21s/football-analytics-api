"""Common response shapes: pagination."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list: data, page, total_pages, total_count."""

    data: list[T]
    page: int
    total_pages: int
    total_count: int
