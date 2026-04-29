from __future__ import annotations

from datetime import datetime, timezone


def _coerce_now(now: datetime | None = None) -> datetime:
    return now if now is not None else datetime.now(timezone.utc).astimezone()


def get_current_time_context(now: datetime | None = None) -> dict[str, str]:
    current = _coerce_now(now)
    hour = current.hour
    if 5 <= hour < 12:
        part_of_day = "morning"
    elif 12 <= hour < 17:
        part_of_day = "afternoon"
    elif 17 <= hour < 22:
        part_of_day = "evening"
    else:
        part_of_day = "night"

    return {
        "iso_datetime": current.isoformat(),
        "date": current.date().isoformat(),
        "time": current.strftime("%H:%M"),
        "weekday": current.strftime("%A"),
        "part_of_day": part_of_day,
    }


def describe_elapsed_time(previous: datetime, current: datetime | None = None) -> str:
    now = _coerce_now(current)
    delta = now - previous
    seconds = max(int(delta.total_seconds()), 0)
    minutes = seconds // 60
    hours = seconds // 3600
    days = delta.days

    if seconds < 120:
        return "just now"
    if minutes < 10:
        return "a few minutes ago"
    if minutes < 60:
        return "within the last hour"
    if hours < 2:
        return "about 1 hour ago"
    if hours < 24:
        return f"about {hours} hours ago"
    if days == 1:
        return "yesterday"
    return f"about {days} days ago"


def maybe_time_acknowledgment(now: datetime | None = None) -> str | None:
    current = _coerce_now(now)
    hour = current.hour
    if 0 <= hour < 5:
        return "It’s late."
    if 22 <= hour <= 23:
        return "It’s getting late."
    if 5 <= hour < 8:
        return "Still early."
    return None