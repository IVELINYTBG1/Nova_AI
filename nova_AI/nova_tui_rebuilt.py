#!/usr/bin/env python3
"""
Nova Terminal UI

Run from your Nova project root:
    python nova_tui_rebuilt.py

Set NOVA_LIVE = True to wire this UI to your real backend.
This version builds Nova once at startup and reuses that instance.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Input, Static

NOVA_LIVE = True


@dataclass
class BackendStatus:
    live: bool = False
    ready: bool = False
    llm_name: str = "stub"
    stt_name: str = "stub"
    tts_name: str = "stub"
    vision_name: str = "stub"
    camera_ready: bool = False
    memory_line: str = "Memory: unavailable"
    error: str | None = None


class NovaBackend:
    def __init__(self, live: bool = False) -> None:
        self.live = live
        self.app: Any | None = None
        self.status = BackendStatus(live=live)

    async def initialize(self) -> None:
        if not self.live:
            self.status = BackendStatus(
                live=False,
                ready=True,
                llm_name="groq_oss_120b (stub)",
                stt_name="groq_gpt_turbo_stt (stub)",
                tts_name="fish_speech_api (stub)",
                vision_name="llama_scout (stub)",
                camera_ready=False,
                memory_line="Memory: stub mode",
            )
            return

        try:
            from nova.bootstrap import build_nova  # type: ignore
            from nova.config.settings import load_settings  # type: ignore
        except Exception as exc:
            self.status.error = f"Import failed: {exc}"
            return

        try:
            settings = await asyncio.to_thread(load_settings)
            self.app = await asyncio.to_thread(build_nova, settings)
            registry = getattr(self.app, "provider_registry", None)
            camera_service = getattr(self.app, "camera_service", None)

            llm_name = "unknown"
            stt_name = "unknown"
            tts_name = "unknown"
            vision_name = "unknown"

            if registry is not None:
                try:
                    llm_name = getattr(registry.get_primary_llm(), "model_name", None) or getattr(
                        registry.get_primary_llm(), "name", "unknown"
                    )
                except Exception:
                    pass
                try:
                    stt_name = getattr(registry.get_stt(), "model_name", None) or getattr(
                        registry.get_stt(), "name", "unknown"
                    )
                except Exception:
                    pass
                try:
                    tts_name = getattr(registry.get_tts(), "model_name", None) or getattr(
                        registry.get_tts(), "name", "unknown"
                    )
                except Exception:
                    pass
                try:
                    vision_name = getattr(registry.get_vision(), "model_name", None) or getattr(
                        registry.get_vision(), "name", "unknown"
                    )
                except Exception:
                    pass

            memory_line = "Memory: unavailable"
            try:
                if self.app is not None and hasattr(self.app, "memory_stats_line"):
                    memory_line = await asyncio.to_thread(self.app.memory_stats_line)
            except Exception:
                pass

            camera_ready = False
            try:
                if camera_service is not None and hasattr(camera_service, "is_available"):
                    camera_ready = bool(camera_service.is_available())
            except Exception:
                pass

            self.status = BackendStatus(
                live=True,
                ready=True,
                llm_name=llm_name,
                stt_name=stt_name,
                tts_name=tts_name,
                vision_name=vision_name,
                camera_ready=camera_ready,
                memory_line=memory_line,
            )
        except Exception as exc:
            self.status.error = f"Backend init failed: {exc}"

    async def reply(self, text: str) -> str:
        if not self.live:
            await asyncio.sleep(0.2 + random.random() * 0.35)
            return self._stub_response(text)

        if self.app is None:
            return f"[error] Nova backend not ready: {self.status.error or 'unknown error'}"

        try:
            return await asyncio.to_thread(self.app.handle_text, text)
        except Exception as exc:
            return f"[error] Nova backend failed: {exc}"

    @staticmethod
    def _stub_response(text: str) -> str:
        stubs: dict[str, list[str]] = {
            "greet": [
                "Yes. I'm here.",
                "Online. What do you need?",
                "Running. Go ahead.",
            ],
            "feeling": [
                "Steady. Energy high, engagement locked in.",
                "Calm. Present. Core systems are stable.",
                "Running well. No major faults detected.",
            ],
            "recognize": [
                "Identity gate is stubbed in this mode. Live verification is offline.",
                "I can't verify identity in stub mode.",
                "Recognition needs live backend mode.",
            ],
            "memory": [
                "Memory is stubbed here. Use live mode for real recall.",
                "I can simulate memory, but not query your real store in stub mode.",
                "Live vector memory is not connected in this mode.",
            ],
            "plan": [
                "Possible plan:\n1. Verify routing\n2. Test memory\n3. Check vision\n4. Clean model config\n5. Harden the UI loop",
            ],
            "default": [
                "Understood.",
                "Acknowledged.",
                "Processing that now.",
                "That needs more live context to answer precisely.",
            ],
        }
        lo = text.lower()
        if any(k in lo for k in ["there", "hello", "hey", "ping", "hi"]):
            return random.choice(stubs["greet"])
        if any(k in lo for k in ["feeling", "state", "how are", "energy", "mood"]):
            return random.choice(stubs["feeling"])
        if any(k in lo for k in ["recognize", "who am i", "is this me", "see me"]):
            return random.choice(stubs["recognize"])
        if any(k in lo for k in ["remember", "memory", "what do you know"]):
            return random.choice(stubs["memory"])
        if any(k in lo for k in ["plan", "steps", "approach"]):
            return random.choice(stubs["plan"])
        return random.choice(stubs["default"])


CSS = """
Screen {
    background: #05080f;
    color: #e8f4f8;
}

#header {
    height: 3;
    background: #080d18;
    border-bottom: tall #00e5ff 30%;
    padding: 0 2;
    layout: horizontal;
    align: center middle;
}

#logo {
    color: #e8f4f8;
    text-style: bold;
    width: auto;
}

#logo-sub {
    color: #007a99;
    width: auto;
    margin-left: 2;
}

#status-row {
    width: 1fr;
    layout: horizontal;
    align: right middle;
}

.status-pill {
    color: #6a8a99;
    width: auto;
    margin-left: 2;
}

.status-pill.active {
    color: #00ff9f;
}

.status-pill.cyan {
    color: #00e5ff;
}

.status-pill.warn {
    color: #ffaa00;
}

#provbar {
    height: 1;
    background: #080d18;
    border-bottom: tall #00e5ff 15%;
    padding: 0 2;
    layout: horizontal;
    align: left middle;
}

.provtag {
    color: #4a6a7a;
    width: auto;
    margin-right: 3;
}

.provtag.active {
    color: #007a99;
}

.provtag.warn {
    color: #ffaa00;
}

#statebar {
    height: 1;
    background: #060b14;
    border-bottom: tall #00e5ff 10%;
    padding: 0 2;
}

#log {
    background: #05080f;
    border: none;
    padding: 1 2;
    height: 1fr;
}

#inputzone {
    height: 5;
    background: #0a1020;
    border-top: tall #00e5ff 25%;
    padding: 1 2;
}

#input-row {
    height: 1;
    layout: horizontal;
    align: left middle;
    margin-bottom: 1;
}

#prompt-label {
    color: #00e5ff;
    width: auto;
    text-style: bold;
}

#user-input {
    background: transparent;
    border: none;
    color: #e8f4f8;
    width: 1fr;
    padding: 0 1;
}

#input-hint {
    color: #2a4a5a;
    height: 1;
}

Footer {
    background: #080d18;
    color: #2a4a5a;
    border-top: tall #00e5ff 10%;
}
"""


class MessageLog(ScrollableContainer):
    DEFAULT_CSS = "MessageLog { height: 1fr; }"

    def add_sys(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.mount(Static(f"[dim #2a4a5a]{ts}[/] [#2a4a5a]SYS ›[/] [#3a5a6a]{text}[/]", markup=True))
        self.scroll_end(animate=False)

    def add_user(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.mount(Static(f"[dim #2a4a5a]{ts}[/] [#6a8a99]You ›[/] [#a0c4d0]{text}[/]", markup=True))
        self.scroll_end(animate=False)

    def add_nova(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        lines = text.splitlines() or [""]
        self.mount(Static(f"[dim #2a4a5a]{ts}[/] [bold #00e5ff]Nova ›[/] [#e8f4f8]{lines[0]}[/]", markup=True))
        for line in lines[1:]:
            self.mount(Static(f" [#e8f4f8]{line}[/]", markup=True))
        self.scroll_end(animate=False)

    def add_thinking(self) -> Static:
        widget = Static(" [italic #007a99]thinking...[/]", markup=True)
        self.mount(widget)
        self.scroll_end(animate=False)
        return widget

    def clear_log(self) -> None:
        for child in list(self.children):
            child.remove()


class StateBar(Static):
    energy: reactive[float] = reactive(0.92)
    engagement: reactive[float] = reactive(0.82)
    patience: reactive[float] = reactive(0.98)
    mood: reactive[float] = reactive(0.73)

    def _bar(self, value: float, width: int = 8) -> str:
        filled = round(value * width)
        return "█" * filled + "░" * (width - filled)

    def render(self) -> str:
        def color_for(v: float) -> str:
            if v >= 0.7:
                return "#00ff9f"
            if v >= 0.4:
                return "#00e5ff"
            return "#ffaa00"

        def fmt(label: str, value: float) -> str:
            return f"[#4a6a7a]{label}[/] [{color_for(value)}]{self._bar(value)} {int(value * 100):3d}%[/]"

        return (
            f" {fmt('ENERGY', self.energy)} "
            f"{fmt('ENGAGE', self.engagement)} "
            f"{fmt('PATIENCE', self.patience)} "
            f"{fmt('MOOD', self.mood)}"
        )

    def update_on_message(self, msg_len: int) -> None:
        self.energy = max(0.05, self.energy - (0.06 if msg_len >= 240 else 0.02))
        self.engagement = min(1.0, self.engagement + 0.08)
        self.patience = max(0.0, self.patience - (0.03 if msg_len <= 3 else 0.005))
        self.mood = min(1.0, self.mood + (self.engagement - 0.5) * 0.04)


class NovaTUI(App):
    CSS = CSS
    TITLE = "NOVA"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
        Binding("f1", "ping", "Ping"),
        Binding("f2", "do_plan", "Plan"),
        Binding("f3", "do_memory", "Memory"),
        Binding("f4", "do_recognize", "Recognize"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.backend = NovaBackend(live=NOVA_LIVE)
        self._statebar: StateBar | None = None
        self._log: MessageLog | None = None
        self._provider_labels: dict[str, Static] = {}
        self._camera_label: Static | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Static("◈ NOVA", id="logo")
            yield Static("modular ai orchestrator", id="logo-sub")
            with Horizontal(id="status-row"):
                yield Static("● booting", id="status-live", classes="status-pill warn")
                yield Static("● backend", id="status-backend", classes="status-pill")
                yield Static("● memory", id="status-memory", classes="status-pill")

        with Horizontal(id="provbar"):
            self._provider_labels["llm"] = Static("llm: pending", classes="provtag")
            self._provider_labels["stt"] = Static("stt: pending", classes="provtag")
            self._provider_labels["tts"] = Static("tts: pending", classes="provtag")
            self._provider_labels["vision"] = Static("vision: pending", classes="provtag")
            self._camera_label = Static("camera: pending", classes="provtag")
            yield self._provider_labels["llm"]
            yield self._provider_labels["stt"]
            yield self._provider_labels["tts"]
            yield self._provider_labels["vision"]
            yield self._camera_label

        self._statebar = StateBar(id="statebar")
        yield self._statebar

        self._log = MessageLog(id="log")
        yield self._log

        with Vertical(id="inputzone"):
            with Horizontal(id="input-row"):
                yield Static("You ›", id="prompt-label")
                yield Input(placeholder="say something real and I'll respond.", id="user-input")
            yield Static(
                "[dim]Enter[/] send [dim]Ctrl+L[/] clear [dim]F1[/] ping [dim]F2[/] plan [dim]F3[/] memory [dim]F4[/] recognize [dim]Ctrl+C[/] quit",
                id="input-hint",
                markup=True,
            )
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._boot_sequence(), exclusive=True)
        self.query_one("#user-input", Input).focus()

    async def _boot_sequence(self) -> None:
        assert self._log is not None
        self._log.add_sys("runtime initialized")
        self._log.add_sys("loading backend...")
        await self.backend.initialize()
        self._apply_backend_status()

        if self.backend.status.ready:
            self._log.add_sys(f"primary llm: {self.backend.status.llm_name}")
            self._log.add_sys(f"stt: {self.backend.status.stt_name} · tts: {self.backend.status.tts_name}")
            self._log.add_sys(f"vision: {self.backend.status.vision_name}")
            self._log.add_sys(self.backend.status.memory_line)
            self._log.add_sys(f"camera: {'ready' if self.backend.status.camera_ready else 'unavailable'}")
            self._log.add_nova("Online.")
        else:
            self._log.add_sys(f"backend failed: {self.backend.status.error or 'unknown error'}")
            self._log.add_nova("I booted into degraded mode.")

    def _apply_backend_status(self) -> None:
        status_live = self.query_one("#status-live", Static)
        status_backend = self.query_one("#status-backend", Static)
        status_memory = self.query_one("#status-memory", Static)
        s = self.backend.status

        if s.ready:
            status_live.update("● online")
            status_live.set_classes("status-pill active")
            status_backend.update("● live" if s.live else "● stub")
            status_backend.set_classes("status-pill cyan")
            status_memory.update("● memory")
            status_memory.set_classes("status-pill cyan")
        else:
            status_live.update("● degraded")
            status_live.set_classes("status-pill warn")
            status_backend.update("● failed")
            status_backend.set_classes("status-pill warn")
            status_memory.update("● unknown")
            status_memory.set_classes("status-pill")

        self._provider_labels["llm"].update(f"llm: {s.llm_name}")
        self._provider_labels["stt"].update(f"stt: {s.stt_name}")
        self._provider_labels["tts"].update(f"tts: {s.tts_name}")
        self._provider_labels["vision"].update(f"vision: {s.vision_name}")
        assert self._camera_label is not None
        self._camera_label.update(f"camera: {'ready' if s.camera_ready else 'unavailable'}")

    @on(Input.Submitted, "#user-input")
    async def on_submit(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        inp = self.query_one("#user-input", Input)
        inp.value = ""
        assert self._log is not None and self._statebar is not None
        self._log.add_user(text)
        self._statebar.update_on_message(len(text))
        thinking = self._log.add_thinking()
        reply = await self.backend.reply(text)
        thinking.remove()
        self._log.add_nova(reply)
        inp.focus()

    def action_clear(self) -> None:
        assert self._log is not None
        self._log.clear_log()
        self._log.add_sys("session cleared")

    def action_ping(self) -> None:
        inp = self.query_one("#user-input", Input)
        inp.value = "are you there Nova"
        inp.action_submit()

    def action_do_plan(self) -> None:
        inp = self.query_one("#user-input", Input)
        inp.value = "plan steps to improve Nova's orchestrator"
        inp.action_submit()

    def action_do_memory(self) -> None:
        inp = self.query_one("#user-input", Input)
        inp.value = "what do you remember"
        inp.action_submit()

    def action_do_recognize(self) -> None:
        inp = self.query_one("#user-input", Input)
        inp.value = "do you recognize me"
        inp.action_submit()


if __name__ == "__main__":
    NovaTUI().run()