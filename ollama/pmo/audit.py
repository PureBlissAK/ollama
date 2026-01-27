"""Audit Trail - Comprehensive Remediation History and Rollback.

This module provides detailed audit trails for all remediation actions,
including fix history, rollback capability, compliance timelines, and
effectiveness metrics.

Features:
    - Detailed fix history (what, when, why, who, result)
    - One-click rollback for failed fixes
    - Compliance timeline visualization
    - Fix effectiveness metrics (success rate, duration)
    - Export audit logs (JSON, CSV)

Example:
    >>> from ollama.pmo.audit import AuditTrail
    >>> audit = AuditTrail(repo="kushin77/ollama")
    >>> audit.log_fix("sec-001", success=True, duration_ms=1250)
    >>> history = audit.get_history(limit=10)
"""

import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Single audit trail entry."""

    entry_id: str
    timestamp: datetime
    fix_id: str
    fix_type: str
    description: str
    success: bool
    duration_ms: int
    files_modified: List[str]
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    triggered_by: str  # manual, scheduled, event
    error_message: Optional[str] = None
    rollback_available: bool = False
    rolled_back: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """Create from dictionary."""
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            fix_id=data["fix_id"],
            fix_type=data["fix_type"],
            description=data["description"],
            success=data["success"],
            duration_ms=data["duration_ms"],
            files_modified=data.get("files_modified", []),
            before_state=data.get("before_state", {}),
            after_state=data.get("after_state", {}),
            triggered_by=data.get("triggered_by", "manual"),
            error_message=data.get("error_message"),
            rollback_available=data.get("rollback_available", False),
            rolled_back=data.get("rolled_back", False),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "fix_id": self.fix_id,
            "fix_type": self.fix_type,
            "description": self.description,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "files_modified": self.files_modified,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "triggered_by": self.triggered_by,
            "error_message": self.error_message,
            "rollback_available": self.rollback_available,
            "rolled_back": self.rolled_back,
            "metadata": self.metadata,
        }


class AuditTrail:
    """Comprehensive audit trail for remediation actions.

    Tracks all remediation fixes with detailed history, rollback capability,
    compliance timelines, and effectiveness metrics.

    Attributes:
        repo: GitHub repository (owner/repo format)
        repo_path: Local repository path
        audit_file: Path to audit trail file
        entries: Loaded audit entries

    Example:
        >>> audit = AuditTrail(repo="kushin77/ollama")
        >>> audit.log_fix("dep-001", success=True, files=["requirements.txt"])
        >>> metrics = audit.get_effectiveness_metrics()
        >>> print(f"Success rate: {metrics['overall_success_rate']}%")
    """

    def __init__(
        self,
        repo: Optional[str] = None,
        repo_path: Optional[Path] = None,
    ) -> None:
        """Initialize audit trail.

        Args:
            repo: GitHub repository in owner/repo format
            repo_path: Local path to repository
        """
        self.repo = repo
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

        # Audit file
        self.audit_file = self.repo_path / ".pmo" / "audit_trail.jsonl"
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        # Ensure audit file exists so tests can validate presence
        try:
            self.audit_file.touch(exist_ok=True)
        except Exception:
            pass

        # Load entries
        self.entries: List[AuditEntry] = self._load_audit()

    def log_fix(
        self,
        fix_id: str,
        fix_type: str,
        description: str,
        success: bool,
        duration_ms: int,
        files_modified: Optional[List[str]] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        triggered_by: str = "manual",
        error_message: Optional[str] = None,
        rollback_available: bool = False,
        **metadata: Any,
    ) -> str:
        """Log a remediation fix to audit trail.

        Args:
            fix_id: Unique fix identifier
            fix_type: Category (dependency, security, config, etc.)
            description: Human-readable description
            success: Whether fix succeeded
            duration_ms: Execution time in milliseconds
            files_modified: List of modified files
            before_state: State before fix
            after_state: State after fix
            triggered_by: What triggered this fix (manual, scheduled, event)
            error_message: Error message if failed
            rollback_available: Whether rollback is possible
            **metadata: Additional metadata

        Returns:
            Entry ID

        Example:
            >>> entry_id = audit.log_fix(
            ...     fix_id='dep-001',
            ...     fix_type='dependency',
            ...     description='Updated Python dependencies',
            ...     success=True,
            ...     duration_ms=1250,
            ...     files_modified=['requirements.txt']
            ... )
        """
        entry_id = f"{fix_id}_{int(datetime.now().timestamp())}"

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            fix_id=fix_id,
            fix_type=fix_type,
            description=description,
            success=success,
            duration_ms=duration_ms,
            files_modified=files_modified or [],
            before_state=before_state or {},
            after_state=after_state or {},
            triggered_by=triggered_by,
            error_message=error_message,
            rollback_available=rollback_available,
            metadata=metadata,
        )

        # Append to file
        try:
            with open(self.audit_file, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")

            # Add to memory
            self.entries.append(entry)

            logger.info(
                f"Logged fix: {fix_id} ({'SUCCESS' if success else 'FAILED'}) "
                f"in {duration_ms}ms"
            )

        except Exception as e:
            logger.error(f"Failed to log fix: {e}")

        return entry_id

    def log_rollback(
        self,
        entry_id: str,
        success: bool,
        duration_ms: int,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a rollback operation.

        Args:
            entry_id: ID of entry being rolled back
            success: Whether rollback succeeded
            duration_ms: Rollback duration
            error_message: Error message if failed
        """
        # Find original entry
        original = next((e for e in self.entries if e.entry_id == entry_id), None)
        if not original:
            logger.error(f"Entry not found for rollback: {entry_id}")
            return

        # Mark as rolled back
        original.rolled_back = True

        # Log rollback as new entry
        rollback_id = f"rollback_{entry_id}"
        self.log_fix(
            fix_id=rollback_id,
            fix_type="rollback",
            description=f"Rollback of {original.fix_id}",
            success=success,
            duration_ms=duration_ms,
            files_modified=original.files_modified,
            before_state=original.after_state,
            after_state=original.before_state,
            triggered_by="manual",
            error_message=error_message,
            rollback_available=False,
            original_entry=entry_id,
        )

    def get_history(
        self,
        fix_type: Optional[str] = None,
        success_only: bool = False,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get audit history with filtering.

        Args:
            fix_type: Filter by fix type
            success_only: Only return successful fixes
            since: Only return entries after this datetime
            limit: Maximum results to return

        Returns:
            List of audit entries

        Example:
            >>> history = audit.get_history(fix_type='security', success_only=True)
        """
        filtered = self.entries.copy()

        # Filter by type
        if fix_type:
            filtered = [e for e in filtered if e.fix_type == fix_type]

        # Filter by success
        if success_only:
            filtered = [e for e in filtered if e.success]

        # Filter by date
        if since:
            filtered = [e for e in filtered if e.timestamp >= since]

        # Sort by timestamp (most recent first)
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        # Limit
        return filtered[:limit]

    def get_effectiveness_metrics(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Calculate fix effectiveness metrics.

        Args:
            since: Calculate metrics from this date onward

        Returns:
            Effectiveness metrics

        Example:
            >>> metrics = audit.get_effectiveness_metrics()
            >>> print(f"Success rate: {metrics['overall_success_rate']}%")
        """
        # Filter by date
        entries = self.entries
        if since:
            entries = [e for e in entries if e.timestamp >= since]

        if not entries:
            return {
                "overall_success_rate": 0,
                "total_fixes": 0,
                "successful_fixes": 0,
                "failed_fixes": 0,
                "avg_duration_ms": 0,
                "by_type": {},
            }

        # Overall metrics
        total = len(entries)
        successful = sum(1 for e in entries if e.success)
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0

        # Average duration
        durations = [e.duration_ms for e in entries]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Metrics by type
        by_type: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "successful": 0, "failed": 0, "avg_duration_ms": 0}
        )

        for entry in entries:
            stats = by_type[entry.fix_type]
            stats["total"] += 1
            if entry.success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            stats["durations"] = stats.get("durations", []) + [entry.duration_ms]

        # Calculate averages per type
        for _fix_type, stats in by_type.items():
            durations = stats.pop("durations", [])
            stats["avg_duration_ms"] = sum(durations) / len(durations) if durations else 0
            stats["success_rate"] = (
                stats["successful"] / stats["total"] * 100 if stats["total"] > 0 else 0
            )

        return {
            "overall_success_rate": round(success_rate, 2),
            "total_fixes": total,
            "successful_fixes": successful,
            "failed_fixes": failed,
            "avg_duration_ms": round(avg_duration, 2),
            "by_type": dict(by_type),
            "calculated_at": datetime.now().isoformat(),
        }

    def get_compliance_timeline(
        self,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get compliance score timeline.

        Args:
            days: Number of days to include

        Returns:
            Timeline data points

        Example:
            >>> timeline = audit.get_compliance_timeline(days=30)
            >>> for point in timeline:
            ...     print(f"{point['date']}: {point['score']}%")
        """
        cutoff = datetime.now() - timedelta(days=days)
        entries = [e for e in self.entries if e.timestamp >= cutoff]

        # Group by date
        by_date: Dict[str, List[AuditEntry]] = defaultdict(list)
        for entry in entries:
            date_key = entry.timestamp.date().isoformat()
            by_date[date_key].append(entry)

        # Calculate daily scores
        timeline: List[Dict[str, Any]] = []
        for date_str in sorted(by_date.keys()):
            day_entries = by_date[date_str]
            successful = sum(1 for e in day_entries if e.success)
            total = len(day_entries)
            score = (successful / total * 100) if total > 0 else 0

            timeline.append(
                {
                    "date": date_str,
                    "score": round(score, 2),
                    "total_fixes": total,
                    "successful": successful,
                    "failed": total - successful,
                }
            )

        return timeline

    def export_json(self, output_file: Path, limit: Optional[int] = None) -> None:
        """Export audit trail to JSON file.

        Args:
            output_file: Output file path
            limit: Maximum entries to export

        Example:
            >>> audit.export_json(Path('audit_export.json'))
        """
        entries = self.entries[:limit] if limit else self.entries
        data = [e.to_dict() for e in entries]

        try:
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported {len(entries)} entries to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")

    def export_csv(self, output_file: Path, limit: Optional[int] = None) -> None:
        """Export audit trail to CSV file.

        Args:
            output_file: Output file path
            limit: Maximum entries to export

        Example:
            >>> audit.export_csv(Path('audit_export.csv'))
        """
        entries = self.entries[:limit] if limit else self.entries

        if not entries:
            logger.warning("No entries to export")
            return

        try:
            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(
                    [
                        "Entry ID",
                        "Timestamp",
                        "Fix ID",
                        "Fix Type",
                        "Description",
                        "Success",
                        "Duration (ms)",
                        "Files Modified",
                        "Triggered By",
                        "Error Message",
                    ]
                )

                # Rows
                for entry in entries:
                    writer.writerow(
                        [
                            entry.entry_id,
                            entry.timestamp.isoformat(),
                            entry.fix_id,
                            entry.fix_type,
                            entry.description,
                            entry.success,
                            entry.duration_ms,
                            ",".join(entry.files_modified),
                            entry.triggered_by,
                            entry.error_message or "",
                        ]
                    )

            logger.info(f"Exported {len(entries)} entries to {output_file}")

        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")

    def get_most_common_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most commonly failing fixes.

        Args:
            limit: Number of results to return

        Returns:
            List of fix types with failure counts

        Example:
            >>> failures = audit.get_most_common_failures(limit=5)
            >>> for failure in failures:
            ...     print(f"{failure['fix_id']}: {failure['failure_count']} failures")
        """
        # Count failures by fix ID
        failure_counts: Dict[str, int] = defaultdict(int)
        fix_info: Dict[str, Dict[str, str]] = {}

        for entry in self.entries:
            if not entry.success:
                failure_counts[entry.fix_id] += 1
                fix_info[entry.fix_id] = {
                    "fix_type": entry.fix_type,
                    "description": entry.description,
                }

        # Sort by count
        sorted_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)

        # Format results
        results: List[Dict[str, Any]] = []
        for fix_id, count in sorted_failures[:limit]:
            info = fix_info.get(fix_id, {})
            results.append(
                {
                    "fix_id": fix_id,
                    "fix_type": info.get("fix_type", "unknown"),
                    "description": info.get("description", ""),
                    "failure_count": count,
                }
            )

        return results

    def get_rollback_history(self) -> List[AuditEntry]:
        """Get history of rollback operations.

        Returns:
            List of rollback entries
        """
        return [e for e in self.entries if e.fix_type == "rollback"]

    def _load_audit(self) -> List[AuditEntry]:
        """Load audit entries from file.

        Returns:
            List of audit entries
        """
        entries: List[AuditEntry] = []

        if not self.audit_file.exists():
            return entries

        try:
            with open(self.audit_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        entry = AuditEntry.from_dict(data)
                        entries.append(entry)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Skipping invalid entry: {e}")
                        continue

            logger.info(f"Loaded {len(entries)} audit entries")

        except Exception as e:
            logger.error(f"Failed to load audit: {e}")

        return entries
