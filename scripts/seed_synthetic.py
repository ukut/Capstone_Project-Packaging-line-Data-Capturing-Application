"""Synthetic data generator for the public Capstone demo deployment.

Generates realistic bottling-line shift data with deterministic seeding so the
Render demo always shows the same scenarios. Real brewery data is never used
in this repository.

Run after init_db:
    python -m scripts.seed_synthetic

Sprint 1: populates users, lookups (SKUs, machines, downtime reasons, reject categories).
Sprint 2: populates shifts and entries across several weeks of synthetic operations.
Sprint 3: generator parameters tuned so anomaly rules fire on a known subset of shifts —
          this gives a reliable scripted demo.
"""

import random
from datetime import date, timedelta

# Deterministic seed — same data every run, important for reproducible demos.
SEED = 20260712
random.seed(SEED)


# Placeholder lookups — Sprint 1 replaces with structure derived from real Excel
SAMPLE_SKUS = [
    {"code": "BTL-330-LAG", "description": "Lager 330ml bottle"},
    {"code": "BTL-500-LAG", "description": "Lager 500ml bottle"},
    {"code": "BTL-330-STO", "description": "Stout 330ml bottle"},
    {"code": "CAN-330-LAG", "description": "Lager 330ml can"},
]

SAMPLE_MACHINES = [
    "Depalletizer",
    "Rinser",
    "Filler",
    "Crowner",
    "Labeller",
    "Packer",
]

SAMPLE_DOWNTIME_REASONS = [
    "Filler jam",
    "Bottle breakage",
    "Cap feed empty",
    "Label change",
    "SKU changeover",
    "Operator break",
    "Mechanical fault",
    "Electrical fault",
    "Awaiting bottles",
    "Awaiting crowns",
]

SAMPLE_REJECT_CATEGORIES = [
    "Low fill",
    "No cap",
    "Label crooked",
    "Broken bottle",
    "Foreign object",
]

SAMPLE_USERS = [
    {"username": "admin", "role": "admin", "password": "admin"},
    {"username": "operator1", "role": "operator", "password": "operator1"},
    {"username": "operator2", "role": "operator", "password": "operator2"},
    {"username": "super1", "role": "supervisor", "password": "super1"},
]


def generate_shifts(days_back: int = 30) -> list[dict]:
    """Generate one synthetic shift per day for the last `days_back` days."""
    today = date.today()
    shifts = []
    for offset in range(days_back, 0, -1):
        shift_date = today - timedelta(days=offset)
        sku = random.choice(SAMPLE_SKUS)
        good = random.randint(8000, 14000)
        # 1.5% baseline reject rate, occasional spikes to trigger anomaly rule
        reject_rate = random.choice([0.01, 0.015, 0.02, 0.025, 0.05])
        rejects = int(good * reject_rate / (1 - reject_rate))
        shifts.append(
            {
                "date": shift_date.isoformat(),
                "sku": sku["code"],
                "good_count": good,
                "reject_count": rejects,
            }
        )
    return shifts


def main() -> None:
    print(f"Seeding synthetic data (seed={SEED})...")
    print(f"  Users:             {len(SAMPLE_USERS)}")
    print(f"  SKUs:              {len(SAMPLE_SKUS)}")
    print(f"  Machines:          {len(SAMPLE_MACHINES)}")
    print(f"  Downtime reasons:  {len(SAMPLE_DOWNTIME_REASONS)}")
    print(f"  Reject categories: {len(SAMPLE_REJECT_CATEGORIES)}")

    shifts = generate_shifts(days_back=30)
    print(f"  Generated shifts:  {len(shifts)} (30 days)")

    # Sprint 1: actually persist via repositories
    # session = SessionLocal()
    # try:
    #     UserRepository(session).bulk_create(SAMPLE_USERS)
    #     LookupRepository(session).bulk_create_skus(SAMPLE_SKUS)
    #     ... etc
    #     session.commit()
    # finally:
    #     session.close()

    print("Done. (Sprint 1: wire up persistence)")


if __name__ == "__main__":
    main()
