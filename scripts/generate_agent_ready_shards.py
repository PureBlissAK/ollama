#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def severity_from_labels(labels):
    names = [label.lower() for label in labels]
    if any("critical" in n or "priority-p0" in n for n in names):
        return "critical"
    if any(k in n for n in names for k in ("priority/high", "security", "bug", "high")):
        return "high"
    if any(k in n for n in names for k in ("priority/medium", "performance", "medium")):
        return "medium"
    return "low"


def load_issues(path):
    with open(path, "r", encoding="utf-8") as handle:
        issues = json.load(handle)
    normalized = []
    for issue in issues:
        labels = [label.get("name", "") for label in issue.get("labels", []) if isinstance(label, dict)]
        normalized.append(
            {
                "number": int(issue["number"]),
                "title": issue.get("title", ""),
                "labels": labels,
                "url": issue.get("url"),
                "updated_at": issue.get("updatedAt") or issue.get("updated_at"),
                "severity": severity_from_labels(labels),
            }
        )
    return normalized


def main():
    parser = argparse.ArgumentParser(description="Generate deterministic shards for open agent-ready issues")
    parser.add_argument("--input", default=".github/agent_ready_queue.json")
    parser.add_argument("--output", default=".github/agent_ready_shards.json")
    parser.add_argument("--shards", type=int, default=4)
    args = parser.parse_args()

    issues = load_issues(args.input)
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda i: (order.get(i["severity"], 99), i["number"]))

    shards = [{"shard": i + 1, "issues": []} for i in range(args.shards)]
    for idx, issue in enumerate(issues):
        shards[idx % args.shards]["issues"].append(issue)

    for shard in shards:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in shard["issues"]:
            counts[issue["severity"]] += 1
        shard["size"] = len(shard["issues"])
        shard["severity_counts"] = counts
        shard["issue_numbers"] = [issue["number"] for issue in shard["issues"]]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": args.input,
        "open_agent_ready_count": len(issues),
        "shard_count": args.shards,
        "assignment_policy": "severity_then_issue_number_round_robin",
        "shards": shards,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "output": args.output,
        "open_agent_ready_count": len(issues),
        "shard_count": args.shards,
        "shard_sizes": [s["size"] for s in shards],
    }, indent=2))


if __name__ == "__main__":
    main()
