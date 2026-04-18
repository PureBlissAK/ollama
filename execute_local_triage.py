#!/usr/bin/env python3
"""Generate a live, immutable triage manifest for GitHub issues.

This script is idempotent: it reads live GitHub issue state, cross-references
local git history for evidence, and writes a deterministic JSON artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def resolve_token() -> str:
    for key in ("OLLAMA_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=True,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()

    raise RuntimeError("no GitHub token found in env or git credential helper")


class GitHubIssueClient:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ollama-live-triage-manifest",
        }

    def request(self, path: str) -> Any:
        request = urllib.request.Request(f"{self.base_url}{path}", headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code} for {path}: {body}") from exc

    def fetch_open_issues(self) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self.request(f"/issues?state=open&per_page=100&page={page}")
            if not batch:
                break
            for item in batch:
                if "pull_request" not in item:
                    issues.append(item)
            if len(batch) < 100:
                break
            page += 1
        return issues


def git_evidence(issue_number: int) -> list[dict[str, str]]:
    pattern = f"#{issue_number}"
    proc = subprocess.run(
        ["git", "log", "--format=%H%x09%s", "--all", f"--grep={pattern}"],
        capture_output=True,
        text=True,
        check=False,
    )
    results: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        commit, subject = line.split("\t", 1)
        results.append({"commit": commit, "subject": subject})
    return results


def labels(issue: dict[str, Any]) -> set[str]:
    return {label["name"] for label in issue.get("labels", [])}


def summarize(issues: list[dict[str, Any]]) -> dict[str, Any]:
    wave_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    agent_ready: list[dict[str, Any]] = []
    needs_evidence: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for issue in issues:
        issue_labels = labels(issue)
        for label in issue_labels:
            label_counts[label] += 1
            if label.startswith("wave/"):
                wave_counts[label] += 1

        item = {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "labels": sorted(issue_labels),
            "updated_at": issue["updated_at"],
        }

        if "needs-evidence" in issue_labels:
            item["evidence_commits"] = git_evidence(issue["number"])
            needs_evidence.append(item)

        if "status/triaged" in issue_labels and "status/planned-wave" in issue_labels and "needs-evidence" not in issue_labels:
            agent_ready.append(item)

        if "blocked" in issue_labels or "status/blocked" in issue_labels:
            blocked.append(item)

    close_candidates = [issue for issue in needs_evidence if issue.get("evidence_commits")]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "open_issue_count": len(issues),
        "agent_ready_count": len(agent_ready),
        "needs_evidence_count": len(needs_evidence),
        "close_candidate_count": len(close_candidates),
        "blocked_count": len(blocked),
        "wave_counts": dict(sorted(wave_counts.items())),
        "top_labels": label_counts.most_common(25),
        "close_candidates": close_candidates,
        "needs_evidence": needs_evidence,
        "agent_ready": agent_ready,
        "blocked": blocked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate live GitHub issue triage manifest")
    parser.add_argument("--repo", default="kushin77/ollama", help="GitHub repository owner/name")
    parser.add_argument("--output", default=".github/live_triage_manifest.json", help="Output JSON file path")
    args = parser.parse_args()

    token = resolve_token()
    client = GitHubIssueClient(args.repo, token)
    issues = client.fetch_open_issues()
    manifest = summarize(issues)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"open issues: {manifest['open_issue_count']}")
    print(f"agent ready: {manifest['agent_ready_count']}")
    print(f"needs evidence: {manifest['needs_evidence_count']}")
    print(f"close candidates: {manifest['close_candidate_count']}")
    print(f"wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
