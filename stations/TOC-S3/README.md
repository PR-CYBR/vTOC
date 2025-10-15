# TOC-S3 Agent Operations

TOC-S3 fuses telemetry streams for autonomous agent planning. Provision the `toc_s3` schema and seed agent-centric events for integration testing.

## Onboarding steps

1. `export DATABASE_URL_TOC_S3="postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s3"`
2. Run `./onboard.sh`.
3. Execute `python seed.py` to publish synthetic mission intents.
