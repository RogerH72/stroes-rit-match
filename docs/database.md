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
- **WerkbonControle** (uit `Werkbonnen.xlsx`, **uitsluitend voor de
  volledigheidscontrole, geen input voor de matching zelf** — zie
  `docs/business-rules.md`): Werkbon, Medewerker, Datum, laatste/huidige Fase-status.
  Reistijd/Werktijd/Titel/Monteur meegereden uit dit bestand worden niet opgeslagen.
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

Voorzien voor later (roadmap-fase 4/5): een "bekende-locaties"-koppeltabel (onthoudt
handmatig bevestigde locatiekoppelingen, zodat het uitzonderingenlijstje elke week
korter wordt). PoC-opslag: csv-koppelbestand. Productie-opslag: tabel in de database
(Django-admin).

## Known limitations / deprecated fields

Nog geen.
