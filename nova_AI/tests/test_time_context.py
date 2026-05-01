from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nova.core.time_context import describe_elapsed_time, get_current_time_context, maybe_time_acknowledgment



def test_get_current_time_context_maps_morning() -> None:
    ctx = get_current_time_context(datetime(2026, 4, 29, 8, 0, tzinfo=timezone.utc))
    assert ctx["part_of_day"] == "morning"



def test_get_current_time_context_maps_afternoon() -> None:
    ctx = get_current_time_context(datetime(2026, 4, 29, 14, 0, tzinfo=timezone.utc))
    assert ctx["part_of_day"] == "afternoon"



def test_get_current_time_context_maps_evening() -> None:
    ctx = get_current_time_context(datetime(2026, 4, 29, 19, 0, tzinfo=timezone.utc))
    assert ctx["part_of_day"] == "evening"



def test_get_current_time_context_maps_night() -> None:
    ctx = get_current_time_context(datetime(2026, 4, 29, 23, 0, tzinfo=timezone.utc))
    assert ctx["part_of_day"] == "night"



def test_describe_elapsed_time_for_small_delta() -> None:
    current = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)
    previous = current - timedelta(seconds=30)
    assert describe_elapsed_time(previous, current) == "just now"



def test_describe_elapsed_time_for_one_hour() -> None:
    current = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)
    previous = current - timedelta(hours=1)
    assert describe_elapsed_time(previous, current) == "about 1 hour ago"



def test_describe_elapsed_time_for_two_days() -> None:
    current = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)
    previous = current - timedelta(days=2)
    assert describe_elapsed_time(previous, current) == "about 2 days ago"



def test_maybe_time_acknowledgment_for_late_night() -> None:
    phrase = maybe_time_acknowledgment(datetime(2026, 4, 29, 23, 30, tzinfo=timezone.utc))
    assert phrase is not None



def test_maybe_time_acknowledgment_for_midday_can_be_none() -> None:
    phrase = maybe_time_acknowledgment(datetime(2026, 4, 29, 13, 0, tzinfo=timezone.utc))
    assert phrase is None