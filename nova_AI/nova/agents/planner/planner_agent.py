from __future__ import annotations

from typing import Any

from nova.agents.base_agent import BaseAgent
from nova.core.result_types import AgentMetadata, AgentResult, ModelRequest


class PlannerAgent(BaseAgent):
    metadata = AgentMetadata(
        name="planner",
        version="0.1.0",
        description="Creates short step-by-step plans for user goals.",
        capabilities=["plan.goal"],
        input_schema="{'goal': str, 'context': str | None, 'planning_prompt': str | None}",
        output_schema="{'steps': list[str]}",
        safety_level="safe",
        undoable=False,
    )

    def __init__(self, router: Any) -> None:
        self._router = router

    def execute(self, input_data: dict[str, Any]) -> AgentResult:
        try:
            goal = str(input_data.get("goal", "")).strip()
            context = input_data.get("context") or ""
            planning_prompt = str(input_data.get("planning_prompt", "")).strip()
            request = ModelRequest(
                task_type="plan",
                system_prompt=planning_prompt,
                user_text=goal,
                context=context,
            )
            model_response = self._router.generate(request)
            if not model_response.success:
                return AgentResult(success=False, error=model_response.error or "Planning model failed.")
            steps = [line.strip() for line in model_response.text.splitlines() if line.strip()]
            return AgentResult(success=True, data={"steps": steps})
        except Exception as exc:
            return self._safe_failure(exc)