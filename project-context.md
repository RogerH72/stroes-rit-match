# Project Context — Stroes-Rit-Match (RMW)

## What is it?

Een applicatie ("RMW – Ritten Match Werkbon") die per monteur en per werkdag de
ingevulde werkbonnen uit Syntess vergelijkt met de rit-, tijd- en locatiegegevens uit
RouteVision, om afwijkingen te signaleren en bij te kunnen sturen. Dit is géén simpele
één-op-één koppeling (werkbon A ↔ rit A), maar een tijdlijn-reconstructie +
afwijkingsdetectie per monteur per dag.

## Who is it for?

**Stroes Bouw en Techniek (SBTT)**, een klein installatiebedrijf (familiebedrijf).
Contactpersoon: **Wim Stroes** (schrijft namens het bedrijf van zijn zoon). Vond Roger
via ChatGPT toen hij zocht naar een "access specialist".

## What problem does it solve?

Minder handmatig controlewerk, een objectieve vergelijking van werkbon vs.
werkelijkheid, en het systematisch opsporen van onverklaarde stops/ritten en
afwijkende reistijden.

## Purpose

Voor SBTT: een productieklare app die aantoonbaar tijd bespaart t.o.v. hun bestaande
Access-programma. Voor Roger: een maatwerkopdracht die gefaseerd wordt aangeboden —
eerst een kleine PoC, dan pas een onderbouwde offerte voor de volledige app.

## What is currently being built?

Wim heeft op **31-08-2026 akkoord gegeven op de volledige offerte** voor de complete
app (na overleg met zijn IT-supportpartner) — niet alleen op een aparte PoC-stap; zie
de statuscorrectie van 01-09-2026 in `docs/decisions.md`. De eerder voorziene
live-PoC-fase met 1-2 monteurs bij de klant is vervallen en niet uitgevoerd.

De bredere technische validatie (2 monteurs — Jesse Verkerk en Dennis van de Berg —
over 4 weken, W30 t/m W33) is afgerond op 01-09-2026 en positief: 78% resp. 93% van de
werkbonnen automatisch teruggevonden, met steeds verklaarbare afwijkingen. Zie
`docs/decisions.md` en `docs/demo.md` voor de details. Eerstvolgende stap: de bouw van
de volledige app. Het beoogde eindresultaat blijft: bestand-in/bestand-uit matching op
basis van de 3 dagelijkse Syntess Excel-exports en de RouteVision-download, uitmondend
in een weekoverzicht per monteur met SOORT-codes (K=klant, L=locatie, C=crediteur,
W=werkbon, ?=onbekend, O=onverklaard, R=reistijd) en afwijkingen t.o.v. tolerantie —
conform het eindresultaat dat de klant al zelf in Excel had ontworpen.

## Guiding documents

- `GUIDELINES.md` — huidige projectblauwdruk.
- `docs/*.md` — gedetailleerde specificaties (zie documentatiekaart in GUIDELINES.md).

## Intended working method

Per `werkwijze-project`: ontwerpbeslissingen worden besproken en expliciet bevestigd
in chat/Cowork, daarna als precieze instructie naar een code tool gebracht.

**Vastgelegd (01-09-2026):** het bouwen van de webapp zelf gebeurt in een aparte
Claude Code-sessie (los terminalvenster op Rogers computer), niet in deze
Cowork-sessie — vanwege langlopende/interactieve stappen (Django-dev-server,
Docker-builds/logs, migraties) waar een doorlopende terminalsessie praktischer voor
is dan de kortlopende, per-opdracht shells van Cowork. Ontwerp, besluiten en
documentatie-onderhoud blijven hier. Zie `docs/decisions.md` (01-09-2026).

De volledige voorgeschiedenis, functionele vragen (37 stuks), risico-analyse en het
meerwerk-idee snelheidscontrole (05-09-2026 vastgelegd als aparte, later apart te
offreren fase) staan in de brainstorm-sessie
`D:\AI\brainstorm-sessies\stroes-rit-match-werkbon` (`overzicht.md`, `sessies.md`,
`besluiten.md`) — raadplegen bij twijfel over eerdere afwegingen. Klantbronmateriaal
(analyse, origineel Excel-overzicht, ChatGPT-voorstel) staat in `D:\STROES`.
