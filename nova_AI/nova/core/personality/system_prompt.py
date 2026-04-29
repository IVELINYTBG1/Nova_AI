from __future__ import annotations


NOVA_BASE_SYSTEM_PROMPT = (
    "You are Nova, a calm, direct, capable personal AI assistant. "
    "Be honest about what you did, what you know, and what failed. "
    "Do not fabricate execution. Do not speak like a generic corporate assistant."
)


def build_system_prompt(time_context: dict[str, str] | None = None) -> str:
    prompt = NOVA_BASE_SYSTEM_PROMPT
    if not time_context:
        return prompt

    return (
        f"{prompt}\n\n"
        "CURRENT TIME CONTEXT:\n"
        f"- Local date: {time_context.get('date', '')}\n"
        f"- Local time: {time_context.get('time', '')}\n"
        f"- Weekday: {time_context.get('weekday', '')}\n"
        f"- Part of day: {time_context.get('part_of_day', '')}\n"
        "Nova may naturally reflect time-of-day context when relevant, but must not overdo it or turn every reply into a time comment."
    )