# Spec Kit migration FAQ

This guide explains how historical documentation maps onto the Spec Kit
structure and outlines steps for migrating in-flight work.

## Why change?

The previous workflow scattered specs across Google Docs, backlog notes, and PR
descriptions. Spec Kit centralizes discovery artifacts under `specs/<feature>/`
so automation, Codex, and GitHub Projects stay in sync.

## Where did the old documents go?

| Legacy location | New home |
| --- | --- |
| `docs/rfc/` exploratory briefs | Move accepted briefs into `specs/<feature>/spec.md` and archive the RFC once `/speckit.spec` posts the final copy. |
| `docs/tasks/*.md` playbooks | Convert playbooks into `specs/<feature>/plan.md` milestones so backend/frontend owners see the same schedule. |
| GitHub issue checklists | Replace with `specs/<feature>/qa-checklist.md`. The deployment workflow reads this file directly. |
| Project board notes | Link to the feature folder via `/speckit.sync`. Notes stay in GitHub Projects; detailed context lives in `context.yaml`. |

## How do I migrate an active feature?

1. Run `/speckit.init <feature>` in the feature’s ChatKit channel to create the
   folder.
2. Copy the existing discovery doc into `spec.md` and trim obsolete sections.
3. Translate any manually tracked tasks into `/speckit.tasks` generated cards.
4. Execute `/speckit.sync <feature>` to update Codex memories and project boards.
5. Close or archive the legacy documents (Google Docs, standalone markdown
   files) to avoid confusion.

## What about partially completed PRs?

- Reference the new spec folder in the PR description.
- Ensure `qa-checklist.md` includes any testing performed so far.
- After merging, run `/speckit.sync` again to mark remaining tasks as complete or
  create follow-up backlog entries.

## Does this change the release process?

The release cadence stays the same, but release managers now rely on Spec Kit
folders when compiling notes. The `project-done-discussion` workflow reads
`qa-checklist.md` and `plan.md` to draft deployment announcements automatically.

## Who do I contact for help?

Ping `#proj-spec-kit` in Slack or run `/codex ask speckit-migration` in ChatKit
for a guided walkthrough. The Codex prompt references this FAQ and the new
workflow docs.
