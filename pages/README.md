# vTOC Documentation Deployment

This branch is published automatically to GitHub Pages and should not be updated manually. All documentation sources live on the `main` branch under the [`docs/`](https://github.com/vasa-dev/vTOC/tree/main/docs) directory and are rendered with [MkDocs](https://www.mkdocs.org/).

## Workflow Summary

1. **Author content on `main`:** Add or update Markdown files inside `docs/` and commit them to the `main` (or `prod`) branch. Remember to keep front-page navigation current in [`mkdocs.yml`](https://github.com/vasa-dev/vTOC/blob/main/mkdocs.yml) when you introduce new top-level sections.
2. **Open a pull request:** Changes should be reviewed through the standard PR process. The `docs-pages` workflow runs on every push to `main` or `prod` that touches documentation sources.
3. **Automatic publish:** When documentation updates land on `main` or `prod`, the GitHub Actions workflow builds the MkDocs site and deploys the resulting HTML into this branch using `actions/deploy-pages`. The content served at https://vasa-dev.github.io/vTOC/ (or the configured Pages URL) always reflects the latest successful deployment.

## Responsibilities for vTOC-AgentKit

- Keep documentation edits confined to the source tree in `docs/` and update `mkdocs.yml` if navigation needs to change.
- Ensure that the documentation build passes locally (`mkdocs build --strict`) before opening a PR.
- Avoid committing directly to the `pages` branch. The CI workflow overwrites this branch on every deploy.

## Previewing Documentation Locally

1. Install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r docs/requirements.txt
   ```
2. Run the live preview server from the repository root:
   ```bash
   mkdocs serve
   ```
3. Visit http://127.0.0.1:8000 in your browser to review the site. MkDocs hot-reloads when you edit Markdown files.

When satisfied with the preview, commit your changes to `main` and let the workflow publish the update.
