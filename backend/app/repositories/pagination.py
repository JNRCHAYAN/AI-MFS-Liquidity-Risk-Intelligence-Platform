"""Pagination and stable sorting primitives shared by every repository.

Rules enforced here (see AGENTS.md and the build plan section 5):

* Every list query is paginated and bounded. ``MAX_PAGE_LIMIT`` is a hard cap;
  requesting more is a validation error, not a silent clamp, so a caller
  cannot accidentally fetch the whole table.
* Sorting is always *total*: the repository appends a unique tie-breaker
  (the primary key) so two rows with equal sort keys cannot swap between
  pages, which would duplicate or drop rows across pagination boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar

#: Default and maximum page sizes. 200 keeps a single page's payload bounded.
DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 200


class SortOrder(StrEnum):
    """Sort direction for a whitelisted sortable field."""

    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class SortSpec:
    """A sort key. ``field`` must exist in the repository's sortable map."""

    field: str
    order: SortOrder = SortOrder.DESC

    def __post_init__(self) -> None:
        if not self.field or not self.field.isidentifier():
            raise ValueError(f"Invalid sort field {self.field!r}")


@dataclass(frozen=True)
class PageParams:
    """Validated pagination request."""

    limit: int = DEFAULT_PAGE_LIMIT
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.limit > MAX_PAGE_LIMIT:
            raise ValueError(f"limit must be <= {MAX_PAGE_LIMIT}")
        if self.offset < 0:
            raise ValueError("offset must be >= 0")


ItemT = TypeVar("ItemT")


@dataclass
class Page(Generic[ItemT]):
    """A page of results plus the total count for the same filter."""

    items: list[ItemT]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        """Whether rows exist beyond this page."""
        return self.offset + len(self.items) < self.total
