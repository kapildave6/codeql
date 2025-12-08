# Global CodeQL Workflow Scanner Setup

This guide explains how to set up a reusable workflow scanner that can be used across multiple repositories without duplicating code.

## Architecture

The solution uses GitHub's **reusable workflows** feature:
- **Central Repository**: Contains the scanner script and reusable workflow
- **Target Repositories**: Only need a simple workflow file that calls the reusable workflow

## Setup Instructions

### Step 1: Set Up Central Repository

1. **Create a central repository** (e.g., `your-org/security-scanner` or use this repository)

2. **Ensure the scanner script is accessible** at:
   ```
   .github/scripts/scan_workflows.py
   ```

3. **Create the reusable workflow** at:
   ```
   .github/workflows/reusable-scan-workflows.yml
   ```

### Step 2: Use in Target Repositories

In each repository where you want to scan workflows, create a simple workflow file:

**File:** `.github/workflows/scan-workflows.yml`

```yaml
name: "Scan Workflows for Security Issues"

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]
  schedule:
    - cron: '0 0 * * 0' # Weekly on Sunday
  workflow_dispatch:

jobs:
  scan:
    uses: your-org/security-scanner/.github/workflows/reusable-scan-workflows.yml@main
    # Optional: customize the category
    # with:
    #   category: "custom-category-name"
```

**Important:** Replace `your-org/security-scanner` with your actual central repository path.

### Step 3: Grant Permissions

The reusable workflow needs access to the target repository. Ensure:

1. The central repository is **public**, OR
2. The target repository grants access to the central repository's workflow

For private central repositories, you may need to configure workflow access in repository settings.

## Alternative: Using a GitHub Action

If you prefer a more flexible approach, you can create a custom GitHub Action. Here's how:

### Create Action in Central Repository

**File:** `action.yml` (in root of central repository)

```yaml
name: 'Workflow Security Scanner'
description: 'Scans GitHub Actions workflows for id-token: write permission'
inputs:
  category:
    description: 'Category for SARIF upload'
    required: false
    default: 'workflow-security-scan'
runs:
  using: 'composite'
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.x'
    
    - name: Download scanner script
      shell: bash
      run: |
        curl -o scan_workflows.py https://raw.githubusercontent.com/${{ github.repository }}/${{ github.ref_name }}/.github/scripts/scan_workflows.py
        chmod +x scan_workflows.py
    
    - name: Scan workflows
      shell: bash
      run: |
        python3 scan_workflows.py
    
    - name: Upload SARIF
      if: always()
      uses: github/codeql-action/upload-sarif@v4
      with:
        sarif_file: results.sarif
        category: ${{ inputs.category }}
```

**Usage in target repositories:**

```yaml
name: "Scan Workflows"

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: your-org/security-scanner@main
        with:
          category: "workflow-security-scan"
```

## Recommended Approach: Reusable Workflow

The **reusable workflow** approach is recommended because:
- ✅ Simpler setup in target repositories
- ✅ Better permission handling
- ✅ Easier to maintain
- ✅ No need to publish as a separate action

## Organization-Level Setup

For organization-wide deployment:

### Option 1: Organization Workflow Template

1. Create the reusable workflow in a central repository
2. Share the workflow file as a template
3. Teams can copy the calling workflow to their repositories

### Option 2: Repository Template

1. Create a repository template with the workflow file
2. Teams create new repositories from the template
3. The workflow is automatically included

### Option 3: Automation Script

Create a script to add the workflow to multiple repositories:

```bash
#!/bin/bash
# add-scanner.sh

REPOS=(
  "org/repo1"
  "org/repo2"
  "org/repo3"
)

CENTRAL_REPO="your-org/security-scanner"
BRANCH="main"

for repo in "${REPOS[@]}"; do
  echo "Adding scanner to $repo"
  # Use GitHub CLI or API to create the workflow file
  gh workflow create "$repo" \
    --file .github/workflows/scan-workflows.yml \
    --repo "$CENTRAL_REPO" \
    --ref "$BRANCH"
done
```

## Updating the Scanner

When you update the scanner script in the central repository:

1. **Update the script** in the central repository
2. **Tag a new release** (optional, for versioning)
3. **Target repositories automatically use the latest version** (if using `@main`) or update the reference

To pin to a specific version, use:
```yaml
uses: your-org/security-scanner/.github/workflows/reusable-scan-workflows.yml@v1.0.0
```

## Troubleshooting

### Permission Errors

If you see permission errors:
- Ensure the central repository workflow has access to target repositories
- Check that `security-events: write` permission is granted
- For private central repos, configure workflow access in repository settings

### Script Not Found

If the script download fails:
- Verify the script path in the central repository
- Ensure the branch/tag reference is correct
- Check that the repository is accessible (public or permissions granted)

### Workflow Not Triggering

- Verify the workflow file is in `.github/workflows/` directory
- Check YAML syntax is valid
- Ensure the branch names match your repository's default branch

## Best Practices

1. **Version Pinning**: Use tags/versions instead of `@main` for production
2. **Centralized Updates**: Update scanner logic in one place
3. **Documentation**: Keep this guide updated with any changes
4. **Testing**: Test updates in a test repository before deploying widely
5. **Monitoring**: Monitor workflow runs across repositories

## Example: Complete Target Repository Setup

Create `.github/workflows/scan-workflows.yml`:

```yaml
name: "Security Workflow Scanner"

on:
  push:
    branches: [ "main", "master", "develop" ]
  pull_request:
    branches: [ "main", "master", "develop" ]
  schedule:
    - cron: '0 0 * * 0' # Weekly on Sunday
  workflow_dispatch:

jobs:
  scan-workflows:
    uses: your-org/security-scanner/.github/workflows/reusable-scan-workflows.yml@main
    secrets: inherit
```

That's it! Just 15 lines of YAML in each target repository.

## Migration from Local Setup

If you already have the workflow in individual repositories:

1. Set up the central repository with the reusable workflow
2. Replace the existing workflow file with the simple calling workflow
3. Remove the local `scan_workflows.py` script (no longer needed)
4. Test the workflow run

---

**Last Updated:** [Current Date]  
**Central Repository:** `your-org/security-scanner`  
**Maintainer:** [Your Team]

