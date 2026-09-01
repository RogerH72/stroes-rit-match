# RMW — Rit-Match-Werkbon

Matching tool for Stroes Bouw en Techniek (SBTT). RMW compares the completed
werkbonnen from Syntess against the trip, time and location data from
RouteVision, per monteur and per working day, and flags deviations.

Background and scope: `project-context.md`, `GUIDELINES.md` and `docs/`.
The project documentation is Dutch by design; code, comments and commit
messages are English, and all UI text is Dutch (see `docs/decisions.md`,
2026-09-01).

## Status

Roadmap phase 1 (project setup). No matching logic yet — see `docs/roadmap.md`.

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

## Configuration

All environment-specific settings come from environment variables; see
`.env.example` for the full list. `.env` is git-ignored and must never be
committed, and neither may any customer data (Syntess/RouteVision exports).

## Layout

```text
manage.py
rmw/           Django project (settings, urls, wsgi/asgi)
matching/      Application: matching logic, models, admin (still empty)
docs/          Project documentation (Dutch)
```
