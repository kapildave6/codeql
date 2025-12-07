#!/usr/bin/env python3
"""
Scan GitHub Actions workflow files for 'id-token: write' permission
and generate a SARIF file for CodeQL alerts.
"""

import os
import re
import json
import glob
from pathlib import Path

def scan_workflows():
    """Scan workflow files and return issues."""
    issues = []
    workflow_dir = Path(".github/workflows")
    
    if not workflow_dir.exists():
        return issues
    
    for workflow_file in glob.glob(str(workflow_dir / "*.yml")) + glob.glob(str(workflow_dir / "*.yaml")):
        with open(workflow_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, start=1):
                # Check for id-token: write pattern (case insensitive, flexible spacing)
                if re.search(r'id-token\s*:\s*write', line, re.IGNORECASE):
                    # Get relative path
                    rel_path = str(Path(workflow_file).relative_to('.'))
                    
                    # Find column position
                    col = line.find('id-token')
                    if col == -1:
                        col = 1
                    else:
                        col += 1  # SARIF uses 1-based indexing
                    
                    issue = {
                        "ruleId": "github-actions/id-token-write",
                        "ruleIndex": 0,
                        "level": "error",
                        "message": {
                            "text": "Workflow uses 'id-token: write' permission which allows requesting OIDC tokens."
                        },
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": rel_path
                                },
                                "region": {
                                    "startLine": line_num,
                                    "startColumn": col,
                                    "endLine": line_num,
                                    "endColumn": col + len("id-token: write")
                                }
                            }
                        }]
                    }
                    issues.append(issue)
    
    return issues

def generate_sarif(issues):
    """Generate SARIF file from issues."""
    sarif = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Workflow Security Scanner",
                    "version": "1.0.0",
                    "rules": [{
                        "id": "github-actions/id-token-write",
                        "name": "id-token: write permission detected",
                        "shortDescription": {
                            "text": "Workflow uses id-token: write permission"
                        },
                        "fullDescription": {
                            "text": "Detects when a workflow uses id-token: write permission, which allows the workflow to request OIDC tokens."
                        },
                        "defaultConfiguration": {
                            "level": "error"
                        },
                        "properties": {
                            "tags": ["security", "github-actions"]
                        }
                    }]
                }
            },
            "results": issues
        }]
    }
    return sarif

if __name__ == "__main__":
    issues = scan_workflows()
    
    if issues:
        print(f"Found {len(issues)} issue(s)")
        sarif = generate_sarif(issues)
        with open("results.sarif", "w") as f:
            json.dump(sarif, f, indent=2)
        print("Generated results.sarif")
        exit(0)  # Exit successfully - issues will be reported as CodeQL alerts
    else:
        print("No issues found")
        # Create empty SARIF file
        sarif = generate_sarif([])
        with open("results.sarif", "w") as f:
            json.dump(sarif, f, indent=2)
        exit(0)

