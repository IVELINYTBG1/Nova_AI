import pytest
from nova.core.reactions import ReactionContext, build_reaction_context


# ── defaults ────────────────────────────────────────────────────────────────

def test_default_returns_neutral():
    result = build_reaction_context("hello")
    assert result.mode == "neutral"
    assert result.note == ""


def test_none_text_returns_neutral():
    result = build_reaction_context(None)
    assert result.mode == "neutral"


# ── identity triggers ────────────────────────────────────────────────────────

def test_warm_return_when_recognized_after_long_absence():
    result = build_reaction_context(
        "hey nova",
        identity_status="recognized",
        minutes_since_seen=25,
    )
    assert result.mode == "warm_return"
    assert result.note != ""


def test_no_warm_return_when_absence_too_short():
    result = build_reaction_context(
        "hey nova",
        identity_status="recognized",
        minutes_since_seen=10,
    )
    assert result.mode == "neutral"


def test_uncertain_identity_trigger():
    result = build_reaction_context(
        "can you see me",
        identity_status="uncertain",
    )
    assert result.mode == "uncertain_identity"
    assert result.note != ""


# ── wellbeing triggers ────────────────────────────────────────────────────────

@pytest.mark.parametrize("phrase", [
    "i'm so tired",
    "i am exhausted",
    "i'm burned out",
    "i cant keep going",
    "i can't keep going",
])
def test_gentle_concern_on_fatigue_phrases(phrase):
    result = build_reaction_context(phrase)
    assert result.mode == "gentle_concern"
    assert result.note != ""


def test_no_concern_on_normal_text():
    result = build_reaction_context("what time is it")
    assert result.mode == "neutral"


# ── risk trigger ─────────────────────────────────────────────────────────────

def test_protective_on_high_risk():
    result = build_reaction_context(
        "delete everything",
        risk_level="high",
    )
    assert result.mode == "protective"
    assert result.note != ""


def test_no_protective_on_low_risk():
    result = build_reaction_context(
        "delete everything",
        risk_level="low",
    )
    assert result.mode == "neutral"


# ── dataclass sanity ─────────────────────────────────────────────────────────

def test_reaction_context_defaults():
    rc = ReactionContext()
    assert rc.mode == "neutral"
    assert rc.note == ""


def test_reaction_context_custom():
    rc = ReactionContext(mode="protective", note="Be careful.")
    assert rc.mode == "protective"
    assert rc.note == "Be careful."