# Setup Codex CLI action

This composite action installs the Codex CLI and wires up authentication so subsequent workflow steps can call `codex` without additional configuration.

## Inputs

| Name | Required | Description |
| ---- | -------- | ----------- |
| `version` | No (default: `latest`) | Version of the Codex CLI to install. Provide an explicit semantic version (for example, `1.4.2`) or leave as `latest` to receive the newest published release. |
| `api-key` | **Yes** | API key used by the Codex CLI for authentication. This should come from the `CODEX_API_KEY` repository secret. |
| `base-url` | No | Override for the Codex API base URL. Useful when pointing at a self-hosted Codex deployment (for example, `${{ vars.CODEX_BASE_URL }}`). |

## Outputs

| Name | Description |
| ---- | ----------- |
| `codex-path` | Absolute path to the installed `codex` executable added to `PATH`. |
| `codex-version` | Version string reported by `codex --version`. |

## Example

```yaml
steps:
  - name: Check out repository
    uses: actions/checkout@v4

  - name: Setup Codex CLI
    uses: ./.github/actions/setup-codex
    with:
      version: latest
      api-key: ${{ secrets.CODEX_API_KEY }}
      base-url: ${{ vars.CODEX_BASE_URL }}

  - name: Summarize commits
    run: codex chat --model gpt-4.1 --input "Summarize the recent changes"
```

## Required secrets and variables

* `CODEX_API_KEY` — repository secret used to authenticate with Codex.
* (Optional) `CODEX_BASE_URL` — repository variable used when the workflow targets a self-hosted Codex deployment instead of the default cloud endpoint.
