# GUIDELINES — Stroes-Rit-Match (RMW)

_Last updated: 2026-09-03_

## Project identity

RMW (Ritten Match Werkbon) matcht Syntess-werkbonnen tegen RouteVision-ritdata per
monteur per dag, reconstrueert een dagtijdlijn en signaleert afwijkingen (onverklaarde
stops, adres-mismatches, afwijkende reistijden) t.o.v. een tolerantietabel per
activiteit. Klant: Stroes Bouw en Techniek (SBTT). **Status: offerte voor de volledige
app geaccordeerd (31-08-2026); de bredere technische validatie (2 monteurs, 4 weken)
is afgerond en positief (01-09-2026, zie `docs/decisions.md`). De bouw van de
volledige app kan beginnen.**

## Technology stack

**Vastgelegd via het OvO (v1.8, geaccordeerd door Wim Stroes op 31-08-2026) voor de
eerste werkende versie** — dit is geen open richting meer, maar getekende scope:

- Python/Django-webapp, bestandsgebaseerd: leest dagelijks de Syntess-exports en de
  RouteVision-download uit een servermap; geen API-koppeling in deze versie.
- Django-admin voor de beheerschermen (koppeltabellen, tolerantietabel).
- Oplevering als lichte, zelfstandige Docker-container, geplaatst in de omgeving die
  SBTT/Stric beschikbaar stelt (bij voorkeur een bestaande Proxmox-/VM-omgeving,
  anders een kleine VPS).

Zie `docs/roadmap.md` voor de bouwvolgorde en `docs/architecture.md` voor het ontwerp
van het trigger-mechanisme (bestandsdetectie). Bewust buiten deze eerste versie:
directe API-koppeling met Syntess/RouteVision, een uitgebreider dashboard, Access/
Power BI als reporting-schil, automatische signalering, een serviceabonnement — zie
`docs/roadmap.md` voor de volledige lijst.

## Current architecture

**Fase 1 (projectopzet) is gebouwd (01-09-2026):** Django 5.2 LTS-project `rmw` met
app `matching` (Python 3.13), SQLite voor ontwikkeling, instellingen via
omgevingsvariabelen (`.env.example`), en een Docker-basis (`Dockerfile` +
`docker-compose.yml`, gunicorn + WhiteNoise, healthcheck op `/health/`) die lokaal
draait. Lokale Git-repo aanwezig; de GitHub-repo aangemaakt en gekoppeld
(`github.com/RogerH72/stroes-rit-match`, private). Zie `docs/changelog.md`
(01-09-2026).

**Fase 2 (data-inlezing) is gebouwd (02-09-2026) en volledig afgerond (03-09-2026):**
bestandsdetectie met polling (5 min) + stabiliteitscheck (30 min, los instelbaar), de
vier ruwe importmodellen (Uren, Rit, Relatie, WerkbonControle) en de
`ImportedFile`-bijhoudtabel. 74 tests groen. Gepusht naar GitHub, lokale
Django-superuser werkt, en de Docker-build is gecontroleerd: build, migraties,
healthcheck en admin allemaal groen. Zie `docs/changelog.md` en `docs/decisions.md`
(02-09-2026 en 03-09-2026).

Beoogde PoC-architectuur: een los
Python-script dat de Syntess-exports en de RouteVision-download inleest, per
monteur/dag een tijdlijn reconstrueert, matcht tegen bekende locaties
(straatnaam-fallback wanneer postcode niet exact matcht; depot-vóór-werk-regel), en
een weekoverzicht wegschrijft. Zie `docs/architecture.md`.

## Application / module overview

- `rmw/` — Django-projectconfiguratie (settings, urls, wsgi/asgi).
- `matching/` — de applicatie: matchinglogica, modellen en admin (nu nog leeg;
  gevuld in roadmap-fase 2 t/m 6).

De PoC zelf was één script (`D:\STROES\PoC-demo\rmw_sbtt.py`).

## Current development principles

- **Taal (01-09-2026):** code (variabelen, comments), commit-messages en instructies
  naar een code tool zijn Engels, vanaf de bouw van de webapp — zelfde conventie als
  ReplayCalcTool. UI en klantcommunicatie blijven altijd Nederlands. De al bestaande
  Nederlandstalige projectdocumentatie wordt niet met terugwerkende kracht vertaald.
  **Uitzondering:** Nederlandse domeintermen uit het door SBTT ontworpen format
  (Werkbon, Monteur, Rit, SOORT-codes K/L/C/W/?/O/R, koppeltabel, tolerantietabel)
  blijven letterlijk Nederlands in modelnamen/velden — zelfde principe als "Totaal
  Montage" bij ReplayCalcTool. Zie `docs/decisions.md`.
- Bouwen gebeurt in een aparte Claude Code-sessie, niet in Cowork (zie
  `docs/decisions.md`, 01-09-2026).

## Current architectural constraints

Syntess-ontsluiting is voor de PoC beperkt tot 3 dagelijkse Excel-exports (geen
API/DB-toegang); een betaalde Syntess-API-koppeling wordt bewust uitgesteld.
RouteVision-data komt voor de PoC uit een handmatige download, niet uit de API.

## Current priorities

1. **Gedaan (01-09-2026).** Bredere technische validatie op 2 monteurs x 4 weken
   (Jesse Verkerk 78%, Dennis van de Berg 93% werkbonnen automatisch teruggevonden) —
   resultaat vergelijkbaar met of beter dan de eerdere test op monteur M5 (82%).
   Afwijkingen blijven verklaarbaar op de bredere dataset. Zie `docs/decisions.md`
   (01-09-2026) en `docs/demo.md`.
2. **Gedaan (01-09-2026).** Roadmap-fase 1 volledig afgerond: Django-project,
   Docker-basis, lokale Git-repo én de private GitHub-repo
   (`github.com/RogerH72/stroes-rit-match`) aangemaakt, gekoppeld en gepusht (zie
   `docs/changelog.md`).
3. **Gedaan (02-09-2026).** Roadmap-fase 2 (data-inlezing) gebouwd en gecommit.
   Zie `docs/changelog.md` en `docs/decisions.md`.
4. **Gedaan (03-09-2026).** Restpunten van fase 2 afgehandeld: `git push` (4 commits
   naar `origin/main`), lokale Django-superuser opnieuw aangemaakt en login bevestigd,
   en de Docker-build gecontroleerd (build, migraties, healthcheck, admin — allemaal
   groen). Zie `docs/changelog.md` (03-09-2026).
5. **Eerstvolgende stap:** roadmap-fase 3 (reken-/matchmotor) hier bespreken en
   bevestigen, pas daarna een instructie naar de Claude Code-sessie.

**Vervallen:** de eerder voorziene live-PoC-fase met 1-2 monteurs bij de klant (~1
week, in overleg met Wim) — het akkoord van 31-08-2026 betrof al de volledige
offerte, niet alleen een PoC-stap. Zie `docs/decisions.md`.

## Important warnings

Mogelijk meerwerk (een snelheidscontrole per locatie op basis van RouteVision-data)
raakt AVG/medewerkersmonitoring en vereist een zorgvuldig juridisch/HR-traject naast de
techniek — nog geen besluit. Zie `docs/decisions.md`.

## Documentation map

```text
Architecture      → docs/architecture.md
Database          → docs/database.md
Business rules    → docs/business-rules.md
UI specification  → docs/ui-spec.md
Current demo      → docs/demo.md
Roadmap           → docs/roadmap.md
Decisions         → docs/decisions.md
Changelog         → docs/changelog.md
Deploy runbook    → DRAAIBOEK.md (root van de repository)
```
