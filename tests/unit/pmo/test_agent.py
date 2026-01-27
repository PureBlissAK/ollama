"""Tests for PMO Agent."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

from ollama.pmo.agent import PMOAgent, PMOValidationError


@pytest.fixture
def valid_pmo_yaml():
    """Valid pmo.yaml fixture."""
    return {
        "organizational": {
            "project": "test-project",
            "team": "platform-engineering",
            "owner": "test@company.com",
            "department": "Engineering",
        },
        "lifecycle": {
            "lifecycle_status": "active",
            "environment": "production",
            "tier": "tier-1",
            "criticality": "high",
            "support_level": "24x7",
        },
        "business": {
            "business_unit": "Product",
            "product": "Test Product",
            "service_category": "Application",
            "sla_tier": "gold",
        },
        "technical": {
            "stack": "python",
            "architecture": "microservices",
            "data_classification": "confidential",
            "compliance_frameworks": "soc2,hipaa",
        },
        "financial": {
            "cost_center": "CC-12345",
            "budget_code": "ENG-2026-Q1",
            "charge_code": "TEST-001",
            "approved_budget": 50000,
        },
        "git": {
            "git_repo": "https://github.com/kushin77/test-repo",
            "git_branch": "main",
            "created_by": "creator@company.com",
        },
    }


@pytest.fixture
def temp_repo(tmp_path, valid_pmo_yaml):
    """Create temporary repository with pmo.yaml."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    # Create pmo.yaml
    pmo_file = repo_dir / "pmo.yaml"
    with open(pmo_file, "w") as f:
        yaml.dump(valid_pmo_yaml, f)

    # Create .git directory
    git_dir = repo_dir / ".git"
    git_dir.mkdir()

    return repo_dir


class TestPMOAgentInit:
    """Tests for PMOAgent initialization."""

    def test_valid_repo_format(self, temp_repo):
        """Test initialization with valid repo format."""
        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        assert agent.repo_owner == "kushin77"
        assert agent.repo_name == "test-repo"
        assert agent.repo_full_name == "kushin77/test-repo"
        assert agent.repo_path == temp_repo

    def test_invalid_repo_format(self):
        """Test initialization with invalid repo format."""
        with pytest.raises(ValueError, match="Invalid repo format"):
            PMOAgent(repo="invalid-repo-format")

    def test_missing_repo_path(self):
        """Test initialization with non-existent repo path."""
        with pytest.raises(PMOValidationError, match="Repository path not found"):
            PMOAgent(repo="kushin77/test-repo", repo_path="/nonexistent/path")


class TestPMOYAMLValidation:
    """Tests for pmo.yaml validation."""

    def test_load_valid_pmo_yaml(self, temp_repo):
        """Test loading valid pmo.yaml."""
        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        data = agent.load_pmo_yaml()

        assert isinstance(data, dict)
        assert "organizational" in data
        assert "lifecycle" in data
        assert "business" in data
        assert "technical" in data
        assert "financial" in data
        assert "git" in data

    def test_load_missing_pmo_yaml(self, tmp_path):
        """Test loading pmo.yaml when file doesn't exist."""
        repo_dir = tmp_path / "empty-repo"
        repo_dir.mkdir()

        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(repo_dir))

        with pytest.raises(PMOValidationError, match="pmo.yaml not found"):
            agent.load_pmo_yaml()

    def test_validate_complete_pmo_yaml(self, temp_repo, valid_pmo_yaml):
        """Test validation of complete pmo.yaml."""
        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        result = agent.validate_pmo_yaml(valid_pmo_yaml)

        assert result["valid"] is True
        assert result["score"] == 100
        assert result["populated_labels"] == 24
        assert result["total_labels"] == 24
        assert len(result["errors"]) == 0

    def test_validate_partial_pmo_yaml(self, temp_repo):
        """Test validation of partial pmo.yaml (min 20 labels)."""
        partial_data = {
            "organizational": {
                "project": "test-project",
                "team": "platform-engineering",
                "owner": "test@company.com",
                "department": "Engineering",
            },
            "lifecycle": {
                "lifecycle_status": "active",
                "environment": "production",
                "tier": "tier-1",
                "criticality": "high",
                "support_level": "24x7",
            },
            "business": {
                "business_unit": "Product",
                "product": "Test Product",
                "service_category": "Application",
                "sla_tier": "gold",
            },
            "technical": {
                "stack": "python",
                "architecture": "microservices",
                "data_classification": "confidential",
                "compliance_frameworks": "soc2",
            },
            "financial": {
                "cost_center": "CC-12345",
                "budget_code": "ENG-2026-Q1",
                "charge_code": "TEST-001",
                "approved_budget": 50000,
            },
            "git": {
                "git_repo": "https://github.com/kushin77/test-repo",
                "git_branch": "main",
                # Missing 'created_by' (23/24 labels)
            },
        }

        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        result = agent.validate_pmo_yaml(partial_data)

        assert result["valid"] is True  # Still valid with 23/24
        assert result["populated_labels"] == 23
        assert len(result["errors"]) == 1
        assert any("created_by" in err for err in result["errors"])

    def test_validate_insufficient_labels(self, temp_repo):
        """Test validation fails with <20 labels."""
        insufficient_data = {
            "organizational": {
                "project": "test-project",
                "team": "platform-engineering",
            },
            "lifecycle": {
                "lifecycle_status": "active",
            },
            "business": {},
            "technical": {},
            "financial": {},
            "git": {},
        }

        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        result = agent.validate_pmo_yaml(insufficient_data)

        assert result["valid"] is False  # <20 labels
        assert result["populated_labels"] < 20
        assert len(result["errors"]) > 0

    def test_validate_missing_category(self, temp_repo):
        """Test validation fails with missing category."""
        incomplete_data = {
            "organizational": {
                "project": "test-project",
                "team": "platform-engineering",
                "owner": "test@company.com",
                "department": "Engineering",
            },
            # Missing 'lifecycle' category
            "business": {},
            "technical": {},
            "financial": {},
            "git": {},
        }

        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        result = agent.validate_pmo_yaml(incomplete_data)

        assert result["valid"] is False
        assert any("Missing category: lifecycle" in err for err in result["errors"])


class TestComplianceValidation:
    """Tests for full compliance validation."""

    def test_validate_compliance_all_passing(self, temp_repo):
        """Test full compliance with all checks passing."""
        # Setup mock GitHub repo
        with patch("ollama.pmo.agent.GITHUB_AVAILABLE", True):
            with patch.object(PMOAgent, "__init__", lambda self, *args, **kwargs: None):
                agent = PMOAgent.__new__(PMOAgent)
                agent.repo_path = temp_repo
                agent.github_repo = None  # No GitHub API

                # Create workflows directory
                workflows_dir = temp_repo / ".github" / "workflows"
                workflows_dir.mkdir(parents=True)
                (workflows_dir / "pmo-validation.yml").touch()
                (workflows_dir / "compliance-check.yml").touch()

                # Create hooks directory
                hooks_dir = temp_repo / ".git" / "hooks"
                hooks_dir.mkdir(parents=True, exist_ok=True)
                pre_commit = hooks_dir / "pre-commit"
                pre_commit.touch()
                pre_commit.chmod(0o755)
                commit_msg = hooks_dir / "commit-msg"
                commit_msg.touch()
                commit_msg.chmod(0o755)

                # Mock subprocess for GPG check
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = Mock(stdout="true\n", returncode=0)

                    result = agent.validate_compliance()

                assert result["checks"]["pmo_yaml"] is True
                assert result["checks"]["workflows"] is True
                assert result["checks"]["git_hooks"] is True
                assert result["checks"]["gpg_signing"] is True
                assert result["score"] > 0


class TestAutoRemediation:
    """Tests for auto-remediation features."""

    def test_auto_remediate_enables_gpg(self, temp_repo):
        """Test auto-remediation enables GPG signing."""
        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        # Mock successful git config
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = agent.auto_remediate_drift()

        assert "gpg_signing" in result["fixes"]


class TestGitHubLabelSetup:
    """Tests for GitHub label setup."""

    def test_setup_labels_without_github(self, temp_repo):
        """Test label setup fails without GitHub API."""
        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        with pytest.raises(RuntimeError, match="GitHub API not available"):
            agent.setup_github_labels()


class TestPRValidation:
    """Tests for PR compliance validation."""

    def test_validate_pr_without_github(self, temp_repo):
        """Test PR validation fails without GitHub API."""
        agent = PMOAgent(repo="kushin77/test-repo", repo_path=str(temp_repo))

        with pytest.raises(RuntimeError, match="GitHub API not available"):
            agent.validate_pr_compliance(pr_number=1)
