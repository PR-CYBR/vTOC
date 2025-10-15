# TOC-S1 Coastal Watch

The TOC-S1 station monitors littoral traffic and coastal sensors. Use the onboarding script to apply migrations against the `toc_s1` schema and seed maritime telemetry for demos.

## Onboarding steps

1. Export the station database URL:
   ```bash
   export DATABASE_URL_TOC_S1="postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s1"
   ```
2. Run `./onboard.sh` to apply migrations.
3. Execute `python seed.py` to populate baseline sensors and signals.
