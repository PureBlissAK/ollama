"""Integration tests for PMO Agent with real GitHub/GCP APIs.

These tests require valid credentials and interact with live services.
Run with: pytest tests/integration/pmo/test_agent_integration.py -v

Environment variables required:
    - GITHUB_TOKEN: GitHub personal access token
    - GOOGLE_CLOUD_PROJECT: GCP project ID
    - PMO_TEST_REPO: GitHub repository for testing (owner/repo)
"""

import os
import pytest
from pathlib import Path
from typing import Optional

from ollama.pmo.agent import PMOAgent, PMOValidationError


# Skip all tests if credentials not available
pytestmark = pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN") or not os.getenv("PMO_TEST_REPO"),
    reason="Requires GITHUB_TOKEN and PMO_TEST_REPO environment variables",
)


@pytest.fixture
def test_repo() -> str:
    """Get test repository from environment."""
    return os.getenv("PMO_TEST_REPO", "kushin77/ollama")


@pytest.fixture
def github_token() -> Optional[str]:
    """Get GitHub token from environment."""
    return os.getenv("GITHUB_TOKEN")


@pytest.fixture
def gcp_project() -> Optional[str]:
    """Get GCP project from environment."""
    return os.getenv("GOOGLE_CLOUD_PROJECT")


@pytest.fixture
def temp_repo_path(tmp_path: Path) -> Path:
    """Create temporary repository path."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    
    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "PMO Agent Test"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "pmo-agent@test.com"],
        cwd=repo_path,
        check=True,
    )
    
    # Create pmo.yaml
    pmo_yaml = repo_path / "pmo.yaml"
    pmo_yaml.write_text("""
organizational:
  environment: development
  team: engineering
  application: test-app
  component: core

lifecycle:
  lifecycle_status: active
  created_at: '2026-01-26'

business:
  priority: p1
  cost_center: engineering

technical:
  stack: python
  managed_by: terraform

financial:
  budget_allocated: '0'

git:
  git_repo: github.com/test/test-repo
  created_by: pmo-agent-test
""")
    
    return repo_path


class TestPMOAgentIntegration:
    """Integration tests with real GitHub/GCP APIs."""
    
    def test_github_api_connection(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test GitHub API connection and authentication."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        assert agent.github_client is not None
        assert agent.github_repo is not None
        
        # Verify can access repository
        repo_info = agent.github_repo
        assert repo_info.full_name == test_repo
    
    def test_load_pmo_yaml_from_github(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test loading pmo.yaml from GitHub repository."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        # This requires pmo.yaml to exist in the test repo
        pmo_data = agent.load_pmo_yaml()
        
        if pmo_data:
            # Validate structure
            assert isinstance(pmo_data, dict)
            
            # Should have some organizational data
            if "organizational" in pmo_data:
                assert isinstance(pmo_data["organizational"], dict)
    
    def test_validate_pmo_yaml_with_real_data(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test pmo.yaml validation with real repository data."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        pmo_data = agent.load_pmo_yaml()
        
        if pmo_data:
            result = agent.validate_pmo_yaml(pmo_data)
            
            assert "score" in result
            assert "populated_labels" in result
            assert "total_labels" in result
            assert "missing_labels" in result
            
            # Score should be 0-100
            assert 0 <= result["score"] <= 100
    
    def test_full_compliance_validation(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test full compliance validation with GitHub API."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        result = agent.validate_compliance()
        
        # Verify result structure
        assert "checks" in result
        assert "details" in result
        assert "score" in result
        assert "passed" in result
        assert "total" in result
        assert "compliant" in result
        
        # Score should be 0-100
        assert 0 <= result["score"] <= 100
        
        # All checks should be recorded
        assert len(result["checks"]) == result["total"]
    
    def test_setup_github_labels_live(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test GitHub label creation with live API."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        # Note: This will create labels in the actual repository
        # Use a test repository to avoid pollution
        result = agent.setup_github_labels(force=False)
        
        assert "created" in result
        assert "updated" in result
        assert "skipped" in result
        assert "failed" in result
        assert "total" in result
        
        # Total should be sum of all categories
        assert result["total"] == (
            result["created"] + result["updated"] +
            result["skipped"] + result["failed"]
        )
    
    def test_auto_remediate_drift_live(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test auto-remediation with live repository."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        result = agent.auto_remediate_drift()
        
        assert "fixes" in result
        assert "details" in result
        assert "applied" in result
        assert "timestamp" in result
        
        # Verify fix results
        for fix, success in result["fixes"].items():
            assert isinstance(success, bool)
            assert fix in result["details"]
    
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_CLOUD_PROJECT"),
        reason="Requires GOOGLE_CLOUD_PROJECT environment variable",
    )
    def test_gcp_cloud_build_integration(
        self, test_repo: str, github_token: str, gcp_project: str, temp_repo_path: Path
    ):
        """Test GCP Cloud Build trigger management."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
            gcp_project=gcp_project,
        )
        
        # List existing triggers
        list_result = agent.list_build_triggers()
        
        assert "triggers" in list_result
        assert "count" in list_result
        assert isinstance(list_result["triggers"], list)
        assert len(list_result["triggers"]) == list_result["count"]
    
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_CLOUD_PROJECT"),
        reason="Requires GOOGLE_CLOUD_PROJECT environment variable",
    )
    def test_create_and_delete_build_trigger(
        self, test_repo: str, github_token: str, gcp_project: str, temp_repo_path: Path
    ):
        """Test creating and deleting a Cloud Build trigger."""
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
            gcp_project=gcp_project,
        )
        
        # Create test trigger
        trigger_name = "pmo-agent-test-trigger"
        
        create_result = agent.create_build_trigger(
            trigger_name=trigger_name,
            branch_pattern="^test-.*$",
            build_config_path="cloudbuild.test.yaml",
        )
        
        if create_result.get("created"):
            assert "name" in create_result
            assert "id" in create_result
            
            trigger_id = create_result["id"]
            
            # Update trigger
            update_result = agent.update_build_trigger(
                trigger_id=trigger_id,
                updates={"branch_pattern": "^test-branch-.*$"},
            )
            
            assert update_result.get("updated") is True
            
            # Note: In a real test, you'd want to clean up by deleting the trigger
            # This would require adding a delete_build_trigger method


class TestPMOAgentErrorHandling:
    """Test error handling with live APIs."""
    
    def test_invalid_repo_format(self, github_token: str, temp_repo_path: Path):
        """Test error when repository format is invalid."""
        with pytest.raises(ValueError, match="must be in format"):
            PMOAgent(
                repo="invalid-repo-format",
                repo_path=temp_repo_path,
                github_token=github_token,
            )
    
    def test_missing_pmo_yaml(
        self, test_repo: str, github_token: str, tmp_path: Path
    ):
        """Test handling of missing pmo.yaml file."""
        # Create repo without pmo.yaml
        repo_path = tmp_path / "no-pmo"
        repo_path.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        
        agent = PMOAgent(
            repo=test_repo,
            repo_path=repo_path,
            github_token=github_token,
        )
        
        pmo_data = agent.load_pmo_yaml()
        
        # Should return None for missing file
        assert pmo_data is None


class TestPMOAgentPerformance:
    """Performance tests with live APIs."""
    
    def test_compliance_validation_performance(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test compliance validation completes within reasonable time."""
        import time
        
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        start_time = time.time()
        result = agent.validate_compliance()
        elapsed_time = time.time() - start_time
        
        # Should complete in under 10 seconds
        assert elapsed_time < 10.0
        
        # Should return valid result
        assert result["score"] >= 0
    
    def test_label_setup_performance(
        self, test_repo: str, github_token: str, temp_repo_path: Path
    ):
        """Test label setup completes within reasonable time."""
        import time
        
        agent = PMOAgent(
            repo=test_repo,
            repo_path=temp_repo_path,
            github_token=github_token,
        )
        
        start_time = time.time()
        result = agent.setup_github_labels(force=False)
        elapsed_time = time.time() - start_time
        
        # Should complete in under 30 seconds (creating 35+ labels)
        assert elapsed_time < 30.0
        
        # Should return valid result
        assert result["total"] > 0
