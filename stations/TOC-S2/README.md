# TOC-S2 Air Tasking Cell

TOC-S2 orchestrates airborne ISR platforms. The onboarding workflow provisions the `toc_s2` schema and seeds flight tracks for tasking demos.

## Onboarding steps

1. `export DATABASE_URL_TOC_S2="postgresql+psycopg2://vtoc:vtocpass@localhost:5432/vtoc?options=-csearch_path%3Dtoc_s2"`
2. Run `./onboard.sh`.
3. Execute `python seed.py` to insert flight sorties and assignments.
