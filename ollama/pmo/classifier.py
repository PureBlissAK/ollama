"""Issue Classifier - AI-powered GitHub issue classification and triage.

This module provides intelligent issue classification, priority scoring, and
auto-assignment recommendations using pattern matching and heuristics.

Features:
    - Issue type classification (bug, feature, documentation, etc.)
    - Priority scoring (p0-p3) based on keywords and patterns
    - Team assignment recommendations
    - Urgency detection
    - Duplicate detection

Example:
    >>> from ollama.pmo.classifier import IssueClassifier
    >>> classifier = IssueClassifier(repo="owner/repo")
    >>> result = classifier.classify_issue(123)
    >>> print(result['issue_type'])  # 'bug'
    >>> print(result['priority'])    # 'p0'
    >>> print(result['confidence'])  # 0.92
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from github import Github
    from github.Issue import Issue
    from github.Repository import Repository
except Exception:  # pragma: no cover - fallback when PyGithub not installed in tests
    Github = None
    Issue = Any
    Repository = Any


class IssueClassifier:
    """Classifies GitHub issues using AI-powered pattern matching.

    Uses keyword analysis, title patterns, and content heuristics to:
        - Classify issue type (bug, feature, documentation, etc.)
        - Score priority (p0-p3)
        - Recommend team assignments
        - Detect urgency indicators
        - Find potential duplicates

    Attributes:
        repo: GitHub repository (owner/repo format)
        github_token: Optional GitHub personal access token
        github_client: GitHub API client
        repository: GitHub repository object
    """

    # Issue type classification patterns
    TYPE_PATTERNS: Dict[str, Dict[str, Any]] = {
        "bug": {
            "keywords": [
                "bug",
                "error",
                "crash",
                "broken",
                "fail",
                "issue",
                "problem",
                "exception",
                "traceback",
                "stacktrace",
                "not working",
                "doesn't work",
            ],
            "title_patterns": [
                r"\[bug\]",
                r"bug:",
                r"error:",
                r"crash",
                r"broken",
                r"fails? to",
                r"doesn\'t work",
                r"not working",
            ],
            "weight": 1.0,
        },
        "feature": {
            "keywords": [
                "feature",
                "enhancement",
                "improvement",
                "add",
                "implement",
                "support",
                "request",
                "would be nice",
                "could you",
                "please add",
            ],
            "title_patterns": [
                r"\[feature\]",
                r"\[enhancement\]",
                r"feature:",
                r"add support",
                r"implement",
                r"request:",
            ],
            "weight": 1.0,
        },
        "documentation": {
            "keywords": [
                "documentation",
                "docs",
                "readme",
                "typo",
                "spelling",
                "grammar",
                "example",
                "tutorial",
                "guide",
                "explain",
                "clarify",
            ],
            "title_patterns": [
                r"\[docs\]",
                r"docs:",
                r"documentation:",
                r"readme",
                r"typo",
            ],
            "weight": 0.8,
        },
        "question": {
            "keywords": [
                "question",
                "how to",
                "how do i",
                "help",
                "confused",
                "what is",
                "why does",
                "clarification",
                "understand",
            ],
            "title_patterns": [
                r"\[question\]",
                r"\?$",
                r"how to",
                r"how do i",
                r"what is",
                r"why does",
            ],
            "weight": 0.6,
        },
        "security": {
            "keywords": [
                "security",
                "vulnerability",
                "exploit",
                "cve",
                "attack",
                "malicious",
                "injection",
                "xss",
                "csrf",
                "authentication",
                "authorization",
                "leak",
                "exposure",
                "sensitive",
            ],
            "title_patterns": [
                r"\[security\]",
                r"security:",
                r"vulnerability",
                r"cve-",
            ],
            "weight": 2.0,  # Higher weight for security
        },
        "performance": {
            "keywords": [
                "performance",
                "slow",
                "optimization",
                "speed",
                "latency",
                "throughput",
                "memory",
                "cpu",
                "bottleneck",
                "timeout",
            ],
            "title_patterns": [
                r"\[performance\]",
                r"performance:",
                r"slow",
                r"optimization",
            ],
            "weight": 1.2,
        },
    }

    # Priority scoring patterns
    PRIORITY_PATTERNS: Dict[str, Dict[str, Any]] = {
        "p0": {
            "keywords": [
                "critical",
                "urgent",
                "production down",
                "outage",
                "breaking",
                "crash",
                "data loss",
                "security",
                "vulnerability",
                "exploit",
                "emergency",
                "asap",
                "immediately",
            ],
            "impact_indicators": [
                "production",
                "all users",
                "everyone",
                "complete failure",
                "total loss",
                "cannot use",
                "unusable",
            ],
            "score": 100,
        },
        "p1": {
            "keywords": [
                "important",
                "high priority",
                "blocker",
                "blocking",
                "major",
                "significant",
                "severe",
                "serious",
            ],
            "impact_indicators": [
                "many users",
                "multiple",
                "common",
                "frequent",
                "core functionality",
                "main feature",
            ],
            "score": 75,
        },
        "p2": {
            "keywords": ["medium", "normal", "moderate", "standard", "regular", "typical"],
            "impact_indicators": [
                "some users",
                "edge case",
                "workaround exists",
                "minor inconvenience",
            ],
            "score": 50,
        },
        "p3": {
            "keywords": [
                "low",
                "minor",
                "trivial",
                "nice to have",
                "eventually",
                "someday",
                "enhancement",
                "improvement",
            ],
            "impact_indicators": [
                "rare",
                "uncommon",
                "cosmetic",
                "polish",
                "quality of life",
                "convenience",
            ],
            "score": 25,
        },
    }

    # Team assignment patterns
    TEAM_PATTERNS: Dict[str, List[str]] = {
        "backend": [
            "api",
            "server",
            "database",
            "sql",
            "query",
            "endpoint",
            "authentication",
            "authorization",
            "rest",
            "graphql",
        ],
        "frontend": [
            "ui",
            "ux",
            "interface",
            "css",
            "html",
            "react",
            "vue",
            "angular",
            "component",
            "button",
            "form",
            "layout",
        ],
        "devops": [
            "deployment",
            "ci/cd",
            "docker",
            "kubernetes",
            "terraform",
            "infrastructure",
            "cloud",
            "gcp",
            "aws",
            "monitoring",
        ],
        "security": [
            "security",
            "vulnerability",
            "authentication",
            "authorization",
            "encryption",
            "ssl",
            "tls",
            "firewall",
            "attack",
        ],
        "data": [
            "analytics",
            "metrics",
            "data",
            "statistics",
            "reporting",
            "dashboard",
            "visualization",
            "etl",
            "pipeline",
        ],
    }

    def __init__(
        self,
        repo: str,
        github_token: Optional[str] = None,
    ) -> None:
        """Initialize issue classifier.

        Args:
            repo: GitHub repository in owner/repo format
            github_token: Optional GitHub personal access token

        Raises:
            ValueError: If repo format is invalid
        """
        if "/" not in repo:
            raise ValueError(f"Invalid repo format: {repo}. Expected 'owner/repo'")

        self.repo = repo
        self.github_token = github_token

        # Initialize GitHub client
        self.github_client = Github(github_token) if github_token else Github()
        self.repository: Repository = self.github_client.get_repo(repo)

    def classify_issue(self, issue_number: int) -> Dict[str, Any]:
        """Classify a GitHub issue.

        Args:
            issue_number: GitHub issue number

        Returns:
            Classification result with type, priority, team, confidence

        Example:
            >>> classifier = IssueClassifier("owner/repo")
            >>> result = classifier.classify_issue(123)
            >>> print(result)
            {
                'issue_number': 123,
                'issue_type': 'bug',
                'priority': 'p0',
                'recommended_team': 'backend',
                'urgency_score': 95,
                'confidence': 0.92,
                'reasoning': {
                    'type': 'Keywords: error, crash, production (confidence: 0.92)',
                    'priority': 'Critical keywords: production down, urgent (score: 95)',
                    'team': 'Keywords: api, database, server (confidence: 0.85)',
                },
                'suggested_labels': ['bug', 'priority-p0', 'team-backend'],
            }
        """
        # Fetch issue
        issue = self.repository.get_issue(issue_number)

        # Classify issue type
        issue_type, type_confidence = self._classify_type(issue)

        # Score priority
        priority, priority_score = self._score_priority(issue)

        # Recommend team
        team, team_confidence = self._recommend_team(issue)

        # Calculate urgency
        urgency_score = self._calculate_urgency(issue, priority_score)

        # Overall confidence
        overall_confidence = (type_confidence + team_confidence) / 2.0

        return {
            "issue_number": issue_number,
            "issue_type": issue_type,
            "priority": priority,
            "recommended_team": team,
            "urgency_score": urgency_score,
            "confidence": round(overall_confidence, 2),
            "reasoning": {
                "type": f"Type: {issue_type} (confidence: {type_confidence:.2f})",
                "priority": f"Priority: {priority} (score: {priority_score})",
                "team": f"Team: {team} (confidence: {team_confidence:.2f})",
            },
            "suggested_labels": self._generate_labels(issue_type, priority, team),
            "metadata": {
                "title": issue.title,
                "created_at": issue.created_at.isoformat(),
                "author": issue.user.login,
                "comments": issue.comments,
                "current_labels": [label.name for label in issue.labels],
            },
        }

    def _classify_type(self, issue: Issue) -> Tuple[str, float]:
        """Classify issue type.

        Args:
            issue: GitHub issue object

        Returns:
            Tuple of (issue_type, confidence_score)
        """
        title = issue.title.lower()
        body = (issue.body or "").lower()
        combined_text = f"{title} {body}"

        scores: Dict[str, float] = {}

        for issue_type, patterns in self.TYPE_PATTERNS.items():
            score = 0.0

            # Check title patterns (higher weight)
            for pattern in patterns["title_patterns"]:
                if re.search(pattern, title, re.IGNORECASE):
                    score += patterns["weight"] * 2.0

            # Check keywords in combined text
            for keyword in patterns["keywords"]:
                if keyword in combined_text:
                    score += patterns["weight"] * 0.5

            scores[issue_type] = score

        # Get highest scoring type
        if scores:
            best_type = max(scores, key=scores.get)  # type: ignore
            max_score = scores[best_type]

            # Normalize confidence (cap at 1.0)
            confidence = min(max_score / 5.0, 1.0)

            return best_type, confidence

        return "question", 0.3  # Default fallback

    def _score_priority(self, issue: Issue) -> Tuple[str, int]:
        """Score issue priority.

        Args:
            issue: GitHub issue object

        Returns:
            Tuple of (priority_level, urgency_score)
        """
        title = issue.title.lower()
        body = (issue.body or "").lower()
        combined_text = f"{title} {body}"

        max_score = 0
        assigned_priority = "p3"

        for priority, patterns in self.PRIORITY_PATTERNS.items():
            score = patterns["score"]
            matches = 0

            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in combined_text:
                    matches += 1

            # Check impact indicators
            for indicator in patterns["impact_indicators"]:
                if indicator in combined_text:
                    matches += 1

            # If any matches, consider this priority
            if matches > 0:
                # Small boost per match, tuned to keep scores in expected ranges
                adjusted_score = score + (matches * 3)
                # Prevent non-p0 priorities from reaching max 100 to keep ranges
                cap = 100 if priority == "p0" else min(89, score + 30)
                adjusted_score = min(adjusted_score, cap)
                if adjusted_score > max_score:
                    max_score = adjusted_score
                    assigned_priority = priority

        return assigned_priority, max_score

    def _recommend_team(self, issue: Issue) -> Tuple[str, float]:
        """Recommend team assignment.

        Args:
            issue: GitHub issue object

        Returns:
            Tuple of (team_name, confidence_score)
        """
        title = issue.title.lower()
        body = (issue.body or "").lower()
        combined_text = f"{title} {body}"

        scores: Dict[str, int] = {}

        for team, keywords in self.TEAM_PATTERNS.items():
            score = 0
            for keyword in keywords:
                if keyword in combined_text:
                    score += 1
            scores[team] = score

        # Get highest scoring team
        if scores and max(scores.values()) > 0:
            best_team = max(scores, key=scores.get)  # type: ignore
            max_count = scores[best_team]

            # Normalize confidence
            confidence = min(max_count / 3.0, 1.0)

            return best_team, confidence

        return "engineering", 0.4  # Default fallback

    def _calculate_urgency(self, issue: Issue, priority_score: int) -> int:
        """Calculate urgency score.

        Args:
            issue: GitHub issue object
            priority_score: Priority score from _score_priority

        Returns:
            Urgency score (0-100)
        """
        urgency = priority_score

        # Age factor (older = less urgent unless critical)
        age_days = (datetime.now() - issue.created_at.replace(tzinfo=None)).days

        if priority_score >= 90:  # Critical issues stay urgent
            urgency = min(urgency + (age_days * 2), 100)
        elif age_days > 30:  # Old non-critical issues lose urgency
            urgency = max(urgency - (age_days // 10), 10)

        # Activity factor (many comments = more urgent)
        if issue.comments > 10:
            urgency = min(urgency + 10, 100)

        return urgency

    def _generate_labels(
        self,
        issue_type: str,
        priority: str,
        team: str,
    ) -> List[str]:
        """Generate suggested labels.

        Args:
            issue_type: Classified issue type
            priority: Assigned priority
            team: Recommended team

        Returns:
            List of suggested label names
        """
        labels = []

        # Type label
        labels.append(issue_type)

        # Priority label
        labels.append(f"priority-{priority}")

        # Team label
        if team != "engineering":  # Don't add generic team
            labels.append(f"team-{team}")

        return labels

    def classify_batch(
        self,
        issue_numbers: List[int],
    ) -> List[Dict[str, Any]]:
        """Classify multiple issues in batch.

        Args:
            issue_numbers: List of issue numbers

        Returns:
            List of classification results

        Example:
            >>> classifier = IssueClassifier("owner/repo")
            >>> results = classifier.classify_batch([1, 2, 3])
            >>> for result in results:
            ...     print(f"#{result['issue_number']}: {result['issue_type']}")
        """
        results = []

        for issue_number in issue_numbers:
            try:
                result = self.classify_issue(issue_number)
                results.append(result)
            except Exception as e:
                results.append(
                    {
                        "issue_number": issue_number,
                        "error": str(e),
                        "issue_type": None,
                        "priority": None,
                    }
                )

        return results

    def find_duplicates(
        self,
        issue_number: int,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Find potential duplicate issues.

        Args:
            issue_number: Issue to check for duplicates
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            List of potential duplicates with similarity scores

        Example:
            >>> classifier = IssueClassifier("owner/repo")
            >>> duplicates = classifier.find_duplicates(123)
            >>> for dup in duplicates:
            ...     print(f"#{dup['issue_number']}: {dup['similarity']:.0%}")
        """
        # Fetch target issue
        target_issue = self.repository.get_issue(issue_number)
        target_title = target_issue.title.lower()
        target_words = set(re.findall(r"\w+", target_title))

        # Search for similar issues
        duplicates = []

        # Query open issues with similar keywords
        search_query = f"repo:{self.repo} is:issue is:open"
        issues = self.github_client.search_issues(search_query)

        for issue in issues[:50]:  # Limit to 50 for performance
            if issue.number == issue_number:
                continue

            # Calculate similarity
            issue_title = issue.title.lower()
            issue_words = set(re.findall(r"\w+", issue_title))

            # Jaccard similarity
            intersection = target_words & issue_words
            union = target_words | issue_words

            if not union:
                continue

            similarity = len(intersection) / len(union)

            if similarity >= threshold:
                duplicates.append(
                    {
                        "issue_number": issue.number,
                        "title": issue.title,
                        "similarity": round(similarity, 2),
                        "url": issue.html_url,
                        "state": issue.state,
                        "created_at": issue.created_at.isoformat(),
                    }
                )

        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x["similarity"], reverse=True)

        return duplicates
