# Demo — Stroes-Rit-Match (RMW) — PoC

## Demo purpose

Valideren of automatische matching tussen Syntess-werkbonnen en RouteVision-ritdata
betrouwbaar genoeg is om SBTT objectief inzicht te geven in afwijkingen, vóórdat een
onderbouwde offerte voor de volledige app wordt opgesteld.

## Target audience

Wim Stroes / Stroes Bouw en Techniek (SBTT) — als besluitvormer voor een go/no-go op de
volledige app.

## Scenario

1-2 monteurs worden gevolgd over ongeveer één week. Voor elke werkdag worden de 3
dagelijkse Syntess Excel-exports en de RouteVision-download ingelezen, wordt een
dagtijdlijn per monteur gereconstrueerd, en wordt een weekoverzicht opgeleverd met
SOORT-codes (K=klant, L=locatie, C=crediteur, W=werkbon, ?=onbekend, O=onverklaard,
R=reistijd) en afwijkingen t.o.v. tolerantie — zoals de klant dat zelf al in Excel had
voorgesteld.

## Current scope

- Bestand-in/bestand-uit: 3 Syntess Excel-exports (automatisch, servermap) +
  RouteVision-download (handmatig).
- Matching op basis van straatnaam-fallback wanneer postcode niet exact matcht;
  depot-vóór-werk-regel.
- Weekoverzicht per monteur als Excel/HTML-output.
- Instelbare drempel voor onverklaarde stops.

## Explicit out-of-scope

- Geen productiestack-keuze (geen Django, geen database) tijdens de PoC.
- Geen betaalde Syntess-API-koppeling.
- Geen automatische RouteVision-API-koppeling (nog handmatige download).
- Het snelheidscontrole-meerwerk — apart traject; op 05-09-2026 vastgelegd als een
  aparte, later apart te offreren fase (zie `docs/decisions.md`).
- Geen volledige vervanging van het bestaande Access-programma; wel een
  tijdwinst-indicatie zoals Wim expliciet wil zien.

## Current demo priorities

1. **Gedaan (26-08-2026).** De 3 Syntess-exports, de Ritten-CSV en de
   RouteVision-PDF zijn beoordeeld op aanwezige velden en gebruikt in een
   PoC-matchrun op monteur M5 (week 3–7 aug 2026); bevindingen staan in
   `D:\STROES\PoC-demo\RMW_PoC_bevindingen.html`. Het go/no-go-punt is
   hiermee beantwoord: het matchingsconcept werkt op echte data (9 van de 11
   werkbonnen automatisch teruggevonden, tijden kloppen waar gematcht).
2. **Vervallen (01-09-2026).** Een live-PoC-fase met 1-2 monteurs bij de klant was
   hier voorzien als volgende stap, maar het akkoord van Wim (31-08-2026) betrof al de
   volledige offerte voor de complete app — deze stap is niet uitgevoerd en ook niet
   meer gepland als aparte offerte-stap. Zie `docs/decisions.md` (01-09-2026).
3. **Gedaan (01-09-2026).** Bredere technische validatie: 2 monteurs (Jesse Verkerk,
   Dennis van de Berg) over 4 weken (W30 t/m W33, 20 juli-16 aug 2026), op nieuwe
   RouteVision-downloads gecombineerd met de bestaande Syntess-exports, geanonimiseerd
   via `D:\STROES\anonimiseer_stroes.py`. Matching met de ongewijzigde heuristiek uit
   `rmw_sbtt.py`, generiek gemaakt in
   `D:\STROES\Validatie-W30-W33\geanonimiseerd\validatie_2monteurs_4weken.py`.
   Resultaat: Jesse Verkerk 29/37 werkbonnen automatisch teruggevonden (78%, 18
   werkdagen), Dennis van de Berg 28/30 (93%, 16 werkdagen — W33 bleek een
   vakantieweek). Vergelijkbaar met of beter dan de eerdere M5-week (82%). Gemiste
   werkbonnen blijven verklaarbaar via hetzelfde bekende patroon
   (werkbon-adres vs. straat/postcode-suffix in de RouteVision-data); één
   recidiverende klant kwam twee keer voor met dezelfde mismatch. Nieuwe observatie:
   het verschil tussen gefactureerde en "op locatie"-uren is bij Jesse Verkerk
   relatief groter (~37%) dan in de eerdere validatie (~11%) — geen matchingprobleem,
   wel een aandachtspunt voor de bouwfase (onvolledige/niet-aansluitende GPS-tracks).
   Zie `docs/decisions.md` (01-09-2026). Dit was de laatste stap vóór de bouw; de
   kwalitatieve go/no-go is positief.
4. De tijdwinst t.o.v. het bestaande Access-programma inzichtelijk maken — nu relevant
   voor de bouwfase.

## Demo-specific blockers

- Geen blocker meer op de voorbeeldbestanden: deze staan al in `D:\STROES`
  en zijn al gebruikt voor een matchrun (zie "Current demo priorities"
  hierboven). Bekende datakwirks uit die run (velden vaak leeg, geen
  klant/leverancier-onderscheid in de Relaties-export, naamformaat verschilt
  tussen bronnen) zijn gedocumenteerd in `RMW_PoC_bevindingen.html` en hebben
  al een aanpak in de PoC-logica.
- Exacte tolerantiewaarden per activiteit nog te bevestigen met de klant (bron:
  `20260424 RMW-Overzicht ....xlsx` in de brainstorm-sessie).
