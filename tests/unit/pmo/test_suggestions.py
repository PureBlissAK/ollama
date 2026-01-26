from ollama.pmo.suggestions import SmartSuggestionsEngine


def test_suggestions_ordering():
    engine = SmartSuggestionsEngine()
    query = "cost optimization and savings"
    candidates = [
        "reduce cost and save money",
        "improve model accuracy",
        "increase throughput and latency improvements",
    ]
    results = engine.suggest(query, candidates, top_k=2)
    assert results[0][0] == "reduce cost and save money"
    assert results[0][1] >= results[1][1]


def test_suggestions_top_k_limits():
    engine = SmartSuggestionsEngine()
    candidates = [f"candidate {i}" for i in range(10)]
    res = engine.suggest("candidate", candidates, top_k=5)
    assert len(res) == 5
