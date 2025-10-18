# `main` branch guide

The `main` branch is the default entry point for contributors. It contains the latest documentation, tooling, and integration
workflows that support day-to-day development. Updates land here only after they have been promoted through production so that
local environments always reflect what is currently running in the field.

## What lives here

- Documentation updates, walkthroughs, and onboarding material
- Tooling automation that accelerates developer workflows
- References to the latest production release that has passed health verification

## Contribution expectations

1. Start feature work from a topic branch that targets `prod`.
2. Use the preview and CI pipelines to validate changes before requesting a review.
3. After a deployment succeeds, wait for the automated `prod → main` synchronization PR and review the diff before merging.

This branch intentionally avoids manual merges from any source other than the production synchronization to keep the release
story easy to audit.
