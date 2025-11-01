# Creating the Stage Branch

## Problem

The Stage CI Report workflow (`.github/workflows/stage-ci-report.yml`) fails with the error:

```
RequestError [HttpError]: No commit found for the ref stage
```

This occurs because the workflow attempts to read and update the README.md file on the `stage` branch (line 84), but the branch doesn't exist yet.

## Solution

The `stage` branch needs to be created in the repository. This can be done in two ways:

### Option 1: Using the GitHub Actions Workflow (Recommended)

1. Navigate to the Actions tab in the GitHub repository
2. Select the "Create Stage Branch" workflow from the left sidebar
3. Click "Run workflow" and confirm
4. The workflow will create the `stage` branch from the current `main` branch

### Option 2: Using the Script Manually

If you have a GitHub token with appropriate permissions:

```bash
GITHUB_TOKEN=<your-token> node scripts/create-stage-branch.js
```

### Option 3: Manual Git Commands (For Repository Maintainers)

If you have push access to the repository:

```bash
git checkout -b stage
git push origin stage
```

## Verification

Once the branch is created, you can verify it exists by:

1. Visiting `https://github.com/PR-CYBR/vTOC/tree/stage`
2. Running `git ls-remote --heads origin stage` locally
3. Re-running the Stage CI Report workflow to confirm it completes successfully

## Background

The `stage` branch is part of the vTOC automation workflow:

- Codex automation promotes green builds from `main` into `stage`
- The Stage CI pipeline runs tests and builds against the `stage` branch
- The Stage CI Report workflow updates the README.md on the `stage` branch with recent run history
- This provides downstream operators with visibility into the autonomous build loop's health

See the "Codex automation and the stage branch" section in the main README.md for more details.
