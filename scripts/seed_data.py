"""Seed data for lookup tables — with governance refinements.

- BCS categories ship LOCKED (is_locked=True): the five standard group-wide
  categories. SKUs are synthetic; BCS/loss/machine taxonomy is real (standard
  industry terms, not proprietary data).
- Each Type of Loss carries a suggested_bcs_code: the BCS bucket the operator
  form pre-selects (operator can override).
"""

# BCS — the five standard categories, all locked.
BCS_CATEGORIES = [
    {"code": "ChangeOverTime", "description": "Time lost changing brand/SKU", "is_locked": True},
    {
        "code": "MinorStopAndSpeedLoss",
        "description": "Short stops and speed loss",
        "is_locked": True,
    },
    {
        "code": "PlannedDownTime",
        "description": "Planned maintenance / scheduled stops",
        "is_locked": True,
    },
    {"code": "Breakdown", "description": "Unplanned equipment failure", "is_locked": True},
    {
        "code": "ExternalStops",
        "description": "Stoppage outside packaging control",
        "is_locked": True,
    },
]

# Type of Loss — operational vocabulary, each with a suggested BCS bucket.
# Note CILT and Inspection Stop map to PlannedDownTime by default, but the
# operator can override (e.g. an inspection that turns into a breakdown).
LOSS_TYPES = [
    {
        "code": "ChangeOverTime",
        "description": "Changeover between products",
        "suggested_bcs_code": "ChangeOverTime",
    },
    {
        "code": "MinorStopAndSpeedLoss",
        "description": "Minor stop / speed loss",
        "suggested_bcs_code": "MinorStopAndSpeedLoss",
    },
    {
        "code": "PlannedDownTime",
        "description": "Planned maintenance",
        "suggested_bcs_code": "PlannedDownTime",
    },
    {"code": "Breakdown", "description": "Equipment breakdown", "suggested_bcs_code": "Breakdown"},
    {
        "code": "ExternalStops",
        "description": "External, not packaging-controlled",
        "suggested_bcs_code": "ExternalStops",
    },
    {
        "code": "CILT",
        "description": "Clean, Inspect, Lubricate, Tighten",
        "suggested_bcs_code": "PlannedDownTime",
    },
    {
        "code": "InspectionStop",
        "description": "Inspection-related stop",
        "suggested_bcs_code": "PlannedDownTime",
    },
]

MACHINES = [
    {"name": "Depalletizer"},
    {"name": "Rinser"},
    {"name": "FillerCrowner"},
    {"name": "Labeller"},
    {"name": "Pasteurizer"},
    {"name": "Packer"},
    {"name": "Palletizer"},
]

# Synthetic SKUs — replace on the private intranet deployment.
SKUS = [
    {"code": "Brew Malt(33cl)", "description": "Malt drink 330ml bottle"},
    {"code": "Brew Malt(60cl)", "description": "Malt drink 600ml bottle"},
    {"code": "Brew Lager(33cl)", "description": "Lager 330ml bottle"},
    {"code": "Brew Lager(50cl)", "description": "Lager 500ml bottle"},
    {"code": "Brew Stout(33cl)", "description": "Stout 330ml bottle"},
]

USERS = [
    {"username": "admin", "role": "admin", "password": "admin"},
    {"username": "operator1", "role": "operator", "password": "operator1"},
    {"username": "super1", "role": "supervisor", "password": "super1"},
]
