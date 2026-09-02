# Changelog — Stroes-Rit-Match (RMW)

## 2026-08-31 — Project aangemaakt

Project `stroes-rit-match` opgezet in `D:\PROJECTS\stroes-rit-match`, naar aanleiding
van het officiële akkoord van Wim Stroes. Voortbouwend op de brainstorm-sessie
`D:\AI\brainstorm-sessies\stroes-rit-match-werkbon`.

## 2026-08-31 — Documentatiestructuur gecorrigeerd

`docs/demo.md` alsnog toegevoegd (PoC-scope, doelgroep, scenario, prioriteiten,
blockers) en de documentatiekaart in `GUIDELINES.md` en de documentenlijst in
`CLAUDE.md` bijgewerkt, zodat de structuur volledig aansluit bij de AI-Efficient
Project Documentation Architecture.

## 2026-09-01 — Statuscorrectie: akkoord betrof volledige offerte, live-PoC vervallen

De documentatie beschreef eerder een gefaseerde aanpak (eerst een live-PoC met 1-2
monteurs bij de klant, dan pas een onderbouwde offerte). In werkelijkheid was het
akkoord van Wim (31-08-2026) al akkoord op de volledige offerte voor de complete app;
de live-PoC-met-klant-stap is niet uitgevoerd en vervallen. `GUIDELINES.md`,
`project-context.md`, `docs/demo.md` en `docs/decisions.md` zijn bijgewerkt om dit te
reflecteren. Eerstvolgende stap: een bredere eigen technische validatie (meer
weken/monteurs dan de eerdere test op monteur M5) vóór de bouw van de volledige app
start.

## 2026-09-01 — Bredere technische validatie afgerond (positief)

De bredere technische validatie (2 monteurs, 4 weken: W30 t/m W33) is uitgevoerd en
positief afgerond — 78% resp. 93% van de werkbonnen automatisch teruggevonden, met
verklaarbare afwijkingen, vergelijkbaar met of beter dan de eerdere validatie op
monteur M5. Zie `docs/decisions.md` en `docs/demo.md` voor de details. Dit was de
laatste stap vóór de bouw; `GUIDELINES.md` en `project-context.md` zijn bijgewerkt.
Eerstvolgende stap: de bouw van de volledige app.

## 2026-09-01 — Roadmap toegevoegd, stack-tekst gecorrigeerd naar OvO-scope

`docs/roadmap.md` toegevoegd: de bouwvolgorde voor de eerste werkende versie,
gebaseerd op de scope-opsomming uit het geaccordeerde OvO (v1.8, 31-08-2026).
`GUIDELINES.md`, `docs/architecture.md` en `CLAUDE.md` bijgewerkt (documentatiekaart
+ documentenlijst) en de stack-tekst gecorrigeerd: die zei nog "richting nog niet
vastgelegd", terwijl het OvO de stack al vastlegt (Python/Django, bestandsgebaseerd,
Docker-container). Zie `docs/decisions.md` voor de volledige toelichting.

## 2026-09-01 — Werkwijze bouwfase vastgelegd: Claude Code + Git/GitHub vanaf fase 1

Vastgelegd dat het bouwen van de webapp in een aparte Claude Code-sessie gebeurt
(niet in Cowork), en dat fase 1 van de roadmap een lokale Git-repo + GitHub-repo
opzet. `project-context.md`, `docs/decisions.md` en `docs/roadmap.md` bijgewerkt.

## 2026-09-01 — Taalconventie vastgelegd: code/instructies Engels, UI/docs Nederlands

Op basis van het ReplayCalcTool-precedent vastgelegd dat code, commit-messages en
instructies naar een code tool vanaf nu Engels zijn; UI en klantcommunicatie blijven
Nederlands; de al bestaande Nederlandstalige projectdocumentatie blijft staan.
`CLAUDE.md`, `GUIDELINES.md` en `docs/decisions.md` bijgewerkt.

## 2026-09-01 — Taalconventie aangevuld: Nederlandse domeintermen blijven staan

Verduidelijkt dat Nederlandse domeintermen uit het door SBTT ontworpen format
(Werkbon, Monteur, Rit, SOORT-codes, koppeltabel, tolerantietabel) letterlijk
Nederlands blijven in modelnamen/velden, ook al is de rest van de code Engels — zelfde
principe als "Totaal Montage" bij ReplayCalcTool. `CLAUDE.md`, `GUIDELINES.md` en
`docs/decisions.md` bijgewerkt.

## 2026-09-01 — Fase 1 uitgevoerd: Django-project, Docker-basis en Git-repo

Roadmap-fase 1 (projectopzet) gebouwd in een aparte Claude Code-sessie, conform
`docs/decisions.md` (01-09-2026). Nog geen matchinglogica — alleen het fundament.

- **Django-project** `rmw` met app `matching`, Python 3.13 en Django 5.2 LTS
  (`requirements.txt`). SQLite voor ontwikkeling; de productiedatabase is bewust nog
  niet gekozen (buiten scope fase 1). Omgevingsafhankelijke instellingen komen uit
  omgevingsvariabelen (`RMW_SECRET_KEY`, `RMW_DEBUG`, `RMW_ALLOWED_HOSTS`,
  `RMW_DB_PATH`, `RMW_INBOX_DIR`), gedocumenteerd in `.env.example`.
- **Nederlandse UI-instellingen:** `LANGUAGE_CODE = nl-nl`, tijdzone
  `Europe/Amsterdam`, Django-admin met Nederlandse kop ("RMW — Ritten Match Werkbon").
- **Docker-basis:** `Dockerfile` (python:3.13-slim, gunicorn, WhiteNoise voor
  statische bestanden, non-root gebruiker) en `docker-compose.yml` (named volume voor
  database + inbox, automatische `migrate` bij start, healthcheck op `/health/`).
  Geverifieerd: `docker compose up --build` draait, admin bereikbaar op poort 8000.
- **Git:** lokale repo geïnitialiseerd met `.gitignore` en `.gitattributes` die
  secrets (`.env`), de database en klantdata (Syntess-/RouteVision-exports, `*.xlsx`,
  `*.csv`) buiten versiebeheer houden. Eerste commit met de volledige projectopzet.
- **README.md** toegevoegd met start-instructies (lokaal en via Docker).

Nog niet gedaan: de private GitHub-repo onder RogerH72 (`stroes-rit-match`) —
GitHub CLI is niet geïnstalleerd op de werkplek, dus dit vereist een handmatige
stap. Eerstvolgende bouwstap: fase 2 (data-inlezing), pas na expliciete bevestiging.

## 2026-09-01 — Fase 1 volledig afgerond: GitHub-repo aangemaakt en gepusht

De private GitHub-repo `github.com/RogerH72/stroes-rit-match` is handmatig
aangemaakt (leeg, zonder README/.gitignore), lokaal als `origin` gekoppeld, en de
twee bestaande commits zijn gepusht (`git push -u origin main`, door Roger zelf
bevestigd — pushen vereist expliciete goedkeuring, conform de review-discipline uit
`werkwijze-project`). Roadmap-fase 1 (projectopzet) is hiermee volledig afgerond.
Eerstvolgende stap: fase 2 (data-inlezing), pas te bespreken en te bevestigen
voordat er een instructie naar Claude Code gaat.
