"""Integration tests for Repository Analyzer."""

import os
from pathlib import Path

import pytest

from ollama.pmo.analyzer import RepositoryAnalyzer


# Skip integration tests if environment not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("PMO_RUN_INTEGRATION_TESTS"),
    reason="Integration tests skipped (set PMO_RUN_INTEGRATION_TESTS=1 to enable)",
)


class TestRepositoryAnalyzerIntegration:
    """Integration tests for RepositoryAnalyzer with real projects."""
    
    def test_analyze_ollama_repository(self) -> None:
        """Test analysis of ollama repository."""
        # Analyze current repository
        repo_path = Path(__file__).parent.parent.parent.parent
        
        analyzer = RepositoryAnalyzer(repo_path, confidence_threshold=0.6)
        result = analyzer.analyze()
        
        # Verify structure
        assert 'organizational' in result
        assert 'technical' in result
        assert 'confidence' in result
        
        # Verify Python stack detected
        assert result['technical']['stack'] == 'python'
        assert result['confidence']['stack'] > 0.5
        
        # Verify confidence scores
        assert 0.0 <= result['confidence']['overall'] <= 1.0
        assert isinstance(result['needs_review'], bool)
    
    def test_generate_pmo_yaml_complete(self, tmp_path: Path) -> None:
        """Test complete pmo.yaml generation."""
        # Create sample Python project
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        
        # Add Python indicators
        (project_dir / "requirements.txt").write_text("fastapi>=0.104.0\n")
        (project_dir / "main.py").write_text("print('Hello')")
        (project_dir / "api").mkdir()
        
        # Add package.json for app name
        import json
        package_data = {"name": "test-app", "version": "1.0.0"}
        (project_dir / "package.json").write_text(json.dumps(package_data))
        
        # Analyze and generate
        analyzer = RepositoryAnalyzer(project_dir)
        pmo_data = analyzer.generate_pmo_yaml()
        
        # Verify pmo.yaml structure
        assert 'organizational' in pmo_data
        assert 'lifecycle' in pmo_data
        assert 'business' in pmo_data
        assert 'technical' in pmo_data
        assert 'financial' in pmo_data
        assert 'git' in pmo_data
        
        # Verify detected values
        assert pmo_data['technical']['stack'] == 'python'
        assert pmo_data['organizational']['application'] == 'test-app'
        assert pmo_data['organizational']['component'] == 'api'
        
        # Verify file created
        pmo_file = project_dir / 'pmo.yaml'
        assert pmo_file.exists()
        
        # Verify no internal fields in output
        assert 'confidence' not in pmo_data
        assert 'needs_review' not in pmo_data
    
    def test_confidence_scoring_accuracy(self) -> None:
        """Test confidence scoring with known project."""
        # Analyze ollama repository (comprehensive project)
        repo_path = Path(__file__).parent.parent.parent.parent
        
        analyzer = RepositoryAnalyzer(repo_path)
        result = analyzer.analyze()
        
        # Should have high confidence due to comprehensive structure
        assert result['confidence']['stack'] > 0.7  # Clear Python project
        assert result['confidence']['application'] > 0.6  # Has package metadata
        
        # Overall confidence should be reasonable
        assert result['confidence']['overall'] > 0.5
    
    def test_multi_stack_detection(self, tmp_path: Path) -> None:
        """Test detection in mixed-language project."""
        # Create project with Python + Node.js
        (tmp_path / "requirements.txt").touch()
        (tmp_path / "package.json").write_text('{"name": "hybrid"}')
        (tmp_path / "main.py").touch()
        (tmp_path / "index.js").touch()
        
        analyzer = RepositoryAnalyzer(tmp_path)
        result = analyzer.analyze()
        
        # Should detect primary stack (likely Python due to file count)
        assert result['technical']['stack'] in ['python', 'nodejs']
        assert result['confidence']['stack'] > 0.0
    
    def test_performance_benchmark(self) -> None:
        """Benchmark analyzer performance."""
        import time
        
        repo_path = Path(__file__).parent.parent.parent.parent
        analyzer = RepositoryAnalyzer(repo_path)
        
        start = time.time()
        result = analyzer.analyze()
        elapsed = time.time() - start
        
        # Should complete analysis in <5 seconds
        assert elapsed < 5.0, f"Analysis took {elapsed:.2f}s (expected <5s)"
        
        # Should return valid result
        assert result['confidence']['overall'] >= 0.0


class TestRepositoryAnalyzerErrorHandling:
    """Test error handling in RepositoryAnalyzer."""
    
    def test_missing_git_repo_graceful_fallback(self, tmp_path: Path) -> None:
        """Test graceful fallback when git commands fail."""
        # Create non-git directory
        analyzer = RepositoryAnalyzer(tmp_path)
        
        # Should not crash, should use fallbacks
        result = analyzer.analyze()
        
        assert 'organizational' in result
        assert 'git' in result
        # Should have fallback git repo URL
        assert 'github.com/unknown/' in result['git']['git_repo']
    
    def test_corrupted_package_json(self, tmp_path: Path) -> None:
        """Test handling of corrupted package.json."""
        # Create invalid package.json
        (tmp_path / "package.json").write_text("{ invalid json }")
        
        analyzer = RepositoryAnalyzer(tmp_path)
        result = analyzer.analyze()
        
        # Should not crash, should use fallback app name
        assert result['organizational']['application'] == tmp_path.name
    
    def test_large_repository_performance(self, tmp_path: Path) -> None:
        """Test performance with large repository (limited scan)."""
        # Create many files
        for i in range(150):
            (tmp_path / f"file{i}.py").touch()
        
        import time
        analyzer = RepositoryAnalyzer(tmp_path)
        
        start = time.time()
        stack, _ = analyzer._detect_stack()
        elapsed = time.time() - start
        
        # Should still be fast (scans only 100 files)
        assert elapsed < 2.0, f"Stack detection took {elapsed:.2f}s"
        assert stack == 'python'
