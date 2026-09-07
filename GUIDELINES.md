# GUIDELINES — Stroes-Rit-Match (RMW)

_Last updated: 2026-09-07_

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

**Fase 3 (reken-/matchmotor) is gebouwd (03-09-2026):** de gevalideerde
matchheuristiek uit de PoC omgezet naar Django — tijdlijnreconstructie per
monteur/dag, classificatie in SOORT-codes (depot → eigen Uren-regels → overige
koppeltabel → thuis → onverklaard/onbekend), en de koppeltabellen die dat nodig
heeft (`Monteur`, `BekendeLocatie`, `Instelling`, `MeegeredenKoppeling`,
`ToleranceRegel`), nu al als echte, in Django-admin bewerkbare modellen (zie
`docs/decisions.md`, 03-09-2026). 143 tests groen. Twee dingen zijn daarbij aan het
licht gekomen, geen bugs maar aandachtspunten voor de echte configuratie: een
straat-niveau depotadres claimt élk adres op die straat vóór een werkbonmatch, en
het uitsluiten van Werkbonnen.xlsx als matchbron (eerder besluit) geeft een lager
werkbon-hervindingspercentage dan de PoC. Zie `docs/decisions.md` (03-09-2026).

Beoogde PoC-architectuur: een los
Python-script dat de Syntess-exports en de RouteVision-download inleest, per
monteur/dag een tijdlijn reconstrueert, matcht tegen bekende locaties
(straatnaam-fallback wanneer postcode niet exact matcht; depot-vóór-werk-regel), en
een weekoverzicht wegschrijft. Zie `docs/architecture.md`.

## Application / module overview

- `rmw/` — Django-projectconfiguratie (settings, urls, wsgi/asgi).
- `matching/` — de applicatie: importmodellen + admin (fase 2), de koppeltabellen
  en de matchmotor in `matching/timeline/` (fase 3); de uitzonderingen- en
  weekoverzichtschermen volgen in fase 5/6.

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
5. **Gedaan (03-09-2026).** Roadmap-fase 3 (reken-/matchmotor) gebouwd, getest en
   gepusht (`eea759c`), inclusief de koppeltabellen die de motor nodig heeft. Zie
   `docs/changelog.md` en `docs/decisions.md` (03-09-2026).
6. **Gedaan (03-09-2026).** Roadmap-fase 4 (verfijning beheerschermen) volledig
   afgerond en gepusht (`989b6d3`, `c1ca836`): `MatchmotorStatus` (wanneer de
   matching voor het laatst gedraaid heeft, gelukt of niet, hoeveel dagen) —
   read-only, net als `Tijdblok` — met een "Matching nu draaien"-knop in het
   beheerscherm zodat SBTT-personeel dit zelf kan triggeren zonder
   serverdoegang, en een overlap-validatie op `MeegeredenKoppeling` (een junior
   kan niet tegelijk aan twee senioren gekoppeld zijn). 176 tests groen (was
   149). Zie `docs/changelog.md` en `docs/decisions.md` (03-09-2026).
7. **Gedaan (03-09-2026).** Roadmap-fase 5 (uitzonderingenscherm) gebouwd: het
   eerste scherm buiten de Django-admin (`/uitzonderingen/`), waar onverklaarde
   stops per adres gegroepeerd en met één klik gekoppeld kunnen worden aan een
   bekende locatie — waarna de matching direct opnieuw draait. Visuele stijl
   (navy/oranje/groen, uit SBTT's eigen site) vastgelegd in `docs/ui-spec.md`
   en herbruikbaar voor fase 6. 195 tests groen (was 176). Zie
   `docs/changelog.md` en `docs/decisions.md` (03-09-2026).
8. **Gedaan (05-09-2026).** Het snelheidscontrole-meerwerk is als openstaande
   beslissing afgerond: vastgelegd als een aparte, later apart te offreren fase,
   buiten deze roadmap. Puur een documentatiebesluit, geen codewijziging. Zie
   `docs/decisions.md` (05-09-2026), `docs/functioneel-ontwerp.md` §8/§9 en
   `docs/roadmap.md`.
9. **Gedaan (05-09-2026).** Roadmap-fase 6 (weekoverzicht) gebouwd:
   `/weekoverzicht/` toont per monteur per week de gereconstrueerde dagen in
   SBTT's eigen lay-out (legenda, weektotaal per SOORT, per dag een inklapbare
   tabel met dagtotalen), met monteur/week in de URL en een Excel-export
   (`/weekoverzicht/excel/`) met dezelfde SOORT-celkleuren. Twee bewuste
   afwijkingen van het prototype: geen WB-kolom en geen ⚑-signaal (het
   WB-vs-SYS-signaal is niet gebouwd), wél de "gefactureerd vs. op
   locatie"-vergelijking per dag én per week. Een O-blok linkt door naar het
   koppelformulier van fase 5; een onvolledige week meldt expliciet welke dagen
   ontbreken. Geen nieuwe tabellen of velden. 240 tests groen (was 195). Zie
   `docs/changelog.md` en `docs/business-rules.md`.
10. **Gedaan (06-09-2026).** Landingspagina: `/` stuurt door naar
   `/weekoverzicht/` in plaats van naar de admin, en een niet-ingelogde
   bezoeker komt na het inloggen op het weekoverzicht terug (`LOGIN_URL` en
   `LOGIN_REDIRECT_URL` staan nu in `rmw/settings.py`). De "Beheer"-link blijft
   naar `/admin/` wijzen. De standaardweergave zonder parameters (eerste
   actieve monteur alfabetisch + diens meest recent verwerkte week) is
   ongewijzigd gebleven maar nu expliciet vastgelegd — op de huidige week
   openen zou juist een leeg scherm geven. Geen nieuwe tabellen of velden. 250
   tests groen (was 240). Zie `docs/changelog.md` en
   `docs/functioneel-ontwerp.md` §6.
11. **Gedaan (06-09-2026).** Uitloggen en navigatie: de gedeelde kopbalk toont
   de ingelogde gebruiker en een "Uitloggen"-knop (eigen route `/uitloggen/`,
   POST-only, eindigt op het inlogscherm). In de Django-admin bleek niets
   onderdrukt — Django toonde beide links al, maar als "Afmelden" en "Website
   bekijken"; `templates/admin/base_site.html` herbenoemt ze naar "Uitloggen" en
   "Naar het weekoverzicht" en licht ze uit, en `admin.site.site_url` wijst nu
   rechtstreeks naar het weekoverzicht. Geen nieuwe tabellen of velden. 264
   tests groen (was 250). Zie `docs/changelog.md` en `docs/ui-spec.md`.
12. **Gedaan (06-09-2026).** Uitloggen gelijkgetrokken: de admin-uitlogknop post
   nu naar `/uitloggen/`, zodat er één uitlogroute is. Let op de correctie
   daarbij: de twee knoppen kwamen al op hetzelfde inlogscherm uit
   (`AdminSite.logout` erft `LOGOUT_REDIRECT_URL`), dus dit maakt bestaande
   gelijkheid expliciet in plaats van een verschil te repareren. 270 tests
   groen (was 264). Zie `docs/changelog.md` en `docs/ui-spec.md`.
13. **Gedaan (06-09-2026), gecommit en gepusht (`d34e6c2`).** Punt 10-12
   (landingspagina, standaardweergave, sessieblok/uitloggen, admin-kopbalk,
   symmetrische uitlogroute) vastgelegd als één commit — door Roger zelf
   getest en akkoord bevonden. `origin/main` staat op `d34e6c2`, werkboom
   schoon, 270 tests groen. Twee verouderde code-comments (over een vermeend
   verschil tussen de admin-uitlogknop en `/uitloggen/`, dat er dus niet bleek
   te zijn — zie punt 12) zijn bij het naklopen van de staged diff nog
   gecorrigeerd vóór het committen.
14. **Gedaan (06-09-2026), gecommit (`852777b`), inmiddels gepusht (`origin/main` staat op `b5f4197`).** Lokale
   inbox-map als bind-mount (`./data/inbox:/app/data/inbox`, op `web` én
   `scheduler`) toegevoegd aan `docker-compose.yml`, zodat `check_imports` lokaal
   bestanden op de host kan vinden — puur een testvoorziening, raakt de
   productie-servermapkoppeling niet (blijft open punt voor fase 7). Bijvangst:
   de stale kop "Trigger-mechanisme... — ontworpen, nog niet gebouwd" in
   `docs/architecture.md` gecorrigeerd naar "gebouwd". Zie `docs/changelog.md`
   en `docs/architecture.md`.
15. **Gedaan (06-09-2026, avond).** Eerste testrun met échte,
   niet-geanonimiseerde data (4 augustus-bestanden: Uren, Werkbonnen, Relaties,
   RouteVision-CSV) lokaal in Docker, samen met Roger doorlopen. Geen
   codewijziging (alleen database-inhoud en admin-configuratie), dus niets
   hiervan zit in git. Bevindingen:
   - De container bleek een eigen, vrijwel lege database te hebben (Docker-
     volume), los van de host-`db.sqlite3` die Roger via een kale
     `manage.py runserver` gebruikt. Dit zorgde tot twee keer toe voor
     verwarring: eerst geen account/koppeltabellen in de container, later — na
     alles in de container op orde te hebben — weer de oude testdata te zien
     zodra Roger juist de host-`runserver` startte. Voor die avond opgelost door
     de host-database eenmalig in het Docker-volume te zetten; structureel
     opgelost op 07-09-2026, zie punt 16 hieronder.
   - De koppeltabel (`Monteur.bestuurder_code`) bevatte nog de geanonimiseerde
     PoC-testcodes M1/M5 in plaats van de echte RouteVision-bestuurdersnamen.
     Roger heeft dit zelf gecorrigeerd (M1 = Rocco Stroes, zoon van Wim, bestuurder
     "Rocco Prive"; M5 = Jesse Verkerk) en de overige 3 echte monteurs uit de
     data toegevoegd (Dennis van de Berg, Maarten Jaarsma, Mike de Vor).
   - Resultaat: alle 5 echte monteurs gematcht op de volledige
     augustus-dataset (2.471 werkbonnen, 1.190 urenregels, 528 ritten, 701
     tijdblokken over 54 dagen); SOORT-verdeling oogt plausibel bij steekproef.
   - Los aandachtspunt voor de analyse: monteur "Berg D." (medewerkernr. 002)
     staat op `actief=False` maar heeft nog 89 tijdblokken van vóór deze
     testronde staan (niet meeherberekend, want `run_matching` zonder
     `--monteur` slaat niet-actieve monteurs over) — vereist gericht
     `--monteur 002 --force` als hij in de analyse moet meetellen.
16. **Gedaan (07-09-2026).** Lokaal-testen-structuur vastgelegd: testen met
   échte SBTT-data gebeurt voortaan uitsluitend via `docker compose up` — nooit
   meer via een losse `manage.py runserver` tegen de host-`db.sqlite3`, zodat er
   nog maar één database is om naar te kijken. Bewust afgewezen alternatief: de
   database als bind-mount delen tussen host en container (zoals nu al met
   `data/inbox`), vanwege een bekende valkuil van SQLite + bind-mounts op Docker
   Desktop/Windows (WSL2) — de bind-mount gedraagt zich voor file-locking als een
   netwerkbestandssysteem, wat SQLite afraadt vanwege corruptierisico bij
   gelijktijdig schrijven. Geldt alleen voor testen met échte klantdata; de
   gewone ontwikkel-cyclus verandert niet. Zie `docs/decisions.md` (07-09-2026).
17. **Gedaan (07-09-2026), gecommit (`f4d1219`), inmiddels gepusht (`origin/main` staat op `b5f4197`).** Schone
   herimport + herberekening van de augustus-testdataset, met twee bugs
   gevonden en gefixt onderweg (via de Claude Code-sessie, 276 tests groen,
   was 270):
   - **Bug 1 (echt, opgelost):** Excel's eigen tijdelijke lockbestand naast
     een geopend bronbestand (`~$`-prefix, bijv. "~$20260826 Download uit
     Syntess Uren 26 8 2026.xlsx") werd door de bewust losse
     bestandsherkenning gezien als een tweede Uren-/Werkbonnen-export. Elke
     bestandsnaam die met `~$` begint wordt nu geweigerd
     (`matching/ingest/filenames.py`).
   - **Bug 2 (echt, opgelost):** de read-only importtabellen (`Uren`, `Rit`,
     `Relatie`, `WerkbonControle`, `Tijdblok`) misten `has_delete_permission`,
     dus "verwijder geselecteerde items" stond ten onrechte in de
     admin-acties-dropdown (zie `docs/decisions.md`, 03-09-2026, waar dit als
     aanvulling is vastgelegd). De Bad Request die Roger daarbij tegenkwam bij
     het zelf proberen op te ruimen was geen bescherming, maar
     `DATA_UPLOAD_MAX_NUMBER_FIELDS` (1000) die overschreden werd door de
     1190 losse velden op de bevestigingspagina — op een kleinere selectie
     was de verwijdering gewoon doorgegaan.
   - **Reset:** alle rijen in Uren/Rit/Relatie/WerkbonControle/Tijdblok/
     ImportedFile verwijderd en schoon opnieuw ingelezen (2546/1190/2471/528)
     en herberekend (62 dagen, 853 tijdblokken, status succes) — via Docker,
     conform punt 16. Koppeltabellen ongemoeid (voor/na geteld, identiek).
     Dennis van de Berg (nu weer actief) toont correct 152 tijdblokken; week
     32 "Gefactureerd 42,50 uur" komt exact overeen met de som uit Uren.xlsx.
   - **Nieuw aandachtspunt, geen bug:** de RouteVision-ritdata heeft een
     dekkingsgat — Dennis van de Berg heeft alleen ritten 03-08 t/m 24-08
     (een volledig gat in week 33 terwijl er wel 8 uur per dag geboekt is),
     en Maarten Jaarsma stopt al op 15-08. Het weekoverzicht meldt dit
     correct als "onvolledige week", maar dit is een openstaande dekkingsvraag
     over de RouteVision-export zelf, met Wim na te lopen — zie punt 18.
   Zie `docs/changelog.md` en `docs/decisions.md` (07-09-2026).
18. **Gedaan (07-09-2026), gecommit (`cffb19e`), inmiddels gepusht (`origin/main` staat op `b5f4197`).** Beheeractie
   "Data resetten" gebouwd: een eigen admin-scherm
   (`/admin/matching/matchmotorstatus/data-resetten/`), bereikbaar via een link
   naast "Matching nu draaien" op het matchmotor-scherm. "Volledig leegmaken"
   (Tijdblok, Uren, Rit, Relatie, WerkbonControle, ImportedFile) en "periode
   verwijderen" (Tijdblok, Uren, Rit, WerkbonControle op een van–tot
   datumbereik — `vertrekdatum` voor Rit; Relatie en ImportedFile blijven
   bewust buiten de periode-modus). Preview met aantallen per tabel vóór een
   expliciete bevestiging, alleen voor superusers
   (`request.user.is_superuser`, geen modelrecht), geen automatische
   herimport/herberekening erna. Koppeltabellen door geen van beide modi
   geraakt (voor/na getest). 24 tests toegevoegd, 300 groen (was 276).
   Nagelopen op de echte augustus-data in Docker zonder iets te wijzigen: het
   formulier toont de juiste aantallen, een preview verwijdert niets, en een
   bevestigde reset op een lege periode doorloopt de hele keten — de dataset
   bleef intact. Zie `docs/changelog.md` en `docs/decisions.md` (07-09-2026).
19. **Gedaan (07-09-2026, avond).** Eerste uitgebreide testronde na de nieuwe
   "Data resetten"-functie (punt 18): volledige reset, opnieuw ingelezen en
   herberekend, en de resultaten doorgenomen. Twee bevindingen, nog niet naar
   Claude Code gestuurd — Roger test eerst verder:
   - **Bug, bevestigd bij meerdere monteurs, zit in de tijdlijnreconstructie:**
     alleen het middenstuk van de dag komt in de tijdlijn terecht — vanaf de
     eerste rit naar een klant/werkbon-adres tot en met de laatste rit terug
     bij het depotgebied. Zowel het ochtenddeel (rit naar het depot + het
     verblijf daar) als het einde van de dag (verblijf bij het depot + rit
     naar huis) ontbreken structureel. Concreet uitgewerkt op monteur Dennis
     van de Berg (002), 2026-06-02: van de 6 ritten die dag komen alleen de
     middelste 2 (12:10–12:27 en 17:11–17:29, rond het werkbonbezoek) in het
     weekoverzicht terecht; de andere 4 (thuis→depot 's ochtends + het
     verblijf daar, en depot→thuis 's avonds + het verblijf daar) niet. Roger
     heeft de `Rit`-tabel in de Django-admin nagelopen: deze ritten staan daar
     wél correct in (de import is dus correct) — de bug zit aantoonbaar in het
     opbouwen van de tijdblokken. Precieze oorzaak nog niet onderzocht in
     code. Zie `docs/decisions.md` (07-09-2026, avond).
   - **Bevestigd, nog niet gebouwd:** het label "Gefactureerd" in het
     weekoverzicht (dag- en weektotalen) wordt "Totaal (excl. reistijd)" —
     de berekening zelf (som van `Uren.Aantal` tegenover de SOORT=W-duur,
     besluit 05-09-2026) verandert niet, alleen de naam, want niet alle
     geboekte uren (bijv. magazijntijd) worden ook echt aan een klant
     gefactureerd. Zie `docs/decisions.md` (07-09-2026, avond) en
     `docs/functioneel-ontwerp.md` §6.
20. **Besloten (07-09-2026, avond), nog niet gebouwd.** Een vierde
   handmatige SOORT-classificatie **P (Privé)** komt naast K/L/C: voor
   onverklaarde (O-)stops die overduidelijk privé zijn, koppelbaar via
   hetzelfde bestaande koppelformulier (§5) — geen nieuw scherm. Drie
   deelbeslissingen: (1) adres-classificatie net als K/L/C, dus geldt voor
   elke monteur die bij dat adres stopt, geen monteur-specifieke koppeling;
   (2) alleen voor stops die nu al als O verschijnen, geen wijziging aan de
   tolerantiedrempel voor kortere (?)-stops; (3) P telt niet mee in "Totaal
   (excl. reistijd)" maar krijgt een eigen, zichtbare regel. De kleur van P
   in het codepalet (`docs/ui-spec.md`) laat Roger over aan Claude Code, binnen
   de bestaande paletlogica. Zie `docs/decisions.md` (07-09-2026, avond) en
   `docs/functioneel-ontwerp.md` §5/§6.
21. **Eerstvolgende stap:** Roger test verder op de echte data. Zodra hij
   klaar is met deze testronde: één instructie naar de Claude Code-sessie
   voor het bug-onderzoek (punt 19), de label-wijziging (punt 19) en de
   P-classificatie (punt 20) samen, dán het navragen bij Wim van de
   RouteVision-dekkingsgaten bij Dennis van de Berg en Maarten Jaarsma (punt
   17) — dan pas verder met roadmap-fase 7 (oplevering). Het draaiboek staat klaar in `DRAAIBOEK.md`, met drie nog
   niet definitieve onderdelen (VM-gegevens, het `backup_db`-commando, §7
   "eerste inrichting"). Neem daarbij verder mee: bij het configureren van
   het echte depotadres voor SBTT het aandachtspunt uit `docs/decisions.md`
   (03-09-2026) over het straat-niveau depotrisico, en bij de oplevering
   (fase 7/8) dat de instructie aan Wim expliciet foutherstel via "Bekende
   locaties" moet uitleggen (`docs/decisions.md`, 03-09-2026).

**Vervallen:** de eerder voorziene live-PoC-fase met 1-2 monteurs bij de klant (~1
week, in overleg met Wim) — het akkoord van 31-08-2026 betrof al de volledige
offerte, niet alleen een PoC-stap. Zie `docs/decisions.md`.

## Important warnings

Het snelheidscontrole-meerwerk (een snelheidscontrole per locatie op basis van
RouteVision-data) is op 05-09-2026 vastgelegd als een **aparte, later apart te
offreren fase** — geen openstaande ja/nee-vraag binnen deze roadmap en niet iets om
nu op te pakken. Zodra die fase wel aan de orde komt: die controle raakt
AVG/medewerkersmonitoring en vereist een zorgvuldig juridisch/HR-traject naast de
techniek. Zie `docs/decisions.md` (05-09-2026).

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
