# GitHub CodeQL Integration for Workflow Security Scanning

## Overview

This document describes the CodeQL integration setup that automatically detects the use of `id-token: write` permission in GitHub Actions workflow files and creates CodeQL security alerts in the repository's Security tab.

## Problem Statement

GitHub Actions workflows that use `id-token: write` permission can request OIDC (OpenID Connect) tokens, which may pose security risks if not properly managed. While CodeQL doesn't natively support YAML analysis, this solution provides a workaround to scan workflow files and generate CodeQL alerts.

## Solution Architecture

The solution uses a custom GitHub Actions workflow that:
1. Scans all workflow files (`.yml` and `.yaml`) in the `.github/workflows/` directory
2. Detects instances of `id-token: write` permission
3. Generates a SARIF (Static Analysis Results Interchange Format) file
4. Uploads the SARIF file to GitHub, which creates CodeQL alerts in the Security tab

## Components

### 1. Workflow Scanner (`codeql-scan-workflows.yml`)

**Location:** `.github/workflows/codeql-scan-workflows.yml`

This is the main GitHub Actions workflow that orchestrates the scanning process.

**Key Features:**
- Triggers on push, pull requests, and weekly schedule
- Runs on Ubuntu latest
- Requires `security-events: write` permission to create alerts
- Uses Python 3.x to execute the scanning script
- Uploads SARIF results to GitHub Security

**Workflow Triggers:**
- Push to `main` branch
- Pull requests to `main` branch
- Weekly schedule (Sundays at midnight UTC)
- Manual trigger via `workflow_dispatch`

### 2. Scanning Script (`scan_workflows.py`)

**Location:** `.github/scripts/scan_workflows.py`

A Python script that performs the actual scanning and SARIF file generation.

**Functionality:**
- Scans all `.yml` and `.yaml` files in `.github/workflows/`
- Uses regex pattern matching to find `id-token: write` (case-insensitive, flexible spacing)
- Extracts file paths and line numbers for accurate alert location
- Generates SARIF 2.1.0 compliant output
- Creates structured alerts with proper metadata

**Detection Pattern:**
The script searches for the pattern: `id-token\s*:\s*write` (case-insensitive)
- Matches: `id-token: write`, `id-token:write`, `ID-TOKEN: WRITE`, etc.

### 3. Test Workflow (`test-workflow.yml`)

**Location:** `.github/workflows/test-workflow.yml`

A sample workflow file that contains `id-token: write` permission, used to verify the scanner is working correctly.

## How It Works

### Step-by-Step Process

1. **Workflow Trigger**
   - The workflow is triggered by one of the configured events (push, PR, schedule, or manual)

2. **Repository Checkout**
   - The workflow checks out the repository code

3. **Python Environment Setup**
   - Sets up Python 3.x environment using `actions/setup-python@v5`

4. **Scanning Execution**
   - Runs `scan_workflows.py` which:
     - Iterates through all workflow files
     - Searches for `id-token: write` patterns
     - Collects file paths, line numbers, and column positions
     - Generates a SARIF file (`results.sarif`)

5. **SARIF Upload**
   - Uploads the SARIF file using `github/codeql-action/upload-sarif@v4`
   - GitHub processes the SARIF file and creates CodeQL alerts

6. **Alert Creation**
   - Alerts appear in the repository's **Security** tab under **Code scanning alerts**
   - Each alert includes:
     - File path
     - Line number
     - Column position
     - Alert message
     - Severity level (warning)

## SARIF File Structure

The generated SARIF file follows the OASIS SARIF 2.1.0 specification:

```json
{
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
          "level": "warning"
        }]
      }
    },
    "results": [
      {
        "ruleId": "github-actions/id-token-write",
        "level": "warning",
        "message": {
          "text": "Workflow uses 'id-token: write' permission which allows requesting OIDC tokens."
        },
        "locations": [{
          "physicalLocation": {
            "artifactLocation": {
              "uri": ".github/workflows/test-workflow.yml"
            },
            "region": {
              "startLine": 10,
              "startColumn": 7
            }
          }
        }]
      }
    ]
  }]
}
```

## Viewing Alerts

Once the workflow runs and uploads SARIF results:

1. Navigate to your repository on GitHub
2. Go to the **Security** tab
3. Click on **Code scanning alerts**
4. You'll see alerts with:
   - **Rule ID:** `github-actions/id-token-write`
   - **Severity:** Warning
   - **Location:** File path and line number
   - **Message:** Description of the security concern

## Configuration

### Modifying Scan Patterns

To scan for different patterns, edit `.github/scripts/scan_workflows.py`:

```python
# Current pattern (line 28)
if re.search(r'id-token\s*:\s*write', line, re.IGNORECASE):

# Example: Scan for other permissions
if re.search(r'permissions:\s*write', line, re.IGNORECASE):
```

### Changing Workflow Schedule

Edit `.github/workflows/codeql-scan-workflows.yml`:

```yaml
schedule:
  - cron: '0 0 * * 0'  # Weekly on Sunday
  # Other examples:
  # - cron: '0 0 * * *'  # Daily
  # - cron: '0 0 * * 1'  # Weekly on Monday
```

### Adjusting Alert Severity

Modify the SARIF generation in `scan_workflows.py`:

```python
"level": "warning"  # Options: "error", "warning", "note"
```

## Permissions Required

The workflow requires the following permissions:

```yaml
permissions:
  actions: read      # Read workflow information
  contents: read    # Read repository files
  security-events: write  # Create security alerts (required)
```

## Limitations

1. **YAML Language Support:** CodeQL doesn't natively support YAML analysis, which is why we use a custom SARIF upload approach
2. **Pattern Matching:** The scanner uses regex pattern matching, which may have false positives/negatives in complex YAML structures
3. **Line-Level Detection:** Alerts point to the line containing the pattern but may not always identify the exact permission context

## Troubleshooting

### Workflow Not Running
- Check that the workflow file is in `.github/workflows/`
- Verify YAML syntax is valid
- Ensure the branch has the workflow file committed

### No Alerts Appearing
- Check workflow run logs for errors
- Verify `security-events: write` permission is granted
- Ensure SARIF file is being generated (check workflow logs)
- Wait a few minutes for GitHub to process the SARIF upload

### False Positives
- Review the regex pattern in `scan_workflows.py`
- Check if the pattern matches comments or other non-permission contexts
- Adjust the pattern to be more specific if needed

## Best Practices

1. **Regular Scanning:** Keep the weekly schedule enabled for continuous monitoring
2. **PR Checks:** The workflow runs on pull requests to catch issues before merging
3. **Review Alerts:** Regularly review CodeQL alerts in the Security tab
4. **Documentation:** Document legitimate uses of `id-token: write` in workflow comments
5. **Team Awareness:** Ensure team members understand the security implications of OIDC tokens

## Example Alert

When the scanner finds `id-token: write` in a workflow file, it creates an alert like this:

**Alert Details:**
- **Rule:** `github-actions/id-token-write`
- **Severity:** Warning
- **File:** `.github/workflows/test-workflow.yml`
- **Line:** 10
- **Message:** "Workflow uses 'id-token: write' permission which allows requesting OIDC tokens."

## Maintenance

### Updating the Scanner

1. Modify `scan_workflows.py` for new detection patterns
2. Test locally before committing:
   ```bash
   python3 .github/scripts/scan_workflows.py
   ```
3. Check the generated `results.sarif` file
4. Commit and push changes
5. Monitor workflow runs to ensure alerts are created correctly

### Version Updates

Keep the GitHub Actions versions updated:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `github/codeql-action/upload-sarif@v4`

## Related Resources

- [GitHub CodeQL Documentation](https://docs.github.com/en/code-security/code-scanning)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [OIDC Token Security](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

## Support

For issues or questions:
1. Check workflow run logs in the Actions tab
2. Review the Security tab for alert details
3. Consult the troubleshooting section above
4. Contact the security team for assistance

---

**Last Updated:** [Current Date]  
**Version:** 1.0.0  
**Maintainer:** [Your Team/Name]

