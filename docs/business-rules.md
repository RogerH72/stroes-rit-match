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
  van de werkbon** — bevestigd door Wim (mailwisseling 27/28-08-2026, herbevestigd
  02-09-2026), omdat monteurs die velden niet consequent invullen en er geen
  betrouwbare kloktijden op de werkbon beschikbaar zijn: werktijd begint zodra de
  monteur bij een klantadres stopt, en eindigt zodra hij daar wegrijdt. Tussentijdse
  bezoeken aan een leverancier of de eigen zaak beëindigen de werkdag niet, zolang de
  monteur diezelfde dag nog terugkeert naar de klant — pas het laatste vertrek bij de
  klant die dag geldt als einde werktijd. Het oorspronkelijke wensdoel om de door de
  monteur ingevulde aankomst-/vertrektijd op de werkbon te vergelijken met de
  werkelijkheid (een WB-vs-SYS-signaal) is hiermee bewust niet gebouwd — zie
  `docs/decisions.md` voor een impact-analyse mocht Wim hier ooit op terugkomen.
- **Databronnen voor de matching (vastgelegd 2026-09-02, na inspectie van de
  voorbeeld-databestanden in `voorbeeld-data/`):** van de 3 Syntess-exports drijft de
  matching zelf uitsluitend op **Uren.xlsx** (wie, welke werkbon, welke datum, hoeveel
  uur, welk adres/klant) en de RouteVision-rit-CSV, aangevuld met **Relaties.xlsx**
  voor klant/leverancier-stamgegevens. **Werkbonnen.xlsx wordt niet gebruikt voor de
  matching** — Reistijd/Werktijd daaruit zijn al niet leidend (zie hierboven), en
  Titel/Fase voegen voor de matching zelf niets toe. Werkbonnen.xlsx wordt wél
  ingelezen, maar uitsluitend voor een **volledigheidscontrole**: signaleren of er een
  werkbon bestaat zonder geboekte uren. Daarbij wordt de **laatste/huidige Fase-status**
  van de werkbon gebruikt (niet de volledige historie van fase-overgangen) om onderscheid
  te maken tussen "nog niet gestart" (Fase bijv. Uitgevoerd/Gestopt — verwacht, geen
  signaal) en "afgerond zonder geboekte uren" (Fase Afgehandeld/Gereed zonder
  Uren-regels — wél een afwijking om te tonen). Een monteur die uren boekt op een
  werkbonnummer dat niet in de Werkbonnen-export voorkomt wordt logisch onmogelijk
  geacht (Syntess borgt die referentie zelf), dus dat scenario hoeft niet apart
  gedetecteerd te worden.
- **Ontbrekend bronbestand blokkeert alleen zijn eigen doel (vastgelegd
  2026-09-02):** elk bronbestand wordt onafhankelijk gevolgd. Ontbreekt
  Werkbonnen.xlsx voor een periode terwijl Uren.xlsx er wel is, dan draait de matching/
  tijdlijnreconstructie gewoon door (die leunt niet op Werkbonnen.xlsx) — alleen de
  volledigheidscontrole wordt voor die periode overgeslagen (status "niet uitgevoerd,
  bronbestand ontbrak"), niet het hele weekoverzicht geblokkeerd.
- **"Monteur meegereden" — instelbare 3-standen toggle (verfijnd 2026-09-03,
  zie `docs/decisions.md`):** één globale instelling ("Instellingen"-scherm, fase 4)
  bepaalt hoe een junior monteur zijn rittijden krijgt toegewezen: (1) **Vast** —
  permanent gekoppeld aan één senior monteur; (2) **Periode-/datumgebonden** — een
  koppeltabel met geldigheidsperiode, zodat een junior op verschillende momenten met
  verschillende senioren kan meerijden; (3) **Uit Syntess** — leest de kolom "Monteur
  meegereden" in de Werkbonnen-export rechtstreeks uit. Stand 3 **staat nu uit en kan
  niet gekozen worden**, omdat Syntess dit veld in de praktijk nog niet betrouwbaar
  vult (ligt bij Ruud/RVS Solutions, geen ETA); activeren is een apart, later te nemen
  besluit. Fase 3/4 bouwt standen 1 en 2 echt werkend; stand 3 is een gereserveerde
  keuze zonder importlogica erachter.
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
