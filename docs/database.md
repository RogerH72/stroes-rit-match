# Database — Stroes-Rit-Match (RMW)

## Tables

_Bijgewerkt 2026-09-02, na inspectie van de voorbeeld-databestanden in
`voorbeeld-data/` (echte, geanonimiseerde Syntess/RouteVision-exports). Dit betreft
het functionele niveau voor roadmap-fase 2 (data-inlezing): welke ruwe importtabellen
er komen en waarvoor, niet de definitieve Django-veldtypen — dat is een technische
uitwerking voor de Claude Code-sessie. Fase 2 slaat de bronbestanden 1-op-1 op; de
tijdlijnreconstructie/matchresultaten zelf zijn roadmap-fase 3 en hier nog niet
uitgewerkt._

Voorzien voor fase 2 (ruwe import, één tabel per bronbestand):

- **Uren** (uit `Uren.xlsx`, hoofdbron voor de matching): Medewerker, Naam, Werkbon,
  Datum, Aantal (uren), Taak code, Taak omschrijving, Project opdrachtgever naam,
  Postcode, Plaats, Adres, Begintijd, Eindtijd.
- **Rit** (uit de RouteVision-CSV, hoofdbron voor de matching): Kenteken, Bestuurder,
  Reis van de dag (volgnummer), Reistype, Vertrekdatum/-tijd/-adres/-plaats,
  Aankomstdatum/-tijd/-adres/-plaats, Duur, km-opsplitsing (privé/zakelijk/
  woon-werk + CO2), Maximumsnelheid (+ locatie/tijd/stad van die meting),
  Eindstand, Opmerking.
- **Relatie** (uit `Relaties.xlsx`): Code, Relatienaam, Postcode, Huisnr, E-mail,
  Telefoon — klant/leverancier-stamgegevens.
- **WerkbonControle** (uit `Werkbonnen.xlsx`, **primair voor de
  volledigheidscontrole** — zie `docs/business-rules.md`): Werkbon, Medewerker,
  Datum, laatste/huidige Fase-status, Postcode. **Sinds 03-09-2026 (zie
  `docs/decisions.md`) ook Titel, Tijd, Reistijd en Werktijd.** Van deze velden
  wordt alleen **Postcode** in de matching zelf gebruikt, als vangnet ná de eigen
  geboekte uren en vóór de koppeltabel (zie `matching/timeline/engine.py`); Titel
  is alleen omschrijvingstekst wanneer dat vangnet raak is. Tijd, Reistijd en
  Werktijd worden bewaard maar blijven ongebruikt in de matchlogica — ze zijn
  structureel onbetrouwbaar (bevestigd door Wim), maar bronbestanden worden nooit
  verwijderd van de servermap, dus meelezen nu kost niets en voorkomt een latere
  nieuwe uitleesronde als er ooit alsnog een reden blijkt. Ook **Monteur
  meegereden** wordt sinds 03-09-2026 opgeslagen, ongebruikt en gereserveerd voor
  wanneer stand 3 van de meegereden-toggle ooit apart geactiveerd wordt (zie
  `docs/decisions.md`, 03-09-2026).
  Opslag blijft op het brongrofste niveau: één rij per (Werkbon, Medewerker, Datum),
  omdat een werkbon over meerdere data kan lopen (bijv. Uitgevoerd op de ene dag,
  Gereed op de volgende) — de fase-status wordt per werkbon over al zijn rijen heen
  afgeleid en op elke datumregel van die werkbon gezet. **De volledigheidscontrole
  zelf (fase 3) beoordeelt straks de werkbon als geheel, niet per losse datum**
  (vastgelegd 2026-09-02, zie `docs/functioneel-ontwerp.md` §3b) — de datumregels
  blijven alleen bewaard omdat dat de brongranulariteit is. Gebouwde modelnaam:
  `ImportedFile`/de vier importmodellen zijn in het Engels (generieke technische
  tabellen, geen SBTT-domeinterm, dus toegestaan binnen de taalconventie) — deze
  functionele namen (Uren/Rit/Relatie/WerkbonControle) blijven de leidende
  beschrijving hier.
- **ImportBestand** (gebouwd als `ImportedFile` — Engelse naam, zie toelichting
  hierboven; technische bijhoudtabel voor het trigger-mechanisme uit
  `docs/architecture.md`): bestandsnaam, laatst gemeten bestandsgrootte, tijdstip
  laatste meting, status (wachtend op stabiliteit / stabiel / verwerkt), tijdstip
  verwerkt. Nodig om de stabiliteitscheck (bestandsgrootte 30 minuten ongewijzigd,
  bij een polling-interval van 5 minuten dus 6 metingen op rij — beide apart
  instelbaar, zie `docs/architecture.md`) iets te geven om de vorige meting in te
  bewaren, vóórdat er in fase 3 matchresultaten bestaan om "al verwerkt" aan af te
  leiden. **Elk bronbestand (Uren/Rit/Relatie/WerkbonControle) wordt hierin
  onafhankelijk gevolgd** (vastgelegd 2026-09-02): ontbreekt bijvoorbeeld
  Werkbonnen.xlsx voor een periode terwijl Uren.xlsx er wel is, dan draait de matching
  (die niet op Werkbonnen.xlsx leunt) gewoon door — alleen de volledigheidscontrole
  wordt voor die periode als "niet uitgevoerd, bronbestand ontbrak" gemarkeerd. Zie
  `docs/functioneel-ontwerp.md` §3a.

## Voorzien voor fase 3/4 (matchmotor + koppeltabellen)

_Vastgelegd 2026-09-03, vooruitlopend op de bouw van roadmap-fase 3. Op verzoek van
Roger worden de koppeltabellen die de matchmotor nodig heeft (personeelsnummer↔naam,
bekende locaties, meegereden-instelling, tolerantietabel) nu al als echte
modellen gebouwd, in plaats van pas in fase 4 — zie `docs/decisions.md`
(03-09-2026). Fase 4 verfijnt daarna vooral de admin-schermen (UX, het
uitzonderingen-eenklik-scherm), niet de tabellen zelf._

**Koppeltabellen:**

- **Monteur** — koppelt de twee identificatiesystemen die de bronbestanden gebruiken:
  het Syntess-personeelsnummer (`Uren.Medewerker`) en de RouteVision-bestuurderscode
  (`Rit.Bestuurder`), plus naam en kenteken. Zonder deze koppeling kunnen `Uren` en
  `Rit` niet eens bij elkaar gelegd worden — dit is de eerste, noodzakelijke schakel
  voor de matching.
- **Monteur** heeft sinds 07-09-2026 `thuisadres` + `thuisadres_type` (dezelfde
  precisiekeuze als `BekendeLocatie`: straat of postcode, straat als voorkeur, en
  dezelfde normalisatie via `matching/timeline/normalize.py`). Beide optioneel —
  een leeg thuisadres matcht niets. Vervangt het afleiden van het thuisadres uit
  de ritdata, dat volledig is vervallen (zie `docs/business-rules.md`).
- **BekendeLocatie** — postcode/straat → SOORT + label. Vervangt het
  demo-koppelbestand (`locaties_demo.csv`) uit de PoC. **`soort` is een keuzeveld met
  uitsluitend K (Klant), L (Locatie), C (Crediteur), P (Privé) of T (Thuis) als opties** — dit zijn de
  SOORT-codes die een gebruiker aan een adres kan toekennen. W, ? , O en R volgen
  altijd automatisch uit de matchlogica zelf (W = matcht een werkbon, ? = korte
  onbekende stop, O = onverklaarde stop boven de drempel, R = reistijd) en zijn dus
  geen keuzemogelijkheid in deze tabel. Gebruikers vullen deze tabel via het
  uitzonderingenscherm (fase 5) of rechtstreeks via de beheerschermen (fase 4).
- **Instelling** — één rij (singleton) met configuratie die niet per record maar voor
  de hele app geldt. Bevat vooralsnog `meegereden_modus`: VAST / PERIODE / SYNTESS
  (zie hieronder en `docs/decisions.md`, 03-09-2026).
- **MeegeredenKoppeling** — junior-monteur, senior-monteur, geldig-van, geldig-tot.
  Gebruikt wanneer `Instelling.meegereden_modus = PERIODE`. Voor `meegereden_modus =
  VAST` volstaat een eenvoudig zelf-verwijzend veld op `Monteur`
  (`vaste_meerijder`). `meegereden_modus = SYNTESS` is een gereserveerde keuze zonder
  achterliggende logica — die vereist eerst een uitbreiding van `WerkbonControle` met
  het Syntess-veld "Monteur meegereden", wat nu bewust niet wordt opgeslagen (zie
  `docs/decisions.md`, 02-09-2026).
- **ToleranceRegel** — activiteit (vrije sleutel, met een standaardrij "algemeen") →
  drempel in minuten voor wat nog telt als een "onverklaarde" stop. Vervangt de vaste
  `DREMPEL`-constante (15 minuten) uit de PoC door een instelbare tabel. Exacte
  waarden per activiteit liggen nog niet vast — te bevestigen met de klant (zie
  `docs/functioneel-ontwerp.md` §9, punt 2); de tabel start met alleen de
  standaardwaarde 15 min.

**Matchresultaat:**

- **Tijdblok** — de gereconstrueerde tijdlijn per monteur per dag: monteur, datum,
  volgorde binnen de dag, SOORT-code, starttijd, eindtijd, duur in minuten,
  omschrijving, adres, en (bij SOORT=W) een verwijzing naar de werkbon. Persistent
  opgeslagen — niet elke paginaweergave herberekend — zodat fase 5 (uitzonderingen)
  en fase 6 (weekoverzicht) op stabiele data kunnen bouwen. Herberekenen gebeurt
  expliciet via een management-command (`run_matching`, zelfde patroon als
  `check_imports`), o.a. nodig nadat een koppeltabel is aangepast.
  **Bevat geen WB-vs-SYS-signaalveld** — dat onderdeel van de PoC is bewust niet
  gebouwd (zie `docs/decisions.md`, 02-09-2026).
  **`postcode`/`straat`** (gebouwd 03-09-2026, fase 5) — de genormaliseerde
  matchsleutels van de stop, apart opgeslagen naast de samengestelde `adres`-tekst
  (die alleen voor weergave dient). Het uitzonderingenscherm groepeert en telt
  hierop; bestaande rijen hebben deze velden pas na een `run_matching --force`
  (zie `docs/decisions.md`, 03-09-2026).
- **MatchmotorStatus** (gebouwd 03-09-2026, fase 4, zie `docs/decisions.md`) —
  singleton, zelfde patroon als `Instelling`: wanneer de matching voor het
  laatst gestart/afgerond is, of dat gelukt is (`succes=None` betekent "nog
  nooit gedraaid", een ander signaal dan `False`), hoeveel monteur-dagen
  herberekend zijn, en een eventuele foutmelding. Wordt bijgewerkt door zowel
  het `run_matching`-commando als de "Matching nu draaien"-knop in het
  beheerscherm — een `--dry-run` telt bewust niet mee, want die schrijft niets
  weg.

**Geen aparte tabel, wel een berekening:** de volledigheidscontrole
(Werkbonnen.xlsx-check, zie `docs/business-rules.md`) heeft geen eigen tabel nodig —
het is een service-functie die `WerkbonControle`-rijen per werkbon beoordeelt (op
basis van de al opgeslagen fase-status) en op aanvraag (bijv. bij het weekoverzicht)
het resultaat teruggeeft.

**Het weekoverzicht (fase 6, 05-09-2026) voegt géén tabellen of velden toe.** Het
leest de al opgeslagen `Tijdblok`-rijen en telt daar per dag en per week de minuten
per SOORT bij op; de "Totaal (excl. reistijd)"-kant (tot 07-09-2026
"gefactureerd" genoemd) is een `Sum` over `Uren.aantal` per datum,
op het moment van weergave berekend. Bewust niet opgeslagen: het is een afgeleide van
data die al in de database staat, en opslaan zou een tweede waarheid introduceren die
na elke `run_matching` bijgewerkt moet blijven. `Tijdblok` kreeg er in deze fase één
afgeleide property bij (`koppelsleutel`, postcode-eerst met straat als fallback) —
geen kolom, alleen de gedeelde regel waarmee zowel het uitzonderingenscherm als het
weekoverzicht een stop adresseren.

## Known limitations / deprecated fields

- **Straat-niveau depotrisico (sinds fase 3, 03-09-2026).** De depotprioriteitsregel
  op `BekendeLocatie.is_depot` werkt op straatniveau: een depotadres claimt élk adres
  op diezelfde straat vóór een werkbonmatch. Dit is het gevalideerde PoC-gedrag, geen
  bug, maar een aandachtspunt bij het invoeren van het echte SBTT-depotadres in fase
  4. Zie `docs/decisions.md` (03-09-2026).
- **`Instelling.delete()` alleen op instance-niveau geblokkeerd (sinds fase 3,
  03-09-2026).** De `clean()`/`save()`/`delete()`-overrides op het singleton-model
  `Instelling` voorkomen normaal verwijderen, maar een
  `Instelling.objects.all().delete()` op queryset-niveau omzeilt dat (Django roept
  `delete()` op individuele instances niet aan bij een bulkdelete via een queryset).
  Geaccepteerd, laag risico: geen UI-pad biedt een bulkdelete op `Instelling` aan, en
  de DB-`CheckConstraint` voorkomt hoe dan ook meer dan één rij. Zie
  `docs/decisions.md` (03-09-2026).
