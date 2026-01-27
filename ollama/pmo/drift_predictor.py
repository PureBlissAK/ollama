"""Predictive Drift Detection - Forecast Compliance Issues Before They Occur.

This module provides predictive analytics for compliance drift detection.
It analyzes historical compliance data to forecast future issues and
provides early warning alerts.

Features:
    - Time-series analysis of compliance scores
    - Trend detection and forecasting
    - Anomaly detection (sudden compliance drops)
    - Risk scoring (0-100 based on drift velocity)
    - Early warning alerts
    - Root cause analysis

Example:
    >>> from ollama.pmo.drift_predictor import DriftPredictor
    >>> predictor = DriftPredictor(repo="kushin77/ollama")
    >>> forecast = predictor.predict_drift(days_ahead=30)
    >>> print(f"Predicted score in 30 days: {forecast['predicted_score']}%")
"""

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ComplianceSnapshot:
    """Single point-in-time compliance measurement."""

    timestamp: datetime
    score: float  # 0-100
    passed: int
    total: int
    checks: Dict[str, bool]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComplianceSnapshot":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            score=data["score"],
            passed=data["passed"],
            total=data["total"],
            checks=data.get("checks", {}),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
            "passed": self.passed,
            "total": self.total,
            "checks": self.checks,
            "metadata": self.metadata,
        }


@dataclass
class DriftForecast:
    """Prediction of future compliance drift."""

    current_score: float
    predicted_score: float
    prediction_date: datetime
    confidence: float  # 0-1
    risk_level: str  # low, medium, high, critical
    trending: str  # improving, stable, declining
    velocity: float  # Points per day
    likely_failures: List[str]  # Check names likely to fail

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_score": self.current_score,
            "predicted_score": self.predicted_score,
            "prediction_date": self.prediction_date.isoformat(),
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "trending": self.trending,
            "velocity": self.velocity,
            "likely_failures": self.likely_failures,
        }


class DriftPredictor:
    """Predictive drift detection and forecasting.

    Analyzes historical compliance data to predict future drift
    and provide early warnings before issues occur.

    Attributes:
        repo: GitHub repository (owner/repo format)
        repo_path: Local repository path
        history_file: Path to compliance history file
        min_data_points: Minimum snapshots needed for prediction

    Example:
        >>> predictor = DriftPredictor(repo="kushin77/ollama")
        >>> forecast = predictor.predict_drift(days_ahead=30)
        >>> if forecast.risk_level == 'high':
        ...     print(f"Warning: Score may drop to {forecast.predicted_score}%")
    """

    def __init__(
        self,
        repo: Optional[str] = None,
        repo_path: Optional[Path] = None,
        min_data_points: int = 5,
    ) -> None:
        """Initialize drift predictor.

        Args:
            repo: GitHub repository in owner/repo format
            repo_path: Local path to repository
            min_data_points: Minimum historical snapshots for prediction
        """
        self.repo = repo
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.min_data_points = min_data_points

        # History file
        self.history_file = self.repo_path / ".pmo" / "compliance_history.jsonl"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        # Ensure history file exists for tests and future appends
        try:
            self.history_file.touch(exist_ok=True)
        except Exception:
            pass

        # Load historical data
        self.snapshots: List[ComplianceSnapshot] = self._load_history()

    def record_snapshot(self, compliance_result: Dict[str, Any]) -> None:
        """Record a compliance snapshot to history.

        Args:
            compliance_result: Result from PMOAgent.validate_compliance()
        """
        snapshot = ComplianceSnapshot(
            timestamp=datetime.now(),
            score=compliance_result.get("score", 0),
            passed=compliance_result.get("passed", 0),
            total=compliance_result.get("total", 0),
            checks=compliance_result.get("checks", {}),
            metadata={
                "compliant": compliance_result.get("compliant", False),
                "details": compliance_result.get("details", {}),
            },
        )

        # Append to history file
        try:
            with open(self.history_file, "a") as f:
                f.write(json.dumps(snapshot.to_dict()) + "\n")

            # Add to memory
            self.snapshots.append(snapshot)
            logger.info(f"Recorded compliance snapshot: {snapshot.score}%")

        except Exception as e:
            logger.error(f"Failed to record snapshot: {e}")

    def predict_drift(
        self,
        days_ahead: int = 30,
    ) -> Optional[DriftForecast]:
        """Predict future compliance drift.

        Args:
            days_ahead: Number of days to forecast ahead

        Returns:
            Drift forecast or None if insufficient data

        Example:
            >>> forecast = predictor.predict_drift(days_ahead=30)
            >>> print(f"Risk: {forecast.risk_level}, Trend: {forecast.trending}")
        """
        if len(self.snapshots) < self.min_data_points:
            logger.warning(
                f"Insufficient data for prediction: "
                f"{len(self.snapshots)} < {self.min_data_points}"
            )
            return None

        # Sort by timestamp
        sorted_snapshots = sorted(self.snapshots, key=lambda s: s.timestamp)

        # Calculate trend
        current_score = sorted_snapshots[-1].score
        velocity = self._calculate_velocity(sorted_snapshots)

        # Predict future score
        predicted_score = current_score + (velocity * days_ahead)
        predicted_score = max(0, min(100, predicted_score))  # Clamp to 0-100

        # Calculate confidence based on data consistency
        confidence = self._calculate_confidence(sorted_snapshots)

        # Determine risk level
        risk_level = self._calculate_risk_level(predicted_score, velocity)

        # Determine trend
        trending = self._determine_trend(velocity)

        # Predict likely failures
        likely_failures = self._predict_failures(sorted_snapshots)

        prediction_date = datetime.now() + timedelta(days=days_ahead)

        return DriftForecast(
            current_score=current_score,
            predicted_score=predicted_score,
            prediction_date=prediction_date,
            confidence=confidence,
            risk_level=risk_level,
            trending=trending,
            velocity=velocity,
            likely_failures=likely_failures,
        )

    def detect_anomalies(
        self,
        threshold_std_dev: float = 2.0,
    ) -> List[ComplianceSnapshot]:
        """Detect anomalous compliance scores.

        Args:
            threshold_std_dev: Number of standard deviations for anomaly

        Returns:
            List of anomalous snapshots

        Example:
            >>> anomalies = predictor.detect_anomalies(threshold_std_dev=2.0)
            >>> for snapshot in anomalies:
            ...     print(f"Anomaly at {snapshot.timestamp}: {snapshot.score}%")
        """
        if len(self.snapshots) < 3:
            return []

        # Calculate mean and std dev
        scores = [s.score for s in self.snapshots]
        mean_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores)

        # Find anomalies
        anomalies: List[ComplianceSnapshot] = []
        for snapshot in self.snapshots:
            z_score = abs(snapshot.score - mean_score) / std_dev if std_dev > 0 else 0
            if z_score >= threshold_std_dev:
                anomalies.append(snapshot)
                logger.warning(f"Anomaly detected: {snapshot.score}% " f"(z-score: {z_score:.2f})")

        return anomalies

    def analyze_trends(
        self,
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """Analyze compliance trends over time.

        Args:
            window_days: Rolling window size in days

        Returns:
            Trend analysis results

        Example:
            >>> trends = predictor.analyze_trends(window_days=30)
            >>> print(f"30-day trend: {trends['trend_direction']}")
        """
        if not self.snapshots:
            return {
                "trend_direction": "unknown",
                "average_score": 0,
                "score_volatility": 0,
                "improvement_rate": 0,
            }

        # Filter to window
        cutoff_date = datetime.now() - timedelta(days=window_days)
        windowed = [s for s in self.snapshots if s.timestamp >= cutoff_date]

        if not windowed:
            windowed = self.snapshots  # Use all if window too narrow

        # Calculate metrics
        scores = [s.score for s in windowed]
        avg_score = statistics.mean(scores)
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0

        # Calculate improvement rate
        if len(windowed) >= 2:
            first_half = scores[: len(scores) // 2]
            second_half = scores[len(scores) // 2 :]
            improvement = statistics.mean(second_half) - statistics.mean(first_half)
        else:
            improvement = 0

        # Determine direction
        velocity = self._calculate_velocity(windowed)
        if velocity > 0.5:
            direction = "improving"
        elif velocity < -0.5:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "trend_direction": direction,
            "average_score": avg_score,
            "score_volatility": volatility,
            "improvement_rate": improvement,
            "velocity": velocity,
            "data_points": len(windowed),
            "window_days": window_days,
        }

    def get_risk_score(self) -> Dict[str, Any]:
        """Calculate overall drift risk score.

        Returns:
            Risk assessment

        Example:
            >>> risk = predictor.get_risk_score()
            >>> print(f"Overall risk: {risk['score']}/100 ({risk['level']})")
        """
        if not self.snapshots:
            return {
                "score": 0,
                "level": "unknown",
                "factors": [],
            }

        risk_factors: List[Dict[str, Any]] = []
        total_risk = 0.0

        # Factor 1: Current compliance score (lower = higher risk)
        current = self.snapshots[-1].score
        if current < 80:
            risk = (80 - current) / 80 * 40  # Max 40 points
            total_risk += risk
            risk_factors.append(
                {
                    "name": "Low current compliance",
                    "severity": "high" if current < 60 else "medium",
                    "contribution": risk,
                }
            )

        # Factor 2: Negative velocity
        velocity = self._calculate_velocity(self.snapshots)
        if velocity < 0:
            risk = abs(velocity) * 10  # More negative = more risk
            risk = min(risk, 30)  # Max 30 points
            total_risk += risk
            risk_factors.append(
                {
                    "name": "Declining trend",
                    "severity": "high" if velocity < -2 else "medium",
                    "contribution": risk,
                }
            )

        # Factor 3: High volatility
        scores = [s.score for s in self.snapshots]
        if len(scores) > 1:
            volatility = statistics.stdev(scores)
            if volatility > 10:
                risk = min(volatility / 10 * 20, 20)  # Max 20 points
                total_risk += risk
                risk_factors.append(
                    {
                        "name": "High volatility",
                        "severity": "medium",
                        "contribution": risk,
                    }
                )

        # Factor 4: Recent anomalies
        anomalies = self.detect_anomalies(threshold_std_dev=2.0)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_anomalies = [a for a in anomalies if a.timestamp >= recent_cutoff]
        if recent_anomalies:
            risk = len(recent_anomalies) * 5  # 5 points per anomaly
            risk = min(risk, 10)  # Max 10 points
            total_risk += risk
            risk_factors.append(
                {
                    "name": "Recent anomalies",
                    "severity": "medium",
                    "contribution": risk,
                }
            )

        # Clamp to 0-100
        total_risk = min(total_risk, 100)

        # Determine level
        if total_risk >= 75:
            level = "critical"
        elif total_risk >= 50:
            level = "high"
        elif total_risk >= 25:
            level = "medium"
        else:
            level = "low"

        return {
            "score": round(total_risk, 2),
            "level": level,
            "factors": risk_factors,
            "timestamp": datetime.now().isoformat(),
        }

    def _load_history(self) -> List[ComplianceSnapshot]:
        """Load historical snapshots from file.

        Returns:
            List of compliance snapshots
        """
        snapshots: List[ComplianceSnapshot] = []

        if not self.history_file.exists():
            return snapshots

        try:
            with open(self.history_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        snapshot = ComplianceSnapshot.from_dict(data)
                        snapshots.append(snapshot)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Skipping invalid snapshot: {e}")
                        continue

            logger.info(f"Loaded {len(snapshots)} historical snapshots")

        except Exception as e:
            logger.error(f"Failed to load history: {e}")

        return snapshots

    def _calculate_velocity(self, snapshots: List[ComplianceSnapshot]) -> float:
        """Calculate compliance score velocity (points per day).

        Args:
            snapshots: Historical snapshots

        Returns:
            Velocity in points per day
        """
        if len(snapshots) < 2:
            return 0.0

        # Use linear regression for better accuracy
        # For simplicity, use first and last points
        first = snapshots[0]
        last = snapshots[-1]

        time_diff = (last.timestamp - first.timestamp).total_seconds() / 86400  # days
        if time_diff == 0:
            return 0.0

        score_diff = last.score - first.score
        velocity = score_diff / time_diff

        return velocity

    def _calculate_confidence(self, snapshots: List[ComplianceSnapshot]) -> float:
        """Calculate prediction confidence (0-1).

        Args:
            snapshots: Historical snapshots

        Returns:
            Confidence level (0-1)
        """
        # More data = higher confidence
        data_confidence = min(len(snapshots) / 20, 1.0)

        # Lower volatility = higher confidence
        scores = [s.score for s in snapshots]
        if len(scores) > 1:
            volatility = statistics.stdev(scores)
            volatility_confidence = max(0, 1 - (volatility / 50))
        else:
            volatility_confidence = 0.5

        # Average both factors
        confidence = (data_confidence + volatility_confidence) / 2

        return confidence

    def _calculate_risk_level(self, predicted_score: float, velocity: float) -> str:
        """Calculate risk level based on prediction.

        Args:
            predicted_score: Predicted future score
            velocity: Score velocity

        Returns:
            Risk level: low, medium, high, critical
        """
        if predicted_score < 60 or velocity < -2:
            return "critical"
        elif predicted_score < 75 or velocity < -1:
            return "high"
        elif predicted_score < 85 or velocity < -0.5:
            return "medium"
        else:
            return "low"

    def _determine_trend(self, velocity: float) -> str:
        """Determine trend direction.

        Args:
            velocity: Score velocity

        Returns:
            Trend: improving, stable, declining
        """
        if velocity > 0.5:
            return "improving"
        elif velocity < -0.5:
            return "declining"
        else:
            return "stable"

    def _predict_failures(self, snapshots: List[ComplianceSnapshot]) -> List[str]:
        """Predict which checks are likely to fail.

        Args:
            snapshots: Historical snapshots

        Returns:
            List of check names likely to fail
        """
        # Track failure frequency per check
        failure_counts: Dict[str, int] = defaultdict(int)
        total_counts: Dict[str, int] = defaultdict(int)

        for snapshot in snapshots:
            for check_name, passed in snapshot.checks.items():
                total_counts[check_name] += 1
                if not passed:
                    failure_counts[check_name] += 1

        # Find checks with >30% failure rate
        likely_failures: List[str] = []
        for check_name, total in total_counts.items():
            failures = failure_counts.get(check_name, 0)
            failure_rate = failures / total if total > 0 else 0

            if failure_rate > 0.3:  # 30% failure threshold
                likely_failures.append(check_name)

        return likely_failures
