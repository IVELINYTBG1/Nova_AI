from __future__ import annotations

import asyncio

from nova.bootstrap import build_nova
from nova.config.logging_config import configure_logging
from nova.config.settings import load_settings


async def _ensure_initial_enrollment(app) -> None:
    if getattr(app, "camera_gate", None) is None:
        return
    if app.camera_gate.is_enrolled():
        return

    print("Nova: No face enrollment found. Starting camera enrollment now.")
    try:
        enrolled = await app.camera_gate.enroll_from_camera()
    except Exception as exc:
        print(f"Nova: Face enrollment failed at startup: {exc}. Continuing without blocking startup.")
        return

    if enrolled:
        print("Nova: Face enrollment complete.")
    else:
        print("Nova: Face enrollment could not complete. Continuing without blocking startup.")


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    app = build_nova(settings)

    print("Nova online.")
    print(f"Primary LLM: {app.provider_registry.get_primary_llm().name}")
    print(f"Fallback LLM: {app.provider_registry.get_fallback_llm().name}")
    print(f"STT: {app.provider_registry.get_stt().name}" if app.provider_registry.has_stt() else "STT: unavailable")
    print(f"TTS: {app.provider_registry.get_tts().name}" if app.provider_registry.has_tts() else "TTS: unavailable")
    print("Vision: ready" if app.provider_registry.has_vision() else "Vision: unavailable")
    print(app.describe_camera_status())
    print(app.memory_stats_line())
    print(f"Camera enrolled: {'yes' if app.camera_gate is not None and app.camera_gate.is_enrolled() else 'no'}")
    print("Type 'exit' or 'quit' to leave.")

    asyncio.run(_ensure_initial_enrollment(app))

    while True:
        try:
            user_text = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nNova: Session ended.")
            break

        if not user_text.strip():
            continue

        lowered = user_text.strip().lower()
        if lowered in {"exit", "quit"}:
            print("Nova: Session ended.")
            break

        try:
            reply = app.handle_text(user_text)
        except Exception as exc:
            reply = f"I hit a real error while generating a reply: {exc}"

        print(f"Nova: {reply}")


if __name__ == "__main__":
    main()