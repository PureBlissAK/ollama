"""Deployment plan representation for orchestrator."""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class DeploymentStep:
    target: str
    action: str
    params: Dict[str, Any]


@dataclass
class DeploymentPlan:
    steps: List[DeploymentStep]

    def add_step(self, target: str, action: str, params: Dict[str, Any] | None = None) -> None:
        if params is None:
            params = {}
        self.steps.append(DeploymentStep(target=target, action=action, params=params))

    def serialize(self) -> List[Dict[str, Any]]:
        return [
            {"target": s.target, "action": s.action, "params": s.params}
            for s in self.steps
        ]

    def apply(self) -> None:
        """Apply the deployment plan.

        This is a stub for orchestration tests. Real implementation will
        perform actions against external systems.
        """
        for step in self.steps:
            # no-op in tests; real runner would execute action
            pass
