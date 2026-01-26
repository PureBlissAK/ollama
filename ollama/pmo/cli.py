"""PMO Agent CLI - Command-line interface for PMO operations.

This module provides a Click-based CLI for interacting with the PMO Agent,
enabling validation, remediation, and onboarding operations from the terminal.

Example:
    $ ollama-pmo validate
    $ ollama-pmo remediate --auto-fix
    $ ollama-pmo setup-labels --force
    $ ollama-pmo onboard --interactive
    $ ollama-pmo onboard --ai-powered  # Use AI analyzer
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from ollama.pmo.agent import PMOAgent, PMOValidationError
from ollama.pmo.analyzer import RepositoryAnalyzer


@click.group()
@click.version_option(version="1.0.0")
@click.option(
    "--repo",
    envvar="PMO_REPO",
    help="GitHub repository (owner/repo)",
)
@click.option(
    "--repo-path",
    envvar="PMO_REPO_PATH",
    type=click.Path(exists=True),
    default=".",
    help="Path to local repository",
)
@click.option(
    "--github-token",
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token",
)
@click.option(
    "--gcp-project",
    envvar="GOOGLE_CLOUD_PROJECT",
    help="GCP project ID for Cloud Build integration",
)
@click.pass_context
def cli(
    ctx: click.Context,
    repo: Optional[str],
    repo_path: str,
    github_token: Optional[str],
    gcp_project: Optional[str],
) -> None:
    """PMO Agent CLI - Elite program management automation.
    
    Validate compliance, auto-remediate drift, and manage PMO operations
    across your entire repository ecosystem.
    """
    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj["repo"] = repo
    ctx.obj["repo_path"] = Path(repo_path).resolve()
    ctx.obj["github_token"] = github_token
    ctx.obj["gcp_project"] = gcp_project


@cli.command()
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed validation results"
)
@click.option(
    "--fail-on-score",
    type=int,
    default=80,
    help="Exit with error if score below threshold (default: 80)",
)
@click.pass_context
def validate(ctx: click.Context, verbose: bool, fail_on_score: int) -> None:
    """Validate PMO compliance for the repository.
    
    Checks:
        - pmo.yaml completeness (24 mandatory labels)
        - GitHub labels configured
        - GitHub workflows present
        - Git hooks installed
        - GPG signing enabled
    
    Example:
        $ ollama-pmo validate
        $ ollama-pmo validate --verbose
        $ ollama-pmo validate --fail-on-score 90
    """
    try:
        agent = PMOAgent(
            repo=ctx.obj["repo"],
            repo_path=ctx.obj["repo_path"],
            github_token=ctx.obj["github_token"],
            gcp_project=ctx.obj["gcp_project"],
        )
        
        click.echo("🔍 Validating PMO compliance...")
        click.echo()
        
        result = agent.validate_compliance()
        
        # Display results
        click.echo(f"{'='*60}")
        click.echo(f"PMO Compliance Report - {ctx.obj['repo'] or ctx.obj['repo_path']}")
        click.echo(f"{'='*60}\n")
        
        for check, passed in result["checks"].items():
            status = "✅" if passed else "❌" if passed is False else "⏭️"
            detail = result["details"][check]
            check_name = check.replace("_", " ").title()
            
            if verbose or not passed:
                click.echo(f"{status} {check_name:25s} - {detail}")
        
        click.echo(f"\n{'='*60}")
        
        score = result["score"]
        passed_count = result["passed"]
        total_count = result["total"]
        
        if score >= 90:
            color = "green"
            status_icon = "✅"
            status_text = "EXCELLENT"
        elif score >= fail_on_score:
            color = "yellow"
            status_icon = "⚠️"
            status_text = "COMPLIANT"
        else:
            color = "red"
            status_icon = "❌"
            status_text = "NON-COMPLIANT"
        
        click.echo(
            f"Overall Score: " + click.style(f"{score}%", fg=color, bold=True) +
            f" ({passed_count}/{total_count} checks passed)"
        )
        click.echo(
            f"Status: {status_icon} " + click.style(status_text, fg=color, bold=True)
        )
        click.echo(f"{'='*60}\n")
        
        if score < fail_on_score:
            click.echo(
                click.style(
                    f"❌ Compliance score ({score}%) below threshold ({fail_on_score}%)",
                    fg="red",
                )
            )
            click.echo("💡 Run 'ollama-pmo remediate' to auto-fix issues")
            sys.exit(1)
        
    except PMOValidationError as e:
        click.echo(click.style(f"❌ Validation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--auto-fix/--no-auto-fix",
    default=True,
    help="Automatically apply fixes (default: true)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be fixed without applying"
)
@click.pass_context
def remediate(ctx: click.Context, auto_fix: bool, dry_run: bool) -> None:
    """Auto-remediate compliance drift.
    
    Automatically fixes:
        - Missing GitHub labels
        - Disabled GPG signing
        - Missing pre-commit hooks
        - Incomplete pmo.yaml
        - Missing GitHub workflows
        - Unprotected main branch
    
    Example:
        $ ollama-pmo remediate
        $ ollama-pmo remediate --dry-run
        $ ollama-pmo remediate --no-auto-fix
    """
    try:
        agent = PMOAgent(
            repo=ctx.obj["repo"],
            repo_path=ctx.obj["repo_path"],
            github_token=ctx.obj["github_token"],
            gcp_project=ctx.obj["gcp_project"],
        )
        
        if dry_run:
            click.echo("🔍 Dry run mode - showing what would be fixed...\n")
        else:
            click.echo("🔧 Remediating compliance drift...\n")
        
        if not dry_run and auto_fix:
            result = agent.auto_remediate_drift()
            
            click.echo(f"{'='*60}")
            click.echo("Auto-Remediation Results")
            click.echo(f"{'='*60}\n")
            
            for fix, success in result["fixes"].items():
                status = "✅" if success else "⏭️"
                detail = result["details"][fix]
                fix_name = fix.replace("_", " ").title()
                
                click.echo(f"{status} {fix_name:30s} - {detail}")
            
            click.echo(f"\n{'='*60}")
            click.echo(
                f"Applied {result['applied']} fixes at {result['timestamp']}"
            )
            click.echo(f"{'='*60}\n")
            
            if result["applied"] > 0:
                click.echo(
                    click.style(
                        f"✅ Successfully remediated {result['applied']} issues",
                        fg="green",
                    )
                )
            else:
                click.echo(
                    click.style("⏭️  No fixes needed - repository compliant", fg="yellow")
                )
        else:
            click.echo("⏭️  Skipped remediation (dry-run or auto-fix disabled)")
            
    except PMOValidationError as e:
        click.echo(click.style(f"❌ Remediation error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--force", is_flag=True, help="Overwrite existing labels"
)
@click.pass_context
def setup_labels(ctx: click.Context, force: bool) -> None:
    """Configure standardized GitHub labels.
    
    Creates 35+ labels across 7 categories:
        - Type (7): feat, fix, refactor, etc.
        - Priority (4): p0-p3
        - Component (7): api, database, frontend, etc.
        - Effort (5): xs, s, m, l, xl
        - PMO (4): governance, compliance, etc.
        - Phase (4): phase-1 through phase-4
        - Status (4): in-progress, blocked, etc.
    
    Example:
        $ ollama-pmo setup-labels
        $ ollama-pmo setup-labels --force
    """
    try:
        agent = PMOAgent(
            repo=ctx.obj["repo"],
            repo_path=ctx.obj["repo_path"],
            github_token=ctx.obj["github_token"],
            gcp_project=ctx.obj["gcp_project"],
        )
        
        click.echo("🏷️  Setting up GitHub labels...\n")
        
        result = agent.setup_github_labels(force=force)
        
        click.echo(f"{'='*60}")
        click.echo("GitHub Label Setup Results")
        click.echo(f"{'='*60}\n")
        
        click.echo(f"✅ Created: {result['created']} labels")
        click.echo(f"🔄 Updated: {result['updated']} labels")
        click.echo(f"⏭️  Skipped: {result['skipped']} labels (already exist)")
        
        if result['failed'] > 0:
            click.echo(
                click.style(f"❌ Failed: {result['failed']} labels", fg="red")
            )
        
        click.echo(f"\n{'='*60}")
        click.echo(f"Total labels configured: {result['total']}")
        click.echo(f"{'='*60}\n")
        
        if result['created'] > 0 or result['updated'] > 0:
            click.echo(
                click.style(
                    f"✅ Successfully configured {result['created'] + result['updated']} labels",
                    fg="green",
                )
            )
        else:
            click.echo(
                click.style("⏭️  All labels already configured", fg="yellow")
            )
            
    except PMOValidationError as e:
        click.echo(click.style(f"❌ Label setup error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Interactive questionnaire (default: true)",
)
@click.option(
    "--template",
    type=click.Path(exists=True),
    help="Path to pmo.yaml template",
)
@click.option(
    "--ai-powered",
    "-a",
    is_flag=True,
    help="Use AI analyzer to auto-generate pmo.yaml",
)
@click.option(
    "--confidence-threshold",
    type=float,
    default=0.7,
    help="Minimum AI confidence (0.0-1.0)",
)
@click.pass_context
def onboard(
    ctx: click.Context,
    interactive: bool,
    template: Optional[str],
    ai_powered: bool,
    confidence_threshold: float,
) -> None:
    """Onboard a new repository with PMO governance.
    
    Modes:
        - AI mode (--ai-powered): Auto-analyzes repository (RECOMMENDED)
        - Interactive mode: Manual questionnaire
        - Template mode: Uses existing template
    
    Performs complete repository setup:
        1. Generate pmo.yaml with intelligent defaults
        2. Configure GitHub labels
        3. Install Git hooks
        4. Enable GPG signing
        5. Create GitHub workflows
        6. Enable branch protection
    
    Typical completion time: <5 minutes
    
    Example:
        $ ollama-pmo onboard --ai-powered  # AI analysis (FAST)
        $ ollama-pmo onboard  # Interactive mode
        $ ollama-pmo onboard --template custom-pmo.yaml
    """
    try:
        click.echo("🚀 Starting repository onboarding...\n")
        
        pmo_data = {}
        
        # AI-Powered Mode (NEW)
        if ai_powered:
            click.echo("🤖 AI-Powered Analysis Mode\n")
            click.echo("  ⏳ Analyzing repository structure...")
            
            from ollama.pmo.analyzer import RepositoryAnalyzer
            
            analyzer = RepositoryAnalyzer(
                ctx.obj["repo_path"],
                confidence_threshold=confidence_threshold,
            )
            
            analysis = analyzer.analyze()
            
            click.echo(f"\n📊 Analysis Confidence: {analysis['confidence']['overall']:.0%}")
            click.echo("  Detected:")
            click.echo(f"    Stack:       {analysis['technical']['stack']}")
            click.echo(f"    Environment: {analysis['organizational']['environment']}")
            click.echo(f"    Team:        {analysis['organizational']['team']}")
            click.echo(f"    Application: {analysis['organizational']['application']}")
            click.echo(f"    Component:   {analysis['organizational']['component']}")
            click.echo(f"    Priority:    {analysis['business']['priority']}")
            
            if analysis['needs_review']:
                click.echo(
                    click.style(
                        f"\n⚠️  Confidence {analysis['confidence']['overall']:.0%} below threshold. Manual review recommended.",
                        fg="yellow",
                    )
                )
            
            # Use AI-generated metadata
            pmo_data = {
                "organizational": analysis['organizational'],
                "lifecycle": analysis['lifecycle'],
                "business": analysis['business'],
                "technical": analysis['technical'],
                "financial": analysis['financial'],
                "git": analysis['git'],
            }
            
            if interactive:
                if not click.confirm("\nUse detected values?", default=True):
                    click.echo("\n📋 Enter custom values (press Enter to keep detected):\n")
                    # Allow overrides (abbreviated for brevity)
                    pmo_data["organizational"]["environment"] = click.prompt(
                        "Environment",
                        default=analysis['organizational']['environment'],
                        type=click.Choice(["development", "staging", "production", "sandbox"]),
                    )
        
        elif interactive:
            click.echo("📋 Please answer the following questions:\n")
            
            # Organizational
            pmo_data["organizational"] = {
                "environment": click.prompt(
                    "Environment",
                    default="development",
                    type=click.Choice(["development", "staging", "production", "sandbox"]),
                ),
                "team": click.prompt("Team name", default="engineering"),
                "application": click.prompt(
                    "Application name",
                    default=ctx.obj["repo_path"].name if ctx.obj["repo_path"] else "app",
                ),
                "component": click.prompt("Component", default="core"),
            }
            
            # Lifecycle
            pmo_data["lifecycle"] = {
                "lifecycle_status": click.prompt(
                    "Lifecycle status",
                    default="active",
                    type=click.Choice(["active", "maintenance", "sunset"]),
                ),
                "created_at": click.prompt(
                    "Created date (YYYY-MM-DD)",
                    default=str(Path.cwd()),
                ),
            }
            
            # Business
            pmo_data["business"] = {
                "priority": click.prompt(
                    "Priority",
                    default="p1",
                    type=click.Choice(["p0", "p1", "p2", "p3"]),
                ),
                "cost_center": click.prompt("Cost center", default="engineering"),
            }
            
            # Technical
            pmo_data["technical"] = {
                "stack": click.prompt("Technology stack", default="python"),
                "managed_by": click.prompt(
                    "Managed by",
                    default="terraform",
                    type=click.Choice(["terraform", "manual", "automation"]),
                ),
            }
            
            # Financial
            pmo_data["financial"] = {
                "budget_allocated": click.prompt("Budget allocated", default="0"),
            }
            
            # Git
            pmo_data["git"] = {
                "git_repo": click.prompt(
                    "Git repository",
                    default=f"github.com/{ctx.obj['repo']}" if ctx.obj['repo'] else "github.com/owner/repo",
                ),
                "created_by": click.prompt("Created by", default="pmo-agent"),
            }
        elif template:
            # Load from template
            with open(template, "r") as f:
                pmo_data = yaml.safe_load(f)
        else:
            click.echo("⏭️  Using defaults (non-interactive mode without template)")
        
        # Write pmo.yaml
        pmo_path = ctx.obj["repo_path"] / "pmo.yaml"
        with open(pmo_path, "w") as f:
            yaml.dump(pmo_data, f, default_flow_style=False, sort_keys=False)
        
        click.echo(f"\n✅ Created pmo.yaml at {pmo_path}")
        
        # Initialize agent
        agent = PMOAgent(
            repo=ctx.obj["repo"],
            repo_path=ctx.obj["repo_path"],
            github_token=ctx.obj["github_token"],
            gcp_project=ctx.obj["gcp_project"],
        )
        
        # Run setup tasks
        click.echo("\n🔧 Setting up repository...\n")
        
        tasks = [
            ("Configuring GitHub labels", lambda: agent.setup_github_labels()),
            ("Remediating compliance drift", lambda: agent.auto_remediate_drift()),
            ("Validating final compliance", lambda: agent.validate_compliance()),
        ]
        
        results = {}
        for task_name, task_func in tasks:
            click.echo(f"  ⏳ {task_name}...")
            try:
                results[task_name] = task_func()
                click.echo(f"  ✅ {task_name} complete")
            except Exception as e:
                click.echo(click.style(f"  ❌ {task_name} failed: {e}", fg="red"))
                results[task_name] = {"error": str(e)}
        
        # Final summary
        click.echo(f"\n{'='*60}")
        click.echo("Onboarding Complete")
        click.echo(f"{'='*60}\n")
        
        if "Validating final compliance" in results:
            final_score = results["Validating final compliance"].get("score", 0)
            click.echo(f"Final compliance score: {final_score}%")
            
            if final_score >= 90:
                click.echo(
                    click.style(
                        "✅ Repository is now fully compliant and production-ready!",
                        fg="green",
                        bold=True,
                    )
                )
            else:
                click.echo(
                    click.style(
                        f"⚠️  Repository compliance at {final_score}% (target: 90%+)",
                        fg="yellow",
                    )
                )
                click.echo("💡 Run 'ollama-pmo validate --verbose' for details")
        
    except Exception as e:
        click.echo(click.style(f"❌ Onboarding error: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("issue_numbers", nargs=-1, type=int)
@click.option(
    "--batch", "-b", is_flag=True, help="Process all issues in batch mode"
)
@click.option(
    "--apply-labels", is_flag=True, help="Automatically apply suggested labels"
)
@click.option(
    "--assign-team", is_flag=True, help="Automatically assign to recommended team"
)
@click.option(
    "--find-duplicates", is_flag=True, help="Find and report duplicate issues"
)
@click.option(
    "--min-similarity",
    type=float,
    default=0.7,
    help="Minimum similarity for duplicates (0.0-1.0)",
)
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.pass_context
def triage(
    ctx: click.Context,
    issue_numbers: tuple,
    batch: bool,
    apply_labels: bool,
    assign_team: bool,
    find_duplicates: bool,
    min_similarity: float,
    output_format: str,
) -> None:
    """Intelligently triage GitHub issues with AI classification.
    
    Classifies issues by:
        - Type: bug, feature, documentation, question, security, performance
        - Priority: p0 (critical), p1 (high), p2 (medium), p3 (low)
        - Team: backend, frontend, devops, security, data
        - Urgency: 0-100 score based on age, activity, priority
    
    Can automatically:
        - Apply suggested labels
        - Assign to recommended team
        - Find duplicate issues
    
    Example:
        $ ollama-pmo triage 123  # Classify single issue
        $ ollama-pmo triage 123 124 125  # Multiple issues
        $ ollama-pmo triage 123 --apply-labels  # Auto-label
        $ ollama-pmo triage 123 --find-duplicates  # Find duplicates
        $ ollama-pmo triage --batch  # Process all open issues
        $ ollama-pmo triage 123 --output-format json  # JSON output
    """
    try:
        from ollama.pmo.classifier import IssueClassifier
        import json as json_module
        
        if not ctx.obj["repo"]:
            click.echo(
                click.style("❌ --repo required for issue triage", fg="red"),
                err=True,
            )
            sys.exit(1)
        
        click.echo("🤖 Initializing AI issue classifier...\n")
        
        classifier = IssueClassifier(
            repo=ctx.obj["repo"],
            github_token=ctx.obj["github_token"],
        )
        
        # Determine which issues to process
        if batch:
            click.echo("📋 Batch mode: Processing all open issues...")
            # Get all open issues (simplified - would need GitHub API call)
            click.echo(
                click.style(
                    "⚠️  Batch mode requires issue numbers. Provide issue numbers or use GitHub API.",
                    fg="yellow",
                )
            )
            if not issue_numbers:
                sys.exit(1)
        
        if not issue_numbers:
            click.echo(
                click.style("❌ No issue numbers provided", fg="red"),
                err=True,
            )
            sys.exit(1)
        
        # Process issues
        if len(issue_numbers) == 1:
            click.echo(f"🔍 Classifying issue #{issue_numbers[0]}...\n")
            result = classifier.classify_issue(issue_numbers[0])
            results = [result]
        else:
            click.echo(f"🔍 Classifying {len(issue_numbers)} issues...\n")
            results = classifier.classify_batch(list(issue_numbers))
        
        # Find duplicates if requested
        duplicate_results = {}
        if find_duplicates:
            click.echo("\n🔎 Searching for duplicate issues...\n")
            for issue_num in issue_numbers:
                duplicates = classifier.find_duplicates(issue_num, threshold=min_similarity)
                if duplicates:
                    duplicate_results[issue_num] = duplicates
        
        # Output results
        if output_format == "json":
            output = {
                "classifications": results,
                "duplicates": duplicate_results if find_duplicates else {},
            }
            click.echo(json_module.dumps(output, indent=2, default=str))
            
        elif output_format == "yaml":
            output = {
                "classifications": results,
                "duplicates": duplicate_results if find_duplicates else {},
            }
            click.echo(yaml.dump(output, default_flow_style=False))
            
        else:  # text format
            for result in results:
                if "error" in result:
                    click.echo(
                        click.style(
                            f"❌ Issue #{result['issue_number']}: {result['error']}",
                            fg="red",
                        )
                    )
                    continue
                
                click.echo(f"{'='*60}")
                click.echo(f"Issue #{result['issue_number']}")
                click.echo(f"{'='*60}\n")
                
                # Classification
                click.echo(f"📌 Title: {result['metadata']['title']}")
                click.echo(f"👤 Author: {result['metadata']['author']}")
                click.echo(f"📅 Age: {result['metadata']['age_days']} days")
                click.echo(f"💬 Comments: {result['metadata']['comments']}\n")
                
                # Type
                type_color = {
                    'bug': 'red',
                    'feature': 'green',
                    'documentation': 'blue',
                    'question': 'yellow',
                    'security': 'magenta',
                    'performance': 'cyan',
                }
                click.echo(
                    "Type: " +
                    click.style(result['issue_type'].upper(), fg=type_color.get(result['issue_type'], 'white'), bold=True)
                )
                
                # Priority
                priority_icons = {
                    'p0': '🔴',
                    'p1': '🟡',
                    'p2': '🟢',
                    'p3': '⚪',
                }
                click.echo(
                    f"Priority: {priority_icons.get(result['priority'], '')} " +
                    click.style(result['priority'].upper(), bold=True)
                )
                
                # Team
                click.echo(f"Team: {result['recommended_team'].title()}")
                
                # Urgency
                urgency = result['urgency_score']
                urgency_color = 'red' if urgency >= 80 else 'yellow' if urgency >= 50 else 'green'
                click.echo(
                    "Urgency: " +
                    click.style(f"{urgency}/100", fg=urgency_color, bold=True)
                )
                
                # Confidence
                confidence = result['confidence']
                conf_color = 'green' if confidence >= 0.8 else 'yellow' if confidence >= 0.5 else 'red'
                click.echo(
                    f"Confidence: " +
                    click.style(f"{confidence:.0%}", fg=conf_color)
                )
                
                # Labels
                click.echo(f"\n🏷️  Suggested Labels: {', '.join(result['suggested_labels'])}")
                
                # Reasoning
                click.echo("\n💡 Reasoning:")
                for key, value in result['reasoning'].items():
                    click.echo(f"   {key}: {value}")
                
                # Duplicates
                if find_duplicates and result['issue_number'] in duplicate_results:
                    dups = duplicate_results[result['issue_number']]
                    if dups:
                        click.echo(f"\n🔗 Found {len(dups)} potential duplicates:")
                        for dup in dups[:5]:  # Show top 5
                            click.echo(
                                f"   #{dup['issue_number']}: " +
                                click.style(f"{dup['similarity']:.0%} similar", fg='yellow') +
                                f" - {dup['url']}"
                            )
                
                click.echo()
            
            # Summary
            if len(results) > 1:
                click.echo(f"{'='*60}")
                click.echo("Summary")
                click.echo(f"{'='*60}\n")
                
                # Count by type
                type_counts = {}
                priority_counts = {}
                for r in results:
                    if "error" not in r:
                        type_counts[r['issue_type']] = type_counts.get(r['issue_type'], 0) + 1
                        priority_counts[r['priority']] = priority_counts.get(r['priority'], 0) + 1
                
                click.echo("By Type:")
                for itype, count in sorted(type_counts.items()):
                    click.echo(f"  {itype:20s}: {count}")
                
                click.echo("\nBy Priority:")
                for priority, count in sorted(priority_counts.items()):
                    click.echo(f"  {priority:20s}: {count}")
        
        # Apply actions if requested
        actions_taken = []
        
        if apply_labels and output_format == "text":
            click.echo(f"\n{'='*60}")
            click.echo("Applying Labels")
            click.echo(f"{'='*60}\n")
            click.echo(
                click.style(
                    "⚠️  Auto-labeling not yet implemented. Use GitHub API to apply labels.",
                    fg="yellow",
                )
            )
            actions_taken.append("labels")
        
        if assign_team and output_format == "text":
            click.echo(f"\n{'='*60}")
            click.echo("Assigning Teams")
            click.echo(f"{'='*60}\n")
            click.echo(
                click.style(
                    "⚠️  Auto-assignment not yet implemented. Use GitHub API to assign.",
                    fg="yellow",
                )
            )
            actions_taken.append("assignment")
        
        # Final message
        if output_format == "text":
            click.echo(f"\n✅ Successfully classified {len([r for r in results if 'error' not in r])} issues")
            if find_duplicates and duplicate_results:
                total_dups = sum(len(dups) for dups in duplicate_results.values())
                click.echo(f"🔎 Found {total_dups} potential duplicates")
        
    except Exception as e:
        click.echo(click.style(f"❌ Triage error: {e}", fg="red"), err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
