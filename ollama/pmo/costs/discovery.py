"""Resource discovery stubs for cost optimization."""

from dataclasses import dataclass


@dataclass
class ResourceSnapshot:
    id: str
    type: str
    monthly_cost: float
    metadata: dict[str, str]


def discover_resources() -> list[ResourceSnapshot]:
    """Return a list of discovered resources with estimated monthly costs.

    This is a stub suitable for unit tests; real discovery would call
    cloud provider APIs or inventory systems.
    """
    # Example static data for tests and local runs
    return [
        ResourceSnapshot(
            id="db-primary", type="postgres", monthly_cost=120.0, metadata={"env": "prod"}
        ),
        ResourceSnapshot(
            id="cache-main", type="redis", monthly_cost=45.5, metadata={"env": "prod"}
        ),
        ResourceSnapshot(id="worker-1", type="vm", monthly_cost=200.0, metadata={"env": "staging"}),
    ]
