"""Create database schema.

Run once before first use:
    python -m scripts.init_db

Idempotent — safe to run multiple times.
"""
from app.database import Base, engine

# Importing models registers them with Base.metadata.
# Sprint 1: uncomment as models are added.
# from app.models import user, shift, production, downtime, quality, material, lookup, audit  # noqa


def main() -> None:
    print(f"Creating schema on {engine.url}...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    main()
