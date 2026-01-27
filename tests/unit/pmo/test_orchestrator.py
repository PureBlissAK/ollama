from ollama.pmo.orchestrator.deployment import DeploymentPlan
from ollama.pmo.orchestrator.graph import DependencyGraph


def test_dependency_graph_toposort_simple():
    g = DependencyGraph()
    g.add_edge("service-a", "service-b")
    g.add_edge("service-b", "service-c")
    order = g.topological_sort()
    # service-c should come before service-b and service-a
    assert order.index("service-c") < order.index("service-b")
    assert order.index("service-b") < order.index("service-a")


def test_deployment_plan_serialize_and_add():
    p = DeploymentPlan(steps=[])
    p.add_step("service-a", "deploy", {"version": "v1"})
    serialized = p.serialize()
    assert serialized[0]["target"] == "service-a"
    assert serialized[0]["action"] == "deploy"
