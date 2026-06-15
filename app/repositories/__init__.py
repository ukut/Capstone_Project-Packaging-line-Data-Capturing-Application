"""Repository pattern: all data access goes through these classes.

Concrete repositories added in Sprint 1:
    user_repo.py      — auth queries
    shift_repo.py     — shift lifecycle queries
    production_repo.py
    downtime_repo.py
    quality_repo.py
    material_repo.py
    lookup_repo.py    — read-only access to reference tables
    audit_repo.py     — append-only audit log
"""

from app.repositories.base import BaseRepository

__all__ = ["BaseRepository"]
