# Architecture — Stroes-Rit-Match (RMW)

## Current implementation

Nog niet gebouwd (project gestart 31-08-2026).

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

Bewust buiten deze eerste versie (apart te offreren als vervolgstap): een directe
RouteVision REST API-koppeling (https://rest.routevision.com/docs) i.p.v. de
handmatige download, een Syntess-API-koppeling ("kost direct geld"), en Access/Power
BI als reporting-schil. Zie `docs/roadmap.md` voor de volledige lijst met
uitbreidingen.

### Trigger-mechanisme (bestandsdetectie servermap) — ontworpen, nog niet gebouwd

Vastgelegd in een ontwerpgesprek (01-09-2026), vooruitlopend op de bouw:

- **Detectie: polling, geen filesystem-events.** De servermap (`\\stroes-1909\atrium`)
  is een netwerkshare; event-gebaseerd bestandswatchen (inotify e.d.) is onbetrouwbaar
  op netwerk-/SMB-mounts. Een geplande, periodieke check is daarom het uitgangspunt.
- **Scheduler ingebakken in de Docker-container** (bv. cron/supercronic) die een Django
  management-command aanroept — zelfstandig, geen afhankelijkheid van Stric voor de
  planning zelf (Stric is alleen nodig voor de omgeving en leesrechten, zie de OvO).
- **Interval:** elke 30 minuten.
- **Volledigheid/stabiliteit:** een bestand telt pas mee als de bestandsgrootte over
  twee opeenvolgende checks (dus 30 minuten) ongewijzigd is — beschermt tegen het
  inlezen van een half weggeschreven bestand, ongeacht of de bron direct naar de
  definitieve naam schrijft of niet.
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
