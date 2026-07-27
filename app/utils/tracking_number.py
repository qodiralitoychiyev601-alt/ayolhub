"""Generates human-readable appeal tracking numbers, e.g. GLS-2026-000001."""

from datetime import datetime


def generate_tracking_number(prefix: str, sequence_number: int, year: int | None = None) -> str:
    """
    sequence_number should be the running total count of appeals + 1,
    computed by the caller from the database (AppealRepository.count_all()).
    """
    year = year or datetime.now().year
    return f"{prefix}-{year}-{sequence_number:06d}"
