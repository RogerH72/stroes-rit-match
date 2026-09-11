# Business Rules — Stroes-Rit-Match (RMW)

## Implemented

Gebouwd t/m roadmap-fase 3 (03-09-2026, commit `eea759c`, 143 tests groen — zie
`docs/changelog.md`):

- Tijdlijn-reconstructie per monteur per dag (`matching/timeline/engine.py`,
  `build_day()`), persistent opgeslagen in `Tijdblok`.
- Classificatie in SOORT-codes per tijdblok (K=klant, L=locatie, C=crediteur,
  P=privé en T=thuis (beide 07-09-2026),
  W=werkbon, ?=onbekend, O=onverklaard) volgens de gevalideerde prioriteitsvolgorde:
  depot-`BekendeLocatie` (L) → eigen Uren-regel op postcode/straat (W) → overige
  `BekendeLocatie` op straat/postcode (K/L/C/P/T) → het thuisadres van de monteur
  (T, sinds 07-09-2026 opgeslagen in plaats van laten vallen) →
  tolerantiecheck (O of ?). R (reistijd) volgt uit de tussenliggende ritten. Conform
  het eindresultaat dat de klant zelf al in Excel had ontworpen; sinds fase 6
  (05-09-2026) toont het weekoverzicht deze codes ook daadwerkelijk.
- Matchingregels, gevalideerd op echte data: postcode-exact is niet genoeg →
  straatnaam-fallback; een depotbezoek vóór werk wordt herkend (op straatniveau, zie
  het aandachtspunt in `docs/database.md` en `docs/decisions.md`, 03-09-2026).
- **Het thuisadres wordt ingevuld, niet afgeleid** (vastgelegd 07-09-2026, na twee
  eerdere bijstellingen dezelfde dag): elke monteur heeft een eigen veld
  `thuisadres` op `Monteur`, met dezelfde precisiekeuze als een `BekendeLocatie`
  (straatnaam of postcode, straat als voorkeur). Een stop op dat adres krijgt
  **SOORT T (Thuis)** en staat gewoon in de tijdlijn.
  De eerdere aanpak — afleiden uit de eerste vertrek- en laatste aankomstplaats van
  elke gereden dag — is volledig vervallen, zonder terugval. Die detectie kon een
  toevallige dagrand niet onderscheiden van een echt tweede adres, en elke misser
  gooide stilzwijgend ritten weg: ritten waarvan vertrek én aankomst allebei als
  "thuis" golden werden geschrapt als "rondje met de bus om het huis". Op de
  juni-dataset kostte dat 28 ritten over 12 dagen, waarvan tweemaal een volledige
  werkdag (Dennis van de Berg, 24 en 25 juni, met 8 geboekte uren en nul
  tijdblokken). Zie `docs/changelog.md` (07-09-2026).
- **"Bestanden nu inlezen"** (gebouwd 08-09-2026) — derde knop op het
  matchmotor-beheerscherm, naast "Matching nu draaien" en "Data resetten".
  Roept `scan_share(force=True)` aan: leest direct in wat er klaarstaat, zonder
  de stabiliteitsmarge af te wachten. Geen reprocess van al-verwerkte bestanden
  (dat blijft command-line-only) en geen automatische matching erna — inlezen en
  herberekenen blijven twee aparte, bewuste stappen (docs/decisions.md,
  08-09-2026).
- **"Bestanden uploaden"** (gebouwd 09-09-2026) — vierde knop op hetzelfde
  scherm, onder de andere drie. Terugval voor zolang de netwerkshare niet
  werkt: de gekozen bestanden worden onder hun eigen naam in diezelfde
  servermap gezet en meteen ingelezen. **Alleen de zojuist geüploade bestanden
  worden ingelezen** (`import_named_files()`, gecorrigeerd 11-09-2026, zie
  `docs/decisions.md`): de stabiliteitsmarge overslaan is te verdedigen voor een
  bestand dat compleet over HTTP is binnengekomen, maar niet voor wat er verder
  toevallig in de inbox ligt. Dat blijft ongemoeid en houdt zijn eigen
  pollingschema. Een naam
  die daar al staat wordt geweigerd en nooit overschreven; een naam die
  `classify_filename()` niet herkent wordt eveneens geweigerd. Beide
  weigeringen gelden per bestand — de rest van de batch gaat door. Geen
  automatische matching erna, en geen opruiming van geüploade bestanden: ze
  blijven op de servermap staan als elk ander ingelezen bestand
  (docs/decisions.md, 09-09-2026). Het formulier staat sinds 09-09-2026
  bovenaan het scherm, in een eigen blok boven de andere drie: zolang de
  servermap niet werkt is dit de enige manier om data in de app te krijgen.
- **Importbestanden alleen-lezen** (gebouwd 09-09-2026) — `ImportedFile` is in
  de admin niet meer toe te voegen, te wijzigen of te verwijderen, net als de
  vier importtabellen en `Tijdblok`. Deze tabel is geen kopie van de servermap
  maar de administratie waar `scan_share()` en de matching op afgaan; een
  handmatig op "verwerkt" gezette status zou de app een bestand laten overslaan
  dat nooit is ingelezen. Herverwerken blijft daarmee volledig
  command-line-only (`check_imports --reprocess`) of gaat via "Data resetten"
  (docs/decisions.md, 09-09-2026).
- **Ingest-robuustheid tegen niet-schemaconforme Atrium-XML en
  kolomnaam-hoofdletters** (gebouwd 08-09-2026) —
  `matching/ingest/parsers/base.py` repareert drie bekende niet-conforme
  XML-tokens (`WindowWidth`/`WindowHeight`/`firstPageNo`) in een kopie in het
  geheugen vóór het inlezen — het bestand op de servermap wordt nooit
  overschreven — en beide readers matchen kolomnamen hoofdletterongevoelig
  (exacte naam gaat vóór). Geldt voor alle vier bronbestanden. Een bestand dat
  al conform is gaat ongewijzigd door; een écht ontbrekende kolom levert nog
  steeds een `ParseError` (docs/decisions.md, 08-09-2026).
- **Klant/leverancier-suggestie bij het koppelformulier** (gebouwd
  08-09-2026) — matcht de postcode van een onverklaarde groep tegen
  `Relatie.postcode` (aan beide kanten genormaliseerd, want `Relatie.postcode`
  staat ruw uit Excel in de database). Eén relatie op die postcode → soort en
  label voorgevuld; meerdere → een keuzelijst, pas na een keuze voorgevuld;
  geen → formulier blijft leeg. Het blijft een suggestie: er wordt niets
  opgeslagen tot de gebruiker zelf op "Koppelen" drukt. **Lettermapping:**
  Relatie "K" (Klant) → SOORT **K**, Relatie "L" (Leverancier) → SOORT **C**
  (Crediteur) — nooit SOORT "L", want dat betekent Locatie. Een lege of
  onbekende letter levert geen suggestie op. Matching op huisnummer is niet
  mogelijk: `normalize.street()` knipt het huisnummer bewust af, dus een
  postcode die meerdere panden dekt kan de verkeerde relatie voorstellen — de
  gebruiker ziet de suggestie en kan ervan afwijken.
- **Een monteur zonder ingevuld thuisadres krijgt geen gok.** Zijn ochtend- en
  avondstops doorlopen gewoon de rest van de prioriteitsvolgorde en eindigen
  meestal als O (onverklaard) — zichtbaar en corrigeerbaar via het
  uitzonderingenscherm, in plaats van onzichtbaar fout. Staat de bus om de hoek in
  plaats van op het huisadres, dan is dat adres daar als T te koppelen.
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
  **Alleen urenregels mét een werkbonnummer doen mee aan de werkbon-matching
  (gecorrigeerd 11-09-2026, zie `docs/decisions.md`):** een `Uren`-regel zonder
  werkbonnummer (kantoor, verlof, reisuren, magazijnonderhoud — ruim de helft
  van de urenregels in de juni-data) komt niet in de matchindex. Zo'n regel
  hoort bij geen enkele werkbon, dus kan een stop er ook niet aan toegewezen
  worden; de stop valt door naar de volgende stappen (koppeltabel, thuis,
  onverklaard). Dit maakt de code gelijk aan wat de aansluitingstabel hieronder
  al als regel noemde ("die kunnen per definitie geen W-blok opleveren").
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
- **Een herberekening ruimt vervallen dagen op binnen zijn eigen selectie
  (gebouwd 11-09-2026, zie `docs/decisions.md`):** een expliciete herberekening
  (de knop "Matching nu draaien", of `run_matching --force`) verwijdert niet
  alleen de dagen die hij opnieuw opbouwt, maar ook de al opgeslagen dagen die
  géén resultaat meer opleveren — een junior die van zijn meerijderkoppeling is
  losgekoppeld, of een dag waarvan de ritten door een gecorrigeerde import zijn
  verdwenen. Zonder deze opruiming bleven die dagen met hun oude tijdblokken in
  het weekoverzicht en het uitzonderingenscherm staan terwijl de run "gelukt"
  meldde. De grens is de gevraagde selectie: een herberekening voor één monteur
  raakt geen andere monteur, en een herberekening over een datumrange raakt geen
  dag erbuiten. Een run zonder `--force` verwijdert niets — die laat bestaande
  dagen juist met rust — en een `--dry-run` meldt ze alleen.
- **Geen overlappende meegereden-periodes voor dezelfde junior (gebouwd
  03-09-2026, fase 4):** een junior monteur kan niet tegelijk aan twee
  senioren gekoppeld zijn in `MeegeredenKoppeling`. Beide grenzen tellen mee
  (dezelfde dag geldt al als overlap) en een open einddatum telt als
  onbepaald lang — consistent met hoe `geldt_op()` een koppeling al
  toepaste.

**Weergaveregels van het weekoverzicht (gebouwd 05-09-2026, roadmap-fase 6,
240 tests groen):**

- **Aansluiting per werkbon** (07-09-2026) — onder elk dagoverzicht staat een
  tabel met één regel per werkbon die die dag voorkomt: de vereniging van de
  werkbonnen in `Uren.xlsx` en die van de SOORT=W-tijdblokken, niet het snijvlak.
  Per regel: **Op locatie** (opgetelde duur van de SOORT=W-tijdblokken met dat
  werkbonnummer die dag), **Gedeclareerd** (som van `Uren.Aantal` voor die
  werkbon/datum) en het verschil. Álle werkbonnen van de dag krijgen een regel,
  ook de kloppende: een werkbon met uren maar zonder enkel W-blok is het
  scherpste signaal dat deze tabel kan geven, en die zou onzichtbaar zijn als
  "geen regel" ook "geen probleem" kon betekenen.
  Twee regels vallen buiten het werkbon-stramien. **"Klant (niet aan werkbon
  gekoppeld)"** draagt de totale SOORT=K-duur van die dag: een `BekendeLocatie`
  met SOORT K heeft nergens in de data een werkbonnummer, dus daar hoort geen
  gedeclareerd-cijfer bij. **"Zonder werkbonnummer (indirect)"** draagt de uren
  die in `Uren.xlsx` géén werkbonnummer hebben (kantoor, verlof, reisuren,
  magazijnonderhoud); die kunnen per definitie geen W-blok opleveren. Een
  ontbrekende kant wordt als "–" getoond, niet als 0,00 — de vraag is daar niet
  van toepassing, in plaats van gesteld en leeg teruggekomen.
  Het dagtotaal onderaan telt W én K op tegenover alle geboekte uren van die dag,
  en is daarmee het antwoord op de vraag waarvoor deze tabel er is: is er tijd
  besteed die nergens op gedeclareerd is. **L (Locatie) en C (Crediteur) tellen
  bewust niet mee** — dit gaat over aan een klant gekoppelde uren.
  Niet te verwarren met de volledigheidscontrole op `Werkbonnen.xlsx` (besluit
  02-09-2026): die kijkt over de hele levensloop van een werkbon of een afgeronde
  werkbon ooit uren kreeg. Deze aansluiting vergelijkt per dag twee al aanwezige
  bronnen, alleen per werkbon in plaats van geblendet.
- **Klantnaam bij "Aansluiting per werkbon"** (08-09-2026) — een extra
  kolom Klant, direct naast de werkbonnummer-kolom, met
  `Uren.project_opdrachtgever_naam` voor exact die (datum, werkbon).
  Alleen de werkbon-rijen krijgen een naam; KLANT/INDIRECT/totaal tonen
  een streepje, net als de rest van de tabel. Geen opzoekactie op een
  andere datum van dezelfde werkbon — een werkbon die alleen via de
  Werkbonnen.xlsx-postcode-vangnet is gematcht toont dus ook een
  streepje. Aandachtspunt (nog open, zie `docs/decisions.md`): hoe vaak
  dat laatste voorkomt is nog te bekijken op echte data.
- **Totaal (excl. reistijd) vs. op locatie** (label bijgesteld 07-09-2026, was
  "Gefactureerd" — de berekening is ongewijzigd; deze regel blijft naast de
  aansluitingstabel hierboven bestaan als snel totaalcijfer) — per dag en per week wordt de som van
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
- **Zelfkoppeling-check op `Monteur.vaste_meerijder`.** Gelijkgetrokken met
  de al bestaande check op `MeegeredenKoppeling` (junior != senior): een
  monteur mag zichzelf niet als vaste meerijder kiezen. `CheckConstraint` +
  `clean()`-validatie (docs/decisions.md, 08-09-2026; commit `bcd57af`).

## Designed but not implemented

- **"Monteur meegereden", stand 3 (Uit Syntess)** — leest de kolom "Monteur
  meegereden" in de Werkbonnen-export rechtstreeks uit. Staat nu uit en kan niet
  gekozen worden, omdat Syntess dit veld in de praktijk nog niet betrouwbaar vult
  (ligt bij Ruud/RVS Solutions, geen ETA); activeren is een apart, later te nemen
  besluit en vereist bovendien een uitbreiding van `WerkbonControle` met dat veld.
- Exacte tolerantiewaarden per activiteit — nog te bevestigen met de klant (bron:
  `20260424 RMW-Overzicht ....xlsx` in de brainstorm-sessie); de tabel en het
  mechanisme zijn al gebouwd, alleen met de standaardwaarde.
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
