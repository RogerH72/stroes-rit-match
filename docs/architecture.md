# Architecture — Stroes-Rit-Match (RMW)

## Current implementation

**Fase 2 (data-inlezing) is gebouwd (02-09-2026) en volledig afgerond (03-09-2026).**
Bestandsdetectie (`matching/ingest/`, polling + stabiliteitscheck zoals hieronder
beschreven) en de vier ruwe importmodellen (Uren, Rit, Relatie, WerkbonControle) plus
`ImportedFile`-bijhoudtabel zijn gebouwd en getest (74 tests groen, plus een
handmatige eind-tot-eind-run tegen de echte voorbeeldbestanden). Zie
`docs/changelog.md` voor de volledige technische samenvatting en `docs/decisions.md`
voor de openstaande/besliste punten die daarbij naar boven kwamen. De Docker-image-
build met de nieuwe `scripts/`-map en `openpyxl` is gecontroleerd (03-09-2026): build,
migraties, healthcheck en admin (in de container) allemaal groen.

## Target architecture

**PoC:** los Python-script, bestand-in/bestand-uit (3 Syntess Excel-exports +
RouteVision-download → weekoverzicht Excel/HTML per monteur).

**Productie (vastgelegd via het OvO v1.8, geaccordeerd 31-08-2026, voor de eerste
werkende versie — geen open richting meer):** Django-webapp met de reken-/matchmotor
in Python; Django-admin voor de beheerschermen (koppeltabellen: bekende locaties,
monteur-voertuig, personeelsnummer-naam, relaties; tolerantietabel per activiteit);
bestandsgebaseerd, geen API-koppeling met Syntess/RouteVision in deze versie;
oplevering als lichte, zelfstandige Docker-container. Zie `docs/roadmap.md` voor de
bouwvolgorde.

**Routing/toegang (06-09-2026).** De root-URL (`/`) is de voordeur van de
*applicatie*, niet van de admin: `/` stuurt door naar `/weekoverzicht/`. De
Django-admin blijft het enige inlogscherm (`LOGIN_URL = "/admin/login/"`), zodat
een anonieme bezoeker via `?next=` terugkomt op het scherm dat hij vroeg;
`LOGIN_REDIRECT_URL = "/weekoverzicht/"` vangt een inlog zonder bestemming op.
Zie `docs/functioneel-ontwerp.md` §6.

Bewust buiten deze eerste versie (apart te offreren als vervolgstap): een directe
RouteVision REST API-koppeling (https://rest.routevision.com/docs) i.p.v. de
handmatige download, een Syntess-API-koppeling ("kost direct geld"), en Access/Power
BI als reporting-schil. Zie `docs/roadmap.md` voor de volledige lijst met
uitbreidingen.

## Deployment (fase 7, vooruitlopend vastgelegd)

Zelfde patroon als ReplayCalcTool: lokaal bouwen, Docker-container, geplaatst
door Stric op een eigen VM vanaf de private GitHub-repo. Productiedatabase blijft
SQLite (niet PostgreSQL) — zie `docs/decisions.md` (03-09-2026) voor de afweging.
Het volledige, stap-voor-stap draaiboek staat in `DRAAIBOEK.md` (root van de
repository); drie onderdelen daarin zijn nog niet definitief (VM-gegevens bij
Stric, het nog te bouwen `backup_db`-commando, en §7 "eerste inrichting" die op
de fase 4/5-beheerschermen wacht).

### Trigger-mechanisme (bestandsdetectie servermap) — ontworpen, nog niet gebouwd

Vastgelegd in een ontwerpgesprek (01-09-2026), vooruitlopend op de bouw:

- **Detectie: polling, geen filesystem-events.** De servermap (`\\stroes-1909\atrium`)
  is een netwerkshare; event-gebaseerd bestandswatchen (inotify e.d.) is onbetrouwbaar
  op netwerk-/SMB-mounts. Een geplande, periodieke check is daarom het uitgangspunt.
- **Scheduler ingebakken in de Docker-container.** Gebouwd als een aparte
  compose-service uit hetzelfde image (`scripts/scheduler.sh`, een eenvoudige loop
  die `check_imports` elke `POLL_INTERVAL_MINUTES` aanroept) in plaats van
  cron/supercronic — geen extra pakket in het image nodig, logging gaat naar stdout.
  Zelfstandig, geen afhankelijkheid van Stric voor de planning zelf (Stric is alleen
  nodig voor de omgeving en leesrechten, zie de OvO).
- **Polling-interval:** elke 5 minuten (instelbaar via configuratie/env-var).
- **Stabiliteitsmarge:** een bestand telt pas mee als de bestandsgrootte gedurende 30
  minuten ongewijzigd blijft — bij een polling-interval van 5 minuten dus 6
  opeenvolgende checks op rij. De marge is los van het polling-interval instelbaar
  (eigen configuratie/env-var), zodat beide onafhankelijk kunnen worden bijgesteld
  (vastgelegd 2026-09-02). Beschermt tegen het inlezen van een half weggeschreven
  bestand, ongeacht of de bron direct naar de definitieve naam schrijft of niet.
- **Bij ontbrekende/onvolledige bestanden einde dag:** loggen + een statusveld
  ("laatste succesvolle run") in het beheerscherm. Geen automatische e-mail — dat valt
  buiten scope (zie de OvO, punt 2a: geen automatische signalering).
- **Herverwerken:** alleen handmatig via een knop in het beheerscherm, nooit
  automatisch — het weekoverzicht verandert nooit stilletjes.
- **Bijhouden wat al verwerkt is:** puur via de database (de matchresultaten per
  dag/monteur die de app toch al moet opslaan om het weekoverzicht te tonen). Geen
  aparte "verwerkt"-map en geen bestanden die worden verplaatst of verwijderd op de
  servermap — zie `docs/decisions.md` voor de afweging.
- **Servermap-locatie bevestigd (mailwisseling Wim, 27/28-08-2026):**
  `\\stroes-1909\atrium\Autoprint\RUUDS`. De exacte bestandsnaam-conventie van de
  automatische productie-export (Syntess/RouteVision) is nog niet bekend — de
  bestanden in `D:\STROES` zijn handmatig benoemde PoC-exports. Te bevestigen met
  Stric/RVS Solutions/RouteVision vóór de bestandsherkenning in de trigger definitief
  wordt vastgelegd.
- **RouteVision-aanlevering is geen taak van de app.** De app leest en verwerkt
  automatisch wat er in de servermap staat; het dagelijks plaatsen van het
  RouteVision-bestand in die map is aan SBTT/Stric, niet iets dat Roger download of
  automatiseert (bevestigd met Sander van Stric, en verduidelijkt in de OvO v1.8,
  punt 2a).

## Superseded decisions

Nog geen.
