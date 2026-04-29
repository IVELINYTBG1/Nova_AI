from __future__ import annotations

from pathlib import Path

AGENT_FORBIDDEN = [
    "nova.core.orchestrator",
    "nova.core.execution",
    "nova.core.registry",
    "nova.core.queue",
    "nova.core.memory",
    "nova.core.personality",
    "nova.core.model_router",
    "nova.core.iomembrane",
    "nova.core.language",
]

PROVIDER_FORBIDDEN = [
    "nova.core.orchestrator",
    "nova.core.registry",
    "nova.core.queue",
    "nova.core.memory",
    "nova.agents",
]


def _assert_no_forbidden_imports(directory: str, forbidden: list[str]) -> None:
    for path in Path(directory).rglob('*.py'):
        text = path.read_text(encoding='utf-8')
        for marker in forbidden:
            assert marker not in text, f"Forbidden import marker '{marker}' found in {path}"



def test_agents_have_no_forbidden_core_imports() -> None:
    _assert_no_forbidden_imports('nova/agents', AGENT_FORBIDDEN)



def test_providers_have_no_forbidden_core_or_agent_imports() -> None:
    _assert_no_forbidden_imports('nova/providers', PROVIDER_FORBIDDEN)