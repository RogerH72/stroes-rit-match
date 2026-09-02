# RMW — Rit-Match-Werkbon

Matching tool for Stroes Bouw en Techniek (SBTT). RMW compares the completed
werkbonnen from Syntess against the trip, time and location data from
RouteVision, per monteur and per working day, and flags deviations.

Background and scope: `project-context.md`, `GUIDELINES.md` and `docs/`.
The project documentation is Dutch by design; code, comments and commit
messages are English, and all UI text is Dutch (see `docs/decisions.md`,
2026-09-01).

## Status

Roadmap phase 2 (data ingestion): the app detects the four source files on the
server share and imports them into raw tables. No matching or timeline logic yet
— that is phase 3. See `docs/roadmap.md`.

## Stack

- Python 3.13, Django 5.2 LTS
- SQLite for development (no production database chosen yet)
- Docker for a light, self-contained deployment

## Local development

```bash
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/macOS

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/admin/.

## Running in Docker

```bash
docker compose up --build
```

The app is served on http://localhost:8000/ (`/health/` for a liveness check).
Database and inbox live in the `rmw-data` volume, so a rebuild keeps the data.
Create an admin user in the running container:

```bash
docker compose exec web python manage.py createsuperuser
```

## File detection and import

A scheduler inside the container runs `manage.py check_imports` every
`POLL_INTERVAL_MINUTES`. It measures every recognised file on the share and reads
one once its size has stayed unchanged for `STABILITY_MINUTES` — with the
defaults, six unchanged measurements in a row. Files on the share are only ever
read: nothing is moved, renamed or deleted, and the database alone records what
has been processed.

Each of the four sources is tracked separately, so a missing or still-growing
file for one of them never holds up the others.

Run a check by hand (the manual trigger during development):

```bash
python manage.py check_imports                              # normal run
python manage.py check_imports --path voorbeeld-data --force  # import right away
python manage.py check_imports --dry-run                    # report, write nothing
python manage.py check_imports --reprocess --force          # re-read processed files
```

For local development, point `SERVERMAP_PATH` at an ordinary folder (the default
is `data/inbox`) and drop copies of the sample exports in it.

## Tests

```bash
python manage.py test matching
```

The suite writes its own miniature exports, so it runs on a fresh clone. The
tests in `matching/tests/test_sample_data.py` additionally run against the real
anonymised exports in `voorbeeld-data/` and are skipped when that folder is
absent.

## Configuration

All environment-specific settings come from environment variables; see
`.env.example` for the full list. `.env` is git-ignored and must never be
committed, and neither may any customer data (Syntess/RouteVision exports).

Phase 2 adds three:

| Variable | Default | Meaning |
| --- | --- | --- |
| `SERVERMAP_PATH` | `data/inbox` | Folder that is watched for the source files. On the server: a mount of `\\stroes-1909\atrium\Autoprint\RUUDS`. |
| `POLL_INTERVAL_MINUTES` | `5` | How often the share is checked. |
| `STABILITY_MINUTES` | `30` | How long a file's size must stay unchanged before it is read. |

## Layout

```text
manage.py
rmw/                    Django project (settings, urls, wsgi/asgi)
matching/
  models.py             Raw import tables + import bookkeeping
  ingest/               File detection, stability rule, parsers
  management/commands/  check_imports
  tests/
scripts/scheduler.sh    Poll loop used by the scheduler container
docs/                   Project documentation (Dutch)
```
