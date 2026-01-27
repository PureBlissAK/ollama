"""Tests for Auto-Remediation Engine."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from ollama.pmo.remediation import (
    RemediationEngine,
    RemediationFix,
    RemediationResult,
)
from ollama.pmo.drift_predictor import DriftPredictor, ComplianceSnapshot, DriftForecast
from ollama.pmo.scheduler import SchedulerEngine, ScheduledTask, TaskStatus, TriggerType
from ollama.pmo.audit import AuditTrail, AuditEntry
import time
import json

# ============================================================================
# REMEDIATION ENGINE TESTS
# ============================================================================


class TestRemediationEngine:
    """Tests for RemediationEngine class."""

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """Create temporary repository."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Create .pmo directory
        (repo_path / ".pmo").mkdir()

        # Create requirements.txt
        (repo_path / "requirements.txt").write_text("requests==2.28.0\n")

        # Create Dockerfile
        (repo_path / "Dockerfile").write_text("FROM python:3.9\n")

        # Create README.md
        (repo_path / "README.md").write_text("# Test Repo\n")

        return repo_path

    @pytest.fixture
    def engine(self, temp_repo):
        """Create remediation engine."""
        return RemediationEngine(repo_path=temp_repo)

    def test_init(self, engine, temp_repo):
        """Test engine initialization."""
        assert engine.repo_path == temp_repo
        assert engine.audit_file.exists()
        assert isinstance(engine.results, list)

    def test_get_all_fixes(self, engine):
        """Test getting all available fixes."""
        fixes = engine._get_all_fixes()

        assert len(fixes) > 0
        assert all(isinstance(f, RemediationFix) for f in fixes)

        # Check we have all categories
        fix_types = {f.fix_type for f in fixes}
        assert "dependency" in fix_types
        assert "security" in fix_types
        assert "config" in fix_types
        assert "documentation" in fix_types
        assert "performance" in fix_types

    def test_get_dependency_fixes(self, engine):
        """Test dependency fix detection."""
        fixes = engine._get_dependency_fixes()

        # Should find requirements.txt and Dockerfile
        assert len(fixes) >= 2

        fix_ids = {f.fix_id for f in fixes}
        assert "dep-001" in fix_ids  # Python dependencies
        assert "dep-003" in fix_ids  # Docker images

    def test_get_security_fixes(self, engine):
        """Test security fix detection."""
        fixes = engine._get_security_fixes()

        # Should have at least 3 security fixes
        assert len(fixes) >= 3

        # Check severity levels
        severities = {f.severity for f in fixes}
        assert "critical" in severities
        assert "high" in severities

    def test_remediate_advanced_dry_run(self, engine):
        """Test dry run mode."""
        result = engine.remediate_advanced(dry_run=True)

        assert result["dry_run"] is True
        assert result["fixes_available"] > 0
        assert "fixes" in result
        assert len(result["fixes"]) > 0

    def test_remediate_advanced_with_filter(self, engine):
        """Test remediation with type filter."""
        result = engine.remediate_advanced(fix_types=["dependency"], dry_run=True)

        assert all(f["type"] == "dependency" for f in result["fixes"])

    def test_remediate_advanced_severity_threshold(self, engine):
        """Test severity threshold filtering."""
        result = engine.remediate_advanced(severity_threshold="high", dry_run=True)

        # Should only include high and critical severity
        severities = {f["severity"] for f in result["fixes"]}
        assert "low" not in severities
        assert "medium" not in severities

    def test_apply_fix(self, engine):
        """Test applying a single fix."""
        fix = RemediationFix(
            fix_id="test-001",
            fix_type="config",
            severity="low",
            description="Test fix",
            affected_files=[],
            fix_function=lambda f: [],
        )

        result = engine._apply_fix(fix)

        assert isinstance(result, RemediationResult)
        assert result.fix_id == "test-001"
        assert result.success is True
        assert result.duration_ms > 0

    def test_apply_fix_failure(self, engine):
        """Test fix application failure."""

        def failing_fix(fix):
            raise ValueError("Test error")

        fix = RemediationFix(
            fix_id="test-002",
            fix_type="security",
            severity="high",
            description="Failing fix",
            affected_files=[],
            fix_function=failing_fix,
        )

        result = engine._apply_fix(fix)

        assert result.success is False
        assert result.error_message == "Test error"

    def test_prepare_rollback(self, engine, temp_repo):
        """Test rollback data preparation."""
        # Create test file
        test_file = temp_repo / "test.txt"
        test_file.write_text("original content")

        fix = RemediationFix(
            fix_id="test-003",
            fix_type="config",
            severity="low",
            description="Test rollback",
            affected_files=["test.txt"],
            fix_function=lambda f: [],
        )

        rollback_data = engine._prepare_rollback(fix)

        assert str(test_file) in rollback_data
        assert rollback_data[str(test_file)] == "original content"

    def test_audit_logging(self, engine):
        """Test audit trail logging."""
        fix = RemediationFix(
            fix_id="test-004",
            fix_type="documentation",
            severity="low",
            description="Test audit",
            affected_files=[],
            fix_function=lambda f: [],
        )

        result = engine._apply_fix(fix)

        # Check audit file was created
        assert engine.audit_file.exists()

        # Check entry was logged
        with open(engine.audit_file, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0

            last_entry = json.loads(lines[-1])
            assert last_entry["fix_id"] == "test-004"

    def test_rollback_fix(self, engine, temp_repo):
        """Test fix rollback."""
        # Create test file
        test_file = temp_repo / "rollback_test.txt"
        test_file.write_text("original")

        def modify_file(fix):
            test_file.write_text("modified")
            return [str(test_file)]

        fix = RemediationFix(
            fix_id="test-005",
            fix_type="config",
            severity="low",
            description="Test rollback",
            affected_files=[str(test_file)],
            fix_function=modify_file,
            rollback_function=engine._rollback_file_change,
        )

        # Apply fix
        result = engine._apply_fix(fix)
        assert test_file.read_text() == "modified"

        # Rollback
        success = engine.rollback_fix("test-005")
        assert success is True
        assert test_file.read_text() == "original"

    def test_get_audit_history(self, engine):
        """Test retrieving audit history."""
        # Apply some fixes
        for i in range(3):
            fix = RemediationFix(
                fix_id=f"test-{i:03d}",
                fix_type="config",
                severity="low",
                description=f"Test fix {i}",
                affected_files=[],
                fix_function=lambda f: [],
            )
            engine._apply_fix(fix)

        # Get history
        history = engine.get_audit_history(limit=10)
        assert len(history) >= 3

        # Most recent first
        assert history[0]["fix_id"] == "test-002"


# ============================================================================
# DRIFT PREDICTOR TESTS
# ============================================================================


class TestDriftPredictor:
    """Tests for DriftPredictor class."""

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """Create temporary repository."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".pmo").mkdir()
        return repo_path

    @pytest.fixture
    def predictor(self, temp_repo):
        """Create drift predictor."""
        return DriftPredictor(repo_path=temp_repo)

    def test_init(self, predictor, temp_repo):
        """Test predictor initialization."""
        assert predictor.repo_path == temp_repo
        assert predictor.history_file.exists()
        assert isinstance(predictor.snapshots, list)

    def test_record_snapshot(self, predictor):
        """Test recording compliance snapshot."""
        compliance_result = {
            "score": 85.5,
            "passed": 17,
            "total": 20,
            "compliant": True,
            "checks": {"pmo_yaml": True, "github_labels": False},
            "details": {},
        }

        predictor.record_snapshot(compliance_result)

        assert len(predictor.snapshots) == 1
        snapshot = predictor.snapshots[0]
        assert snapshot.score == 85.5
        assert snapshot.passed == 17
        assert snapshot.total == 20

    def test_predict_drift_insufficient_data(self, predictor):
        """Test prediction with insufficient data."""
        forecast = predictor.predict_drift(days_ahead=30)
        assert forecast is None

    def test_predict_drift_improving_trend(self, predictor):
        """Test prediction with improving trend."""
        # Record snapshots with improving scores
        for i in range(10):
            compliance = {
                "score": 70.0 + i * 2,  # 70, 72, 74, ...
                "passed": 14 + i,
                "total": 20,
                "compliant": True,
                "checks": {},
                "details": {},
            }
            predictor.record_snapshot(compliance)
            time.sleep(0.01)  # Small delay for timestamp differences

        forecast = predictor.predict_drift(days_ahead=30)

        assert forecast is not None
        assert isinstance(forecast, DriftForecast)
        assert forecast.trending == "improving"
        assert forecast.velocity > 0
        assert forecast.predicted_score > forecast.current_score

    def test_predict_drift_declining_trend(self, predictor):
        """Test prediction with declining trend."""
        # Record snapshots with declining scores
        for i in range(10):
            compliance = {
                "score": 90.0 - i * 2,  # 90, 88, 86, ...
                "passed": 18 - i,
                "total": 20,
                "compliant": True,
                "checks": {},
                "details": {},
            }
            predictor.record_snapshot(compliance)
            time.sleep(0.01)

        forecast = predictor.predict_drift(days_ahead=30)

        assert forecast is not None
        assert forecast.trending == "declining"
        assert forecast.velocity < 0
        assert forecast.predicted_score < forecast.current_score

    def test_detect_anomalies(self, predictor):
        """Test anomaly detection."""
        # Record normal scores
        for _ in range(5):
            compliance = {"score": 80.0, "passed": 16, "total": 20, "checks": {}, "details": {}}
            predictor.record_snapshot(compliance)

        # Record anomaly
        anomaly = {"score": 50.0, "passed": 10, "total": 20, "checks": {}, "details": {}}
        predictor.record_snapshot(anomaly)

        anomalies = predictor.detect_anomalies(threshold_std_dev=2.0)
        assert len(anomalies) >= 1
        assert any(a.score == 50.0 for a in anomalies)

    def test_analyze_trends(self, predictor):
        """Test trend analysis."""
        # Record improving trend
        for i in range(10):
            compliance = {
                "score": 70.0 + i * 3,
                "passed": 14 + i,
                "total": 20,
                "checks": {},
                "details": {},
            }
            predictor.record_snapshot(compliance)

        trends = predictor.analyze_trends(window_days=30)

        assert trends["trend_direction"] == "improving"
        assert trends["average_score"] > 70
        assert trends["improvement_rate"] > 0

    def test_get_risk_score(self, predictor):
        """Test risk score calculation."""
        # Record low scores (high risk)
        for _ in range(5):
            compliance = {"score": 60.0, "passed": 12, "total": 20, "checks": {}, "details": {}}
            predictor.record_snapshot(compliance)

        risk = predictor.get_risk_score()

        assert "score" in risk
        assert "level" in risk
        assert "factors" in risk
        assert risk["score"] > 0
        assert risk["level"] in ["low", "medium", "high", "critical"]

    def test_compliance_snapshot_serialization(self):
        """Test snapshot to/from dict conversion."""
        snapshot = ComplianceSnapshot(
            timestamp=datetime.now(),
            score=85.5,
            passed=17,
            total=20,
            checks={"test": True},
            metadata={"key": "value"},
        )

        # To dict
        data = snapshot.to_dict()
        assert data["score"] == 85.5
        assert data["passed"] == 17

        # From dict
        restored = ComplianceSnapshot.from_dict(data)
        assert restored.score == 85.5
        assert restored.passed == 17


# ============================================================================
# SCHEDULER ENGINE TESTS
# ============================================================================


class TestSchedulerEngine:
    """Tests for SchedulerEngine class."""

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """Create temporary repository."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".pmo").mkdir()
        return repo_path

    @pytest.fixture
    def scheduler(self, temp_repo):
        """Create scheduler engine."""
        return SchedulerEngine(repo_path=temp_repo)

    def test_init(self, scheduler, temp_repo):
        """Test scheduler initialization."""
        assert scheduler.repo_path == temp_repo
        assert scheduler.history_file.exists()
        assert scheduler.running is False
        assert isinstance(scheduler.tasks, dict)

    def test_schedule_daily(self, scheduler):
        """Test daily task scheduling."""
        task_id = scheduler.schedule_daily(hour=2, minute=30)

        assert task_id in scheduler.tasks
        task = scheduler.tasks[task_id]
        assert task.name == "Daily Remediation"
        assert task.trigger_type == TriggerType.CRON
        assert task.next_run is not None

    def test_schedule_weekly(self, scheduler):
        """Test weekly task scheduling."""
        task_id = scheduler.schedule_weekly(day_of_week=1, hour=3)

        assert task_id in scheduler.tasks
        task = scheduler.tasks[task_id]
        assert task.trigger_type == TriggerType.CRON
        assert task.next_run is not None

    def test_schedule_monthly(self, scheduler):
        """Test monthly task scheduling."""
        task_id = scheduler.schedule_monthly(day=15, hour=4)

        assert task_id in scheduler.tasks
        task = scheduler.tasks[task_id]
        assert task.trigger_type == TriggerType.CRON
        assert task.next_run is not None

    def test_on_event(self, scheduler):
        """Test event-triggered task registration."""
        called = []

        def handler():
            called.append(True)

        task_id = scheduler.on_event("test_event", handler)

        assert task_id in scheduler.tasks
        task = scheduler.tasks[task_id]
        assert task.trigger_type == TriggerType.EVENT
        assert task.schedule == "test_event"

    def test_trigger_event(self, scheduler):
        """Test triggering an event."""
        called = []

        def handler(**kwargs):
            called.append(kwargs)

        scheduler.on_event("test_event", handler)
        scheduler.trigger_event("test_event", data="test_data")

        # Process queue
        scheduler.start()
        time.sleep(0.5)
        scheduler.stop()

        assert len(called) > 0

    def test_run_task(self, scheduler):
        """Test running a task manually."""
        called = []

        def test_function():
            called.append(True)
            return {"status": "completed"}

        task_id = scheduler.schedule_daily(hour=2, function=test_function)
        result = scheduler.run_task(task_id)

        assert result is not None
        assert result.success is True
        assert len(called) == 1

    def test_get_tasks(self, scheduler):
        """Test getting all tasks."""
        scheduler.schedule_daily(hour=2)
        scheduler.schedule_weekly(day_of_week=1)

        tasks = scheduler.get_tasks()
        assert len(tasks) >= 2
        assert all("task_id" in t for t in tasks)

    def test_get_task_history(self, scheduler):
        """Test getting task history."""

        def test_function():
            return {"status": "completed"}

        task_id = scheduler.schedule_daily(hour=2, function=test_function)
        scheduler.run_task(task_id)

        history = scheduler.get_task_history(task_id=task_id)
        assert len(history) >= 1
        assert history[0]["task_id"] == task_id


# ============================================================================
# AUDIT TRAIL TESTS
# ============================================================================


class TestAuditTrail:
    """Tests for AuditTrail class."""

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """Create temporary repository."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / ".pmo").mkdir()
        return repo_path

    @pytest.fixture
    def audit(self, temp_repo):
        """Create audit trail."""
        return AuditTrail(repo_path=temp_repo)

    def test_init(self, audit, temp_repo):
        """Test audit trail initialization."""
        assert audit.repo_path == temp_repo
        assert audit.audit_file.exists()
        assert isinstance(audit.entries, list)

    def test_log_fix(self, audit):
        """Test logging a fix."""
        entry_id = audit.log_fix(
            fix_id="test-001",
            fix_type="dependency",
            description="Test fix",
            success=True,
            duration_ms=1250,
            files_modified=["requirements.txt"],
        )

        assert entry_id is not None
        assert len(audit.entries) == 1

        entry = audit.entries[0]
        assert entry.fix_id == "test-001"
        assert entry.success is True
        assert entry.duration_ms == 1250

    def test_log_rollback(self, audit):
        """Test logging a rollback."""
        # Log original fix
        entry_id = audit.log_fix(
            fix_id="test-002",
            fix_type="security",
            description="Original fix",
            success=True,
            duration_ms=1000,
            rollback_available=True,
        )

        # Log rollback
        audit.log_rollback(entry_id, success=True, duration_ms=500)

        # Should have 2 entries now (original + rollback)
        assert len(audit.entries) >= 2

        # Find rollback entry
        rollback = next((e for e in audit.entries if e.fix_type == "rollback"), None)
        assert rollback is not None

    def test_get_history_filtering(self, audit):
        """Test history filtering."""
        # Log multiple fixes
        audit.log_fix("dep-001", "dependency", "Dep fix", True, 1000)
        audit.log_fix("sec-001", "security", "Sec fix", True, 1500)
        audit.log_fix("dep-002", "dependency", "Dep fix 2", False, 800)

        # Filter by type
        dep_history = audit.get_history(fix_type="dependency")
        assert len(dep_history) == 2
        assert all(e.fix_type == "dependency" for e in dep_history)

        # Filter by success
        success_history = audit.get_history(success_only=True)
        assert all(e.success for e in success_history)

    def test_get_effectiveness_metrics(self, audit):
        """Test effectiveness metrics calculation."""
        # Log various fixes
        audit.log_fix("test-001", "dependency", "Fix 1", True, 1000)
        audit.log_fix("test-002", "dependency", "Fix 2", True, 1200)
        audit.log_fix("test-003", "security", "Fix 3", False, 800)

        metrics = audit.get_effectiveness_metrics()

        assert metrics["total_fixes"] == 3
        assert metrics["successful_fixes"] == 2
        assert metrics["failed_fixes"] == 1
        assert metrics["overall_success_rate"] == pytest.approx(66.67, rel=0.01)
        assert "by_type" in metrics

    def test_get_compliance_timeline(self, audit):
        """Test compliance timeline generation."""
        # Log fixes over several days
        for i in range(5):
            audit.log_fix(f"test-{i}", "config", f"Fix {i}", i % 2 == 0, 1000)

        timeline = audit.get_compliance_timeline(days=30)
        assert len(timeline) > 0
        assert all("date" in point for point in timeline)
        assert all("score" in point for point in timeline)

    def test_export_json(self, audit, temp_repo):
        """Test JSON export."""
        # Log some fixes
        audit.log_fix("test-001", "dependency", "Fix 1", True, 1000)
        audit.log_fix("test-002", "security", "Fix 2", True, 1200)

        output_file = temp_repo / "audit_export.json"
        audit.export_json(output_file)

        assert output_file.exists()

        # Verify content
        with open(output_file, "r") as f:
            data = json.load(f)
            assert len(data) == 2

    def test_export_csv(self, audit, temp_repo):
        """Test CSV export."""
        # Log some fixes
        audit.log_fix("test-001", "dependency", "Fix 1", True, 1000)
        audit.log_fix("test-002", "security", "Fix 2", False, 1200)

        output_file = temp_repo / "audit_export.csv"
        audit.export_csv(output_file)

        assert output_file.exists()

        # Verify content
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 3  # Header + 2 entries

    def test_get_most_common_failures(self, audit):
        """Test getting most common failures."""
        # Log multiple failures for same fix
        audit.log_fix("dep-001", "dependency", "Dep fix", False, 1000)
        audit.log_fix("dep-001", "dependency", "Dep fix", False, 1100)
        audit.log_fix("dep-001", "dependency", "Dep fix", True, 1200)
        audit.log_fix("sec-001", "security", "Sec fix", False, 800)

        failures = audit.get_most_common_failures(limit=5)

        assert len(failures) > 0
        assert failures[0]["fix_id"] == "dep-001"
        assert failures[0]["failure_count"] == 2

    def test_get_rollback_history(self, audit):
        """Test getting rollback history."""
        # Log fix and rollback
        entry_id = audit.log_fix("test-001", "config", "Fix", True, 1000, rollback_available=True)
        audit.log_rollback(entry_id, success=True, duration_ms=500)

        rollbacks = audit.get_rollback_history()
        assert len(rollbacks) >= 1
        assert all(e.fix_type == "rollback" for e in rollbacks)
