# Quickstart

1. Review the five bot spec directories under `specs/` to understand scope and dependencies.
2. Run `pnpm install` followed by `pnpm lint` and `pnpm test` to exercise baseline QA automation.
3. Generate updated architecture diagrams using Mermaid templates in `docs/diagrams/` (create if absent) and embed them in docs.
4. Execute integration tests via `pnpm --filter bot-shared test` and platform-specific suites (`bot-telegram`, `bot-slack`, `bot-discord`).
5. Assemble rollout checklist by combining shared runtime deployment steps with platform-specific runbooks.
6. Publish updated documentation and QA configs, then notify contributors in the `#vtoc` Slack channel with summary and next steps.
