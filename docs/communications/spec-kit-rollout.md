# Spec Kit rollout announcement

To: Engineering, Automation, Operations
When: Next team stand-up and weekly async update

We have shipped the Spec Kit workflow that unifies discovery, planning, and
execution across backend, frontend, and automation teams. Please review the
following resources before starting new work:

- README — Spec-driven development (see main repository README)
- [Backlog management lifecycle](../backlog.md#spec-artifact-lifecycle)
- [Quick start step 5](../QUICKSTART.md#5-draft-specs-and-plans-with-spec-kit)
- [Task authoring guide](../tasks/README.md)
- [Integration reference](../workflows/spec-kit-integration.md)
- [Migration FAQ](../spec-kit-migration.md)

## Onboarding checklist updates

Add these items to the station onboarding tracker in Notion (template: `Station
Engineer Onboarding v4`):

- [ ] Complete `/speckit.init` and `/speckit.spec` dry run in the sandbox
      ChatKit channel.
- [ ] Read `docs/spec-kit-migration.md` and confirm understanding with your
      mentor.
- [ ] Create a sample task via `/speckit.tasks demo-feature --ad-hoc` and verify
      it appears in GitHub Projects after running `/speckit.sync`.

## Internal comms

- Post this summary in `#announcements` with links to the docs above.
- Mention Spec Kit adoption in the next onboarding cohort welcome email.
- Tag `@release-managers` so they update the deployment checklist template with
  references to `qa-checklist.md`.

Tracking owner: `github:releasecaptain` (update if responsibilities change).
