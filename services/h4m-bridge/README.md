# H4M Bridge Service

The H4M bridge scans mounted H4M storage for IQ capture files and decoded log
exports, extracts basic metadata, and forwards structured events to the vTOC
backend. The service is implemented in Python and designed to run on a worker
with `/mnt/h4m` mounted locally.

## Supported formats

The bridge recognises two high-level families of log files:

| Type     | Extensions                                    | Metadata extraction |
|----------|------------------------------------------------|---------------------|
| IQ       | `.iq`, `.cfile`, `.iq.tar`, `.iq.gz`           | Size, modified time, first 32 bytes preview |
| Decoded  | `.json`, `.ndjson`, `.log`, `.txt`             | Size, modified time, first line (JSON parsed when available) |

Additional extensions can be added in `h4m_bridge/scanner.py`.

## Usage

```bash
python -m h4m_bridge.cli \
  --storage /mnt/h4m \
  --backend-url https://backend.example.com/api/h4m/logs \
  --dedup-state /var/lib/h4m-bridge/state.json
```

### Environment variables

The CLI accepts environment overrides for the most common parameters:

- `H4M_STORAGE` – storage root (defaults to `/mnt/h4m`).
- `H4M_BACKEND_URL` – backend endpoint for posting log events.
- `H4M_DEDUP_STATE` – location of the deduplication state file.

### Dry run mode

Pass `--dry-run` to disable HTTP requests and deduplication state updates. The
service still scans files and logs the summary of work that *would* be
performed. This is useful for verifying configuration prior to enabling
imports.

## Deduplication

Imported files are tracked in a JSON state file keyed by the absolute path and
file signature (size + modified timestamp). Subsequent runs skip unchanged
files to avoid sending duplicate events. The deduplication logic lives in
`h4m_bridge/dedup.py`.

## Logging & summaries

The bridge logs each discovered file at debug level and prints a structured
summary at the end of every run. Summary data includes total processed files,
number imported, duplicates skipped, failures, and a per-type breakdown.

## Development

Install dependencies (only standard library is required) and run tests with
pytest:

```bash
pip install -r requirements.txt  # optional, standard library only
pytest services/h4m-bridge/tests
```

Fixture-based tests provide coverage for scanning, deduplication, and dry-run
behaviour. Test fixtures live under `services/h4m-bridge/tests/fixtures`.

