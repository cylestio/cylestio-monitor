#!/usr/bin/env python3
"""
Comprehensive security scanning script for Cylestio Monitor.

This script runs multiple security scans and generates a consolidated report.
"""

import os
import subprocess
import sys
import json
import datetime
import argparse
from pathlib import Path


def setup_directories():
    """Create necessary directories for reports."""
    reports_dir = Path("security-reports")
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def run_command(cmd, description, output_file=None):
    """Run a command and capture output."""
    print(f"Running {description}...")

    try:
        if output_file:
            with open(output_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
        else:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

        if result.returncode != 0:
            print(f"Warning: {description} completed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
        else:
            print(f"{description} completed successfully")

        return result
    except Exception as e:
        print(f"Error running {description}: {e}")
        return None


def run_bandit_scan(reports_dir):
    """Run Bandit security scan."""
    output_file = reports_dir / "bandit-report.json"
    return run_command(
        ["bandit", "-r", "src", "-f", "json", "-o", str(output_file)],
        "Bandit security scan"
    )


def run_dependency_scan(reports_dir):
    """Run pip-audit dependency scan."""
    output_file = reports_dir / "dependency-audit.json"
    return run_command(
        ["pip-audit", "--format", "json", "--output", str(output_file)],
        "pip-audit dependency scan"
    )


def run_secrets_scan(reports_dir):
    """Run detect-secrets scan."""
    output_file = reports_dir / "secrets-scan.json"
    return run_command(
        ["detect-secrets", "scan", "--all-files"],
        "detect-secrets scan",
        output_file
    )


def run_semgrep_scan(reports_dir):
    """Run Semgrep scan."""
    output_file = reports_dir / "semgrep-results.json"
    return run_command(
        ["semgrep", "--config=p/python", "--config=p/security-audit", "src/", "--json"],
        "Semgrep scan",
        output_file
    )


def generate_summary_report(reports_dir):
    """Generate a summary report of all scans."""
    summary_file = reports_dir / "security-summary.md"

    with open(summary_file, "w") as f:
        f.write(f"# Cylestio Monitor Security Scan Summary\n\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Bandit summary
        bandit_file = reports_dir / "bandit-report.json"
        if bandit_file.exists():
            try:
                with open(bandit_file) as bf:
                    bandit_data = json.load(bf)
                    f.write("## Bandit Security Issues\n\n")

                    results = bandit_data.get("results", [])
                    metrics = bandit_data.get("metrics", {})

                    if results:
                        f.write(f"Found {len(results)} potential issues\n\n")

                        # Group by severity
                        issues_by_severity = {}
                        for issue in results:
                            severity = issue.get("issue_severity", "unknown")
                            if severity not in issues_by_severity:
                                issues_by_severity[severity] = []
                            issues_by_severity[severity].append(issue)

                        for severity, issues in issues_by_severity.items():
                            f.write(f"### {severity.capitalize()} Severity ({len(issues)})\n\n")
                            for issue in issues:
                                f.write(f"- [{issue.get('test_id')}] {issue.get('issue_text')}\n")
                                f.write(f"  - File: {issue.get('filename')}:{issue.get('line_number')}\n")
                            f.write("\n")
                    else:
                        f.write("No issues found\n\n")
            except Exception as e:
                f.write(f"Error parsing Bandit results: {e}\n\n")

        # Dependency scan summary
        dep_file = reports_dir / "dependency-audit.json"
        if dep_file.exists():
            try:
                with open(dep_file) as df:
                    dep_data = json.load(df)
                    f.write("## Dependency Vulnerabilities\n\n")

                    vulns = dep_data.get("vulnerabilities", [])
                    if vulns:
                        f.write(f"Found {len(vulns)} vulnerabilities\n\n")

                        # Group by severity
                        vulns_by_severity = {}
                        for vuln in vulns:
                            severity = vuln.get("severity", "unknown")
                            if severity not in vulns_by_severity:
                                vulns_by_severity[severity] = []
                            vulns_by_severity[severity].append(vuln)

                        for severity, severity_vulns in sorted(vulns_by_severity.items(),
                                                          key=lambda x: {"critical": 0, "high": 1, "medium": 2,
                                                                         "low": 3, "unknown": 4}.get(x[0], 5)):
                            f.write(f"### {severity.capitalize()} Severity ({len(severity_vulns)})\n\n")
                            for vuln in severity_vulns:
                                f.write(f"- {vuln.get('name')} {vuln.get('version')}: {vuln.get('id')}\n")
                                f.write(f"  - Description: {vuln.get('description')}\n")
                                f.write(f"  - Fixed in: {vuln.get('fix_versions', ['unknown'])}\n")
                            f.write("\n")
                    else:
                        f.write("No vulnerabilities found\n\n")
            except Exception as e:
                f.write(f"Error parsing dependency results: {e}\n\n")

        # Secrets scan summary
        secrets_file = reports_dir / "secrets-scan.json"
        if secrets_file.exists():
            try:
                with open(secrets_file) as sf:
                    secrets_data = json.load(sf)
                    f.write("## Secret Detection\n\n")

                    results = secrets_data.get("results", {})
                    if results:
                        total_secrets = sum(len(secrets) for secrets in results.values())
                        f.write(f"Found {total_secrets} potential secrets in {len(results)} files\n\n")

                        for filename, secrets in results.items():
                            f.write(f"### {filename}\n\n")
                            for secret in secrets:
                                f.write(f"- Line {secret.get('line_number')}: {secret.get('type')}\n")
                            f.write("\n")
                    else:
                        f.write("No secrets found\n\n")
            except Exception as e:
                f.write(f"Error parsing secrets results: {e}\n\n")

    print(f"Summary report generated: {summary_file}")
    return summary_file


def main():
    """Run all security scans and generate reports."""
    parser = argparse.ArgumentParser(description="Generate security reports for Cylestio Monitor")
    parser.add_argument("--bandit", action="store_true", help="Run Bandit scan")
    parser.add_argument("--dependencies", action="store_true", help="Run dependency scan")
    parser.add_argument("--secrets", action="store_true", help="Run secrets scan")
    parser.add_argument("--semgrep", action="store_true", help="Run Semgrep scan")
    parser.add_argument("--all", action="store_true", help="Run all scans")

    args = parser.parse_args()

    # If no specific scan is requested, run all
    if not (args.bandit or args.dependencies or args.secrets or args.semgrep):
        args.all = True

    reports_dir = setup_directories()

    if args.all or args.bandit:
        run_bandit_scan(reports_dir)

    if args.all or args.dependencies:
        run_dependency_scan(reports_dir)

    if args.all or args.secrets:
        run_secrets_scan(reports_dir)

    if args.all or args.semgrep:
        run_semgrep_scan(reports_dir)

    summary_file = generate_summary_report(reports_dir)

    print("\nSecurity scan complete")
    print(f"Summary report: {summary_file}")


if __name__ == "__main__":
    main()
