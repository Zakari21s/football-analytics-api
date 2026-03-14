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


def build_paginated_response(
    *,
    data: list[T],
    total_count: int,
    page: int,
    limit: int,
) -> PaginatedResponse[T]:
    """Helper to compute total_pages and construct a PaginatedResponse."""
    total_pages = (total_count + limit - 1) // limit if total_count else 0
    return PaginatedResponse[T](  # type: ignore[call-arg]
        data=data,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )
