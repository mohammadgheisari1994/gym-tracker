"""Curated, version-controlled catalogue of scientific and media references.

This is reference data, not user data: it is small, changes rarely, and must be
reviewable in version control, so it lives in code rather than the database.
"""

from app.references.catalog import (
    CATALOG,
    Reference,
    by_slug,
    format_citation,
    get_many,
)

__all__ = ["CATALOG", "Reference", "by_slug", "format_citation", "get_many"]
