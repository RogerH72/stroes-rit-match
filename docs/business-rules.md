# Business Rules — Stroes-Rit-Match (RMW)

## Implemented

Gebouwd t/m roadmap-fase 3 (03-09-2026, commit `eea759c`, 143 tests groen — zie
`docs/changelog.md`):

- Tijdlijn-reconstructie per monteur per dag (`matching/timeline/engine.py`,
  `build_day()`), persistent opgeslagen in `Tijdblok`.
- Classificatie in SOORT-codes per tijdblok (K=klant, L=locatie, C=crediteur,
  W=werkbon, ?=onbekend, O=onverklaard) volgens de gevalideerde prioriteitsvolgorde:
  depot-`BekendeLocatie` (L) → eigen Uren-regel op postcode/straat (W) → overige
  `BekendeLocatie` op straat/postcode (K/L/C) → thuisadres (laten vallen) →
  tolerantiecheck (O of ?). R (reistijd) volgt uit de tussenliggende ritten. Conform
  het eindresultaat dat de klant zelf al in Excel had ontworpen; sinds fase 6
  (05-09-2026) toont het weekoverzicht deze codes ook daadwerkelijk.
- Matchingregels, gevalideerd op echte data: postcode-exact is niet genoeg →
  straatnaam-fallback; een depotbezoek vóór werk wordt herkend (op straatniveau, zie
  het aandachtspunt in `docs/database.md` en `docs/decisions.md`, 03-09-2026).
- **Het thuisadres wordt afgeleid, niet vastgelegd** (bijgesteld 07-09-2026): niemand
  registreert waar een monteur woont, dus de app leidt het af uit de eerste vertrek-
  en de laatste aankomstplaats van elke dag die hij reed. Twee soorten dagranden
  tellen daarbij níét mee: het depot (een monteur die zijn bus bij het magazijn
  ophaalt begint en eindigt daar, maar het magazijn is niemands huis) en een adres
  dat RouteVision niet heeft kunnen bepalen (`-`). Zonder die twee uitzonderingen
  belandden het depot en de placeholder tussen de "thuisstraten", waarna elke rit
  van huis naar depot, van depot naar depot en van depot naar huis werd weggegooid
  als "rondje met de bus om het huis" — en verdween het begin en einde van zo'n dag
  volledig uit de tijdlijn. Zie `docs/changelog.md` (07-09-2026).
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
- **Databronnen voor de matching (vastgelegd 2026-09-02, gebouwd 2026-09-03,
  verfijnd 2026-09-03):** van de 3 Syntess-exports drijft de matching primair op
  **Uren.xlsx** (wie, welke werkbon, welke datum, hoeveel uur, welk adres/klant) en
  de RouteVision-rit-CSV, aangevuld met **Relaties.xlsx** voor klant/
  leverancier-stamgegevens. **Werkbonnen.xlsx speelt nu ook een beperkte rol in de
  matching**, uitsluitend via de kolom **Postcode**: als vangnet ná de eigen
  geboekte uren en vóór de koppeltabel, voor het geval het adres in Uren.xlsx niet
  matcht maar de (vaak preciezere, uit de planning afkomstige) Werkbonnen-postcode
  wel — precies zoals de PoC dit ook deed. Reistijd/Werktijd/Tijd blijven, ondanks
  dat ze sinds 03-09-2026 wél worden opgeslagen (zie `docs/decisions.md`),
  ongebruikt in de matchlogica: structureel onbetrouwbaar, dus geen matchbron.
  Werkbonnen.xlsx wordt daarnaast nog steeds ingelezen voor de
  **volledigheidscontrole**: signaleren of er een werkbon bestaat zonder geboekte
  uren, op basis van de laatste/huidige Fase-status. Zie `docs/decisions.md`
  (03-09-2026) voor de volledige afweging. **Gebouwd en gemeten (03-09-2026,
  commit `37b4d71`, 149 tests groen):** het hervindingspercentage voor M5 ging op
  de voorbeeld-data van 73% naar 82% — nagenoeg gelijk aan wat de PoC op diezelfde
  week haalde. Belangrijk operationeel punt: bestaande `WerkbonControle`-rijen
  hebben pas een postcode nadat Werkbonnen.xlsx opnieuw is ingelezen (de migratie
  zelf is puur additief met lege standaardwaarden) — na elke deploy van deze
  wijziging moet `check_imports --force --reprocess` (zonder `--path`, dan pakt
  hij de echte servermap) gevolgd door `run_matching --force` gedraaid worden,
  anders blijft het vangnet stil. Zie `DRAAIBOEK.md`.
- **Ontbrekend bronbestand blokkeert alleen zijn eigen doel (vastgelegd en gebouwd
  2026-09-02):** elk bronbestand wordt onafhankelijk gevolgd. Ontbreekt
  Werkbonnen.xlsx voor een periode terwijl Uren.xlsx er wel is, dan draait de
  matching/tijdlijnreconstructie gewoon door — alleen de volledigheidscontrole wordt
  voor die periode overgeslagen.
- **"Monteur meegereden" — instelbare 3-standen toggle (verfijnd en standen 1+2
  gebouwd 2026-09-03, zie `docs/decisions.md`):** één globale instelling
  (`Instelling.meegereden_modus`) bepaalt hoe een junior monteur zijn rittijden
  krijgt toegewezen: (1) **Vast** — permanent gekoppeld aan één senior monteur
  (`Monteur.vaste_meerijder`), werkend gebouwd; (2) **Periode-/datumgebonden** — de
  `MeegeredenKoppeling`-tabel, werkend gebouwd; (3) **Uit Syntess** — gereserveerde
  keuze zonder achterliggende logica, staat uit en kan niet gekozen worden (zie
  "Designed but not implemented").
- Tolerantietabel per activiteit als instelbare `ToleranceRegel`-tabel (vervangt de
  vaste PoC-constante van 15 minuten), gebouwd met één standaardrij ("algemeen",
  15 min) als fallback. Exacte waarden per activiteit nog te bevestigen met de klant
  (zie "Designed but not implemented").
- Koppeltabellen `Monteur` en `BekendeLocatie` als bewerkbare Django-admin-modellen,
  incl. `BekendeLocatie.soort` beperkt tot K/L/C als gebruikerskeuze (zie
  `docs/database.md`).
- **Matching zelf opnieuw draaien, zonder serverdoegang (gebouwd 03-09-2026,
  fase 4, zie `docs/decisions.md`):** de matching draait niet automatisch op
  een schema — alleen `check_imports` doet dat. Tot deze build kon alleen jij/
  Claude Code de matching herberekenen, via de command line. Nu staat er een
  "Matching nu draaien"-knop in het beheerscherm (`MatchmotorStatus`), zodat
  SBTT-personeel dit zelf kan triggeren nadat ze een koppeltabel hebben
  aangepast. Draait synchroon (geen achtergrondtaken-systeem — onnodig op deze
  schaal, één klant, ruim onder een seconde).
- **Geen overlappende meegereden-periodes voor dezelfde junior (gebouwd
  03-09-2026, fase 4):** een junior monteur kan niet tegelijk aan twee
  senioren gekoppeld zijn in `MeegeredenKoppeling`. Beide grenzen tellen mee
  (dezelfde dag geldt al als overlap) en een open einddatum telt als
  onbepaald lang — consistent met hoe `geldt_op()` een koppeling al
  toepaste.

**Weergaveregels van het weekoverzicht (gebouwd 05-09-2026, roadmap-fase 6,
240 tests groen):**

- **Totaal (excl. reistijd) vs. op locatie** (label bijgesteld 07-09-2026, was
  "Gefactureerd" — de berekening is ongewijzigd) — per dag en per week wordt de som van
  `Uren.Aantal` (de in Syntess geboekte uren van die monteur op die datum)
  gezet tegenover de opgetelde duur van de **SOORT=W**-tijdblokken (de tijd dat
  de monteur volgens RouteVision daadwerkelijk op een werkbon-adres stond). Dit
  is een signaal om na te lopen, geen fout: twee bekende verklaringen zijn uren
  die op het eigen bedrijfsadres zijn geboekt (een depotstop is per definitie L,
  nooit W — zie de prioriteitsvolgorde hierboven) en uren die één persoon voor
  een heel team op zijn eigen naam boekt. Beide komen voor in de
  voorbeelddata.
- **Geen WB-vs-SYS-signaal in het scherm** — het prototype had een WB-kolom en een
  ⚑-signaal die de handmatig ingevulde werkbontijd met de RouteVision-tijd
  vergeleken. Die zijn bewust niet overgenomen; zie de regel over werktijd
  hierboven en `docs/decisions.md` (02-09-2026).
- **Een week is nooit stil onvolledig** — alleen dagen met een gereconstrueerde
  tijdlijn tellen mee in de dag- en weektotalen. Werkdagen (ma t/m vr) zonder
  tijdlijn worden apart gemeld, met de uren die er wél op geboekt zijn; die uren
  blijven buiten het weektotaal, omdat ze anders zouden worden afgezet tegen
  W-blokken die niet bestaan. Dagen die nog moeten komen (later deze week) tellen
  niet als ontbrekend, en weekenddagen worden alleen getoond als er ritdata voor
  is.
- **Uren worden per datum opgeteld, niet per werkbon** — een monteur boekt
  regelmatig meerdere werkbonnen op één dag; de vergelijking gaat over de dag als
  geheel.

## Designed but not implemented

- **"Monteur meegereden", stand 3 (Uit Syntess)** — leest de kolom "Monteur
  meegereden" in de Werkbonnen-export rechtstreeks uit. Staat nu uit en kan niet
  gekozen worden, omdat Syntess dit veld in de praktijk nog niet betrouwbaar vult
  (ligt bij Ruud/RVS Solutions, geen ETA); activeren is een apart, later te nemen
  besluit en vereist bovendien een uitbreiding van `WerkbonControle` met dat veld.
- Exacte tolerantiewaarden per activiteit — nog te bevestigen met de klant (bron:
  `20260424 RMW-Overzicht ....xlsx` in de brainstorm-sessie); de tabel en het
  mechanisme zijn al gebouwd, alleen met de standaardwaarde.
- **Klant/leverancier-onderscheid** — was een open datavraag, maar wordt bij de bron
  opgelost: Ruud (RVS Solutions) gaat dit onderscheid zelf aan de Relaties-export
  toevoegen. Mogelijk hoeft de app dit dan niet meer zelf via een koppeltabel af te
  leiden — te bevestigen zodra de aangepaste export er is.
- Meerwerk: snelheidscontrole per locatie (RouteVision-snelheid vs.
  maximumsnelheid) — op 05-09-2026 vastgelegd als een aparte, later apart te
  offreren fase, buiten deze roadmap. Zie `docs/decisions.md`.
- **SOORT-classificatie P (Privé)** — besloten 07-09-2026 (avond), vierde keuze
  op `BekendeLocatie.soort` naast K/L/C, zelfde koppelmechanisme als het
  uitzonderingenscherm nu al biedt. Telt niet mee in "Totaal (excl. reistijd)",
  krijgt een eigen regel in het weekoverzicht. Kleur in het codepalet aan
  Claude Code overgelaten, binnen de bestaande paletlogica. Zie
  `docs/decisions.md` en `docs/functioneel-ontwerp.md` §5/§6.

## Superseded

Nog geen.
