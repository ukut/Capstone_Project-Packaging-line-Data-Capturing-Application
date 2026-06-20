"""Loss-classification service.

Two small pieces of business logic that support the governance refinements:

1. suggest_bcs_for_loss_type(): given a Type of Loss, return the BCS category
   the operator form should pre-select. The operator may override it.

2. assert_bcs_editable(): guards admin edits to BCS categories. A locked BCS
   category cannot be modified or deactivated except by an admin who explicitly
   passes is_admin=True. This enforces the "BCS is a controlled standard" rule
   in code, not just by convention.
"""


class LockedCategoryError(Exception):
    """Raised when a non-admin attempts to modify a locked BCS category."""


def suggest_bcs_for_loss_type(loss_type, bcs_by_code: dict):
    """Return the suggested BCSCategory for a given LossType, or None.

    Args:
        loss_type: a LossType instance (has .suggested_bcs_code)
        bcs_by_code: mapping of BCS code -> BCSCategory instance

    Returns:
        The suggested BCSCategory, or None if no mapping exists.
    """
    code = getattr(loss_type, "suggested_bcs_code", None)
    if not code:
        return None
    return bcs_by_code.get(code)


def assert_bcs_editable(bcs_category, *, is_admin: bool) -> None:
    """Raise LockedCategoryError if a non-admin tries to edit a locked category.

    Locked BCS categories are part of the group standard. Only an admin may
    change them, and even then it should be rare and deliberate.
    """
    if getattr(bcs_category, "is_locked", False) and not is_admin:
        raise LockedCategoryError(
            f"BCS category '{bcs_category.code}' is a locked standard "
            "and can only be modified by an admin."
        )
