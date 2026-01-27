"""Unit tests for Issue Classifier."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from ollama.pmo.classifier import IssueClassifier


class TestIssueClassifierInit:
    """Test IssueClassifier initialization."""

    def test_init_valid_repo(self) -> None:
        """Test initialization with valid repository."""
        with patch("ollama.pmo.classifier.Github"):
            classifier = IssueClassifier(repo="owner/repo")
            assert classifier.repo == "owner/repo"

    def test_init_with_token(self) -> None:
        """Test initialization with GitHub token."""
        with patch("ollama.pmo.classifier.Github") as mock_github:
            classifier = IssueClassifier(repo="owner/repo", github_token="token123")
            mock_github.assert_called_once_with("token123")

    def test_init_invalid_repo_format(self) -> None:
        """Test initialization with invalid repo format."""
        with pytest.raises(ValueError, match="Invalid repo format"):
            IssueClassifier(repo="invalid-repo")


class TestIssueTypeClassification:
    """Test issue type classification."""

    @patch("ollama.pmo.classifier.Github")
    def test_classify_bug_from_title(self, mock_github: MagicMock) -> None:
        """Test bug classification from title."""
        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.title = "[BUG] Application crashes on startup"
        mock_issue.body = "The app fails to start."

        # Setup mock repository
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        issue_type, confidence = classifier._classify_type(mock_issue)

        assert issue_type == "bug"
        assert confidence > 0.5

    @patch("ollama.pmo.classifier.Github")
    def test_classify_feature_from_keywords(self, mock_github: MagicMock) -> None:
        """Test feature classification from keywords."""
        mock_issue = MagicMock()
        mock_issue.title = "Add support for dark mode"
        mock_issue.body = "It would be nice to have dark mode feature."

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        issue_type, confidence = classifier._classify_type(mock_issue)

        assert issue_type == "feature"
        assert confidence > 0.3

    @patch("ollama.pmo.classifier.Github")
    def test_classify_documentation(self, mock_github: MagicMock) -> None:
        """Test documentation classification."""
        mock_issue = MagicMock()
        mock_issue.title = "[DOCS] Fix typo in README"
        mock_issue.body = "There's a spelling error in the documentation."

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        issue_type, confidence = classifier._classify_type(mock_issue)

        assert issue_type == "documentation"
        assert confidence > 0.4

    @patch("ollama.pmo.classifier.Github")
    def test_classify_security_high_confidence(self, mock_github: MagicMock) -> None:
        """Test security classification with high confidence."""
        mock_issue = MagicMock()
        mock_issue.title = "[SECURITY] SQL injection vulnerability"
        mock_issue.body = "Found a security vulnerability that allows injection attacks."

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        issue_type, confidence = classifier._classify_type(mock_issue)

        assert issue_type == "security"
        assert confidence > 0.6


class TestPriorityScoring:
    """Test priority scoring."""

    @patch("ollama.pmo.classifier.Github")
    def test_score_p0_critical(self, mock_github: MagicMock) -> None:
        """Test P0 scoring for critical issues."""
        mock_issue = MagicMock()
        mock_issue.title = "URGENT: Production down - complete outage"
        mock_issue.body = "Critical issue affecting all users immediately."

        classifier = IssueClassifier(repo="owner/repo")
        priority, score = classifier._score_priority(mock_issue)

        assert priority == "p0"
        assert score >= 90

    @patch("ollama.pmo.classifier.Github")
    def test_score_p1_high_priority(self, mock_github: MagicMock) -> None:
        """Test P1 scoring for high priority issues."""
        mock_issue = MagicMock()
        mock_issue.title = "Important: Major feature broken for many users"
        mock_issue.body = "This is blocking core functionality."

        classifier = IssueClassifier(repo="owner/repo")
        priority, score = classifier._score_priority(mock_issue)

        assert priority == "p1"
        assert 70 <= score < 90

    @patch("ollama.pmo.classifier.Github")
    def test_score_p3_low_priority(self, mock_github: MagicMock) -> None:
        """Test P3 scoring for low priority issues."""
        mock_issue = MagicMock()
        mock_issue.title = "Nice to have: Small UI improvement"
        mock_issue.body = "This is a minor cosmetic enhancement."

        classifier = IssueClassifier(repo="owner/repo")
        priority, score = classifier._score_priority(mock_issue)

        assert priority == "p3"
        assert score < 50


class TestTeamRecommendation:
    """Test team recommendation."""

    @patch("ollama.pmo.classifier.Github")
    def test_recommend_backend_team(self, mock_github: MagicMock) -> None:
        """Test backend team recommendation."""
        mock_issue = MagicMock()
        mock_issue.title = "API endpoint returning wrong data"
        mock_issue.body = "The database query seems incorrect on the server."

        classifier = IssueClassifier(repo="owner/repo")
        team, confidence = classifier._recommend_team(mock_issue)

        assert team == "backend"
        assert confidence > 0.5

    @patch("ollama.pmo.classifier.Github")
    def test_recommend_frontend_team(self, mock_github: MagicMock) -> None:
        """Test frontend team recommendation."""
        mock_issue = MagicMock()
        mock_issue.title = "Button not rendering correctly"
        mock_issue.body = "CSS issue with the UI component in React."

        classifier = IssueClassifier(repo="owner/repo")
        team, confidence = classifier._recommend_team(mock_issue)

        assert team == "frontend"
        assert confidence > 0.5

    @patch("ollama.pmo.classifier.Github")
    def test_recommend_devops_team(self, mock_github: MagicMock) -> None:
        """Test devops team recommendation."""
        mock_issue = MagicMock()
        mock_issue.title = "Docker deployment failing in CI/CD"
        mock_issue.body = "Kubernetes pods not starting correctly."

        classifier = IssueClassifier(repo="owner/repo")
        team, confidence = classifier._recommend_team(mock_issue)

        assert team == "devops"
        assert confidence > 0.5

    @patch("ollama.pmo.classifier.Github")
    def test_recommend_default_team(self, mock_github: MagicMock) -> None:
        """Test default team recommendation."""
        mock_issue = MagicMock()
        mock_issue.title = "General question about the project"
        mock_issue.body = "Just wondering about something."

        classifier = IssueClassifier(repo="owner/repo")
        team, confidence = classifier._recommend_team(mock_issue)

        assert team == "engineering"
        assert confidence < 0.5


class TestUrgencyCalculation:
    """Test urgency score calculation."""

    @patch("ollama.pmo.classifier.Github")
    def test_urgency_critical_recent(self, mock_github: MagicMock) -> None:
        """Test urgency for recent critical issue."""
        mock_issue = MagicMock()
        mock_issue.created_at = datetime.now() - timedelta(hours=2)
        mock_issue.comments = 5

        classifier = IssueClassifier(repo="owner/repo")
        urgency = classifier._calculate_urgency(mock_issue, priority_score=95)

        assert urgency >= 95

    @patch("ollama.pmo.classifier.Github")
    def test_urgency_old_non_critical(self, mock_github: MagicMock) -> None:
        """Test urgency for old non-critical issue."""
        mock_issue = MagicMock()
        mock_issue.created_at = datetime.now() - timedelta(days=60)
        mock_issue.comments = 2

        classifier = IssueClassifier(repo="owner/repo")
        urgency = classifier._calculate_urgency(mock_issue, priority_score=50)

        # Old issues lose urgency
        assert urgency < 50

    @patch("ollama.pmo.classifier.Github")
    def test_urgency_many_comments(self, mock_github: MagicMock) -> None:
        """Test urgency boost from many comments."""
        mock_issue = MagicMock()
        mock_issue.created_at = datetime.now() - timedelta(days=5)
        mock_issue.comments = 15

        classifier = IssueClassifier(repo="owner/repo")
        urgency = classifier._calculate_urgency(mock_issue, priority_score=60)

        # Many comments increase urgency
        assert urgency > 60


class TestLabelGeneration:
    """Test suggested label generation."""

    @patch("ollama.pmo.classifier.Github")
    def test_generate_labels_bug_p0_backend(self, mock_github: MagicMock) -> None:
        """Test label generation for bug with priority and team."""
        classifier = IssueClassifier(repo="owner/repo")
        labels = classifier._generate_labels("bug", "p0", "backend")

        assert "bug" in labels
        assert "priority-p0" in labels
        assert "team-backend" in labels

    @patch("ollama.pmo.classifier.Github")
    def test_generate_labels_skip_generic_team(self, mock_github: MagicMock) -> None:
        """Test label generation skips generic engineering team."""
        classifier = IssueClassifier(repo="owner/repo")
        labels = classifier._generate_labels("feature", "p2", "engineering")

        assert "feature" in labels
        assert "priority-p2" in labels
        assert "team-engineering" not in labels  # Skipped


class TestCompleteClassification:
    """Test complete issue classification."""

    @patch("ollama.pmo.classifier.Github")
    def test_classify_issue_complete(self, mock_github: MagicMock) -> None:
        """Test complete issue classification."""
        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "[BUG] Critical: API endpoint crashes"
        mock_issue.body = (
            "Server error when calling /api/users endpoint. Production issue affecting all users."
        )
        mock_issue.created_at = datetime.now() - timedelta(hours=1)
        mock_issue.comments = 3
        mock_issue.user.login = "testuser"
        mock_issue.labels = []

        # Setup mock repository
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        result = classifier.classify_issue(123)

        # Verify structure
        assert result["issue_number"] == 123
        assert "issue_type" in result
        assert "priority" in result
        assert "recommended_team" in result
        assert "urgency_score" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "suggested_labels" in result
        assert "metadata" in result

        # Verify metadata
        assert result["metadata"]["title"] == mock_issue.title
        assert result["metadata"]["author"] == "testuser"
        assert result["metadata"]["comments"] == 3


class TestBatchClassification:
    """Test batch classification."""

    @patch("ollama.pmo.classifier.Github")
    def test_classify_batch_multiple_issues(self, mock_github: MagicMock) -> None:
        """Test batch classification of multiple issues."""
        # Setup mock issues
        mock_issue1 = MagicMock()
        mock_issue1.number = 1
        mock_issue1.title = "[BUG] Error"
        mock_issue1.body = "Bug description"
        mock_issue1.created_at = datetime.now()
        mock_issue1.comments = 0
        mock_issue1.user.login = "user1"
        mock_issue1.labels = []

        mock_issue2 = MagicMock()
        mock_issue2.number = 2
        mock_issue2.title = "[FEATURE] New feature"
        mock_issue2.body = "Feature description"
        mock_issue2.created_at = datetime.now()
        mock_issue2.comments = 0
        mock_issue2.user.login = "user2"
        mock_issue2.labels = []

        # Setup mock repository
        mock_repo = MagicMock()
        mock_repo.get_issue.side_effect = [mock_issue1, mock_issue2]
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        results = classifier.classify_batch([1, 2])

        assert len(results) == 2
        assert results[0]["issue_number"] == 1
        assert results[1]["issue_number"] == 2

    @patch("ollama.pmo.classifier.Github")
    def test_classify_batch_with_error(self, mock_github: MagicMock) -> None:
        """Test batch classification handles errors gracefully."""
        mock_repo = MagicMock()
        mock_repo.get_issue.side_effect = Exception("API error")
        mock_github.return_value.get_repo.return_value = mock_repo

        classifier = IssueClassifier(repo="owner/repo")
        results = classifier.classify_batch([999])

        assert len(results) == 1
        assert "error" in results[0]
        assert results[0]["issue_type"] is None


class TestDuplicateDetection:
    """Test duplicate issue detection."""

    @patch("ollama.pmo.classifier.Github")
    def test_find_duplicates_similar_titles(self, mock_github: MagicMock) -> None:
        """Test finding duplicates with similar titles."""
        # Setup target issue
        target_issue = MagicMock()
        target_issue.number = 123
        target_issue.title = "Bug in user authentication"

        # Setup potential duplicate
        duplicate_issue = MagicMock()
        duplicate_issue.number = 456
        duplicate_issue.title = "Bug in user authentication system"
        duplicate_issue.html_url = "https://github.com/owner/repo/issues/456"
        duplicate_issue.state = "open"
        duplicate_issue.created_at = datetime.now()

        # Setup mocks
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = target_issue

        mock_search_results = MagicMock()
        mock_search_results.__iter__ = MagicMock(return_value=iter([duplicate_issue]))
        mock_search_results.__getitem__ = MagicMock(return_value=[duplicate_issue])

        mock_client = MagicMock()
        mock_client.get_repo.return_value = mock_repo
        mock_client.search_issues.return_value = mock_search_results
        mock_github.return_value = mock_client

        classifier = IssueClassifier(repo="owner/repo")
        duplicates = classifier.find_duplicates(123, threshold=0.5)

        # Should find the duplicate
        assert len(duplicates) > 0
        assert duplicates[0]["issue_number"] == 456
        assert duplicates[0]["similarity"] >= 0.5
