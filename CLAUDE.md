# CLAUDE.md — Stroes-Rit-Match (RMW)

## What this project is

RMW (Ritten Match Werkbon) is een matchingtool voor Stroes Bouw en Techniek (SBTT) die
per monteur en per werkdag de ingevulde werkbonnen uit Syntess vergelijkt met de rit-,
tijd- en locatiegegevens uit RouteVision, om afwijkingen te signaleren. Volledige
achtergrond staat in `project-context.md`.

## Authoritative documents

- `project-context.md` — wat dit project is en waarom het bestaat.
- `GUIDELINES.md` — het huidige projectblauwdruk: architectuur, stack, prioriteiten,
  beperkingen. Lees dit voor elke wijziging.
- `docs/architecture.md`, `docs/database.md`, `docs/business-rules.md`,
  `docs/ui-spec.md`, `docs/demo.md`, `docs/roadmap.md` — gedetailleerde
  specificaties, alleen laden wanneer een taak dat onderdeel raakt.
- `docs/decisions.md` — waarom eerdere besluiten zijn genomen.
- `docs/changelog.md` — chronologische geschiedenis. Niet nodig voor normale taken.

## How to select documentation for a task

Lees altijd eerst `project-context.md` en `GUIDELINES.md`. Lees daarna alleen het
`docs/*.md`-bestand dat relevant is voor de taak (business-logica → `docs/business-rules.md`,
database → `docs/database.md`, enz.). Lees verdere documenten als de taak dat vereist.

## Development principles

- **Taal (vastgelegd 01-09-2026, zie `docs/decisions.md`):** UI en
  klantcommunicatie altijd Nederlands. De al bestaande projectdocumentatie
  (`CLAUDE.md`, `GUIDELINES.md`, `docs/*.md`) blijft Nederlands. Code (variabelen,
  comments), commit-messages en nieuwe instructies naar een code tool zijn vanaf nu
  Engels — zelfde conventie als ReplayCalcTool ("UI language: Dutch", rest Engels).
  **Uitzondering:** Nederlandse domeintermen die letterlijk uit het door SBTT
  ontworpen format komen (Werkbon, Monteur, Rit, de SOORT-codes K/L/C/W/?/O/R,
  koppeltabel, tolerantietabel) blijven ongewijzigd Nederlands in modelnamen/velden
  — net als "Totaal Montage" bij ReplayCalcTool. Alleen generieke code/structuur is
  Engels.
- PoC eerst: forceer geen productiestack-beslissingen vóór het matchingsconcept
  gevalideerd is op echte data.
- Herkomst/achtergrond van de opdracht staat in de brainstorm-sessie
  `D:\AI\brainstorm-sessies\stroes-rit-match-werkbon` — raadpleeg daar `besluiten.md`
  bij twijfel over eerdere afwegingen (bijv. het snelheidscontrole-meerwerk).
- Bronmateriaal van de klant staat in `D:\STROES` (analyse, requirements, origineel
  Excel-overzicht met business rules).

## Ground rules

- Verzin geen architectuur of business rules die niet zijn vastgelegd. Vraag bij
  twijfel of iets onduidelijk/onbeslist is, in plaats van te gokken.
- Meng geen huidige regels met historische/vervallen besluiten — label duidelijk als
  iets een verleden besluit is in plaats van huidige richtlijn.
- Houd de documentatie actueel: werk na een bouwstap het relevante specialistische
  document en/of `GUIDELINES.md` bij (zie `werk-project-status`).
