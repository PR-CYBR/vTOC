# Project done discussion workflow

The **Project done discussion** workflow opens a GitHub Discussion summarizing finished project items.

## Triggers
- Responds to `projects_v2_item` events whenever an item is edited or converted.

## Required secrets and variables
- `secrets.GITHUB_TOKEN` must permit discussion creation.
- Repository variables configure output: `vars.PROJECT_DONE_DISCUSSION_CATEGORY_ID`, optional `vars.PROJECT_DONE_DISCUSSION_TITLE_PREFIX`, `vars.PROJECT_DONE_DISCUSSION_LABELS`, and field name overrides (`vars.PROJECT_STATUS_FIELD_NAMES`, `vars.PROJECT_DONE_STATUS_VALUE`, etc.).

## Jobs and major steps
### `post-discussion` job
- Parses the project item context inside `Post discussion`, loading field values and ensuring the status matches the configured Done value.
- Builds discussion content from the backlog link, Codex plan/run references, related PRs, and metadata discovered in the GraphQL query.
- Creates the discussion via `createDiscussion` and adds labels when requested.

## Expected artifacts
- The workflow does not upload artifacts; the resulting GitHub Discussion is the primary output.

## Common failure modes
- Missing `PROJECT_DONE_DISCUSSION_CATEGORY_ID` halts the run inside `Post discussion`.
- Items that have not reached the Done status cause the step to exit early without posting.
- If the backlog, plan, or run fields referenced in the configuration are absent, the workflow produces incomplete context or exits when required data is missing.
