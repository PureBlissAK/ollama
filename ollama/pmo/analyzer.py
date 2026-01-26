"""Repository Analyzer - AI-powered project analysis for pmo.yaml generation.

This module analyzes repository structure, code, and configuration files to
intelligently determine project metadata for automated pmo.yaml generation.

Features:
    - Technology stack detection (Python, Node.js, Java, Go, etc.)
    - Environment detection (production, staging, development)
    - Team/ownership detection from CODEOWNERS, package.json, pyproject.toml
    - Component detection from directory structure
    - Cost/priority inference from project characteristics

Example:
    >>> from ollama.pmo.analyzer import RepositoryAnalyzer
    >>> analyzer = RepositoryAnalyzer("/home/user/my-project")
    >>> metadata = analyzer.analyze()
    >>> print(metadata['stack'])  # 'python'
    >>> print(metadata['confidence'])  # 0.95
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class RepositoryAnalyzer:
    """Analyzes repository to generate intelligent pmo.yaml metadata.
    
    Uses heuristics and pattern matching to detect:
        - Technology stack from file extensions and config files
        - Environment from branch names, deployment configs
        - Team ownership from CODEOWNERS, package metadata
        - Application/component names from directories
        - Priority from repository activity and size
    
    Attributes:
        repo_path: Path to repository root
        confidence_threshold: Minimum confidence for auto-generation (0.0-1.0)
    """
    
    # Technology stack detection patterns
    STACK_PATTERNS = {
        'python': {
            'files': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile', 'poetry.lock'],
            'extensions': ['.py'],
            'weight': 1.0,
        },
        'nodejs': {
            'files': ['package.json', 'yarn.lock', 'package-lock.json'],
            'extensions': ['.js', '.ts', '.jsx', '.tsx'],
            'weight': 1.0,
        },
        'java': {
            'files': ['pom.xml', 'build.gradle', 'settings.gradle'],
            'extensions': ['.java'],
            'weight': 1.0,
        },
        'go': {
            'files': ['go.mod', 'go.sum'],
            'extensions': ['.go'],
            'weight': 1.0,
        },
        'rust': {
            'files': ['Cargo.toml', 'Cargo.lock'],
            'extensions': ['.rs'],
            'weight': 1.0,
        },
        'ruby': {
            'files': ['Gemfile', 'Gemfile.lock'],
            'extensions': ['.rb'],
            'weight': 1.0,
        },
    }
    
    # Environment detection patterns
    ENVIRONMENT_PATTERNS = {
        'production': ['prod', 'production', 'main', 'master'],
        'staging': ['staging', 'stage', 'preprod'],
        'development': ['dev', 'develop', 'development'],
        'sandbox': ['sandbox', 'test', 'experiment'],
    }
    
    # Priority detection patterns
    PRIORITY_PATTERNS = {
        'p0': ['critical', 'production', 'core', 'main', 'primary'],
        'p1': ['important', 'high', 'essential'],
        'p2': ['medium', 'normal', 'standard'],
        'p3': ['low', 'minor', 'experimental'],
    }
    
    def __init__(
        self,
        repo_path: Path,
        confidence_threshold: float = 0.7,
    ) -> None:
        """Initialize repository analyzer.
        
        Args:
            repo_path: Path to repository root
            confidence_threshold: Minimum confidence for auto-generation (default: 0.7)
        """
        self.repo_path = Path(repo_path).resolve()
        self.confidence_threshold = confidence_threshold
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
    
    def analyze(self) -> Dict[str, Any]:
        """Perform complete repository analysis.
        
        Returns:
            Dict with analyzed metadata and confidence scores
            
        Example:
            >>> analyzer = RepositoryAnalyzer("/path/to/repo")
            >>> result = analyzer.analyze()
            >>> print(result['organizational']['stack'])
            'python'
            >>> print(result['confidence']['overall'])
            0.87
        """
        # Detect technology stack
        stack, stack_confidence = self._detect_stack()
        
        # Detect environment
        environment, env_confidence = self._detect_environment()
        
        # Detect team/ownership
        team, team_confidence = self._detect_team()
        
        # Detect application name
        application, app_confidence = self._detect_application_name()
        
        # Detect component
        component, comp_confidence = self._detect_component()
        
        # Detect priority
        priority, priority_confidence = self._detect_priority()
        
        # Detect lifecycle status
        lifecycle_status, lifecycle_confidence = self._detect_lifecycle_status()
        
        # Calculate overall confidence
        overall_confidence = sum([
            stack_confidence,
            env_confidence,
            team_confidence,
            app_confidence,
            comp_confidence,
            priority_confidence,
            lifecycle_confidence,
        ]) / 7.0
        
        return {
            'organizational': {
                'environment': environment,
                'team': team,
                'application': application,
                'component': component,
            },
            'lifecycle': {
                'lifecycle_status': lifecycle_status,
                'created_at': self._get_creation_date(),
            },
            'business': {
                'priority': priority,
                'cost_center': team,  # Default to team name
            },
            'technical': {
                'stack': stack,
                'managed_by': 'terraform',  # Default assumption
            },
            'financial': {
                'budget_allocated': '0',  # Requires manual input
            },
            'git': {
                'git_repo': self._detect_git_repo(),
                'created_by': 'pmo-agent-analyzer',
            },
            'confidence': {
                'overall': round(overall_confidence, 2),
                'stack': round(stack_confidence, 2),
                'environment': round(env_confidence, 2),
                'team': round(team_confidence, 2),
                'application': round(app_confidence, 2),
                'component': round(comp_confidence, 2),
                'priority': round(priority_confidence, 2),
                'lifecycle': round(lifecycle_confidence, 2),
            },
            'needs_review': overall_confidence < self.confidence_threshold,
        }
    
    def _detect_stack(self) -> Tuple[str, float]:
        """Detect primary technology stack.
        
        Returns:
            Tuple of (stack_name, confidence_score)
        """
        scores: Dict[str, float] = {}
        
        for stack, patterns in self.STACK_PATTERNS.items():
            score = 0.0
            
            # Check for stack-specific files
            for file in patterns['files']:
                if (self.repo_path / file).exists():
                    score += patterns['weight']
            
            # Check for file extensions (scan top 100 files)
            file_count = 0
            extension_matches = 0
            
            for root, _, files in os.walk(self.repo_path):
                # Skip common ignore directories
                if any(skip in root for skip in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']):
                    continue
                
                for file in files:
                    file_count += 1
                    if file_count > 100:
                        break
                    
                    if any(file.endswith(ext) for ext in patterns['extensions']):
                        extension_matches += 1
                
                if file_count > 100:
                    break
            
            if file_count > 0:
                score += (extension_matches / file_count) * patterns['weight']
            
            scores[stack] = score
        
        # Get highest scoring stack
        if scores:
            best_stack = max(scores, key=scores.get)  # type: ignore
            # If no evidence found, return unknown
            if scores[best_stack] <= 0:
                return 'unknown', 0.0

            confidence = min(scores[best_stack] / 2.0, 1.0)  # Normalize to 0-1
            return best_stack, confidence

        return 'unknown', 0.0
    
    def _detect_environment(self) -> Tuple[str, float]:
        """Detect deployment environment.
        
        Returns:
            Tuple of (environment, confidence_score)
        """
        # Check git branch name
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                branch = result.stdout.strip().lower()
                
                for env, patterns in self.ENVIRONMENT_PATTERNS.items():
                    if any(pattern in branch for pattern in patterns):
                        return env, 0.8
        except Exception:
            pass
        
        # Check for deployment config files
        deployment_configs = {
            'production': ['docker-compose.prod.yml', 'config/production.yaml', '.env.production'],
            'staging': ['docker-compose.staging.yml', 'config/staging.yaml', '.env.staging'],
            'development': ['docker-compose.dev.yml', 'config/development.yaml', '.env.development'],
        }
        
        for env, configs in deployment_configs.items():
            if any((self.repo_path / config).exists() for config in configs):
                return env, 0.7
        
        # Default to development
        return 'development', 0.5
    
    def _detect_team(self) -> Tuple[str, float]:
        """Detect team/ownership.
        
        Returns:
            Tuple of (team_name, confidence_score)
        """
        # Check CODEOWNERS file
        codeowners_paths = [
            self.repo_path / 'CODEOWNERS',
            self.repo_path / '.github' / 'CODEOWNERS',
            self.repo_path / 'docs' / 'CODEOWNERS',
        ]
        
        for codeowners_path in codeowners_paths:
            if codeowners_path.exists():
                try:
                    content = codeowners_path.read_text()
                    # Extract team names (e.g., @org/team-name)
                    teams = re.findall(r'@[\w-]+/([\w-]+)', content)
                    if teams:
                        return teams[0], 0.9
                except Exception:
                    pass
        
        # Check package.json for author
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                if 'author' in data:
                    author = data['author']
                    if isinstance(author, str):
                        return author.split()[0].lower(), 0.7
                    elif isinstance(author, dict) and 'name' in author:
                        return author['name'].split()[0].lower(), 0.7
            except Exception:
                pass
        
        # Check pyproject.toml for authors
        pyproject = self.repo_path / 'pyproject.toml'
        if pyproject.exists():
            try:
                import tomli
                data = tomli.loads(pyproject.read_text())
                if 'tool' in data and 'poetry' in data['tool']:
                    authors = data['tool']['poetry'].get('authors', [])
                    if authors and isinstance(authors[0], str):
                        return authors[0].split()[0].lower(), 0.7
            except Exception:
                pass
        
        # Default to engineering
        return 'engineering', 0.5
    
    def _detect_application_name(self) -> Tuple[str, float]:
        """Detect application name.
        
        Returns:
            Tuple of (app_name, confidence_score)
        """
        # Try package.json
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                if 'name' in data:
                    return data['name'], 0.9
            except Exception:
                pass
        
        # Try pyproject.toml
        pyproject = self.repo_path / 'pyproject.toml'
        if pyproject.exists():
            try:
                import tomli
                data = tomli.loads(pyproject.read_text())
                if 'project' in data and 'name' in data['project']:
                    return data['project']['name'], 0.9
                elif 'tool' in data and 'poetry' in data['tool']:
                    name = data['tool']['poetry'].get('name')
                    if name:
                        return name, 0.9
            except Exception:
                pass
        
        # Use directory name
        return self.repo_path.name, 0.6
    
    def _detect_component(self) -> Tuple[str, float]:
        """Detect primary component type.
        
        Returns:
            Tuple of (component, confidence_score)
        """
        # Check for common directory structures
        if (self.repo_path / 'api').exists() or (self.repo_path / 'src' / 'api').exists():
            return 'api', 0.7
        
        if (self.repo_path / 'frontend').exists() or (self.repo_path / 'client').exists():
            return 'frontend', 0.7
        
        if (self.repo_path / 'database').exists() or (self.repo_path / 'migrations').exists():
            return 'database', 0.7
        
        if (self.repo_path / 'infrastructure').exists() or (self.repo_path / 'terraform').exists():
            return 'infrastructure', 0.7
        
        # Default to core
        return 'core', 0.5
    
    def _detect_priority(self) -> Tuple[str, float]:
        """Detect project priority.
        
        Returns:
            Tuple of (priority, confidence_score)
        """
        app_name = self.repo_path.name.lower()
        
        for priority, patterns in self.PRIORITY_PATTERNS.items():
            if any(pattern in app_name for pattern in patterns):
                return priority, 0.6
        
        # Check README for keywords
        readme_paths = [self.repo_path / 'README.md', self.repo_path / 'README']
        for readme_path in readme_paths:
            if readme_path.exists():
                try:
                    content = readme_path.read_text().lower()
                    for priority, patterns in self.PRIORITY_PATTERNS.items():
                        if any(pattern in content for pattern in patterns):
                            return priority, 0.5
                except Exception:
                    pass
        
        # Default to p1
        return 'p1', 0.4
    
    def _detect_lifecycle_status(self) -> Tuple[str, float]:
        """Detect lifecycle status.
        
        Returns:
            Tuple of (status, confidence_score)
        """
        # Check for archived/deprecated markers
        readme_paths = [self.repo_path / 'README.md', self.repo_path / 'README']
        for readme_path in readme_paths:
            if readme_path.exists():
                try:
                    content = readme_path.read_text().lower()
                    
                    if 'deprecated' in content or 'archived' in content:
                        return 'sunset', 0.8
                    
                    if 'maintenance mode' in content or 'no longer maintained' in content:
                        return 'maintenance', 0.7
                except Exception:
                    pass
        
        # Default to active
        return 'active', 0.6
    
    def _get_creation_date(self) -> str:
        """Get repository creation date.
        
        Returns:
            ISO format date string
        """
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '--reverse', '--format=%aI', '--max-count=1'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                date_str = result.stdout.strip()
                if date_str:
                    # Extract just the date part (YYYY-MM-DD)
                    return date_str.split('T')[0]
        except Exception:
            pass
        
        # Fallback to today
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    def _detect_git_repo(self) -> str:
        """Detect Git repository URL.
        
        Returns:
            Repository URL in format github.com/owner/repo
        """
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                url = result.stdout.strip()
                
                # Parse various Git URL formats
                # SSH: git@github.com:owner/repo.git
                # HTTPS: https://github.com/owner/repo.git
                
                if 'github.com' in url:
                    # Extract owner/repo
                    match = re.search(r'github\.com[:/]([\w-]+/[\w-]+)', url)
                    if match:
                        repo = match.group(1).replace('.git', '')
                        return f'github.com/{repo}'
        except Exception:
            pass
        
        # Fallback
        return f'github.com/unknown/{self.repo_path.name}'
    
    def generate_pmo_yaml(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate complete pmo.yaml from analysis.
        
        Args:
            output_path: Optional path to write pmo.yaml (default: repo_path/pmo.yaml)
            
        Returns:
            Generated pmo.yaml as dict
            
        Example:
            >>> analyzer = RepositoryAnalyzer("/path/to/repo")
            >>> pmo_data = analyzer.generate_pmo_yaml()
            >>> print(pmo_data['organizational']['stack'])
        """
        analysis = self.analyze()
        
        # Build pmo.yaml structure (exclude confidence and needs_review)
        pmo_data = {
            'organizational': analysis['organizational'],
            'lifecycle': analysis['lifecycle'],
            'business': analysis['business'],
            'technical': analysis['technical'],
            'financial': analysis['financial'],
            'git': analysis['git'],
        }
        
        # Write to file if path provided
        if output_path is None:
            output_path = self.repo_path / 'pmo.yaml'
        
        with open(output_path, 'w') as f:
            yaml.dump(pmo_data, f, default_flow_style=False, sort_keys=False)
        
        return pmo_data
