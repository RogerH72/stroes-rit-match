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
19. **Gebouwd (07-09-2026).** De tijdlijnbug uit de vorige testronde is
   gefixt en gecommit (`4d219c2`, 308 tests groen): het depot belandde tussen
   de automatisch afgeleide "thuisstraten" van een monteur, waardoor
   `_trim_home_hops()` elke rit tussen huis en depot wegzag als "de bus voor
   de deur verzetten" — op de hele dataset ging het aantal tijdblokken van
   1169 naar 1356. Geverifieerd op Dennis van de Berg, 2026-06-02: alle 6
   ritten weer zichtbaar. Zie `docs/changelog.md` (07-09-2026) voor de
   volledige analyse.
   **Restbevinding, leidt tot punt 21 hieronder:** dezelfde detectie mist nog
   steeds een frequentietoets — een straat die een monteur maar een enkele
   keer als dagrand had (bijv. Rolweg/Forêtweg bij Dennis, Marsweg bij
   Maarten Jaarsma) telt óók mee als "thuis", waardoor 28 ritten over 12
   dagen nog wegvallen; het scherpste geval: twee volledig lege dagen bij
   Dennis (24/25-06-2026) terwijl hij wél 8 uur boekte.
   De label-wijziging "Gefactureerd" → "Totaal (excl. reistijd)" is ook
   gebouwd en gecommit (`bf1c077`, 309 tests groen), op de pagina, in de
   Excel-export en in de dagregel "… → locatie". Berekening ongewijzigd.
20. **Gebouwd (07-09-2026).** SOORT-classificatie **P (Privé)** gecommit
   (`117a648`, 320 tests groen), precies zoals besloten: vierde keuze op
   `BekendeLocatie.soort`, via het bestaande koppelformulier, geen wijziging
   aan de tolerantielogica, eigen regel per dag/week naast "Totaal (excl.
   reistijd)" (verschijnt alleen als er privé-tijd is). Kleur `#C2185B`
   (karmijn), door Claude Code gekozen. Migratie 0007 bevestigd een no-op.
21. **Gebouwd (07-09-2026).** Thuisadres-veld op `Monteur` (`thuisadres` +
   `thuisadres_type`, straat/postcode, beide optioneel) en nieuwe SOORT-code
   **T (Thuis)** gecommit (`67b6df4`, 327 tests groen), precies zoals
   besloten: T op dezelfde plek in de prioriteitsvolgorde als de oude
   (verwijderde) thuisstraat-stap, óók koppelbaar via het bestaande
   uitzonderingenscherm (koppeltabel wint van het veld), geen apart
   weektotaal, kleur `#6D4C41` (bruin, door Claude Code gekozen). De
   frequentiedetectie (`home_streets_for()`, `_trim_home_hops()`) is volledig
   verwijderd, geen terugval. Resultaat op de echte juni-dataset: **782 van
   782 ritten** komen nu in de tijdlijn terecht (was 754) — de restbevinding
   uit punt 19 is daarmee volledig opgelost, niet alleen voor het depot.
   Dennis van de Berg's 24 en 25 juni geven nu 9 en 8 tijdblokken in plaats
   van nul.
   **Eigen toevoeging van Claude Code, wél vastleggen als regel:** op een
   "meegereden"-dag telt het thuisadres van de tijdlijn-monteur zelf, niet
   dat van de senior/bestuurder wiens ritten die dag opbouwen — logisch (het
   is diens huis niet), maar niet expliciet in de instructie gevraagd. Zie
   `docs/decisions.md` (07-09-2026).
   **Aandachtspunt bij het testen (geen bug, wel even nakijken):** tijdens
   het testen op echte data zijn per ongeluk 2 bestaande `BekendeLocatie`-
   rijen verwijderd door een hoofdletterongevoelige `LIKE`-match op een
   testfilter (`test 4 klant` op 4104AR, `Test klant` op 4105JC — beide K,
   geen depot) en direct daarna hersteld uit de eerder uitgelezen waarden.
   Roger: een blik op deze twee rijen in de admin waard voordat je verder
   gaat.
22. **Gedaan (07-09-2026).** Gepusht naar `origin/main`, en de twee per
   ongeluk verwijderde/herstelde `BekendeLocatie`-rijen uit punt 21 zijn door
   Roger gecontroleerd — in orde.
23. **Gebouwd (07-09-2026).** "Aansluiting per werkbon" gecommit
   (`69c151b`, 23 tests erbij, 343 groen), op de pagina én in de Excel-export,
   precies zoals besloten (alle werkbonnen van de dag, losse K-regel, geen
   L/C, geen weekversie). **Eigen toevoeging van Claude Code, wél vastleggen
   als regel:** 256 van de 462 urenregels in de juni-data hebben géén
   werkbonnummer (kantoor, verlof, reisuren, magazijnonderhoud) — zonder een
   aparte regel daarvoor zou het tabeltotaal niet aansluiten op de bestaande
   dagregel erboven. Er is daarom een tweede losse regel bijgekomen: **"Zonder
   werkbonnummer (indirect)"**, met die geboekte-maar-niet-aan-een-werkbon-
   gebonden uren. Een kant die niet van toepassing is toont een
   gedachtestreepje, nooit 0,00 (0,00 zou beweren dat de vraag gesteld is en
   leeg terugkwam). Geen migratie nodig (pure weergave-aggregatie), geen
   nieuwe kleur (bestaande waarschuwingskleur `#D97706`, alleen bij een
   werkelijk verschil, niet op de totaalregel — anders licht de kolom op door
   centverschillen). Geverifieerd op de echte juni-data: Jesse Verkerk 17
   juni toont WB260917 met 1,50 gedeclareerd tegen 0,00 op locatie; Dennis
   van de Berg 6 juni toont 0,38 uur klant-tijd zonder enige boeking — beide
   gevallen die in de oude, geblendete dagregel onzichtbaar wegvielen. Zie
   `docs/decisions.md` en `docs/changelog.md` (07-09-2026).
24. **Gedaan (08-09-2026).** Twee documentatiebesluiten vastgelegd, geen
   codewijziging: (1) het invullen van het thuisadres per monteur is
   toegevoegd als verplicht onderdeel van de opleverinstructie aan Wim,
   naast het al vastgelegde foutherstel-punt (03-09-2026); (2) een extra
   kolom "Klant" bij "Aansluiting per werkbon" is besloten (bron:
   `Uren.project_opdrachtgever_naam`), nog niet gebouwd — instructie naar
   de Claude Code-sessie volgt. Zie `docs/decisions.md`,
   `docs/functioneel-ontwerp.md` §6/§7 en `docs/business-rules.md`.
25. **Gebouwd (08-09-2026).** De klantnaam-kolom bij "Aansluiting per
   werkbon" (punt 24) is gebouwd: `Uren.project_opdrachtgever_naam` op de
   werkbon-rijen, op de pagina en in de Excel-export, 349 tests groen (was
   343). Aandachtspunt gemeld door Claude Code, bewust zo gelaten: een
   werkbon die een dag alleen via de Werkbonnen.xlsx-postcode-vangnet
   wordt gematcht (dus zonder eigen Uren-regel die dag) toont altijd een
   streepje bij Klant — geen bug, de bewuste "geen opzoekactie"-regel,
   maar te herbekijken zodra een echte week is doorgerekend. Zie
   `docs/decisions.md` en `docs/functioneel-ontwerp.md` §6.
26. **Eerstvolgende stap:** het navragen bij Wim van de RouteVision-
   dekkingsgaten bij Dennis van de Berg en Maarten Jaarsma (punt 17) — dan
   pas verder met roadmap-fase 7 (oplevering). Vergeet niet eerst nog te
   pushen (2 commits staan klaar op `main`). Het draaiboek staat klaar in `DRAAIBOEK.md`, met drie nog
   niet definitieve onderdelen (VM-gegevens, het `backup_db`-commando, §7
   "eerste inrichting"). Neem daarbij verder mee: bij het configureren van
   het echte depotadres voor SBTT het aandachtspunt uit `docs/decisions.md`
   (03-09-2026) over het straat-niveau depotrisico, en bij de oplevering
   (fase 7/8) dat de instructie aan Wim expliciet foutherstel via "Bekende
   locaties" moet uitleggen (`docs/decisions.md`, 03-09-2026).
27. **Gedaan (08-09-2026).** De RouteVision-dekkingsgaten uit punt 26
   (Dennis van de Berg, gat in week 33; Maarten Jaarsma, geen data vanaf
   15-08) zijn verklaard: Roger heeft toegang tot RouteVision gekregen en
   ziet bij beide monteurs dat de data vanaf 01-09-2026 weer terugkomt —
   een vakantieperiode, bevestigd in een eerder gesprek met Wim. Geen
   exportprobleem, dus geen actie nodig richting Stric/RouteVision en geen
   aanpassing aan de matchlogica of het weekoverzicht: de geboekte uren
   die dag zijn verlofuren (net als kantoor/reisuren/magazijnonderhoud
   gewoon geboekte uren zonder ritdata, zie `docs/business-rules.md`), en
   de melding "onvolledige week" is precies het bedoelde gedrag wanneer er
   geen ritdata is om een tijdlijn op te bouwen. De overige punten uit
   punt 26 (pushen, de drie nog niet definitieve DRAAIBOEK.md-onderdelen,
   het depotadres-aandachtspunt, de foutherstel-instructie) blijven de
   eerstvolgende stappen richting roadmap-fase 7. Zie `docs/decisions.md`
   (08-09-2026).
28. **Gedaan (08-09-2026).** Naar aanleiding van een aangepaste
   Relaties.xlsx van Wim (nieuwe kolom "Klant of leverancier", K/L) is
   besloten, nog niet gebouwd: het koppelformulier in het
   uitzonderingenscherm krijgt een voorstel op basis van `Relatie`
   (matchend op postcode, want een betrouwbaar huisnummer ontbreekt),
   met een keuzelijst bij meerdere kandidaten op dezelfde postcode. Geen
   automatische classificatie — de gebruiker bevestigt nog steeds zelf.
   Aandachtspunt voor de bouw: Relatie "L" (Leverancier) moet als SOORT
   C (Crediteur) voorgesteld worden, niet als "L" (Locatie in
   `BekendeLocatie.soort` betekent iets anders). Zie `docs/decisions.md`
   en `docs/functioneel-ontwerp.md` §5/§9.
29. **Gebouwd (08-09-2026).** De klant/leverancier-suggestie uit punt 28 is
   gebouwd en getest, 364 tests groen (was 349). Nieuw veld
   `Relatie.klant_of_leverancier` (migratie `0009`, blank toegestaan zodat
   een oudere Relaties.xlsx zonder die kolom blijft importeren), de
   suggestielogica in `matching/views.py` en een keuzelijst in
   `koppelen.html` bij meerdere relaties op dezelfde postcode. De
   lettermapping (Relatie "L" → SOORT C, nooit SOORT L) staat vast in een
   test die daar expliciet op asserteert. Zie `docs/decisions.md` en
   `docs/functioneel-ontwerp.md` §5.
30. **Gebouwd (08-09-2026), met een belangrijke bevinding.** Bij het
   importeren van het nieuwe `Relaties.xlsx` bleek de app de **ruwe
   Atrium-export helemaal niet te kunnen lezen**: Atrium schrijft
   niet-schemaconforme XML-attribuutnamen (`WindowWidth`/`firstPageNo`) waar
   openpyxl op afbreekt. Dat bleef tot nu toe verborgen doordat elk
   voorbeeldbestand ooit door Excel is opgeslagen, wat de fout stilzwijgend
   repareert — op de servermap gebeurt dat niet. De ingest-laag
   (`matching/ingest/parsers/base.py`) repareert dit nu in een kopie in het
   geheugen en zoekt kolomnamen hoofdletterongevoelig (de nieuwe kolom heet
   `klant of leverancier`, met kleine k). 379 tests groen (was 364), met een
   regressietest die de afwijking nabouwt (geen klantbestand in de
   repository — `.gitignore` weert workbooks om AVG-redenen). Het echte
   bestand importeert nu: 2561
   relaties, en 23 van de 61 onverklaarde groepen krijgen daardoor een
   suggestie. **Nog te doen:** Wim/RVS informeren dat de Atrium-export
   niet-schemaconforme XML schrijft — niet blokkerend, de app kan er nu
   tegen. Zie `docs/decisions.md` en `docs/architecture.md`.

31. **Besloten (08-09-2026), nog niet gebouwd.** Naar aanleiding van het
   handmatig moeten draaien van `check_imports --force` om te testen, komt
   er een derde knop "Bestanden nu inlezen" op het bestaande
   matchmotor-beheerscherm, naast "Matching nu draaien" en "Data
   resetten". Roept `scan_share(force=True)` aan (dezelfde functie als het
   command-line commando, geen reprocess van al-verwerkte bestanden). Blijft
   een aparte, bewuste stap los van "Matching nu draaien" — geen
   automatische koppeling. Zie `docs/decisions.md` en
   `docs/functioneel-ontwerp.md` §4.

32. **Besloten (08-09-2026) — inmiddels gebouwd, zie punt 30.** Het nieuwe,
   echt ongemoeide Relaties.xlsx van Wim bleek niet importeerbaar: Atrium schrijft
   niet-schemaconforme XML (`WindowWidth`/`firstPageNo` i.p.v.
   `windowWidth`/`firstPageNumber`), gemaskeerd tot nu toe omdat elk eerder
   testbestand ooit door Excel is geopend en zo stilzwijgend gerepareerd.
   Daarnaast heet de nieuwe kolom `klant of leverancier` met een kleine
   letter, terwijl de parser hoofdlettergevoelig zocht. Besloten: beide
   fixen in de gedeelde ingest-laag (`matching/ingest/parsers/base.py`),
   niet alleen in de Relaties-parser, want het risico geldt voor alle vier
   bronbestanden. Zie `docs/decisions.md` en `docs/functioneel-ontwerp.md`
   §3a.
33. **Gebouwd (08-09-2026).** De knop "Bestanden nu inlezen" uit punt 31 staat
   op het matchmotor-beheerscherm, boven "Matching nu draaien" — de volgorde
   waarin de twee stappen in de praktijk gezet worden. POST-only, gated op
   `matching.change_matchmotorstatus`, roept `scan_share(force=True)` aan
   zonder reprocess en zonder de matching mee te laten draaien; een test
   controleert dat laatste expliciet. 391 tests groen (was 379). Zie
   `docs/decisions.md` en `docs/functioneel-ontwerp.md` §4.

34. **Gebouwd (08-09-2026).** Bij het testen van "monteur vast laten
   meerijden" bleek `Monteur.vaste_meerijder` geen check te hebben tegen
   zelfkoppeling (een monteur kan zichzelf als eigen vaste meerijder
   kiezen) — anders dan `MeegeredenKoppeling`, die deze check al wel
   heeft. Gelijkgetrokken: `CheckConstraint` + `clean()`-validatie, zelfde
   patroon. De tweede gemelde klacht (een vastgelegde koppeling wijzigen
   lukt, verwijderen niet) is live getest in de container en bleek geen
   codefout — het veld is gewoon leegbaar. Waarschijnlijke oorzaak:
   Django's standaard leeg-label `---------` leest niet als
   "verwijderen"; opgelost met een duidelijker label ("— geen vaste
   meerijder —") op `MonteurAdmin`. Bijvangst: een verouderd
   code-commentaar in `matching/timeline/meegereden.py` dat nog beweert
   dat overlappende periode-koppelingen niet worden tegengehouden, is
   rechtgezet — dat klopt niet meer sinds die check (07-09-2026) is
   toegevoegd. 398 tests groen (was 391). Commit `bcd57af`. Zie
   `docs/decisions.md` en `docs/functioneel-ontwerp.md` §3b.

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
