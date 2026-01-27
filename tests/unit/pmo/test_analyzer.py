"""Unit tests for Repository Analyzer."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ollama.pmo.analyzer import RepositoryAnalyzer


class TestRepositoryAnalyzer:
    """Test suite for RepositoryAnalyzer class."""

    def test_init_valid_path(self, tmp_path: Path) -> None:
        """Test initialization with valid repository path."""
        analyzer = RepositoryAnalyzer(tmp_path)
        assert analyzer.repo_path == tmp_path
        assert analyzer.confidence_threshold == 0.7

    def test_init_custom_confidence(self, tmp_path: Path) -> None:
        """Test initialization with custom confidence threshold."""
        analyzer = RepositoryAnalyzer(tmp_path, confidence_threshold=0.85)
        assert analyzer.confidence_threshold == 0.85

    def test_init_invalid_path(self) -> None:
        """Test initialization with non-existent path."""
        with pytest.raises(ValueError, match="does not exist"):
            RepositoryAnalyzer(Path("/nonexistent/path"))


class TestStackDetection:
    """Test technology stack detection."""

    def test_detect_python_stack(self, tmp_path: Path) -> None:
        """Test detection of Python project."""
        # Create Python project indicators
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "main.py").touch()

        analyzer = RepositoryAnalyzer(tmp_path)
        stack, confidence = analyzer._detect_stack()

        assert stack == "python"
        assert confidence > 0.5

    def test_detect_nodejs_stack(self, tmp_path: Path) -> None:
        """Test detection of Node.js project."""
        # Create Node.js project indicators
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "index.js").touch()

        analyzer = RepositoryAnalyzer(tmp_path)
        stack, confidence = analyzer._detect_stack()

        assert stack == "nodejs"
        assert confidence > 0.5

    def test_detect_go_stack(self, tmp_path: Path) -> None:
        """Test detection of Go project."""
        (tmp_path / "go.mod").write_text("module test")
        (tmp_path / "main.go").touch()

        analyzer = RepositoryAnalyzer(tmp_path)
        stack, confidence = analyzer._detect_stack()

        assert stack == "go"
        assert confidence > 0.5

    def test_detect_unknown_stack(self, tmp_path: Path) -> None:
        """Test detection with no clear stack."""
        analyzer = RepositoryAnalyzer(tmp_path)
        stack, confidence = analyzer._detect_stack()

        assert stack == "unknown"
        assert confidence == 0.0


class TestEnvironmentDetection:
    """Test environment detection."""

    @patch("subprocess.run")
    def test_detect_production_from_branch(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test production environment detection from git branch."""
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n")

        analyzer = RepositoryAnalyzer(tmp_path)
        env, confidence = analyzer._detect_environment()

        assert env == "production"
        assert confidence == 0.8

    @patch("subprocess.run")
    def test_detect_staging_from_branch(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test staging environment detection from git branch."""
        mock_run.return_value = MagicMock(returncode=0, stdout="staging\n")

        analyzer = RepositoryAnalyzer(tmp_path)
        env, confidence = analyzer._detect_environment()

        assert env == "staging"
        assert confidence == 0.8

    def test_detect_production_from_config(self, tmp_path: Path) -> None:
        """Test production environment detection from config file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "production.yaml").touch()

        analyzer = RepositoryAnalyzer(tmp_path)
        env, confidence = analyzer._detect_environment()

        assert env == "production"
        assert confidence == 0.7

    @patch("subprocess.run")
    def test_detect_development_default(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test default to development environment."""
        mock_run.return_value = MagicMock(returncode=1)

        analyzer = RepositoryAnalyzer(tmp_path)
        env, confidence = analyzer._detect_environment()

        assert env == "development"
        assert confidence == 0.5


class TestTeamDetection:
    """Test team/ownership detection."""

    def test_detect_team_from_codeowners(self, tmp_path: Path) -> None:
        """Test team detection from CODEOWNERS file."""
        (tmp_path / "CODEOWNERS").write_text("* @myorg/engineering-team\n")

        analyzer = RepositoryAnalyzer(tmp_path)
        team, confidence = analyzer._detect_team()

        assert team == "engineering-team"
        assert confidence == 0.9

    def test_detect_team_from_github_codeowners(self, tmp_path: Path) -> None:
        """Test team detection from .github/CODEOWNERS."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        (github_dir / "CODEOWNERS").write_text("* @company/platform-team\n")

        analyzer = RepositoryAnalyzer(tmp_path)
        team, confidence = analyzer._detect_team()

        assert team == "platform-team"
        assert confidence == 0.9

    def test_detect_team_from_package_json(self, tmp_path: Path) -> None:
        """Test team detection from package.json author."""
        package_data = {"name": "test", "author": "DataTeam Engineering"}
        (tmp_path / "package.json").write_text(json.dumps(package_data))

        analyzer = RepositoryAnalyzer(tmp_path)
        team, confidence = analyzer._detect_team()

        assert team == "datateam"
        assert confidence == 0.7

    def test_detect_team_default(self, tmp_path: Path) -> None:
        """Test default team assignment."""
        analyzer = RepositoryAnalyzer(tmp_path)
        team, confidence = analyzer._detect_team()

        assert team == "engineering"
        assert confidence == 0.5


class TestApplicationNameDetection:
    """Test application name detection."""

    def test_detect_from_package_json(self, tmp_path: Path) -> None:
        """Test name detection from package.json."""
        package_data = {"name": "my-awesome-app"}
        (tmp_path / "package.json").write_text(json.dumps(package_data))

        analyzer = RepositoryAnalyzer(tmp_path)
        app_name, confidence = analyzer._detect_application_name()

        assert app_name == "my-awesome-app"
        assert confidence == 0.9

    def test_detect_from_directory_name(self, tmp_path: Path) -> None:
        """Test fallback to directory name."""
        analyzer = RepositoryAnalyzer(tmp_path)
        app_name, confidence = analyzer._detect_application_name()

        assert app_name == tmp_path.name
        assert confidence == 0.6


class TestComponentDetection:
    """Test component detection."""

    def test_detect_api_component(self, tmp_path: Path) -> None:
        """Test API component detection."""
        (tmp_path / "api").mkdir()

        analyzer = RepositoryAnalyzer(tmp_path)
        component, confidence = analyzer._detect_component()

        assert component == "api"
        assert confidence == 0.7

    def test_detect_frontend_component(self, tmp_path: Path) -> None:
        """Test frontend component detection."""
        (tmp_path / "frontend").mkdir()

        analyzer = RepositoryAnalyzer(tmp_path)
        component, confidence = analyzer._detect_component()

        assert component == "frontend"
        assert confidence == 0.7

    def test_detect_database_component(self, tmp_path: Path) -> None:
        """Test database component detection."""
        (tmp_path / "migrations").mkdir()

        analyzer = RepositoryAnalyzer(tmp_path)
        component, confidence = analyzer._detect_component()

        assert component == "database"
        assert confidence == 0.7

    def test_detect_core_default(self, tmp_path: Path) -> None:
        """Test default to core component."""
        analyzer = RepositoryAnalyzer(tmp_path)
        component, confidence = analyzer._detect_component()

        assert component == "core"
        assert confidence == 0.5


class TestPriorityDetection:
    """Test priority detection."""

    def test_detect_p0_from_name(self, tmp_path: Path) -> None:
        """Test P0 priority detection from project name."""
        # Create directory with 'critical' in name
        critical_dir = tmp_path / "critical-service"
        critical_dir.mkdir()

        analyzer = RepositoryAnalyzer(critical_dir)
        priority, confidence = analyzer._detect_priority()

        assert priority == "p0"
        assert confidence > 0.5

    def test_detect_p2_from_readme(self, tmp_path: Path) -> None:
        """Test P2 priority detection from README."""
        (tmp_path / "README.md").write_text(
            "# Standard Service\nThis is a normal priority project."
        )

        analyzer = RepositoryAnalyzer(tmp_path)
        priority, confidence = analyzer._detect_priority()

        assert priority == "p2"
        assert confidence > 0.4

    def test_detect_priority_default(self, tmp_path: Path) -> None:
        """Test default priority assignment."""
        analyzer = RepositoryAnalyzer(tmp_path)
        priority, confidence = analyzer._detect_priority()

        assert priority == "p1"
        assert confidence == 0.4


class TestLifecycleDetection:
    """Test lifecycle status detection."""

    def test_detect_sunset_from_readme(self, tmp_path: Path) -> None:
        """Test sunset status from README."""
        (tmp_path / "README.md").write_text("# DEPRECATED - This project is no longer maintained")

        analyzer = RepositoryAnalyzer(tmp_path)
        status, confidence = analyzer._detect_lifecycle_status()

        assert status == "sunset"
        assert confidence == 0.8

    def test_detect_maintenance_from_readme(self, tmp_path: Path) -> None:
        """Test maintenance status from README."""
        (tmp_path / "README.md").write_text("# Project\nCurrently in maintenance mode.")

        analyzer = RepositoryAnalyzer(tmp_path)
        status, confidence = analyzer._detect_lifecycle_status()

        assert status == "maintenance"
        assert confidence == 0.7

    def test_detect_active_default(self, tmp_path: Path) -> None:
        """Test default to active status."""
        analyzer = RepositoryAnalyzer(tmp_path)
        status, confidence = analyzer._detect_lifecycle_status()

        assert status == "active"
        assert confidence == 0.6


class TestGitRepoDetection:
    """Test Git repository URL detection."""

    @patch("subprocess.run")
    def test_detect_github_ssh_url(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test GitHub SSH URL detection."""
        mock_run.return_value = MagicMock(returncode=0, stdout="git@github.com:myorg/myrepo.git\n")

        analyzer = RepositoryAnalyzer(tmp_path)
        repo_url = analyzer._detect_git_repo()

        assert repo_url == "github.com/myorg/myrepo"

    @patch("subprocess.run")
    def test_detect_github_https_url(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test GitHub HTTPS URL detection."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="https://github.com/myorg/myrepo.git\n"
        )

        analyzer = RepositoryAnalyzer(tmp_path)
        repo_url = analyzer._detect_git_repo()

        assert repo_url == "github.com/myorg/myrepo"

    @patch("subprocess.run")
    def test_detect_git_repo_fallback(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Test fallback when git command fails."""
        mock_run.return_value = MagicMock(returncode=1)

        analyzer = RepositoryAnalyzer(tmp_path)
        repo_url = analyzer._detect_git_repo()

        assert "github.com/unknown/" in repo_url


class TestCompleteAnalysis:
    """Test complete repository analysis."""

    def test_analyze_python_project(self, tmp_path: Path) -> None:
        """Test complete analysis of Python project."""
        # Setup Python project
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "main.py").touch()
        (tmp_path / "api").mkdir()
        (tmp_path / "CODEOWNERS").write_text("* @myorg/platform\n")

        package_data = {"name": "my-service"}
        (tmp_path / "package.json").write_text(json.dumps(package_data))

        analyzer = RepositoryAnalyzer(tmp_path)
        result = analyzer.analyze()

        # Verify organizational metadata
        assert "organizational" in result
        assert result["organizational"]["team"] == "platform"
        assert result["organizational"]["application"] == "my-service"
        assert result["organizational"]["component"] == "api"

        # Verify technical metadata
        assert "technical" in result
        assert result["technical"]["stack"] == "python"

        # Verify confidence scores
        assert "confidence" in result
        assert result["confidence"]["overall"] > 0.0
        assert result["confidence"]["stack"] > 0.5

        # Verify needs_review flag
        assert "needs_review" in result
        assert isinstance(result["needs_review"], bool)

    def test_analyze_nodejs_project(self, tmp_path: Path) -> None:
        """Test complete analysis of Node.js project."""
        package_data = {"name": "frontend-app", "author": "UI Team"}
        (tmp_path / "package.json").write_text(json.dumps(package_data))
        (tmp_path / "index.js").touch()
        (tmp_path / "frontend").mkdir()

        analyzer = RepositoryAnalyzer(tmp_path)
        result = analyzer.analyze()

        assert result["organizational"]["application"] == "frontend-app"
        assert result["organizational"]["component"] == "frontend"
        assert result["technical"]["stack"] == "nodejs"

    def test_generate_pmo_yaml(self, tmp_path: Path) -> None:
        """Test pmo.yaml generation."""
        # Setup project
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "main.py").touch()

        analyzer = RepositoryAnalyzer(tmp_path)
        pmo_data = analyzer.generate_pmo_yaml()

        # Verify pmo.yaml structure
        assert "organizational" in pmo_data
        assert "lifecycle" in pmo_data
        assert "business" in pmo_data
        assert "technical" in pmo_data
        assert "financial" in pmo_data
        assert "git" in pmo_data

        # Verify file was created
        pmo_file = tmp_path / "pmo.yaml"
        assert pmo_file.exists()

        # Verify confidence and needs_review excluded
        assert "confidence" not in pmo_data
        assert "needs_review" not in pmo_data

    def test_high_confidence_analysis(self, tmp_path: Path) -> None:
        """Test high confidence when all indicators present."""
        # Create comprehensive project structure
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'myapp'\n")
        (tmp_path / "main.py").touch()
        (tmp_path / "api").mkdir()
        (tmp_path / "CODEOWNERS").write_text("* @company/backend\n")
        (tmp_path / "README.md").write_text("# Critical Production Service")
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "production.yaml").touch()

        analyzer = RepositoryAnalyzer(tmp_path, confidence_threshold=0.7)
        result = analyzer.analyze()

        # Should have high overall confidence
        assert result["confidence"]["overall"] >= 0.6
        assert result["needs_review"] is False  # Above threshold

    def test_low_confidence_analysis(self, tmp_path: Path) -> None:
        """Test low confidence when few indicators present."""
        # Empty project
        analyzer = RepositoryAnalyzer(tmp_path, confidence_threshold=0.7)
        result = analyzer.analyze()

        # Should have low overall confidence
        assert result["confidence"]["overall"] < 0.7
        assert result["needs_review"] is True  # Below threshold
