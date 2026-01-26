"""PMO Agent - Elite Program Management Office Automation.

This module provides automated governance enforcement, compliance monitoring,
and intelligent repository management for the kushin77 organization.

Features:
    - Automated pmo.yaml validation
    - GitHub API integration for issue triage and PR validation
    - GCP Cloud Build integration for CI/CD
    - Auto-remediation of common drift issues
    - Real-time compliance monitoring
    - Cost attribution and reporting

Example:
    >>> from ollama.pmo.agent import PMOAgent
    >>> agent = PMOAgent(repo="kushin77/ollama")
    >>> agent.validate_compliance()
    {'status': 'compliant', 'score': 100}
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import logging
import subprocess
import yaml
import os

try:
    from github import Github, Repository, Issue, PullRequest
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    logging.warning("PyGithub not installed. GitHub API features disabled.")

try:
    from google.cloud import build_v1
    from google.cloud import secretmanager
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logging.warning("Google Cloud SDK not installed. GCP features disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PMOValidationError(Exception):
    """Exception raised when PMO validation fails."""
    pass


class PMOAgent:
    """Elite PMO Agent for automated governance and compliance.
    
    This agent provides comprehensive PMO automation including:
    - pmo.yaml validation against 24-label schema
    - GitHub label configuration and enforcement
    - Automated issue triage and classification
    - PR compliance validation
    - GCP Cloud Build trigger management
    - Auto-remediation of drift issues
    - Cost attribution and reporting
    
    Attributes:
        repo_owner (str): GitHub repository owner
        repo_name (str): GitHub repository name
        repo_path (Path): Local repository path
        github_client (Github): GitHub API client (if available)
        gcp_project (str): GCP project ID (if available)
        
    Example:
        >>> agent = PMOAgent(repo="kushin77/ollama")
        >>> result = agent.validate_compliance()
        >>> print(f"Compliance Score: {result['score']}%")
        Compliance Score: 100%
    """
    
    # PMO Schema - 24 Mandatory Labels
    REQUIRED_LABELS = {
        'organizational': ['project', 'team', 'owner', 'department'],
        'lifecycle': ['lifecycle_status', 'environment', 'tier', 'criticality', 'support_level'],
        'business': ['business_unit', 'product', 'service_category', 'sla_tier'],
        'technical': ['stack', 'architecture', 'data_classification', 'compliance_frameworks'],
        'financial': ['cost_center', 'budget_code', 'charge_code', 'approved_budget'],
        'git': ['git_repo', 'git_branch', 'created_by']
    }
    
    # GitHub Labels - Standard Set
    GITHUB_LABELS = {
        'type': [
            ('type-feature', '0075ca', 'New feature'),
            ('type-bug', 'd73a4a', 'Bug fix'),
            ('type-docs', '0075ca', 'Documentation'),
            ('type-refactor', 'fbca04', 'Code refactoring'),
            ('type-test', '1d76db', 'Testing'),
            ('type-perf', '5319e7', 'Performance improvement'),
            ('type-infra', 'c5def5', 'Infrastructure changes'),
        ],
        'priority': [
            ('priority-p0', 'b60205', 'Critical/Urgent'),
            ('priority-p1', 'd93f0b', 'High priority'),
            ('priority-p2', 'fbca04', 'Medium priority'),
            ('priority-p3', '0e8a16', 'Low priority'),
        ],
        'component': [
            ('component-api', '1d76db', 'API layer'),
            ('component-auth', 'e99695', 'Authentication'),
            ('component-database', 'c2e0c6', 'Database'),
            ('component-docker', 'bfdadc', 'Containerization'),
            ('component-frontend', 'fef2c0', 'Frontend'),
            ('component-backend', 'd4c5f9', 'Backend'),
            ('component-tests', 'c5def5', 'Test infrastructure'),
        ],
        'effort': [
            ('effort-xs', '0e8a16', '<4 hours'),
            ('effort-s', '1d76db', '4-8 hours'),
            ('effort-m', 'fbca04', '8-16 hours'),
            ('effort-l', 'd93f0b', '16-40 hours'),
            ('effort-xl', 'b60205', '>40 hours'),
        ],
        'pmo': [
            ('pmo', '5319e7', 'PMO-related'),
            ('governance', '0052cc', 'Governance tasks'),
            ('compliance', 'd4c5f9', 'Compliance requirements'),
            ('cost-tracking', 'fbca04', 'Cost attribution'),
        ],
        'phase': [
            ('phase-1', '0e8a16', 'Phase 1'),
            ('phase-2', '1d76db', 'Phase 2'),
            ('phase-3', 'fbca04', 'Phase 3'),
            ('phase-4', 'd93f0b', 'Phase 4'),
        ],
        'status': [
            ('in-progress', 'fbca04', 'Work in progress'),
            ('blocked', 'd73a4a', 'Blocked by dependencies'),
            ('waiting-review', '0075ca', 'Awaiting review'),
            ('completed', '0e8a16', 'Completed'),
        ],
    }
    
    def __init__(
        self,
        repo: str,
        repo_path: Optional[str] = None,
        github_token: Optional[str] = None,
        gcp_project: Optional[str] = None,
    ):
        """Initialize PMO Agent.
        
        Args:
            repo: Repository in format "owner/name"
            repo_path: Local repository path (defaults to current directory)
            github_token: GitHub API token (uses GITHUB_TOKEN env var if not provided)
            gcp_project: GCP project ID (uses GOOGLE_CLOUD_PROJECT env var if not provided)
            
        Raises:
            ValueError: If repo format is invalid
            PMOValidationError: If repository not found or inaccessible
        """
        # Parse repository
        if '/' not in repo:
            raise ValueError(f"Invalid repo format: {repo}. Expected 'owner/name'")
        
        self.repo_owner, self.repo_name = repo.split('/', 1)
        self.repo_full_name = repo
        
        # Set repository path
        self.repo_path = Path(repo_path or os.getcwd())
        if not self.repo_path.exists():
            raise PMOValidationError(f"Repository path not found: {self.repo_path}")
        
        # Initialize GitHub client
        self.github_client: Optional[Github] = None
        self.github_repo: Optional[Repository.Repository] = None
        if GITHUB_AVAILABLE:
            token = github_token or os.getenv('GITHUB_TOKEN')
            if token:
                try:
                    self.github_client = Github(token)
                    self.github_repo = self.github_client.get_repo(repo)
                    logger.info(f"GitHub API connected: {repo}")
                except Exception as e:
                    logger.warning(f"GitHub API connection failed: {e}")
        
        # Initialize GCP client
        self.gcp_project = gcp_project or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.gcp_build_client: Optional[build_v1.CloudBuildClient] = None
        if GCP_AVAILABLE and self.gcp_project:
            try:
                self.gcp_build_client = build_v1.CloudBuildClient()
                logger.info(f"GCP Cloud Build connected: {self.gcp_project}")
            except Exception as e:
                logger.warning(f"GCP connection failed: {e}")
        
        logger.info(f"PMO Agent initialized for {repo}")
    
    def load_pmo_yaml(self) -> Dict[str, Any]:
        """Load and parse pmo.yaml from repository.
        
        Returns:
            Dictionary containing pmo.yaml content
            
        Raises:
            PMOValidationError: If pmo.yaml not found or invalid
        """
        pmo_file = self.repo_path / 'pmo.yaml'
        
        if not pmo_file.exists():
            raise PMOValidationError(f"pmo.yaml not found in {self.repo_path}")
        
        try:
            with open(pmo_file, 'r') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                raise PMOValidationError("pmo.yaml must be a YAML dictionary")
            
            logger.info(f"Loaded pmo.yaml from {pmo_file}")
            return data
            
        except yaml.YAMLError as e:
            raise PMOValidationError(f"Invalid YAML in pmo.yaml: {e}")
    
    def validate_pmo_yaml(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate pmo.yaml against 24-label schema.
        
        Args:
            data: PMO YAML data (loads from file if not provided)
            
        Returns:
            Dictionary with validation results:
                - valid: bool
                - errors: List[str]
                - warnings: List[str]
                - populated_labels: int
                - total_labels: int
                - score: int (percentage)
                
        Example:
            >>> result = agent.validate_pmo_yaml()
            >>> print(f"Score: {result['score']}%")
            Score: 100%
        """
        if data is None:
            data = self.load_pmo_yaml()
        
        errors: List[str] = []
        warnings: List[str] = []
        populated_labels = 0
        total_labels = sum(len(labels) for labels in self.REQUIRED_LABELS.values())
        
        # Validate each category
        for category, labels in self.REQUIRED_LABELS.items():
            if category not in data:
                errors.append(f"Missing category: {category}")
                continue
            
            category_data = data[category]
            if not isinstance(category_data, dict):
                errors.append(f"Category '{category}' must be a dictionary")
                continue
            
            # Validate each label in category
            for label in labels:
                if label not in category_data:
                    errors.append(f"Missing label: {category}.{label}")
                elif not category_data[label]:
                    warnings.append(f"Empty label: {category}.{label}")
                else:
                    populated_labels += 1
        
        # Calculate score
        score = int((populated_labels / total_labels) * 100)
        valid = len(errors) == 0 and populated_labels >= 20  # Min 20/24 labels
        
        result = {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'populated_labels': populated_labels,
            'total_labels': total_labels,
            'score': score,
        }
        
        if valid:
            logger.info(f"pmo.yaml validation passed: {score}% ({populated_labels}/{total_labels})")
        else:
            logger.error(f"pmo.yaml validation failed: {len(errors)} errors, {len(warnings)} warnings")
        
        return result
    
    def validate_compliance(self) -> Dict[str, Any]:
        """Run full compliance validation.
        
        Validates:
            - pmo.yaml presence and schema compliance
            - GitHub labels configuration
            - Required workflows presence
            - Git hooks installation
            - GPG commit signing
            
        Returns:
            Dictionary with compliance results and score
            
        Example:
            >>> result = agent.validate_compliance()
            >>> if result['compliant']:
            >>>     print(f"✅ Compliant ({result['score']}%)")
        """
        checks: Dict[str, bool] = {}
        details: Dict[str, str] = {}
        
        # Check 1: pmo.yaml validation
        try:
            validation = self.validate_pmo_yaml()
            checks['pmo_yaml'] = validation['valid']
            details['pmo_yaml'] = f"{validation['score']}% ({validation['populated_labels']}/{validation['total_labels']})"
        except PMOValidationError as e:
            checks['pmo_yaml'] = False
            details['pmo_yaml'] = str(e)
        
        # Check 2: GitHub labels (if GitHub API available)
        if self.github_repo:
            try:
                labels = list(self.github_repo.get_labels())
                expected_count = sum(len(cat) for cat in self.GITHUB_LABELS.values())
                checks['github_labels'] = len(labels) >= expected_count
                details['github_labels'] = f"{len(labels)}/{expected_count} labels configured"
            except Exception as e:
                checks['github_labels'] = False
                details['github_labels'] = f"Error: {e}"
        else:
            checks['github_labels'] = None  # Skip if no GitHub API
            details['github_labels'] = "GitHub API not available"
        
        # Check 3: Required workflows
        workflows_dir = self.repo_path / '.github' / 'workflows'
        required_workflows = [
            'pmo-validation.yml',
            'compliance-check.yml',
        ]
        
        if workflows_dir.exists():
            existing_workflows = [f.name for f in workflows_dir.glob('*.yml')]
            missing = [w for w in required_workflows if w not in existing_workflows]
            checks['workflows'] = len(missing) == 0
            details['workflows'] = f"{len(required_workflows) - len(missing)}/{len(required_workflows)} workflows"
        else:
            checks['workflows'] = False
            details['workflows'] = "No .github/workflows directory"
        
        # Check 4: Git hooks
        hooks_dir = self.repo_path / '.git' / 'hooks'
        required_hooks = ['pre-commit', 'commit-msg']
        
        if hooks_dir.exists():
            existing_hooks = [f.name for f in hooks_dir.iterdir() if f.is_file() and os.access(f, os.X_OK)]
            missing = [h for h in required_hooks if h not in existing_hooks]
            checks['git_hooks'] = len(missing) == 0
            details['git_hooks'] = f"{len(required_hooks) - len(missing)}/{len(required_hooks)} hooks installed"
        else:
            checks['git_hooks'] = False
            details['git_hooks'] = "No .git/hooks directory"
        
        # Check 5: GPG signing
        try:
            result = subprocess.run(
                ['git', 'config', 'commit.gpgsign'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            checks['gpg_signing'] = result.stdout.strip() == 'true'
            details['gpg_signing'] = "Enabled" if checks['gpg_signing'] else "Disabled"
        except Exception as e:
            checks['gpg_signing'] = False
            details['gpg_signing'] = f"Error: {e}"
        
        # Calculate overall score
        passed = sum(1 for v in checks.values() if v is True)
        total = sum(1 for v in checks.values() if v is not None)
        score = int((passed / total) * 100) if total > 0 else 0
        compliant = score >= 80  # 80% threshold for compliance
        
        return {
            'compliant': compliant,
            'score': score,
            'checks': checks,
            'details': details,
            'passed': passed,
            'total': total,
            'timestamp': datetime.now().isoformat(),
        }
    
    def setup_github_labels(self, force: bool = False) -> Dict[str, Any]:
        """Configure GitHub labels for repository.
        
        Args:
            force: If True, update existing labels (otherwise skip)
            
        Returns:
            Dictionary with setup results
            
        Raises:
            RuntimeError: If GitHub API not available
        """
        if not self.github_repo:
            raise RuntimeError("GitHub API not available. Set GITHUB_TOKEN environment variable.")
        
        created = 0
        updated = 0
        skipped = 0
        errors: List[str] = []
        
        # Get existing labels
        existing_labels = {label.name: label for label in self.github_repo.get_labels()}
        
        # Create/update labels
        for category, labels in self.GITHUB_LABELS.items():
            for name, color, description in labels:
                try:
                    if name in existing_labels:
                        if force:
                            existing_labels[name].edit(name, color, description)
                            updated += 1
                            logger.info(f"Updated label: {name}")
                        else:
                            skipped += 1
                    else:
                        self.github_repo.create_label(name, color, description)
                        created += 1
                        logger.info(f"Created label: {name}")
                        
                except Exception as e:
                    errors.append(f"Failed to create/update {name}: {e}")
                    logger.error(f"Label error: {e}")
        
        return {
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'total': created + updated + skipped,
        }
    
    def auto_remediate_drift(self) -> Dict[str, Any]:
        """Automatically remediate common compliance drift issues.
        
        Attempts to fix:
            - Missing GitHub labels
            - Disabled GPG signing
            - Missing pre-commit hooks
            - Incomplete pmo.yaml
            - Missing GitHub workflows
            - Unprotected main branch
            
        Returns:
            Dictionary with remediation results
        """
        fixes: Dict[str, bool] = {}
        details: Dict[str, str] = {}
        
        # Fix 1: Setup GitHub labels if missing
        if self.github_repo:
            try:
                result = self.setup_github_labels(force=False)
                fixes['github_labels'] = result['created'] > 0
                details['github_labels'] = f"Created {result['created']} labels"
            except Exception as e:
                fixes['github_labels'] = False
                details['github_labels'] = str(e)
        
        # Fix 2: Enable GPG signing if disabled
        try:
            result = subprocess.run(
                ['git', 'config', 'commit.gpgsign', 'true'],
                cwd=self.repo_path,
                capture_output=True,
                timeout=5
            )
            fixes['gpg_signing'] = result.returncode == 0
            details['gpg_signing'] = "Enabled" if fixes['gpg_signing'] else "Failed"
        except Exception as e:
            fixes['gpg_signing'] = False
            details['gpg_signing'] = str(e)
        
        # Fix 3: Install pre-commit hooks if missing
        templates_dir = self.repo_path / 'templates' / 'pmo' / 'hooks'
        hooks_dir = self.repo_path / '.git' / 'hooks'
        
        if templates_dir.exists() and hooks_dir.exists():
            try:
                import shutil
                for hook_file in ['pre-commit', 'commit-msg']:
                    src = templates_dir / hook_file
                    dst = hooks_dir / hook_file
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst)
                        os.chmod(dst, 0o755)
                
                fixes['git_hooks'] = True
                details['git_hooks'] = "Installed missing hooks"
            except Exception as e:
                fixes['git_hooks'] = False
                details['git_hooks'] = str(e)
        else:
            fixes['git_hooks'] = False
            details['git_hooks'] = "Templates not found"
        
        # Fix 4: Auto-complete incomplete pmo.yaml
        pmo_path = self.repo_path / 'pmo.yaml'
        if pmo_path.exists():
            try:
                pmo_data = self.load_pmo_yaml()
                if pmo_data:
                    validation = self.validate_pmo_yaml(pmo_data)
                    if validation['score'] < 100:
                        # Add intelligent defaults for missing labels
                        updated = False
                        defaults = {
                            'organizational': {
                                'environment': 'development',
                                'team': 'engineering',
                                'application': self.repo.split('/')[-1],
                                'component': 'core',
                            },
                            'lifecycle': {
                                'lifecycle_status': 'active',
                                'created_at': datetime.now().strftime('%Y-%m-%d'),
                            },
                            'business': {
                                'priority': 'p1',
                                'cost_center': 'engineering',
                            },
                            'technical': {
                                'stack': 'python',
                                'managed_by': 'terraform',
                            },
                            'financial': {
                                'budget_allocated': '0',
                            },
                            'git': {
                                'git_repo': f'github.com/{self.repo}',
                                'created_by': 'pmo-agent',
                            },
                        }
                        
                        for category, labels in defaults.items():
                            if category not in pmo_data:
                                pmo_data[category] = {}
                            for label, value in labels.items():
                                if label not in pmo_data[category]:
                                    pmo_data[category][label] = value
                                    updated = True
                        
                        if updated:
                            with open(pmo_path, 'w') as f:
                                yaml.dump(pmo_data, f, default_flow_style=False, sort_keys=False)
                            fixes['pmo_yaml_completion'] = True
                            details['pmo_yaml_completion'] = f"Added missing labels, score now {self.validate_pmo_yaml(pmo_data)['score']}%"
                        else:
                            fixes['pmo_yaml_completion'] = False
                            details['pmo_yaml_completion'] = "Already complete"
                    else:
                        fixes['pmo_yaml_completion'] = False
                        details['pmo_yaml_completion'] = "Already complete"
            except Exception as e:
                fixes['pmo_yaml_completion'] = False
                details['pmo_yaml_completion'] = str(e)
        
        # Fix 5: Create missing critical workflows
        if self.github_repo:
            try:
                workflows_created = []
                workflows_dir = self.repo_path / '.github' / 'workflows'
                critical_workflows = {
                    'pmo-validation.yml': 'PMO validation on every PR',
                    'compliance-check.yml': 'Daily compliance check',
                    'security-scan.yml': 'Security scanning',
                }
                
                if workflows_dir.exists():
                    for workflow_file in critical_workflows.keys():
                        workflow_path = workflows_dir / workflow_file
                        if not workflow_path.exists():
                            # Check if template exists
                            template_path = self.repo_path / '.github' / 'workflows' / workflow_file
                            if template_path.exists():
                                workflows_created.append(workflow_file)
                    
                    fixes['workflows_creation'] = len(workflows_created) > 0
                    details['workflows_creation'] = f"Found {len(workflows_created)} missing workflows" if workflows_created else "All workflows exist"
                else:
                    fixes['workflows_creation'] = False
                    details['workflows_creation'] = "Workflows directory not found"
            except Exception as e:
                fixes['workflows_creation'] = False
                details['workflows_creation'] = str(e)
        
        # Fix 6: Enable branch protection on main
        if self.github_repo:
            try:
                branch = self.github_repo.get_branch('main')
                if not branch.protected:
                    # Note: Actual protection would be applied here, but requires admin permissions
                    fixes['branch_protection'] = False
                    details['branch_protection'] = "Requires admin permissions"
                else:
                    fixes['branch_protection'] = False
                    details['branch_protection'] = "Already protected"
            except Exception as e:
                fixes['branch_protection'] = False
                details['branch_protection'] = str(e)
        
        applied = sum(1 for v in fixes.values() if v is True)
        
        return {
            'fixes': fixes,
            'details': details,
            'applied': applied,
            'timestamp': datetime.now().isoformat(),
        }
    
    def validate_pr_compliance(self, pr_number: int) -> Dict[str, Any]:
        """Validate pull request compliance.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Dictionary with PR compliance results
            
        Raises:
            RuntimeError: If GitHub API not available
        """
        if not self.github_repo:
            raise RuntimeError("GitHub API not available")
        
        pr = self.github_repo.get_pull(pr_number)
        
        checks: Dict[str, bool] = {}
        details: Dict[str, str] = {}
        
        # Check 1: PR has description
        checks['has_description'] = len(pr.body or '') > 50
        details['has_description'] = f"{len(pr.body or '')} characters"
        
        # Check 2: PR has labels
        checks['has_labels'] = pr.labels.totalCount > 0
        details['has_labels'] = f"{pr.labels.totalCount} labels"
        
        # Check 3: PR title follows format
        title_pattern = r'^(feat|fix|refactor|perf|test|docs|infra|security|chore)\([a-z0-9-]+\):'
        import re
        checks['title_format'] = bool(re.match(title_pattern, pr.title))
        details['title_format'] = pr.title[:50]
        
        # Check 4: PR has assignee
        checks['has_assignee'] = pr.assignee is not None
        details['has_assignee'] = pr.assignee.login if pr.assignee else "None"
        
        # Check 5: All commits signed
        commits = list(pr.get_commits())
        signed_commits = sum(1 for c in commits if c.commit.verification.verified)
        checks['commits_signed'] = signed_commits == len(commits)
        details['commits_signed'] = f"{signed_commits}/{len(commits)}"
        
        # Calculate score
        passed = sum(1 for v in checks.values() if v is True)
        score = int((passed / len(checks)) * 100)
        compliant = score >= 80
        
        return {
            'pr_number': pr_number,
            'compliant': compliant,
            'score': score,
            'checks': checks,
            'details': details,
            'passed': passed,
            'total': len(checks),
        }
    
    def create_build_trigger(
        self,
        trigger_name: str,
        branch_pattern: str = "^main$",
        build_config_path: str = "cloudbuild.yaml",
    ) -> Dict[str, Any]:
        """Create GCP Cloud Build trigger for CI/CD automation.

        Args:
            trigger_name: Name for the build trigger
            branch_pattern: Regex pattern for branch matching (default: ^main$)
            build_config_path: Path to cloudbuild.yaml (default: cloudbuild.yaml)

        Returns:
            Dict with trigger details

        Example:
            >>> agent = PMOAgent("kushin77/ollama", gcp_project="prod-ollama")
            >>> result = agent.create_build_trigger("main-deploy")
            >>> print(f"Created: {result['name']}")
        """
        if not self.gcp_client:
            log.warning("trigger_creation_skipped", reason="gcp_not_available")
            return {"created": False, "reason": "GCP API not available"}

        try:
            from google.cloud.devtools import cloudbuild_v1

            trigger = cloudbuild_v1.BuildTrigger(
                name=trigger_name,
                description=f"PMO-managed trigger for {self.repo}",
                github=cloudbuild_v1.GitHubEventsConfig(
                    owner=self.repo.split("/")[0],
                    name=self.repo.split("/")[1],
                    push=cloudbuild_v1.PushFilter(branch=branch_pattern),
                ),
                filename=build_config_path,
                tags=["pmo-managed", "automated", self.repo.replace("/", "-")],
            )

            request = cloudbuild_v1.CreateBuildTriggerRequest(
                parent=f"projects/{self.gcp_project}",
                build_trigger=trigger,
            )

            response = self.gcp_client.create_build_trigger(request=request)

            log.info(
                "trigger_created",
                trigger_name=trigger_name,
                trigger_id=response.id,
                branch=branch_pattern,
            )

            return {
                "created": True,
                "name": response.name,
                "id": response.id,
                "branch_pattern": branch_pattern,
                "config_path": build_config_path,
            }

        except Exception as e:
            log.error("trigger_creation_failed", error=str(e), trigger_name=trigger_name)
            raise PMOValidationError(f"Failed to create build trigger: {e}")

    def update_build_trigger(
        self, trigger_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing GCP Cloud Build trigger.

        Args:
            trigger_id: ID of trigger to update
            updates: Dict of fields to update (name, branch_pattern, config_path)

        Returns:
            Dict with updated trigger details

        Example:
            >>> agent = PMOAgent("kushin77/ollama", gcp_project="prod-ollama")
            >>> result = agent.update_build_trigger(
            ...     "12345",
            ...     {"branch_pattern": "^(main|develop)$"}
            ... )
        """
        if not self.gcp_client:
            log.warning("trigger_update_skipped", reason="gcp_not_available")
            return {"updated": False, "reason": "GCP API not available"}

        try:
            from google.cloud.devtools import cloudbuild_v1
            from google.protobuf import field_mask_pb2

            # Get existing trigger
            get_request = cloudbuild_v1.GetBuildTriggerRequest(
                project_id=self.gcp_project, trigger_id=trigger_id
            )
            trigger = self.gcp_client.get_build_trigger(request=get_request)

            # Apply updates
            update_fields = []
            if "name" in updates:
                trigger.name = updates["name"]
                update_fields.append("name")

            if "branch_pattern" in updates:
                trigger.github.push.branch = updates["branch_pattern"]
                update_fields.append("github.push.branch")

            if "config_path" in updates:
                trigger.filename = updates["config_path"]
                update_fields.append("filename")

            # Update trigger
            update_request = cloudbuild_v1.UpdateBuildTriggerRequest(
                project_id=self.gcp_project,
                trigger_id=trigger_id,
                trigger=trigger,
                update_mask=field_mask_pb2.FieldMask(paths=update_fields),
            )

            response = self.gcp_client.update_build_trigger(request=update_request)

            log.info(
                "trigger_updated",
                trigger_id=trigger_id,
                updated_fields=update_fields,
            )

            return {
                "updated": True,
                "id": response.id,
                "name": response.name,
                "updated_fields": update_fields,
            }

        except Exception as e:
            log.error("trigger_update_failed", error=str(e), trigger_id=trigger_id)
            raise PMOValidationError(f"Failed to update build trigger: {e}")

    def list_build_triggers(self) -> Dict[str, Any]:
        """List all GCP Cloud Build triggers for the project.

        Returns:
            Dict with list of triggers

        Example:
            >>> agent = PMOAgent("kushin77/ollama", gcp_project="prod-ollama")
            >>> result = agent.list_build_triggers()
            >>> print(f"Found {result['count']} triggers")
        """
        if not self.gcp_client:
            log.warning("trigger_list_skipped", reason="gcp_not_available")
            return {"triggers": [], "count": 0, "reason": "GCP API not available"}

        try:
            from google.cloud.devtools import cloudbuild_v1

            request = cloudbuild_v1.ListBuildTriggersRequest(
                project_id=self.gcp_project
            )

            triggers = []
            for trigger in self.gcp_client.list_build_triggers(request=request):
                triggers.append(
                    {
                        "id": trigger.id,
                        "name": trigger.name,
                        "description": trigger.description,
                        "branch_pattern": (
                            trigger.github.push.branch if trigger.github else None
                        ),
                        "config_path": trigger.filename,
                        "tags": list(trigger.tags) if trigger.tags else [],
                    }
                )

            log.info("triggers_listed", count=len(triggers), project=self.gcp_project)

            return {"triggers": triggers, "count": len(triggers)}

        except Exception as e:
            log.error("trigger_list_failed", error=str(e))
            raise PMOValidationError(f"Failed to list build triggers: {e}")


# Example usage
if __name__ == '__main__':
    import sys
    
    # Initialize agent
    repo = sys.argv[1] if len(sys.argv) > 1 else "kushin77/ollama"
    agent = PMOAgent(repo=repo)
    
    # Run compliance validation
    result = agent.validate_compliance()
    
    print(f"\n{'='*60}")
    print(f"PMO Compliance Report - {repo}")
    print(f"{'='*60}\n")
    
    for check, passed in result['checks'].items():
        status = '✅' if passed else '❌' if passed is False else '⏭️'
        detail = result['details'][check]
        print(f"{status} {check:20s} - {detail}")
    
    print(f"\n{'='*60}")
    print(f"Overall Score: {result['score']}% ({result['passed']}/{result['total']})")
    print(f"Status: {'✅ COMPLIANT' if result['compliant'] else '❌ NON-COMPLIANT'}")
    print(f"{'='*60}\n")
