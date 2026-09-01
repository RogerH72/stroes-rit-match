# Business Rules — Stroes-Rit-Match (RMW)

## Implemented

Nog geen (project net gestart).

## Designed but not implemented

- Tijdlijn-reconstructie + afwijkingsdetectie per monteur per dag (geen simpele
  1-op-1 koppeling werkbon ↔ rit).
- SOORT-codes per tijdblok in het weekoverzicht: K=klant, L=locatie, C=crediteur,
  W=werkbon, ?=onbekend, O=onverklaard, R=reistijd — conform het eindresultaat dat de
  klant zelf al in Excel had ontworpen.
- Matchingregels, al gevalideerd op echte data: postcode-exact is niet genoeg →
  straatnaam-fallback; een depotbezoek vóór werk wordt herkend. Bekende
  adres-afwijkingen (bv. werkbonadres ≠ busadres) worden als aandachtspunt getoond,
  niet automatisch gematcht.
- **Werktijd bepalen uit ritgegevens (leidend), niet uit de Werktijd/Reistijd-velden
  van de werkbon** — bevestigd door Wim (mailwisseling 27/28-08-2026), omdat monteurs
  die velden niet consequent invullen: werktijd begint zodra de monteur bij een
  klantadres stopt, en eindigt zodra hij daar wegrijdt. Tussentijdse bezoeken aan een
  leverancier of de eigen zaak beëindigen de werkdag niet, zolang de monteur diezelfde
  dag nog terugkeert naar de klant — pas het laatste vertrek bij de klant die dag geldt
  als einde werktijd.
- **"Monteur meegereden"** — twee oplossingsrichtingen afgesproken met Wim, geen keuze
  gemaakt: (A) een junior monteur in de beheerschermen ("Instellingen") hard koppelen
  aan een senior monteur, zodat de junior dezelfde rittijden krijgt toegewezen als de
  senior; (B) testen of Syntess "Monteur meegereden" automatisch kan invullen in de
  Werkbonnen-export, wat de nettere oplossing zou zijn maar nog niet is getest.
- Tolerantietabel per activiteit (drempel voor onverklaarde stops is instelbaar) —
  exacte waarden nog te bevestigen met de klant (bron: `20260424 RMW-Overzicht
  ....xlsx` in de brainstorm-sessie).
- **Klant/leverancier-onderscheid** — was een open datavraag, maar wordt bij de bron
  opgelost: Ruud (RVS Solutions) gaat dit onderscheid zelf aan de Relaties-export
  toevoegen. Mogelijk hoeft de app dit dan niet meer zelf via een koppeltabel af te
  leiden — te bevestigen zodra de aangepaste export er is.
- Mogelijk meerwerk: snelheidscontrole per locatie (RouteVision-snelheid vs.
  maximumsnelheid) — nog geen besluit, zie `docs/decisions.md`.

## Superseded

Nog geen.
