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

## 2026-09-02 — Fase 2 gebouwd: bestandsdetectie servermap en ruwe data-inlezing

Roadmap-fase 2 (data-inlezing) gebouwd in de Claude Code-sessie. Nog géén
matchinglogica of tijdlijnreconstructie — dat is fase 3.

- **Bestandsdetectie (polling):** management-command `check_imports` bekijkt de
  servermap, meet per herkend bestand de bestandsgrootte en leest een bestand pas in
  zodra die grootte lang genoeg ongewijzigd is. Geen filesystem-events, conform
  `docs/architecture.md` (onbetrouwbaar op een SMB-share).
- **Twee losse instellingen, allebei via omgevingsvariabelen:**
  `POLL_INTERVAL_MINUTES` (standaard 5) en `STABILITY_MINUTES` (standaard 30). Het
  benodigde aantal opeenvolgende ongewijzigde metingen wordt daaruit afgeleid
  (30/5 = 6), naar boven afgerond, met een ondergrens van 1 meting voor het geval de
  stabiliteitsmarge korter is dan het polling-interval. De regel zelf staat als losse,
  Django-vrije functie in `matching/ingest/stability.py` en is met gewone unittests
  getest, zonder op een echte timer te wachten.
- **Servermap instelbaar:** `SERVERMAP_PATH` (productie:
  `\\stroes-1909\atrium\Autoprint\RUUDS`, lokaal een gewone map). De fase 1-naam
  `RMW_INBOX_DIR` blijft als alternatief werken.
- **Ruwe importtabellen, één per bronbestand** (`Uren`, `Rit`, `Relatie`,
  `WerkbonControle`), 1-op-1 opgeslagen zoals aangeleverd, plus de bijhoudtabel
  `ImportedFile` (bestandsnaam, laatst gemeten grootte, tijdstip laatste meting,
  status wachtend/stabiel/verwerkt, tijdstip verwerkt). Wat al verwerkt is, wordt
  uitsluitend in de database bijgehouden: geen "verwerkt"-map, en bestanden op de
  servermap worden nooit verplaatst, hernoemd of verwijderd.
- **Elk bronbestand wordt onafhankelijk gevolgd:** één regel per bestand, zodat een
  ontbrekend of nog groeiend `Werkbonnen.xlsx` de verwerking van `Uren.xlsx` en de
  RouteVision-CSV niet blokkeert (`docs/functioneel-ontwerp.md` §3a). Een bestand dat
  niet gelezen kan worden houdt de andere ook niet tegen: de fout wordt vastgelegd en
  de volgende ronde probeert het opnieuw.
- **Fase-status volledigheidscontrole:** `Werkbonnen.xlsx` bevat één regel per
  fase-overgang. Per werkbon wordt één status afgeleid — "afgerond" zodra een regel
  Fase `Afgehandeld` of `Gereed` heeft, anders "nog niet gestart". Opgeslagen per
  (Werkbon, Medewerker, Datum). Reistijd, Werktijd, Titel en "Monteur meegereden"
  worden bewust niet opgeslagen. De controle zelf is fase 3.
- **Parser-details uit de voorbeeldbestanden:** de drie Syntess-exports staan op een
  tabblad `Atrium` (niet het eerste/actieve blad); de RouteVision-CSV is `cp1252` met
  `;` als scheidingsteken en Nederlandse decimaalkomma's; `Relaties.xlsx` heeft een
  lange staart lege regels die wordt overgeslagen.
- **Scheduler in de container:** `scripts/scheduler.sh` draait `check_imports` elke
  `POLL_INTERVAL_MINUTES`, als aparte service uit hetzelfde image
  (`docker-compose.yml`). Een simpele loop in plaats van cron/supercronic: geen extra
  pakket in het image nodig en logging gaat gewoon naar stdout.
- **Handmatig te draaien** tijdens ontwikkeling en testen:
  `check_imports --path <map> --force` (direct inlezen), `--dry-run` (alleen tonen),
  `--reprocess` (al verwerkte bestanden opnieuw inlezen — alleen handmatig; de
  geplande run herverwerkt nooit uit zichzelf). Geen automatische herverwerking en
  geen e-mailsignalering, conform `docs/architecture.md`.
- **Django-admin:** de vier importtabellen zijn read-only zichtbaar (het zijn kopieën
  van de bronbestanden); `ImportedFile` toont de status per bestand. De echte
  beheerschermen (koppeltabellen, tolerantietabel) zijn fase 4.
- **Tests:** 74 tests, groen. De suite maakt zijn eigen miniatuur-exports aan en draait
  dus ook zonder de voorbeeldbestanden; `matching/tests/test_sample_data.py` draait
  daarnaast tegen de echte geanonimiseerde exports in `voorbeeld-data/` en wordt
  overgeslagen als die map ontbreekt. Handmatig end-to-end gecontroleerd tegen de
  voorbeeldbestanden: 31 urenregels, 92 ritten, 2 relaties, 19 werkbonregels.
- **Afhankelijkheid toegevoegd:** `openpyxl` voor de drie Excel-bronnen. Bewust geen
  pandas — te zwaar voor een handvol kolommen in een container die licht moet blijven;
  de CSV gaat via de standaardbibliotheek.

Openstaand aandachtspunt: de bestandsherkenning is bewust ruim gehouden (trefwoord +
extensie) omdat de bestandsnaam-conventie van de automatische export nog niet bevestigd
is met Stric/RVS Solutions/RouteVision (`docs/functioneel-ontwerp.md` §9, punt 1). Zodra
die bekend is hoeft alleen de patronentabel in `matching/ingest/filenames.py` aangepast
te worden.

## 2026-09-03 — Fase 2 restpunten afgerond: push, superuser, Docker-build gecontroleerd

De drie restpunten uit `GUIDELINES.md` (punt 4, 02-09-2026) zijn afgehandeld —
zuiver operationeel, geen ontwerpvraag.

- **Documentatie eerst gecommit.** De 7 documentatiebestanden met de fase 2-updates
  van 02-09-2026 (`GUIDELINES.md`, `docs/architecture.md`, `docs/business-rules.md`,
  `docs/database.md`, `docs/decisions.md`, `docs/functioneel-ontwerp.md`,
  `docs/roadmap.md`) stonden nog los; die zijn gereviewd (alle 7 diffs bevatten
  precies de verwachte fase 2-updates, niets onverwachts) en in commit `9796dd0`
  vastgelegd.
- **Gepusht.** `git push` naar `origin/main`: 4 commits gepubliceerd
  (`61fd4aa`..`9796dd0`), werkboom schoon, branch in sync met origin.
- **Lokale Django-superuser opnieuw aangemaakt.** De oude `db.sqlite3` was tijdens
  het testen verwijderd. `createsuperuser` vereist een TTY en kon niet via de
  Claude Code-tools draaien (`EOFError` op de eerste prompt); Roger heeft de
  gebruiker zelf aangemaakt in een los terminalvenster en de login op
  `http://127.0.0.1:8000/admin/` bevestigd.
- **Docker-build gecontroleerd.** Docker Desktop stond niet aan en is gestart.
  `docker compose up --build`: beide services (`web`, `scheduler`) gebouwd naar
  `rmw:dev`, geen fouten — de nieuwe `scripts/`-map en `openpyxl` zitten er goed in.
  Migraties (`matching.0001_initial`) toegepast bij het opstarten. Healthcheck op
  `/health/` groen (container-status `healthy`). `/` redirect correct naar
  `/admin/login/` (200). Scheduler draait en meldt netjes "Server share
  `/app/data/inbox` is not available; nothing to check" zonder te crashen — het
  bedoelde gedrag bij een ontbrekend/nog niet gemount bronpad. Tijdelijk een
  wegwerp-superuser aangemaakt in de container om de admin-index en alle vijf
  changelists (`importedfile`, `relatie`, `rit`, `uren`, `werkboncontrole`) te
  verifiëren (allemaal 200), daarna weer verwijderd (0 users) en `docker compose
  down` gedraaid.

Roadmap-fase 2 is hiermee volledig afgerond, inclusief de operationele afronding.
Eerstvolgende stap: roadmap-fase 3 (reken-/matchmotor) bespreken en bevestigen,
pas daarna een instructie naar de Claude Code-sessie.

## 2026-09-03 — Fase 3 gebouwd: reken-/matchmotor en koppeltabellen

Na bespreking en bevestiging in de Cowork-sessie (koppeltabellen nu al als echte
Django-modellen, "monteur meegereden" als instelbare 3-standen toggle, `soort` op
`BekendeLocatie` beperkt tot K/L/C als gebruikerskeuze) is een precieze instructie
naar de Claude Code-sessie gegaan. Resultaat, gecontroleerd door de gevalideerde
`matching/models.py` en `matching/timeline/engine.py` zelf te lezen:

- **Koppeltabellen** (`matching/models.py`): `Monteur`, `BekendeLocatie` (met
  `is_depot`-vlag en `soort` beperkt tot K/L/C via model-`choices`),
  `Instelling` (singleton — vaste `pk=1`, `load()`-classmethod, `clean()`/
  `save()`/`delete()`-overrides die verwijderen en dubbele rijen blokkeren, met
  een DB-`CheckConstraint` als achtervang), `MeegeredenKoppeling`
  (periode-gebonden junior→senior-koppeling met een `geldt_op(datum)`-helper),
  `ToleranceRegel` (met een geseede "algemeen"-rij van 15 minuten als fallback),
  `Tijdblok`. Allemaal met normale, bewerkbare `ModelAdmin`-registraties (in
  tegenstelling tot de read-only importtabellen uit fase 2).
- **Matchmotor** (`matching/timeline/engine.py`, 441 regels, uitgebreid
  becommentarieerd per de nieuwe `CLAUDE.md`-afspraak): de gevalideerde
  PoC-heuristiek overgezet — `Koppeltabellen`-dataclass (gesplitst op
  `is_depot`), `DagUren`-dataclass, `home_streets_for()` voor
  thuisadres-detectie, `build_day()` als hoofdfunctie, `_classify_stop()` met de
  exacte prioriteitsvolgorde uit de PoC (1. depot-`BekendeLocatie` → L, 2. eigen
  Uren-regel op postcode-dan-straat, depotstraat uitgesloten → W, 3. overige
  `BekendeLocatie` op straat-dan-postcode → K/L/C, 4. thuisstraat → laten
  vallen, niet opgeslagen, 5. tolerantiecheck tegen `ToleranceRegel` → O bij
  gat ≥ drempel, ? bij gat ≥ 1 minuut, anders laten vallen), `_trim_home_hops()`,
  `_ride_moments()` (met afhandeling van ritten die middernacht overschrijden),
  `_minutes_between()` (met clamping van negatieve duur).
- **Tests**: 143 tests groen, inclusief expliciete regressietests tegen de
  PoC-cijfers (werkbon-hervinding in de verwachte bandbreedte) en tegen de
  depotprioriteitsregel (M1: depot wint van een werkbonmatch).

Twee aandachtspunten kwamen boven, geen bugs — vastgelegd als apart besluit in
`docs/decisions.md` (03-09-2026): een straat-niveau depotadres claimt élk adres
op die straat vóór een werkbonmatch (relevant zodra het echte SBTT-depotadres in
fase 4 wordt ingevoerd), en het eerder genomen besluit om Werkbonnen.xlsx niet als
matchbron te gebruiken geeft een lager werkbon-hervindingspercentage dan de PoC
liet zien (verwacht gevolg van dat besluit, geen motorfout).

Commit `eea759c`, lokaal gecommit en gepusht door Roger (deze Cowork-sessie heeft
geen GitHub-credentials).

Roadmap-fase 3 is hiermee afgerond. Eerstvolgende stap: roadmap-fase 4
(verfijning van de beheerschermen) bespreken en bevestigen.

## 2026-09-03 — Werkbonnen.xlsx-postcode gebouwd als matchvangnet

Uitvoering van het besluit hierboven ("Record decision: Werkbonnen.xlsx postcode
as matching fallback"), gebouwd door de Claude Code-sessie op basis van de
instructie uit deze Cowork-sessie. Commit `37b4d71`, 149 tests groen (was 143).

- `WerkbonControle` uitgebreid met `postcode`, `titel`, `tijd`, `reistijd`,
  `werktijd` en `monteur_meegereden`. Alleen `postcode` wordt door de matchmotor
  gelezen (als vangnet ná de eigen Uren.xlsx-match, vóór de koppeltabel — de
  depotcheck loopt er nog altijd vóór); `titel` is uitsluitend omschrijvingstekst
  wanneer dat vangnet raak is. De rest blijft ongebruikt, zoals bedoeld.
- Nieuwe `WerkbonPostcodes`-klasse in `matching/timeline/engine.py`, analoog aan
  de bestaande `DagUren`, en `_classify_stop()` uitgebreid met de nieuwe stap in
  de prioriteitsvolgorde (tussen de oude stap 2 en 3).
- Parser (`matching/ingest/parsers/werkbonnen.py`) aangepast zodat de gededupliceerde
  rij per (Werkbon, Medewerker, Datum) ook de waarden van de eerst-geziene rij
  bewaart, niet alleen het rijnummer.
- Testresultaat op `voorbeeld-data/`: hervindingspercentage M5 van 73% naar
  81,8% (9/11) — nagenoeg gelijk aan de 82% die de PoC op dezelfde week haalde.
  M1 blijft op 0% (verwacht): zijn werkbonnen liggen op de depotpostcode, en de
  depotregel wint altijd vóórdat het nieuwe vangnet aan de beurt komt. De
  testondergrens is daarom verhoogd van 0,6 naar 0,75.

Twee operationele punten, meegenomen in `docs/business-rules.md` en
`DRAAIBOEK.md`:

1. De migratie zelf is puur additief (lege standaardwaarden) — bestaande
   `WerkbonControle`-rijen krijgen pas een postcode nadat Werkbonnen.xlsx
   opnieuw is ingelezen. Na elke deploy van deze wijziging (dus ook straks bij
   de eerste productie-uitrol): `check_imports --force --reprocess` gevolgd
   door `run_matching --force`, in die volgorde.
2. De commit is getekend met de attributie van de Claude Code-sessie die de
   code daadwerkelijk schreef (Claude Opus 5, `session_01AK64on6x58NHXQc7G9otES`),
   niet met de attributie van deze Cowork-sessie die de instructie opstelde —
   terecht: een commit hoort de sessie te attribueren die de code schreef. Vanaf
   nu wordt een instructie naar Claude Code niet meer voorzien van de eigen
   footer van de opstellende sessie; de uitvoerende sessie gebruikt zijn eigen
   attributie.
