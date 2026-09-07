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

## 2026-09-03 — Klant-uitleg matchmotor toegevoegd

Nieuw `voor-klant/`-mapje voor materiaal dat letterlijk met Wim/SBTT gedeeld
wordt (geen technische documentatie). Eerste document:
`voor-klant/hoe-werkt-de-matching.md`, een uitleg zonder technisch jargon van
hoe de app een werkdag herkent (rit-data leidend, de classificatievolgorde in
gewone taal, de SOORT-codes, en waarom dit betrouwbaar genoeg is — gebaseerd
op de PoC-validatie). Onderhoudsafspraak vastgelegd in `CLAUDE.md`: dit
document wordt bijgewerkt zodra de matchlogica wijzigt, en zodra een
onderdeel dat er nu nog als "niet klaar" in staat (bijv. het
uitzonderingenscherm) gereed komt.

## 2026-09-03 — Fase 4 gebouwd: matching-knop en overlap-validatie

Uitvoering van de fase 4-instructie uit deze Cowork-sessie. Commit `989b6d3`,
173 tests groen (was 149, +24).

- `MatchmotorStatus`: singleton (zelfde patroon als `Instelling`) die
  bijhoudt wanneer de matching voor het laatst gestart/afgerond is, of dat
  gelukt is, hoeveel monteur-dagen herberekend zijn, en een eventuele
  foutmelding. `run_matching_and_record_status()` wikkelt de bestaande
  `run_matching()` in en wordt zowel door het command-line commando als door
  de nieuwe knop aangeroepen, zodat de status altijd klopt ongeacht wie 'm
  triggerde. Een `--dry-run` telt bewust niet mee als een "run" — die
  schrijft niets weg.
- "Matching nu draaien"-knop in het beheerscherm (`MatchmotorStatusAdmin`):
  POST-only, synchroon, herberekent alles (`force=True`, geen filters — voor
  een gerichte herberekening blijft de command line met
  `--monteur`/`--van`/`--tot` beschikbaar). Eind-tot-eind getest tegen de
  ontwikkel-database: 10 monteur-dagen herberekend (146 Tijdblok-rijen) in
  ~165 ms — de empirische onderbouwing om dit synchroon te laten (geen
  achtergrondtaken-systeem, onnodig op deze schaal).
- `MeegeredenKoppeling.clean()` wijst nu twee koppelingen voor dezelfde
  junior af als hun periodes elkaar overlappen (inclusief grenzen — dezelfde
  dag telt al als overlap; een open einddatum telt als onbepaald lang),
  consistent met hoe `geldt_op()` een koppeling al toepaste.

Eén bewuste afwijking van de instructie: de instructie zei "geen ander
gedrag" bij het ombouwen van het command-line commando naar de nieuwe
wrapper-functie — letterlijk genomen zou dat een `--dry-run` ook als
afgeronde run laten registreren, terwijl die niets wegschrijft. De guard
staat daarom in de wrapper zelf, met een test erbij. Goede, verdedigbare
inschatting.

Eén openstaand punt: `MatchmotorStatus` staat nu, anders dan `Tijdblok`, nog
niet expliciet read-only in de admin (alleen toevoegen/verwijderen staat
uit) — een gebruiker met wijzigrechten zou de statusrij handmatig kunnen
aanpassen. Onschadelijk (elke run overschrijft de rij toch), maar
inconsistent met het bestaande read-only-patroon voor systeem-berekende
tabellen (`Tijdblok`, de import-tabellen). Besloten: dit gelijktrekken —
zie het besluit hieronder. Aparte kleine instructie naar Claude Code volgt.

## 2026-09-03 — MatchmotorStatus read-only gemaakt

Uitvoering van het besluit hierboven ("MatchmotorStatus wordt read-only in de
admin"). Commit `c1ca836`, 176 tests groen (was 173, +4: twee tests die
bevestigen dat de rij niet met de hand te wijzigen is via het formulier, één
die expliciet vastlegt dat de knop desondanks blijft werken, één die een
staff-gebruiker zonder de onderliggende Django-permissie blokkeert).

`has_change_permission()` staat nu op `False`, net als bij `Tijdblok`. Omdat
de "Matching nu draaien"-knop zichzelf eerder via diezelfde methode
afschermde, checkt de knop nu rechtstreeks de onderliggende Django-permissie
(`matching.change_matchmotorstatus`) — de rij wordt namelijk bijgewerkt via
`save()`, niet via het admin-formulier, dus de knop blijft werken terwijl het
formulier uitstaat.

Roadmap-fase 4 is hiermee volledig afgerond.

## 2026-09-03 — Fase 5 gebouwd: het uitzonderingenscherm

Eerste scherm buiten de Django-admin, op `/uitzonderingen/`. Groepeert alle
onverklaarde (SOORT O) stops per uniek adres, meest voorkomend eerst, met de
betrokken monteurs/datums. "Koppelen" opent een formulier op basis van het
bestaande `BekendeLocatie`-model, waarna de matching direct opnieuw draait.
Geen "Negeren"-actie, geen "is depot"-optie (dat blijft admin-beheer).

`Tijdblok` kreeg twee nieuwe velden (`postcode`, `straat`) zodat het scherm
niet uit de weergavetekst hoeft te herleiden — bestaande dagen moesten
eenmalig opnieuw doorgerekend worden (`run_matching --force`), zelfde
operationele stap als bij de Werkbonnen.xlsx-uitbreiding eerder deze week.

Visuele stijl komt uit `docs/ui-spec.md` (SBTT's eigen kleuren van
stroesteam.nl), in een gedeelde basispagina die fase 6 (weekoverzicht)
hergebruikt. Bereikbaar via een link op het matchmotor-statusscherm.

Commit `b6cf401`, 195 tests groen (was 176). Eén technische aanpassing buiten
de oorspronkelijke instructie: `rmw/settings.py` valt tijdens `manage.py test`
terug op gewone static-file-opslag, omdat de normale opslag een
`collectstatic`-stap vereist die de testrunner nooit uitvoert — dit raakt
alleen het testen, niet hoe de app in productie draait.

Foutherstel (een verkeerde koppeling terugdraaien via "Bekende locaties" in
de admin, gevolgd door opnieuw matchen) is vastgelegd als verplicht onderdeel
van de opleverinstructie aan Wim — zie `docs/decisions.md`, 03-09-2026.

## 2026-09-05 — Snelheidscontrole-meerwerk vastgelegd als aparte fase

Het snelheidscontrole-meerwerk (RouteVision-snelheid vs. maximumsnelheid per locatie)
is geen openstaande ja/nee-vraag meer binnen deze roadmap, maar een aparte, later
apart te offreren fase — niet iets om nu op te pakken. Verwerkt in
`docs/functioneel-ontwerp.md` §8 (bullet herformuleerd) en §9 (uit de
openstaande-beslissingen-lijst gehaald, toegevoegd aan de opgelost-regel),
`docs/roadmap.md` ("Expliciet buiten deze roadmap"), `GUIDELINES.md` ("Important
warnings" herschreven, nieuw afgerond punt onder "Current priorities"),
`docs/business-rules.md`, `docs/demo.md`, `project-context.md` en `docs/decisions.md`
(nieuw besluit; het oude besluit "Meerwerk snelheidscontrole" is als Superseded
gemarkeerd). Puur documentatie, geen codewijziging.

## 2026-09-05 — Roadmap-fase 6 gebouwd: weekoverzicht (web + Excel)

Het weekoverzicht per monteur per week, in de lay-out die SBTT zelf had ontworpen.
`/weekoverzicht/` toont een legenda, het weektotaal per SOORT en per dag een
inklapbare tabel (aankomst, vertrek, duur, SOORT, omschrijving, adres) met
dagtotalen eronder. Monteur en week worden bovenaan gekozen (dropdown +
weekkiezer) en staan in de URL (`?monteur=<id>&week=<jaar>-W<nr>`), met
vorige/volgende week-links. `/weekoverzicht/excel/` levert dezelfde week als
.xlsx met dezelfde SOORT-celkleuren.

Twee bewuste afwijkingen van het HTML-prototype uit de validatie: de WB-kolom en
het ⚑-signaal zijn weggelaten (dat is het WB-vs-SYS-signaal dat bewust niet
gebouwd is, zie `docs/functioneel-ontwerp.md` §3b), en de "gefactureerd vs. op
locatie"-vergelijking is juist overgenomen — per dag én als weektotaal, als som
van `Uren.Aantal` tegenover de opgetelde duur van de SOORT=W-tijdblokken.

Verder: een SOORT O-blok linkt rechtstreeks naar het koppelformulier van fase 5
(via een gedeelde `Tijdblok.koppelsleutel`, zodat scherm en lijst altijd hetzelfde
adres aanspreken), en een onvolledige week meldt expliciet welke werkdagen
ontbreken inclusief de uren die er wél op geboekt zijn — die uren blijven buiten
het weektotaal.

Geen nieuwe tabellen, velden of migraties: alles wordt berekend uit de al
opgeslagen `Tijdblok`- en `Uren`-rijen. Nieuwe bestanden:
`matching/weekoverzicht.py` (de week samenstellen),
`matching/weekoverzicht_excel.py` (de export) en
`matching/templates/matching/weekoverzicht.html`. De gedeelde basispagina kreeg een
navigatie (Weekoverzicht · Uitzonderingen · Beheer) en een `stijl`-block; de
SOORT-kleuren staan vastgelegd in `docs/ui-spec.md`. 240 tests groen (was 195).

Bij het nalopen op de voorbeelddata bleek één weekvergelijking op het eerste
gezicht alarmerend (106 uur geboekt tegenover 0 uur op locatie). Dat is geen
rekenfout maar echte data: die uren zijn geboekt op het eigen bedrijfsadres (waar
een stop per definitie L is, nooit W) en één persoon boekt daar de uren van een
heel team op zijn naam. Beide verklaringen staan nu op het scherm zelf en in
`docs/business-rules.md`.

## 2026-09-06 — Landingspagina: het weekoverzicht in plaats van de admin

Twee routing-aanpassingen, geen nieuwe modellen of migraties. De root-URL (`/`)
stuurt niet langer door naar `/admin/login/` maar naar `/weekoverzicht/` — het
scherm waar SBTT-personeel de hele dag in werkt, terwijl de beheerschermen
incidenteel zijn. Wie niet is ingelogd loopt daardoor via `/weekoverzicht/` naar
`/admin/login/?next=/weekoverzicht/` en komt ná het inloggen op het weekoverzicht
terug in plaats van in de admin-index; `LOGIN_URL` en `LOGIN_REDIRECT_URL` staan
nu in `rmw/settings.py`, zodat `matching/views.py` met een kale `@login_required`
toekan. De "Beheer"-link in de navigatiebalk wijst onveranderd naar `/admin/`.

De gevraagde derde wijziging — `/weekoverzicht/` zonder parameters op de *huidige*
week openen — is na overleg niet doorgevoerd: het scherm toonde al geen leeg
scherm (eerste actieve monteur alfabetisch + diens meest recent verwerkte week),
en op de huidige week openen zou juist wél een lege pagina geven op een
maandagochtend of na een vakantie. Dat bestaande gedrag is in plaats daarvan
expliciet vastgelegd — in `matching/views.py` (`_weekkeuze` sorteert nu zelf op
naam in plaats van op `Monteur.Meta.ordering` te leunen), in
`docs/functioneel-ontwerp.md` §6 en met drie tests.

Verder bijgewerkt: `docs/architecture.md` (nieuwe alinea "Routing/toegang", er
stond nog niets over URL-configuratie) en `DRAAIBOEK.md` §6, waar de
verificatiestap na deployment nu het kale LAN-adres volgt in plaats van
`/admin/login/`. 250 tests groen (was 240): een nieuw bestand
`matching/tests/test_routing.py` (8 tests) en twee extra tests op de
standaardweergave in `matching/tests/test_weekoverzicht.py`.

## 2026-09-06 — Uitloggen en navigatie: sessieblok in de balk, admin-kop verduidelijkt

De gedeelde kopbalk (`basis.html`) heeft rechts een sessieblok gekregen: de naam van
de ingelogde gebruiker en een "Uitloggen"-knop, zichtbaar op `/weekoverzicht/` en
`/uitzonderingen/`. Uitloggen gaat via een eigen route `/uitloggen/` (Django's
`LogoutView`, POST-only) en eindigt op `/admin/login/?next=/weekoverzicht/`, dus op
het inlogscherm met de terugweg al ingevuld (`LOGOUT_REDIRECT_URL`).

**Bevinding over de admin: er was niets kapot.** Er bestond geen `base_site.html`,
geen eigen admin-CSS en geen aangepaste `site_url`; Django's eigen kopbalk toonde
zowel de uitlog- als de "bekijk site"-link gewoon. Wat ontbrak was herkenbaarheid:
met `LANGUAGE_CODE = "nl-nl"` rendert Django zijn Nederlandse vertalingen, dus
uitloggen heette daar "Afmelden" en de weg terug "Website bekijken" — een derde en
vierde woord voor wat de rest van RMW "Uitloggen" en "Weekoverzicht" noemt, verstopt
in het kleine grijze rijtje tekstlinks rechtsboven.

Daarom is er verduidelijkt in plaats van hersteld: `templates/admin/base_site.html`
overschrijft alleen het `userlinks`-block met dezelfde links onder de bewoording van
de rest van de applicatie ("Naar het weekoverzicht", "Uitloggen"), die twee krijgen
een dun kadertje zodat ze opvallen, en `admin.site.site_url` wijst nu rechtstreeks
naar `/weekoverzicht/` in plaats van naar `/` (dat kwam er ook uit, maar via een
redirect). Het bestand staat in de project-`templates/`-map en niet in
`matching/templates/`, omdat `django.contrib.admin` in `INSTALLED_APPS` vóór
`matching` staat en een app-kopie het dus zou verliezen — daar zit een expliciete
test op.

Geen nieuwe modellen of migraties. 264 tests groen (was 250): nieuw bestand
`matching/tests/test_navigatie.py` (14 tests). Documentatie: `docs/ui-spec.md`
(nieuw hoofdstuk "Sessieblok en uitloggen — Gebouwd", plus de reikwijdte-paragraaf
van vooruitkijkend naar afgerond).

_Correctie (zelfde dag, zie de volgende regel): bij deze wijziging is genoteerd dat
de uitlogknop in de admin op Django's eigen afmeldpagina bleef eindigen. Dat was
onjuist._

## 2026-09-06 — Uitloggen gelijkgetrokken (en een correctie op de vorige regel)

De uitlogknop in de Django-admin post nu naar `/uitloggen/` in plaats van naar
`admin:logout`, zodat de applicatie één uitlogroute heeft in plaats van twee.

**Correctie op de vorige changelog-regel.** Daar stond dat de admin-uitlogknop op
Django's afmeldpagina eindigde en `/uitloggen/` op het inlogscherm — een "bewust
verschil". Dat klopte niet. `AdminSite.logout` is een `LogoutView` zonder
`next_page` en valt dus terug op `settings.LOGOUT_REDIRECT_URL`; Django's
afmeldpagina verschijnt alleen als niets die bestemming zet. Beide knoppen kwamen
daardoor al op `/admin/login/?next=/weekoverzicht/` uit vanaf het moment dat
`LOGOUT_REDIRECT_URL` werd toegevoegd. Nagemeten: `POST /admin/logout/` en `POST
/uitloggen/` gaven allebei `302 → /admin/login/?next=/weekoverzicht/`.

Er viel dus geen gedrag recht te trekken, maar de wijziging is wel doorgevoerd, om
een andere reden: de gelijkheid hing op een terugvalregel binnen Django. Verdween
`LOGOUT_REDIRECT_URL` ooit, dan kwam de afmeldpagina stilletjes terug — alleen voor
wie vanuit de admin uitlogt. Via de eigen route is het expliciet. `admin:logout`
bestaat nog, maar geen scherm linkt er nog naar.

270 tests groen (was 264): `SymmetrischUitloggenTests` legt niet alleen de
bestemming vast maar ook de route, juist omdat de bestemming ook zonder die route
zou kloppen — de test drukt de knop die elke kopbalk daadwerkelijk rendert, in
plaats van naar een vast adres te posten. Gecontroleerd dat de nieuwe tests falen
als de knop wordt teruggezet op `admin:logout`. `docs/ui-spec.md` is op hetzelfde
punt gecorrigeerd.


## 2026-09-06 — Lokale inbox-map als bind-mount in docker-compose

`docker-compose.yml` mount `./data/inbox` nu op `/app/data/inbox`, op zowel `web`
als `scheduler`, naast de bestaande named volume `rmw-data` voor de database (die
blijft ongewijzigd).

Aanleiding: `docker compose exec web python manage.py check_imports --path
/app/data/inbox --dry-run` meldde "no recognised source files found", terwijl de
vier bronbestanden (Syntess Relaties/Uren/Werkbonnen + de RouteVision-CSV) in
`data/inbox` op de host klaarstonden. Oorzaak was geen fout in de detectie:
`/app/data` was alleen de named volume, waarin enkel `db.sqlite3` staat. De map
`/app/data/inbox` — waar `SERVERMAP_PATH` naar wijst — bestond in de container
dus helemaal niet. Nagemeten met een tijdelijke read-only bind-mount: dan werden
alle vier bestanden wél herkend.

Na de wijziging herkent zowel de handmatige aanroep als de achtergrondpoller van
`scheduler` de vier bestanden, alle vier met status `waiting` — correct, want de
stabiliteitsmarge is 6 opeenvolgende ongewijzigde metingen (30 min bij een poll
van 5 min). Voor een directe import zonder wachttijd is `--force` de aangewezen
vlag. `--dry-run` schrijft zelf niets weg: in de wachtende tak van
`_handle_file` wordt `record.save()` overgeslagen.

Puur een voorziening voor lokaal testen. Hoe de productie-servermap
`\\stroes-1909\atrium\Autoprint\RUUDS` op ditzelfde containerpad terechtkomt,
blijft een open punt voor fase 7 (`DRAAIBOEK.md`). `docs/architecture.md` is
bijgewerkt.

Bij dezelfde gelegenheid gecorrigeerd: de kop "Trigger-mechanisme
(bestandsdetectie servermap) — ontworpen, nog niet gebouwd" in
`docs/architecture.md` was achterhaald en suggereerde dat het mechanisme nog moest
komen. Het is gebouwd — `matching/ingest/detection.py`, het commando
`check_imports` en `scripts/scheduler.sh` — dus de kop is nu "gebouwd", met een
verwijzing naar die drie plekken in de inleidende regel eronder. De ontwerpkeuzes
in de sectie zelf (polling, interval, stabiliteitsmarge) zijn ongewijzigd.

## 2026-09-07 — Schone herimport + herberekening, en twee bugs uit de eerste echte-data-test

Na de eerste test op echte SBTT-data (06-09-2026) is de augustus-testdataset
volledig opnieuw ingelezen en doorgerekend, om twee losse eindjes te controleren:
monteur Dennis van de Berg (medewerkernr 002) stond op inactief en werd daardoor
overgeslagen door `run_matching` (Roger heeft hem inmiddels weer actief gezet), en
de ImportedFile-lijst toonde dubbele regels. Alles is via Docker gedaan
(`docker compose exec web python manage.py ...`), conform het besluit van
07-09-2026.

**Bug 1 — Excel-lockbestanden werden als bronbestand herkend (echt, opgelost).**
De dubbele regels in ImportedFile bleken Excel's eigen tijdelijke lockbestanden:
zodra je een bronbestand opent, zet Office er een verborgen kopie naast met een
`~$`-prefix ("~$20260826 Download uit Syntess Uren  26 8 2026.xlsx", 165 bytes).
Dat bestand eindigt op `.xlsx` en bevat het trefwoord "Uren", dus de bewust losse
herkenning in `matching/ingest/filenames.py` pakte het op als een tweede
Uren-export. `classify_filename()` weigert nu elke bestandsnaam die met `~$`
begint (`LOCK_FILE_PREFIX`). Er stond al een test op `~$Uren.xlsx.tmp`, maar die
slaagde alleen op de `.tmp`-extensie — precies de vorm die Office níet gebruikt.

**Bug 2 — de read-only admin-tabellen lieten verwijderen wél toe (echt, opgelost).**
Het besluit van 03-09-2026 legde vast dat `Uren`, `Rit`, `Relatie`,
`WerkbonControle` en `Tijdblok` alleen-lezen zijn in de admin, maar in
`matching/admin.py` waren alleen `has_add_permission` en `has_change_permission`
op False gezet. `has_delete_permission` ontbrak, dus "verwijder geselecteerde
items" stond gewoon in de acties-dropdown. Toegevoegd aan `ReadOnlyImportAdmin`
en `TijdblokAdmin`; Django filtert de acties op dit recht, dus de actie is nu
helemaal niet meer zichtbaar.

De Bad Request die Roger zag was een bijverschijnsel, geen bescherming: de
bevestigingspagina van `delete_selected` rendert één verborgen veld per
geselecteerde rij, en 1190 urenregels overschrijdt `DATA_UPLOAD_MAX_NUMBER_FIELDS`
(1000) — `TooManyFieldsSent` geeft bij `DEBUG=0` een kale 400. Nagemeten: mét
1190 velden een 400, met 50 velden een 200. Dat betekent dat de verwijdering op
een kleinere selectie wél was doorgegaan; de foutmelding verborg een werkend
verwijderpad. Sinds de fix blijven ook die 50 rijen staan.

**De reset zelf.** Verwijderd via de ORM in de container: alle rijen in `Uren`,
`Rit`, `Relatie`, `WerkbonControle`, `Tijdblok` en `ImportedFile`. Ongemoeid
gelaten: `Monteur` (inclusief de door Roger handmatig gecorrigeerde `actief` en
`bestuurder_code`), `BekendeLocatie`, `Instelling`, `MeegeredenKoppeling`,
`ToleranceRegel` en `MatchmotorStatus` — voor en na geteld om dat te bevestigen.
Daarna `check_imports --force` (2546 relaties, 1190 urenregels, 2471 werkbonnen,
528 ritten) en `run_matching --force` (62 dagen, 853 tijdblokken, status succes).

Resultaat: vier ImportedFile-rijen, geen dubbelen, geen `~$`-regels. Dennis heeft
nu 152 tijdblokken uit 133 urenregels en staat in het weekoverzicht; week 32 toont
"Gefactureerd 42,50 uur", wat exact overeenkomt met de som uit Uren.xlsx voor
medewerkernr 002 in die week.

Bij deze controle opgevallen, buiten de scope van deze fixes: de RouteVision-
export bevat voor Dennis alleen ritten van 03-08 t/m 24-08, met een gat in week 33
(ma t/m vr, terwijl er wel 8 uur per dag geboekt is). Ook Maarten Jaarsma stopt op
15-08. Het weekoverzicht meldt dit netjes als "onvolledige week", maar het is een
dekkingsvraag over de RouteVision-export zelf om met Roger na te lopen.

## 2026-09-07 — Beheeractie "Data resetten" gebouwd

Het besluit van vandaag (`docs/decisions.md`, `docs/functioneel-ontwerp.md` §4) is
gebouwd: een eigen admin-scherm met twee modi, los van de generieke Django
bulk-delete-acties — die op de importtabellen bewust dicht blijven staan
(`has_delete_permission=False`) en er sowieso niet geschikt voor waren.

Te bereiken via een link op het matchmotor-scherm, naast "Matching nu draaien";
de twee horen bij elkaar als resetten en daarna bewust opnieuw inlezen.

**Volledig leegmaken** verwijdert Tijdblok, Uren, Rit, Relatie, WerkbonControle en
ImportedFile. **Periode verwijderen** filtert Tijdblok, Uren, Rit en
WerkbonControle op een van-tot bereik (inclusief aan beide kanten), elk op zijn
eigen datumveld — `vertrekdatum` voor Rit, want dat is de dag waarop de matching
een rit ook indeelt. Relatie en ImportedFile blijven bewust buiten de
periode-modus, zodat een periode-reset nooit stilzwijgend de verwerkt-status van
een bronbestand wist; opnieuw inlezen blijft `check_imports --reprocess`.

De koppeltabellen (Monteur, BekendeLocatie, Instelling, MeegeredenKoppeling,
ToleranceRegel, MatchmotorStatus) worden door geen van beide modi geraakt.

Vormgegeven als drie stappen op één endpoint: het formulier (GET), een preview met
het aantal rijen per tabel (POST), en pas daarna de reset zelf (POST mét het
bevestigingsveld, dat alleen op de previewpagina staat). Een eerste POST kán
daardoor niets verwijderen — die kan alleen de vraag stellen. Alleen voor
superusers, gecontroleerd op `request.user.is_superuser` in plaats van op een
modelrecht: dit is een technisch herstelmiddel, geen SBTT-personeelsfunctie, en
het hoort ook niet bij één model waarvan het recht het zou kunnen dragen. De
verwijderingen van een modus draaien in één `transaction.atomic()`.

De logica staat in `matching/reset.py`, apart van de admin — dezelfde opzet als
`matching/timeline/runner.py` bij "Matching nu draaien", zodat het gedrag los van
het scherm te testen is. Tellen en verwijderen draaien op dezelfde querysets, zodat
de preview die iemand bevestigt niet kan afwijken van wat er daarna weggaat. Na
afloop wordt er niets opnieuw ingelezen of herberekend — bewust, net als bij de
bestandsdetectie, die ook nooit uit zichzelf herverwerkt.

24 tests toegevoegd (`matching/tests/test_data_resetten.py`), samen 300 groen: beide
modi, de inclusieve bereikgrenzen, dat een preview niets verwijdert, dat de
koppeltabellen na afloop ongewijzigd zijn, en de superuser-grens — met een
beheerdersaccount dat wél elk modelrecht in de app heeft, zodat de test aantoont
dat rechten niet zijn wat dit scherm opent.

Nagelopen op de echte augustus-data in Docker: het formulier toont de juiste
aantallen (1190 urenregels, 853 tijdblokken, 4 importbestanden), een preview van
week 33 telt 407 rijen zonder er één te verwijderen, en de bevestigde reset van een
lege periode doorloopt de hele keten zonder iets te raken. De augustus-dataset is
bij het testen intact gebleven.

## 2026-09-07 — Bugfix: begin en einde van de dag verdwenen uit de tijdlijn

Gemeld symptoom, gereproduceerd op echte data en consistent over meerdere
monteurs: alleen het middenstuk van een dag kwam in `Tijdblok` terecht. De
ochtendrit naar het depot plus het verblijf daar, en aan het eind het verblijf op
het depot plus de rit naar huis, ontbraken structureel — ongeacht of het om een
rit van drie minuten of een verblijf van bijna vijf uur ging. De `Rit`-tabel zelf
was compleet; de import was dus niet de oorzaak.

**Werkelijke oorzaak: het depot belandde tussen de "thuisstraten".**
`home_streets_for()` leidt het thuisadres af uit de eerste vertrek- en de laatste
aankomstplaats van elke dag die een monteur reed. Die verzameling werd echter
zonder enige frequentietoets samengevoegd — terwijl de docstring van de functie
al wél "de straat die steeds terugkomt" beloofde. Een monteur die zijn bus bij
het magazijn ophaalt, begint of eindigt daar een aantal dagen, en daarmee stond
`randweg` permanent tussen zijn thuisstraten. `_trim_home_hops()` gooit een rit
weg zodra vertrek én aankomst allebei op een thuisstraat liggen — bedoeld voor
"even de bus verzetten voor de deur" — en dat gold vanaf dat moment ook voor élke
rit van huis naar depot, van depot naar depot en van depot naar huis, op alle
dagen.

Bij Dennis van de Berg (002) waren dat 4 van de 50 dagranden op `randweg`, genoeg
om op 02-06-2026 vier van de zes ritten te laten verdwijnen: precies de gemelde
ritten 2, 11, 30 en 33. Zijn feitelijke thuisstraat (`beesdseweg`) was goed voor
38 van die 50 dagranden.

**Fix.** Het depot wordt uitgesloten bij het afleiden van het thuisadres — het is
geconfigureerd (`is_depot`), en het is per definitie niemands huis. Er wordt op
zowel straat als postcode gecontroleerd, omdat een depot op beide manieren
ingericht kan zijn. Bewust géén frequentiedrempel geïntroduceerd: dat zou een
nieuwe business rule zijn (zie het openstaande punt hieronder).

In dezelfde functie meegenomen: een "straat" zonder één letter erin telt niet
meer als thuisstraat. RouteVision schrijft `-` voor een stop die het niet heeft
kunnen bepalen, en die placeholder werd zo een thuisstraat op zichzelf, waarna
elke rit tussen twee onbepaalde adressen wegviel. Dit raakte Jesse Verkerk (005),
die daardoor 5 ritten miste; die dagen zijn nu compleet.

**Verificatie op de echte juni-dataset (Docker).** De tijdlijn van Dennis van de
Berg op 02-06-2026 toont nu alle 6 ritten, met het ochtendverblijf op het depot
(06:52–12:01) en het avondverblijf (17:32–22:15) als L-blokken. Over de hele
dataset ging het aantal tijdblokken van 1169 naar 1356, en van de 782 ritten
komen er nu 754 in de tijdlijn terug tegen 715 daarvoor.

Regressietests toegevoegd in `matching/tests/test_timeline.py`
(`DepotAanDeDagrandenTests`), die de exacte rittenreeks van 02-06-2026 nabouwen —
inclusief de tweede dag die het depot in de thuisstraten bracht, want die
vervuiling loopt over dagen heen: de dag zelf begint en eindigt gewoon thuis en
zou het probleem alleen nooit hebben laten zien. 308 tests groen.

**Openstaand punt (besluit van Roger nodig).** Het onderliggende patroon is
breder dan het depot: `home_streets_for()` neemt nog steeds élke dagrand mee,
hoe zelden ook. Daardoor gelden bij Dennis ook `rolweg` (6 van 50 dagranden) en
`forêtweg` (2 van 50) als thuis, en bij Maarten Jaarsma `marsweg` (8 van 46).
Over de juni-dataset vallen zo nog 28 ritten over 12 dagen weg, waarvan een deel
terecht (echte ritjes binnen de eigen straat) en een deel niet. Het scherpste
geval: Dennis 24-06 en 25-06 leveren nul tijdblokken op terwijl hij beide dagen
8 uur boekte — alle ritten van die dagen lopen tussen Rolweg-adressen. Een
frequentiedrempel zou dit oplossen, maar wélke drempel is een business rule die
niet is vastgelegd; bij Jesse Verkerk zou een strenge drempel bijvoorbeeld
`burgemeester deysstraat` (11 van 34 dagranden) laten vervallen, en of dat een
tweede thuisadres is weet alleen SBTT. Apart te besluiten.

## 2026-09-07 — Label "Gefactureerd" wordt "Totaal (excl. reistijd)"

Uitvoering van het besluit van vandaag (`docs/decisions.md`, 07-09-2026 avond,
`docs/functioneel-ontwerp.md` §6). In de dag- en weektotalen van het
weekoverzicht heet de linkerkant van de vergelijking nu "Totaal (excl.
reistijd)", zowel op de webpagina als in de Excel-export. Op de dagregel stond
"Gefact. → locatie"; dat is "Totaal (excl. reistijd) → locatie" geworden.

Alleen tekst: de berekening blijft de som van `Uren.Aantal` afgezet tegen de
opgetelde duur van de SOORT=W-tijdblokken (besluit 05-09-2026). Niet elk geboekt
uur wordt daadwerkelijk aan een klant gefactureerd — magazijn- en depottijd wordt
wel geboekt maar niet doorbelast — waardoor "Gefactureerd" meer beweerde dan het
getal betekende.

Het veld `gefactureerde_uren` in `matching/weekoverzicht.py` houdt zijn naam: de
waarde verandert niet, en hernoemen zou de Excel-export en elke test raken voor
wat een labelwijziging is. Bij het veld staat nu een comment dat het scherm een
andere naam gebruikt, zodat de twee niet stilletjes uit elkaar lopen. Een test
controleert dat pagina en export hetzelfde label voeren. 309 tests groen.

## 2026-09-07 — Nieuwe SOORT-classificatie P (Privé)

Uitvoering van het besluit van vandaag (`docs/decisions.md` 07-09-2026 avond,
`docs/functioneel-ontwerp.md` §5/§6). Naast K, L en C kan een adres nu als
**P (Privé)** worden gekoppeld. Zonder die keuze bleef een stop die duidelijk
privé was als O (onverklaard) in het uitzonderingenscherm staan, zonder manier om
hem af te handelen.

**Mechanisme, ongewijzigd ten opzichte van K/L/C.** P is een vierde keuze op
`BekendeLocatie.soort` en wordt toegekend via hetzelfde koppelformulier
(`/uitzonderingen/koppelen/<precisie>/<waarde>/`) — geen nieuw scherm. In
`_classify_stop()` was geen enkele wijziging nodig: die stap leest `locatie.soort`
al rechtstreeks, dus P valt vanzelf op dezelfde plaats in de prioriteitsvolgorde
als K/L/C. Ook de tolerantielogica is ongemoeid: alleen stops die al als O
verschijnen zijn koppelbaar. En net als bij K/L/C geldt een classificatie voor
elke monteur die daar stopt, niet per monteur.

**Totalen.** Privé-tijd komt uit de tijdblokken, niet uit `Uren.xlsx`, en raakt
"Totaal (excl. reistijd)" dus per definitie niet. Nieuw is dat ze een eigen,
zichtbaar getal krijgt: `prive_uren` per dag en per week, op de pagina onder de
vergelijking en in de Excel-export als de regel "Privé (SOORT P)". Nadrukkelijk
géén aftrek op de bestaande getallen — privé-tijd is geen werk, maar ook geen
tekort. Een test legt vast dat het koppelen van een adres als P de
geboekte/op-locatie/verschil-cijfers geen millimeter beweegt. De regel verschijnt
alleen als er privé-tijd is, zodat een week zonder privé-stops er onveranderd
uitziet.

**Kleur: `#C2185B`.** De keuze was aan Claude Code gelaten. Van de kleurencirkel
waren teal, blauw, violet, groen, amber en twee grijstinten bezet; de rode helft
was vrij. Bewust karmijn en geen echt rood: rood naast de amberkleurige O zou
lezen als "erger dan onverklaard", terwijl een P-stop juist het tegenovergestelde
is — een stop die verklaard is. Donker genoeg voor de witte codeletter (circa
6:1 contrast met wit) en ver genoeg van het violet van C om in een dichte tabel
uit elkaar te blijven.

**Migratie `0007_alter_bekendelocatie_soort_alter_tijdblok_soort`: een no-op.**
Zoals verwacht bij het toevoegen van een keuze aan een bestaand `CharField`
(`max_length=1`, en "P" is één teken). Nagemeten met `sqlmigrate`: beide
`AlterField`-operaties leveren letterlijk `-- (no-op)` op, dus er verandert niets
aan het schema en de bestaande gegevens worden niet aangeraakt.

320 tests groen.

## 2026-09-07 — Thuisadres wordt ingevuld in plaats van geraden; nieuwe SOORT T (Thuis)

Vervolg op `4d219c2`. Die commit haalde het depot uit de afgeleide thuisstraten,
maar liet de detectie zelf staan — en die kende geen frequentietoets: élke
dagrand telde mee als kandidaat-thuisstraat. Bij Dennis van de Berg golden zo ook
`rolweg` (6 van 50 dagranden) en `forêtweg` (2 van 50) als thuis, bij Maarten
Jaarsma `marsweg` (8 van 46). `_trim_home_hops()` gooide vervolgens elke rit weg
waarvan vertrek én aankomst op zo'n straat lagen: nog altijd 28 ritten over 12
dagen, waarvan tweemaal een hele werkdag (Dennis, 24 en 25 juni — nul tijdblokken
bij 8 geboekte uren).

Besluit van Roger: geen drempel raden, maar het adres opvragen. Zonder SBTT's
eigen kennis van elke monteur is een toevallige dagrand niet te onderscheiden van
een echt tweede vast adres, en elke misser was onzichtbaar.

**`Monteur.thuisadres` + `thuisadres_type`.** Dezelfde precisiekeuze als
`BekendeLocatie` (straatnaam of postcode, straat als voorkeur) en dezelfde
normalisatie uit `matching/timeline/normalize.py`, zodat één adres overal
hetzelfde betekent. Beide velden optioneel. Een ingevulde waarde die niet
normaliseert (bijvoorbeeld "geen postcode" onder precisie postcode) wordt
geweigerd in plaats van stilzwijgend leeggemaakt — een veld dat ingevuld lijkt en
niets matcht is erger dan een leeg veld. Te beheren in het bestaande
Monteur-scherm, dat nu ook op de precisiekeuze filtert.

**Nieuwe SOORT T (Thuis), met twee bronnen.** Primair het `thuisadres`-veld: die
stap staat op precies dezelfde plek in de prioriteitsvolgorde als de oude
thuisstraat-stap (net vóór de tolerantiecheck), maar slaat het blok nu op in
plaats van het te laten vallen. Secundair is T ook een vijfde keuze op
`BekendeLocatie.soort`, koppelbaar via hetzelfde uitzonderingenscherm als K/L/C/P
— voor het geval dat de bus om de hoek staat en dat adres dus nooit gelijk is aan
het opgegeven huisadres. Omdat de koppeltabel-stap boven de thuisadres-stap
staat, wint een handmatige koppeling van het veld.

**Detectie volledig vervallen, zonder terugval.** `home_streets_for()`,
`_home_edge()` en `_trim_home_hops()` zijn verwijderd, net als de
`home_streets`-parameter van `build_day()` en `_classify_stop()` en de cache in
de runner. Er wordt dus niets meer weggefilterd vóór een dag wordt opgebouwd:
elke rit is per constructie een blok. Een monteur zonder ingevuld thuisadres
krijgt zijn ochtend- en avondstops gewoon te zien, meestal als O — zichtbaar en
corrigeerbaar, in plaats van onzichtbaar fout.

Op een meegereden dag wordt het thuisadres van de monteur zelf gebruikt, niet dat
van de bestuurder wiens ritten de dag opbouwen: het huis van die senior is niet
het thuis van deze monteur. Het verschijnt dan als gewone onverklaarde stop, en
is desgewenst als T te koppelen.

**Geen eigen dag- of weektotaal voor T**, anders dan bij P: T-blokken staan in de
dagtabel en tellen mee in het SOORT-totaal, verder niets. Thuis-tijd is minder
een getal dat je wil optellen dan privé-tijd.

**Kleur `#6D4C41`.** Met negen codes is de kleurencirkel vrijwel vol; wat
ongebruikt was, is de gedempte warm-donkere hoek, dus T is een bruin. Het leest
als rustig in plaats van als signaal — wat een stop thuis ook is — en de lage
verzadiging en donkerte houden het uit elkaar met de enige buur in dezelfde
kleurfamilie, het felle amber van O.

**Migratie `0008`.** Twee echte kolommen (`thuisadres`, `thuisadres_type`) en
twee choices-only wijzigingen. Nagemeten met `sqlmigrate`: de `AddField`-operaties
zijn echte schemawijzigingen (SQLite bouwt de tabel opnieuw op) en vullen
bestaande rijen met de opgegeven defaults — `''` voor het adres en `'straat'`
voor de precisie, dus geen datamigratie nodig en geen vragen bij
`makemigrations`. De beide `AlterField`-operaties op `soort` leveren opnieuw
letterlijk `-- (no-op)`, hetzelfde patroon als migratie 0007.

**Tests.** De regressietests uit `4d219c2` (`DepotAanDeDagrandenTests`) toetsten
het mechanisme dat hier verdwijnt; ze zijn herschreven tot `DagrandenTests`, die
dezelfde echte dag van 02-06-2026 nabouwt maar nu bewaakt dat elke rit een blok
wordt en wat de dagranden worden. `HomeStreetTests` is vervangen door
`ThuisadresTests` (normalisatie, lege waarde, geweigerde waarde, precisie).
Verder: T via het koppelformulier, T zonder eigen weektotaal, en een test dat een
monteur zónder thuisadres een gewone O krijgt in plaats van een gok. 327 groen.

**Verificatie op de echte juni-dataset (Docker).** Van 782 ritten komen er nu
**782** in de tijdlijn terecht — het verschil van 28 ritten over 12 dagen is weg.
Het totaal ging van 86 dagen/1356 tijdblokken naar 88 dagen/1408; de twee extra
dagen zijn precies Dennis' 24 en 25 juni, die eerder nul blokken opleverden en nu
9 respectievelijk 8 tellen. Met `Beesdseweg` als testthuisadres kreeg Dennis 6
T-blokken (203 min) op de juiste adressen (Beesdseweg 3a-18 t/m 3a-21); met
postcode `4104AV` als T gekoppeld werden 24 en 25 juni volledige dagen van elf
blokken. Beide testwaarden zijn daarna weer verwijderd en de matching opnieuw
gedraaid, zodat de dataset staat zoals hij stond.
