# GitHub Actions Workflows Overview

This document provides an overview of the GitHub Actions workflows in the vTOC repository, their purposes, dependencies, and configuration requirements.

## Workflow Categories

### 1. CI/CD Workflows

#### ci.yml
- **Purpose**: Runs comprehensive tests, linting, and builds for frontend and backend
- **Triggers**: Push to `main`, `prod`, `stage`; pull requests to these branches
- **Key Jobs**:
  - Alembic database migrations testing
  - Frontend linting, type-checking, and tests (including Playwright)
  - Backend linting, type-checking, and tests
  - Multi-platform Docker image builds
  - Spec Kit task validation
- **Required Secrets**: `GITHUB_TOKEN` (automatic)
- **Notes**: This is the primary quality gate for code changes

#### publish-containers.yml
- **Purpose**: Builds and publishes multi-arch Docker images to GHCR and Docker Hub
- **Triggers**: 
  - Push to `main`, `live`, `prod`
  - Tags matching `v*`
  - Weekly schedule (Monday at 12:00 UTC)
  - Manual dispatch
- **Key Jobs**:
  - Run tests via reusable-tests.yml
  - Build and scan containers via reusable-build-containers.yml
  - Verify Docker Hub production images
  - Generate release summary
- **Required Secrets**:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`
- **Notes**: Only runs on release branches, not on feature or smoke-test branches

#### docs-pages.yml
- **Purpose**: Builds and deploys MkDocs documentation to GitHub Pages
- **Triggers**:
  - Push to `main` or `prod` affecting docs files
  - Manual dispatch
- **Path Filters**: `docs/**`, `mkdocs.yml`, `.github/workflows/docs-pages.yml`
- **Required Permissions**: `contents: read`, `pages: write`, `id-token: write`

### 2. Project Automation Workflows

These workflows integrate with GitHub Projects V2 to automate project management tasks.

#### project-backlog-plan.yml
- **Purpose**: Generates Codex plans for new backlog items
- **Triggers**: `projects_v2_item` created or edited
- **Required Secrets**:
  - `CODEX_API_KEY` - API key for Codex integration
  - `PROJECTS_WORKFLOW_TOKEN` (optional) - Enhanced token for project access
- **Required Variables**:
  - `CODEX_BASE_URL` - Base URL for Codex API
  - `CODEX_CLI_VERSION` (optional) - Specific CLI version
- **Safeguards**: Skips gracefully if secrets are missing (with warning)
- **See**: [project-backlog-plan.md](./project-backlog-plan.md)

#### project-ready-execute.yml
- **Purpose**: Executes Codex plans when project items move to "Ready"
- **Triggers**: `projects_v2_item` edited (status change from Backlog → Ready)
- **Required Secrets**:
  - `CODEX_API_KEY`
  - `PROJECTS_WORKFLOW_TOKEN` (optional)
- **Required Variables**:
  - `CODEX_BASE_URL`
  - `PROJECT_READY_REVIEWERS` (optional) - Team/users to notify
- **Safeguards**: Fails with clear error if required configuration is missing
- **See**: [project-ready-execute.md](./project-ready-execute.md)

#### project-done-discussion.yml
- **Purpose**: Creates GitHub Discussions summarizing completed project items
- **Triggers**: `projects_v2_item` edited or converted (status → Done)
- **Required Variables**:
  - `PROJECT_DONE_DISCUSSION_CATEGORY_ID` - Discussion category node ID
  - `PROJECT_DONE_DISCUSSION_TITLE_PREFIX` (optional)
  - `PROJECT_DONE_DISCUSSION_LABELS` (optional)
- **Safeguards**: Skips gracefully if category ID is missing (with warning)
- **See**: [project-done-discussion.md](./project-done-discussion.md)

#### backlog-project-sync.yml
- **Purpose**: Syncs backlog.yaml with GitHub Projects
- **Triggers**: Push to `codex` branch affecting `backlog/backlog.yaml`
- **Required Variables**: `PROJECT_NAME` environment variable
- **Notes**: Creates project items for new backlog entries

### 3. Discussion & Documentation Workflows

#### main-discussion-summary.yml
- **Purpose**: Creates discussion summaries for commits to main branch
- **Triggers**:
  - Push to `main`
  - Manual dispatch
- **Required Secrets**: `CODEX_API_KEY`
- **Required Variables**:
  - `CODEX_BASE_URL`
  - `DOCS_DISCUSSION_CATEGORY_ID`
  - `DOCS_DISCUSSION_LABELS` (optional)
  - `DOCS_DISCUSSION_TITLE_PREFIX` (optional)
- **Safeguards**: Skips gracefully if configuration is missing (with warning)
- **See**: [main-discussion-summary.md](./main-discussion-summary.md)

### 4. Release & Deployment Workflows

#### live-release-pr.yml
- **Purpose**: Gates pull requests to the `live` branch
- **Triggers**: Pull requests targeting `live`

#### prod-to-live.yml
- **Purpose**: Promotes changes from `prod` to `live`
- **See**: [prod-to-live.md](./prod-to-live.md)

#### build-image-live.yml  
- **Purpose**: Builds live environment images
- **See**: [build-image-live.md](./build-image-live.md)

## Branch Strategy

### Protected Branches
- **main**: Primary development branch, requires PR + CI passing
- **stage**: Staging environment branch
- **prod**: Production-ready branch
- **live**: Live deployment branch

### Feature Branches
- **copilot/*** - Copilot-generated feature branches
- **feature/*** - Manual feature branches

### Smoke Test Branches
- **codex-smoketest-*** - Temporary branches for Codex testing
- **Note**: These branches intentionally skip most workflows (CI, publish-containers, etc.)
- **Expected Behavior**: Workflows triggered on smoke-test branches will show 0 jobs run and may be marked as "failed" by GitHub. This is normal and expected.

## Workflow Dependencies

```
publish-containers.yml
  ├─→ reusable-tests.yml
  └─→ reusable-build-containers.yml

ci.yml (independent)

project-backlog-plan.yml
  └─→ project-ready-execute.yml (via Projects status change)
      └─→ project-done-discussion.yml (via Projects status change)

main-discussion-summary.yml (independent)
docs-pages.yml (independent)
```

## Configuration Checklist

### Required for All Workflows
- ✅ `GITHUB_TOKEN` (automatically provided)

### Required for Container Publishing
- ✅ `DOCKERHUB_USERNAME` - Docker Hub username
- ✅ `DOCKERHUB_TOKEN` - Docker Hub access token

### Required for Project Automation
- ✅ `CODEX_API_KEY` - Codex API authentication key
- ✅ `CODEX_BASE_URL` - Codex API endpoint URL (e.g., `https://api.codex.example.com`)
- ⚠️ `PROJECTS_WORKFLOW_TOKEN` - Optional enhanced token for project access
- ⚠️ `CODEX_CLI_VERSION` - Optional specific version (defaults to "latest")

### Required for Discussion Automation
- ✅ `PROJECT_DONE_DISCUSSION_CATEGORY_ID` - GitHub Discussion category node ID
- ✅ `DOCS_DISCUSSION_CATEGORY_ID` - GitHub Discussion category node ID for docs
- ⚠️ `PROJECT_DONE_DISCUSSION_TITLE_PREFIX` - Optional prefix for discussion titles
- ⚠️ `DOCS_DISCUSSION_TITLE_PREFIX` - Optional prefix for doc discussion titles
- ⚠️ `PROJECT_DONE_DISCUSSION_LABELS` - Optional comma-separated label names
- ⚠️ `DOCS_DISCUSSION_LABELS` - Optional comma-separated label names

### Optional Configuration
- ⚠️ `PROJECT_READY_REVIEWERS` - GitHub users/teams to notify (e.g., `@team/reviewers`)
- ⚠️ `REVIEW_TEAM` - Fallback for reviewer notifications

## Troubleshooting

### "Workflow run completed but shows as failed"
**Symptom**: Workflow is triggered but shows 0 jobs run and is marked as failed.

**Cause**: This happens when a workflow is triggered on a branch that doesn't match the workflow's branch filters.

**Solution**: This is expected behavior for branches like `codex-smoketest-*` that don't match the workflow triggers. These "failures" can be safely ignored.

### "Project workflows are skipping"
**Symptom**: Project automation workflows show warnings and skip execution.

**Cause**: Required secrets or variables are not configured.

**Solution**: 
1. Check the workflow run logs for specific missing configuration
2. Add the required secrets/variables in repository settings
3. Re-trigger the workflow or wait for the next project event

### "Codex CLI installation fails"
**Symptom**: The `setup-codex` action fails during workflow execution.

**Cause**: Network issues, invalid API key, or missing base URL.

**Solution**:
1. Verify `CODEX_API_KEY` is valid
2. Verify `CODEX_BASE_URL` points to a reachable endpoint
3. Check for network connectivity issues in the workflow logs

### "Discussion creation fails"
**Symptom**: Discussion workflows complete but no discussion is created.

**Cause**: Invalid discussion category ID or insufficient permissions.

**Solution**:
1. Verify the category ID is correct (use GraphQL API to find it)
2. Ensure the `GITHUB_TOKEN` or `PROJECTS_WORKFLOW_TOKEN` has `discussions: write` permission
3. Check that the repository has Discussions enabled

## Adding New Workflows

When adding new workflows to this repository:

1. **Document the workflow**: Create a markdown file in `docs/workflows/` explaining:
   - Purpose and triggers
   - Required configuration
   - Job dependencies
   - Example usage

2. **Add safety checks**: Include guards for missing secrets/configuration:
   ```yaml
   - name: Check for required configuration
     run: |
       if [[ -z "${{ secrets.MY_SECRET }}" ]]; then
         echo "::warning::MY_SECRET is not configured."
         exit 0
       fi
   ```

3. **Use appropriate branch filters**: Ensure workflows only run on intended branches:
   ```yaml
   on:
     push:
       branches:
         - main
         - prod
   ```

4. **Update this README**: Add the workflow to the appropriate category above.

## Further Reading

- [Spec Kit Integration](./spec-kit-integration.md) - Codex and Spec Kit workflow integration
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Projects V2 Automation](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project)
