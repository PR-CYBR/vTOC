# TOC-S4 Strategic Hub

TOC-S4 aggregates summaries from the forward stations. Use the onboarding workflow to provision the `toc_s4` schema and seed summary telemetry for leadership dashboards.

## Onboarding steps

1. `export DATABASE_URL_TOC_S4="postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s4"`
2. Run `./onboard.sh`.
3. Execute `python seed.py` to publish command-level rollups.
