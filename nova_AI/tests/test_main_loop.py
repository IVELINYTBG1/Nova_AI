from __future__ import annotations

from types import SimpleNamespace

import importlib
import sys
import types

real_bootstrap = importlib.import_module("nova.bootstrap")
NovaApp = real_bootstrap.NovaApp

fake_bootstrap = types.ModuleType("nova.bootstrap")
fake_bootstrap.build_nova = lambda settings: None
sys.modules["nova.bootstrap"] = fake_bootstrap

import nova.main as main_module


class FakeCameraGate:
    def __init__(self, *, enrolled: bool, verify_result: bool = True, enroll_result: bool = True) -> None:
        self._enrolled = enrolled
        self._verify_result = verify_result
        self._enroll_result = enroll_result
        self.verify_calls = 0
        self.enroll_calls = 0
        self._last_verified_ok = None
        self._last_verified_at = None

    def is_enrolled(self) -> bool:
        return self._enrolled

    async def verify(self) -> bool:
        self.verify_calls += 1
        return self._verify_result

    async def enroll_from_camera(self) -> bool:
        self.enroll_calls += 1
        if self._enroll_result:
            self._enrolled = True
        return self._enroll_result


class FakeRegistry:
    def get_primary_llm(self):
        return SimpleNamespace(name="primary")

    def get_fallback_llm(self):
        return SimpleNamespace(name="fallback")

    def has_stt(self) -> bool:
        return False

    def has_tts(self) -> bool:
        return False

    def has_vision(self) -> bool:
        return True


class FakeCameraService:
    def __init__(self, available: bool = True, frame: bytes | None = b"frame") -> None:
        self.available = available
        self.frame = frame
        self.calls = 0

    def is_available(self) -> bool:
        return self.available

    def capture_frame_bytes(self) -> bytes | None:
        self.calls += 1
        return self.frame


class FakeIdentityGate:
    def __init__(self, decision=None, should_raise: Exception | None = None) -> None:
        self._enrolled_reference_image = b"ref"
        self.decision = decision
        self.should_raise = should_raise
        self.calls = 0

    async def verify_candidate(self, candidate_image: bytes):
        self.calls += 1
        if self.should_raise is not None:
            raise self.should_raise
        return self.decision


class FakeVectorMemory:
    def __init__(self, recalled: list[dict] | None = None) -> None:
        self.recalled = recalled or []
        self.turns: list[tuple[str, str]] = []
        self.facts: list[str] = []

    def store_turn(self, role: str, content: str) -> None:
        self.turns.append((role, content))

    def recall(self, query: str, n: int = 3) -> list[dict]:
        return self.recalled[:n]

    def search_facts(self, query: str, n: int = 3) -> list[dict]:
        return []

    def store_fact(self, content: str, topic: str = "user_context") -> None:
        self.facts.append(content)

    def stats(self) -> dict[str, int]:
        return {"conversation_turns": len(self.turns), "stored_facts": len(self.facts)}


class FakePresenceLoop:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def run(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class FakeApp:
    def __init__(self, camera_gate: FakeCameraGate, reply: str = "ok") -> None:
        self.camera_gate = camera_gate
        self.provider_registry = FakeRegistry()
        self._reply = reply
        self.handled_inputs: list[str] = []
        self._presence_started = False
        self._presence_stopped = False

    def describe_camera_status(self) -> str:
        return "Camera: ready"

    def memory_stats_line(self) -> str:
        return "Memory: 0 conversation turns, 0 stored facts"

    def handle_text(self, text: str) -> str:
        self.handled_inputs.append(text)
        return self._reply

    def start_presence_loop(self) -> None:
        self._presence_started = True

    def stop_presence_loop(self) -> None:
        self._presence_stopped = True


def test_main_loop_allows_response_when_camera_gate_confirms(monkeypatch, capsys) -> None:
    app = FakeApp(FakeCameraGate(enrolled=True, verify_result=True), reply="Hello.")
    inputs = iter(["hello", "exit"])

    monkeypatch.setattr(main_module, "build_nova", lambda settings: app)
    monkeypatch.setattr(main_module, "load_settings", lambda: SimpleNamespace(log_level="INFO"))
    monkeypatch.setattr(main_module, "configure_logging", lambda level: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    main_module.main()

    out = capsys.readouterr().out
    assert "Nova: Hello." in out
    assert "Memory: 0 conversation turns, 0 stored facts" in out
    assert app.handled_inputs == ["hello"]


def test_main_loop_enrolls_on_first_boot_if_not_enrolled(monkeypatch, capsys) -> None:
    camera_gate = FakeCameraGate(enrolled=False, verify_result=True, enroll_result=True)
    app = FakeApp(camera_gate, reply="Hello.")
    inputs = iter(["exit"])

    monkeypatch.setattr(main_module, "build_nova", lambda settings: app)
    monkeypatch.setattr(main_module, "load_settings", lambda: SimpleNamespace(log_level="INFO"))
    monkeypatch.setattr(main_module, "configure_logging", lambda level: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    main_module.main()

    out = capsys.readouterr().out
    assert "Nova: No face enrollment found. Starting camera enrollment now." in out
    assert "Nova: Face enrollment complete." in out
    assert camera_gate.enroll_calls == 1


def test_recognition_question_triggers_identity_gate_immediately() -> None:
    from nova.core.identity_gate import IdentityDecision

    app = NovaApp(
        orchestrator=SimpleNamespace(handle_turn=lambda turn: SimpleNamespace(text="generic")),
        io_membrane=SimpleNamespace(_language_layer=SimpleNamespace(detect=lambda text: "en"), _settings=SimpleNamespace(user_id="boss", session_id="session")),
        registry=SimpleNamespace(),
        execution_service=SimpleNamespace(),
        queue=SimpleNamespace(),
        model_router=SimpleNamespace(),
        provider_registry=FakeRegistry(),
        camera_service=FakeCameraService(),
        identity_gate=FakeIdentityGate(decision=IdentityDecision(True, 0.95, False, "match")),
        camera_gate=FakeCameraGate(enrolled=True),
        vector_memory=None,
        nova_state=None,
        presence_loop=None,
    )

    reply = app.handle_text("do you recognize me")

    assert "Yes. I recognize you" in reply
    assert app.identity_gate.calls == 1


def test_unrelated_question_does_not_trigger_direct_identity_reply() -> None:
    handled: list[str] = []
    app = NovaApp(
        orchestrator=SimpleNamespace(handle_turn=lambda turn: handled.append(turn.text) or SimpleNamespace(text="general reply")),
        io_membrane=SimpleNamespace(_language_layer=SimpleNamespace(detect=lambda text: "en"), _settings=SimpleNamespace(user_id="boss", session_id="session")),
        registry=SimpleNamespace(),
        execution_service=SimpleNamespace(),
        queue=SimpleNamespace(),
        model_router=SimpleNamespace(),
        provider_registry=FakeRegistry(),
        camera_service=FakeCameraService(),
        identity_gate=FakeIdentityGate(should_raise=RuntimeError("should not be called")),
        camera_gate=FakeCameraGate(enrolled=True),
        vector_memory=None,
        nova_state=None,
        presence_loop=None,
    )

    reply = app.handle_text("tell me the weather")

    assert reply == "general reply"
    assert handled == ["tell me the weather"]


def test_store_turn_called_after_response() -> None:
    vector_memory = FakeVectorMemory()
    app = NovaApp(
        orchestrator=SimpleNamespace(handle_turn=lambda turn: SimpleNamespace(text="general reply")),
        io_membrane=SimpleNamespace(_language_layer=SimpleNamespace(detect=lambda text: "en"), _settings=SimpleNamespace(user_id="boss", session_id="session")),
        registry=SimpleNamespace(),
        execution_service=SimpleNamespace(),
        queue=SimpleNamespace(),
        model_router=SimpleNamespace(),
        provider_registry=FakeRegistry(),
        camera_service=FakeCameraService(),
        identity_gate=None,
        camera_gate=None,
        vector_memory=vector_memory,
        nova_state=None,
        presence_loop=None,
    )

    reply = app.handle_text("tell me the weather")

    assert reply == "general reply"
    assert vector_memory.turns == [
        ("user", "tell me the weather"),
        ("nova", "general reply"),
    ]