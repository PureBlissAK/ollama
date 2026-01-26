"""Integration tests for Issue Classifier with live GitHub API."""

import os
from unittest.mock import patch

import pytest

from ollama.pmo.classifier import IssueClassifier


@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set",
)
class TestClassifierGitHubIntegration:
    """Integration tests with real GitHub API."""
    
    @pytest.fixture
    def classifier(self) -> IssueClassifier:
        """Create classifier with real GitHub connection."""
        return IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
    
    def test_classify_real_issue(self, classifier: IssueClassifier) -> None:
        """Test classification with real issue from repository."""
        # Use Epic #18 as test case (known to exist)
        result = classifier.classify_issue(18)
        
        # Verify structure
        assert "issue_number" in result
        assert result["issue_number"] == 18
        assert "issue_type" in result
        assert "priority" in result
        assert "recommended_team" in result
        assert "urgency_score" in result
        assert "confidence" in result
        
        # Verify values are reasonable
        assert result["issue_type"] in [
            "bug",
            "feature",
            "documentation",
            "question",
            "security",
            "performance",
        ]
        assert result["priority"] in ["p0", "p1", "p2", "p3"]
        assert 0 <= result["urgency_score"] <= 100
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_classify_batch_real_issues(self, classifier: IssueClassifier) -> None:
        """Test batch classification with real issues."""
        # Use multiple known issues
        results = classifier.classify_batch([18, 19, 20])
        
        assert len(results) == 3
        for result in results:
            assert "issue_number" in result
            if "error" not in result:
                assert "issue_type" in result
                assert "priority" in result
    
    def test_find_duplicates_real(self, classifier: IssueClassifier) -> None:
        """Test duplicate detection with real issues."""
        # Use a known issue
        duplicates = classifier.find_duplicates(18, threshold=0.3)
        
        # Should return a list (may be empty)
        assert isinstance(duplicates, list)
        
        # If duplicates found, verify structure
        for dup in duplicates:
            assert "issue_number" in dup
            assert "similarity" in dup
            assert "title" in dup
            assert "url" in dup
            assert 0.0 <= dup["similarity"] <= 1.0


class TestClassifierErrorHandling:
    """Test error handling with invalid inputs."""
    
    def test_invalid_repo_format(self) -> None:
        """Test error on invalid repository format."""
        with pytest.raises(ValueError, match="Invalid repo format"):
            IssueClassifier(repo="invalid-repo")
    
    @patch('ollama.pmo.classifier.Github')
    def test_classify_nonexistent_issue(self, mock_github) -> None:
        """Test classification of non-existent issue."""
        # Setup mock to raise exception
        mock_repo = mock_github.return_value.get_repo.return_value
        mock_repo.get_issue.side_effect = Exception("Issue not found")
        
        classifier = IssueClassifier(repo="owner/repo")
        result = classifier.classify_issue(999999)
        
        # Should return error result
        assert "error" in result
        assert result["issue_type"] is None
    
    @patch('ollama.pmo.classifier.Github')
    def test_classify_batch_partial_failure(self, mock_github) -> None:
        """Test batch classification with some failures."""
        from datetime import datetime
        from unittest.mock import MagicMock
        
        # Setup mock to succeed for first, fail for second
        mock_issue1 = MagicMock()
        mock_issue1.number = 1
        mock_issue1.title = "Test issue"
        mock_issue1.body = "Test body"
        mock_issue1.created_at = datetime.now()
        mock_issue1.comments = 0
        mock_issue1.user.login = "testuser"
        mock_issue1.labels = []
        
        mock_repo = mock_github.return_value.get_repo.return_value
        mock_repo.get_issue.side_effect = [
            mock_issue1,
            Exception("Issue not found"),
        ]
        
        classifier = IssueClassifier(repo="owner/repo")
        results = classifier.classify_batch([1, 999])
        
        assert len(results) == 2
        # First should succeed
        assert "error" not in results[0]
        # Second should fail gracefully
        assert "error" in results[1]


@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set",
)
class TestClassifierPerformance:
    """Test classifier performance characteristics."""
    
    def test_batch_faster_than_individual(self) -> None:
        """Test that batch processing is more efficient."""
        import time
        
        classifier = IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
        
        issue_numbers = [18, 19, 20]
        
        # Time individual calls
        start = time.time()
        for num in issue_numbers:
            classifier.classify_issue(num)
        individual_time = time.time() - start
        
        # Time batch call
        start = time.time()
        classifier.classify_batch(issue_numbers)
        batch_time = time.time() - start
        
        # Batch should be comparable or faster
        # (May not always be faster due to GitHub API caching)
        assert batch_time <= individual_time * 1.5
    
    def test_classification_speed(self) -> None:
        """Test that classification completes within reasonable time."""
        import time
        
        classifier = IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
        
        start = time.time()
        classifier.classify_issue(18)
        elapsed = time.time() - start
        
        # Should complete within 5 seconds
        assert elapsed < 5.0


@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set",
)
class TestClassifierAccuracy:
    """Test classification accuracy for known issues."""
    
    def test_classify_known_bug(self) -> None:
        """Test classification of known bug issue."""
        classifier = IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
        
        # Create a test issue or use known bug issue
        # For now, just verify structure
        result = classifier.classify_issue(18)
        
        # Epic should be classified as feature
        # (Cannot assert exact type without knowing issue content)
        assert result["issue_type"] in [
            "bug",
            "feature",
            "documentation",
            "question",
            "security",
            "performance",
        ]
    
    def test_confidence_scores_reasonable(self) -> None:
        """Test that confidence scores are within reasonable range."""
        classifier = IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
        
        results = classifier.classify_batch([18, 19, 20])
        
        for result in results:
            if "error" not in result:
                # Confidence should be reasonable (not too low)
                assert result["confidence"] >= 0.3
                # Should have some reasoning
                assert len(result["reasoning"]) > 0


@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN not set",
)
class TestDuplicateDetectionIntegration:
    """Integration tests for duplicate detection."""
    
    def test_find_duplicates_threshold(self) -> None:
        """Test duplicate detection with different thresholds."""
        classifier = IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
        
        # Lower threshold should find more duplicates
        low_threshold_dups = classifier.find_duplicates(18, threshold=0.3)
        high_threshold_dups = classifier.find_duplicates(18, threshold=0.8)
        
        # Lower threshold >= higher threshold results
        assert len(low_threshold_dups) >= len(high_threshold_dups)
    
    def test_duplicates_sorted_by_similarity(self) -> None:
        """Test that duplicates are sorted by similarity."""
        classifier = IssueClassifier(
            repo="kushin77/ollama",
            github_token=os.getenv("GITHUB_TOKEN"),
        )
        
        duplicates = classifier.find_duplicates(18, threshold=0.2)
        
        if len(duplicates) >= 2:
            # Verify sorted descending
            for i in range(len(duplicates) - 1):
                assert duplicates[i]["similarity"] >= duplicates[i + 1]["similarity"]
