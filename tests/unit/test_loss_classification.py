"""Tests for the loss-classification governance refinements."""
import pytest

from app.services.loss_classification import (
    LockedCategoryError,
    assert_bcs_editable,
    suggest_bcs_for_loss_type,
)


class FakeLossType:
    def __init__(self, suggested_bcs_code):
        self.suggested_bcs_code = suggested_bcs_code


class FakeBCS:
    def __init__(self, code, is_locked=True):
        self.code = code
        self.is_locked = is_locked


# ---------- suggested mapping ----------

def test_suggest_returns_mapped_bcs():
    bcs_by_code = {"Breakdown": FakeBCS("Breakdown"), "PlannedDownTime": FakeBCS("PlannedDownTime")}
    lt = FakeLossType("PlannedDownTime")
    result = suggest_bcs_for_loss_type(lt, bcs_by_code)
    assert result.code == "PlannedDownTime"


def test_suggest_returns_none_when_no_mapping():
    lt = FakeLossType(None)
    assert suggest_bcs_for_loss_type(lt, {}) is None


def test_suggest_returns_none_when_code_not_found():
    lt = FakeLossType("NonExistent")
    assert suggest_bcs_for_loss_type(lt, {"Breakdown": FakeBCS("Breakdown")}) is None


def test_cilt_suggests_planned_downtime_but_is_overridable():
    # CILT maps to PlannedDownTime by default — but this is only a suggestion.
    bcs_by_code = {"PlannedDownTime": FakeBCS("PlannedDownTime"), "Breakdown": FakeBCS("Breakdown")}
    cilt = FakeLossType("PlannedDownTime")
    suggested = suggest_bcs_for_loss_type(cilt, bcs_by_code)
    assert suggested.code == "PlannedDownTime"
    # The operator could still choose Breakdown instead — nothing prevents it.


# ---------- lock enforcement ----------

def test_locked_bcs_blocks_non_admin():
    locked = FakeBCS("Breakdown", is_locked=True)
    with pytest.raises(LockedCategoryError):
        assert_bcs_editable(locked, is_admin=False)


def test_locked_bcs_allows_admin():
    locked = FakeBCS("Breakdown", is_locked=True)
    # Should not raise.
    assert_bcs_editable(locked, is_admin=True)


def test_unlocked_bcs_allows_anyone():
    unlocked = FakeBCS("CustomCategory", is_locked=False)
    # Should not raise even for non-admin.
    assert_bcs_editable(unlocked, is_admin=False)
