# Functioneel Ontwerp — Stroes-Rit-Match (RMW)

_Vastgelegd: 2026-09-02. Bijgewerkt 2026-09-02 na inspectie van de
voorbeeld-databestanden (§2/§3b) en na een robuustheidscheck van de bestandsdetectie
(§3a) — zie `docs/decisions.md`. Dit document beschrijft hoe RMW straks functioneel
werkt — niet hoe het technisch gebouwd wordt (zie `docs/architecture.md`) en niet in
de precieze, terse regel-vorm van `docs/business-rules.md`. Het is bedoeld als
leesbaar naslagwerk: wat doet de app, voor wie, en wat gebeurt er stap voor stap.
Waar een onderdeel nog niet is uitontworpen, staat dat expliciet vermeld — er wordt
hier niets verzonnen._

## 1. Wat de app doet

RMW vergelijkt per monteur en per werkdag de werkbonnen uit Syntess met de rit-, tijd-
en locatiegegevens uit RouteVision. Doel: automatisch signaleren of een werkbon door de
feitelijke rit wordt bevestigd, en afwijkingen (onverklaarde stops, adres-mismatches,
afwijkende reistijden) zichtbaar maken. Geen simpele 1-op-1 koppeling (werkbon A ↔ rit
A), maar een reconstructie van de hele dagtijdlijn per monteur, waarna die tijdlijn
wordt vergeleken met wat er in Syntess is geregistreerd.

Voor de klant (Stroes Bouw en Techniek, contactpersoon Wim Stroes) vervangt dit een
bestaand, handmatig Access-programma.

## 2. Databronnen

De app leest uitsluitend bestanden die op een servermap verschijnen — geen directe
koppeling (API) met Syntess of RouteVision in deze versie. Er zijn 3 dagelijkse
Syntess Excel-exports plus de RouteVision-download, maar niet alle 3 Syntess-exports
worden voor de matching gebruikt:

- **Uren.xlsx** (hoofdbron): wie, welke werkbon, welke datum, hoeveel uur, en op welk
  adres/bij welke klant. Dit is de eenheid die tegen de RouteVision-rit van die dag
  wordt gelegd.
- **RouteVision-download** (hoofdbron): rit-, tijd- en locatiegegevens per
  monteur/voertuig. Het dagelijks plaatsen van dit bestand in de servermap is een
  taak van SBTT/Stric, niet van de app of van Roger.
- **Relaties.xlsx**: klant/leverancier-stamgegevens, los van de matching zelf nodig.
- **Werkbonnen.xlsx**: wordt ingelezen voor een **volledigheidscontrole** —
  signaleren of er een werkbon bestaat zonder geboekte uren (zie §3b). Sinds
  03-09-2026 (zie `docs/decisions.md`) levert de kolom Postcode daarnaast een
  beperkt vangnet voor de matching zelf, voor als het adres in Uren.xlsx niet
  matcht. De overige kolommen (Titel, Tijd, Reistijd, Werktijd, Monteur
  meegereden) worden bewaard maar spelen geen rol in de matchlogica.

Servermap (bevestigd): `\\stroes-1909\atrium\Autoprint\RUUDS`. De exacte
bestandsnaam-conventie van de automatische export is **nog niet bevestigd** met
Stric/RVS Solutions/RouteVision — dit moet nog rond zijn vóór de bestandsherkenning
definitief wordt vastgelegd.

## 3. Verwerking

### 3a. Bestandsdetectie (roadmap-fase 2, eerstvolgende bouwstap)

De app controleert de servermap elke 5 minuten (polling, geen filesystem-events —
onbetrouwbaar op een netwerkshare). Een bestand wordt pas verwerkt als de
bestandsgrootte gedurende 30 minuten ongewijzigd is gebleven — bij een
polling-interval van 5 minuten dus 6 metingen op rij. Polling-interval en
stabiliteitsmarge zijn twee losse, elk apart instelbare instellingen (vastgelegd
2026-09-02): dit voorkomt dat een nog niet volledig weggeschreven bestand wordt
ingelezen, terwijl afwijkingen sneller worden gesignaleerd dan wanneer beide aan
elkaar vastzitten.

Wat er is verwerkt, wordt uitsluitend bijgehouden via de database — er komt geen
aparte "verwerkt"-map en bestanden worden nooit verplaatst of verwijderd op de
servermap. Ontbreken bestanden aan het eind van de dag, dan wordt dat gelogd en
getoond via een statusveld ("laatste succesvolle run") in het beheerscherm — er gaat
geen automatische e-mail uit. Herverwerken van een dag kan alleen handmatig via een
knop in het beheerscherm; het weekoverzicht verandert nooit stilletjes vanzelf.

**Elk bronbestand wordt onafhankelijk gevolgd (vastgelegd 2026-09-02):** de matching/
tijdlijnreconstructie (§3b) draait door zodra Uren + Ritten (+ Relaties) compleet en
stabiel zijn — ongeacht of Werkbonnen.xlsx voor die periode aanwezig is, want dat
bestand is geen input voor de matching. Ontbreekt Werkbonnen.xlsx, dan wordt alleen
de volledigheidscontrole voor die periode niet uitgevoerd (status "controle niet
uitgevoerd, bronbestand ontbrak") — dat blokkeert het weekoverzicht niet. Een
ontbrekend bestand voor het ene doel mag een ander doel dus niet blokkeren.

**Ingest-robuustheid tegen Atrium-eigenaardigheden — gebouwd
(08-09-2026).** Het nieuwe, ongemoeide Relaties.xlsx van Wim bleek
niet-schemaconforme XML te bevatten (`WindowWidth`/`firstPageNo` i.p.v.
`windowWidth`/`firstPageNumber`) — elk eerder testbestand was ooit door Excel
geopend en zo stilzwijgend gerepareerd, dus dit bleef tot nu toe onopgemerkt.
De gedeelde bestandslezer (`matching/ingest/parsers/base.py`) repareert deze
drie bekende tokens in een kopie in het geheugen vóór het inlezen; het bestand
op de servermap wordt nooit aangeraakt, en een al conform bestand gaat
ongewijzigd door. Daarnaast is kolomnaam-matching hoofdletterongevoelig
(aanleiding: de nieuwe kolom heet `klant of leverancier` met kleine letter),
in beide readers. Beide gelden voor alle vier bronbestanden, niet alleen
Relaties.xlsx. 379 tests groen (was 364); de afwijking wordt in de tests
nagemaakt door `factories.ruwe_atrium_workbook()` in plaats van met een echt
klantbestand, want workbooks horen niet in de repository (`.gitignore`, AVG).
Zie `docs/decisions.md`.

### 3b. Tijdlijnreconstructie + matching (roadmap-fase 3)

Per monteur per dag wordt uit de RouteVision-ritgegevens een tijdlijn opgebouwd.
Belangrijk uitgangspunt: **de werktijd wordt afgeleid uit de ritgegevens** (wanneer
stopt/vertrekt de monteur bij een klantadres), **niet** uit de Werktijd/Reistijd-velden
die de monteur zelf in de werkbon invult — omdat die niet consequent worden ingevuld.
Werktijd begint zodra de monteur bij een klantadres stopt en eindigt zodra hij daar
wegrijdt; een tussentijds bezoek aan een leverancier of de eigen zaak beëindigt de
werkdag niet zolang de monteur diezelfde dag nog terugkeert naar de klant — pas het
laatste vertrek bij de klant die dag telt als einde werktijd.

Voor het matchen van locaties geldt: een exacte postcode-match is niet voldoende, er
is een straatnaam-fallback nodig. Een bezoek aan het depot vóór het werk wordt
herkend als zodanig. Bekende adres-afwijkingen (bijvoorbeeld werkbonadres wijkt af van
busadres) worden getoond als aandachtspunt, niet automatisch weggematcht.

Elk tijdblok in de tijdlijn krijgt een SOORT-code:

| Code | Betekenis |
|---|---|
| K | Klant |
| L | Locatie |
| C | Crediteur |
| P | Privé (toegevoegd 07-09-2026) |
| T | Thuis (toegevoegd 07-09-2026) |
| W | Werkbon |
| ? | Onbekend |
| O | Onverklaard |
| R | Reistijd |

Deze indeling is exact het eindresultaat dat de klant zelf al in Excel had ontworpen.

Afwijkingen worden beoordeeld tegen een **tolerantietabel per activiteit** (instelbare
drempel voor wat nog telt als een "onverklaarde" stop). De exacte drempelwaarden
liggen nog niet vast — die moeten nog met de klant worden bevestigd.

**Werkbonnen.xlsx als volledigheidscontrole (vastgelegd 2026-09-02):** los van de
matching wordt gecontroleerd of er een werkbon bestaat zonder geboekte uren in
Uren.xlsx. Daarbij telt de laatste/huidige Fase-status van de werkbon: "nog niet
gestart" (bijv. Fase Uitgevoerd/Gestopt zonder uren) is verwacht en levert geen
signaal op; "afgerond zonder geboekte uren" (Fase Afgehandeld/Gereed zonder uren) is
wél een afwijking die getoond wordt. Het omgekeerde scenario — uren geboekt op een
werkbonnummer dat niet in Werkbonnen.xlsx voorkomt — wordt logisch onmogelijk geacht
(Syntess borgt die referentie zelf) en hoeft niet apart gedetecteerd te worden.

**Controlegranulariteit: per werkbon als geheel, niet per losse datum (vastgelegd
2026-09-02, na een vraag vanuit de bouw):** een werkbon kan over meerdere data lopen
(bijv. Fase Uitgevoerd op 6 augustus, Gereed op 7 augustus). De opslag houdt deze
datumregels apart (fase 2, zie `docs/database.md`), maar de volledigheidscontrole
zelf (fase 3) beoordeelt de werkbon als geheel: "is deze werkbon ooit afgerond zonder
dat er ooit uren op zijn geboekt", niet "klopte de status op déze specifieke datum
met de uren van diezelfde datum". Dat laatste zou onnodig complex zijn en voegt niets
toe aan het doel van de controle.

**Monteur meegereden — instelbare 3-standen toggle (verfijnd 2026-09-03, zie
`docs/decisions.md`):** één globale instelling ("Instellingen"-scherm, fase 4) bepaalt
hoe een junior monteur zijn rittijden krijgt toegewezen:

1. **Vast** — een junior monteur is permanent gekoppeld aan één senior monteur.
2. **Periode-/datumgebonden** — een koppeltabel met geldigheidsperiode (van–tot),
   zodat een junior op verschillende momenten met verschillende senioren kan
   meerijden.
3. **Uit Syntess** — leest de kolom "Monteur meegereden" in de Werkbonnen-export
   rechtstreeks uit. **Staat nu uit en kan niet gekozen worden**: Syntess vult dit
   veld in de praktijk nog niet betrouwbaar (ligt bij Ruud/RVS Solutions, geen ETA).
   Activeren is een apart, later te nemen besluit, en vereist ook een uitbreiding van
   de fase 2-importtabel `WerkbonControle` (die dit veld nu bewust niet opslaat).

Fase 3/4 bouwt de standen 1 en 2 echt werkend (model + matchinglogica); stand 3 is een
gereserveerde keuze zonder importlogica erachter, tot de activatie ervan apart besloten
wordt.

**Zelfkoppeling bij "Vast" tegengaan — gebouwd (08-09-2026).**
`Monteur.vaste_meerijder` miste de check die `MeegeredenKoppeling` al wel
heeft: een monteur kon zichzelf als eigen vaste meerijder kiezen.
Gelijkgetrokken met hetzelfde patroon (`clean()`-validatie +
databaseconstraint). De gemelde klacht dat een vastgelegde vaste koppeling
wel te wijzigen maar niet te verwijderen zou zijn, is live getest en bleek
geen codefout — opgelost met een duidelijker leeg-label ("— geen vaste
meerijder —") op `MonteurAdmin`, in plaats van Django's standaard
`---------` dat niet als "verwijderen" leest. Zie `docs/decisions.md`.

**Werkbon-tijdregistratie (WB-vs-SYS-signaal) — bewust niet gebouwd (vastgelegd
2026-09-02):** het originele wensdoel van de klant om de door de monteur ingevulde
aankomst-/vertrektijd op de werkbon te vergelijken met de werkelijkheid is niet
uitvoerbaar (die kloktijden bestaan niet in de Syntess-data) en is door Wim expliciet
losgelaten ten gunste van "ritgegevens leidend" (zie hierboven). Zie
`docs/decisions.md` voor een impact-analyse voor het geval Wim hier ooit op
terugkomt — geen herontwerp, wel enkele optelbare aanpassingen in fase 2/3/4/6.

**Nog te bevestigen — klant/leverancier-onderscheid:** dit was een open datavraag,
maar wordt mogelijk bij de bron opgelost doordat RVS Solutions dit onderscheid zelf
aan de Relaties-export toevoegt — dan hoeft de app het niet meer zelf af te leiden.
Te bevestigen zodra die aangepaste export er is.

## 4. Beheerschermen (roadmap-fase 4)

Via Django-admin worden de koppeltabellen onderhouden:

- Bekende locaties (met marge/tolerantie).
- Monteur–voertuig, inclusief de "meegereden"-instelling met haar drie standen
  (vast / periode-gebonden / uit Syntess — de laatste voorlopig uitgeschakeld, zie
  §3b), en sinds 07-09-2026 het **thuisadres** van de monteur (straatnaam of
  postcode, straat als voorkeur). Optioneel: is het leeg, dan worden zijn stops
  thuis niet als T herkend maar gewoon als onverklaard getoond, corrigeerbaar via
  §5. Het scherm is te filteren op de precisiekeuze, zodat te zien is wie er nog
  geen adres heeft.
- Personeelsnummer–naam.
- Klant/leverancier-relaties (mogelijk overbodig zodra RVS Solutions dit oplost, zie
  hierboven).
- De tolerantietabel per activiteit.
- Het statusveld "laatste succesvolle run" (zie §3a).

**Data resetten (vastgelegd 07-09-2026, zie `docs/decisions.md`).** Een aparte
beheeractie, los van de reguliere Django bulk-delete-acties op de importtabellen
(die bewust dichtstaan — zie §3a/`docs/decisions.md`). Twee modi: "volledig
leegmaken" (Uren, Rit, Relatie, WerkbonControle, Tijdblok, ImportedFile — de
koppeltabellen blijven altijd ongemoeid) en "periode verwijderen" (van–tot datum,
alleen Uren/Rit/WerkbonControle/Tijdblok; Relatie en ImportedFile blijven daarbuiten,
zodat een periode-reset niet stilletjes de verwerkt-status van een bronbestand
wijzigt). Beide tonen eerst een preview en vereisen een expliciete bevestiging;
alleen beschikbaar voor superusers. Herimporteren/herberekenen na een reset blijft,
net als bij "Matching nu draaien", een bewuste, aparte stap. Gebouwd op
07-09-2026: `matching/reset.py` met het scherm eronder in `matching/admin.py`, te
bereiken via een link op het matchmotor-scherm (zie `docs/changelog.md`).

**Bestanden nu inlezen — gebouwd (08-09-2026).** Een derde knop op hetzelfde
matchmotor-scherm, naast "Matching nu draaien" en "Data resetten". Roept
`scan_share(force=True)` aan (dezelfde functie als `check_imports --force` op
de command line) — geen reprocess van al-verwerkte bestanden, en geen
automatische matching erna: beide blijven bewust aparte, losse stappen.
Aanleiding: SBTT-staff heeft geen shell om `check_imports` mee te draaien, en
het testen van de klant/leverancier-suggestie liet zien dat een bestand in de
inbox zetten niet hetzelfde is als importeren.

De knop staat *boven* "Matching nu draaien", omdat dat ook de volgorde van de
twee stappen is. POST-only en gated op `matching.change_matchmotorstatus`,
net als de bestaande knop. Na afloop meldt het scherm wat er is ingelezen
(bestanden, rijen) plus de zin dat de matching niet is herberekend; een lege
servermap en een servermap waarop niets nieuws staat krijgen elk hun eigen
melding, en een bestand dat niet gelezen kon worden een foutmelding per
bestand — de geslaagde imports uit dezelfde aanroep gaan gewoon door. 391
tests groen (was 379). Zie `docs/decisions.md`.

**Bestanden uploaden — gebouwd (09-09-2026).** Een vierde knop op hetzelfde
scherm, onder de bestaande drie: een gewone bestandskiezer in de browser
(`multiple`, `.xlsx`/`.csv`) waarmee SBTT de Syntess- en RouteVision-bestanden
zelf kan aanleveren. Uitdrukkelijk een **terugval** voor de periode waarin de
netwerkshare van Stric nog niet werkt, en voor een incidentele storing daarna —
geen vervanging van de share-route.

De geüploade bestanden komen onder hun eigen naam in diezelfde servermap
(`SERVERMAP_PATH` / `RMW_INBOX_DIR`) te staan, niet in een aparte uploadmap:
vanaf dat moment zijn het gewone bronbestanden met een gewone
`ImportedFile`-rij, en er wordt achteraf niets opgeruimd. Direct na het
wegschrijven draait `scan_share(force=True)` — uploaden en inlezen zijn hier
bewust één handeling, want een bestand dat compleet over HTTP binnenkomt heeft
geen stabiliteitsmarge nodig. De matching draait ook hier niet automatisch mee.

Twee weigeringen, per bestand zodat één onbruikbaar bestand de rest van de
batch niet kost: een naam die al op de servermap staat wordt geweigerd en
nooit overschreven (het bestand dat er staat kan juist het ingelezen bestand
zijn), en een naam die `classify_filename()` niet herkent wordt geweigerd in
plaats van als genegeerd bestand op de share achtergelaten. POST-only en gated
op `matching.change_matchmotorstatus`, net als de knop ernaast; de melding over
wat er is ingelezen komt uit dezelfde gedeelde helper. 411 tests groen (was
398). Zie `docs/decisions.md`.

Sinds 09-09-2026 staat dit blok **bovenaan** het scherm, boven "Bestanden nu
inlezen", "Matching nu draaien" en "Data resetten", als een eigen sectie met
een eigen koptekst — zolang de servermap niet werkt is het de enige manier om
data in de app te krijgen, en dan hoort het niet onderaan. Alleen de opmaak
is gewijzigd, niet het mechanisme.

**Importbestanden alleen-lezen (09-09-2026).** Het `ImportedFile`-scherm
(schermnaam "Importbestanden") is niet langer bewerkbaar: toevoegen, wijzigen
en verwijderen staan alle drie uit, net als bij de vier importtabellen en
`Tijdblok`. Bekijken blijft gewoon mogelijk — dat is waar het scherm voor is.
Reden: deze tabel is geen kopie van een bronbestand maar de eigen
administratie van wat er al is ingelezen, en zowel `scan_share()` als de
matching gaan erop af. Gevolg: een gerichte herimport van één bestand kan
alleen nog via `check_imports --reprocess` of via "Data resetten" — het
verwijderen van een losse regel was daar tot nu toe de admin-route voor. Zie
`docs/decisions.md`.

## 5. Uitzonderingenscherm (roadmap-fase 5)

Onbekende of afwijkende adressen kunnen in één klik gekoppeld worden aan een bekende
locatie. Eenmaal bevestigde koppelingen worden onthouden (opgeslagen in de
"bekende-locaties"-koppeltabel), zodat de lijst met openstaande uitzonderingen elke
week vanzelf korter wordt.

Besloten (03-09-2026, zie `docs/decisions.md`, "Lichte visuele stijl vastgelegd voor
fase 5"): dit scherm wordt gebouwd als onderdeel van de uiteindelijke webapplicatie,
buiten de Django-admin om — in tegenstelling tot de beheerschermen in §4, die wel
contractueel vastliggen als Django-admin. Reden: dit is een scherm dat SBTT-
medewerkers vaak zullen gebruiken en dat eigen ontwerpaandacht verdient. De visuele
basisstijl (kleuren, typografie, componenten) staat in `docs/ui-spec.md`, gebaseerd
op SBTT's eigen huisstijl (stroesteam.nl). Verdere schermdetails (welke gegevens per
uitzondering getoond worden, het bevestigingsformulier) zijn nog niet uitgewerkt.

**Concreet ontworpen (03-09-2026, zie `docs/decisions.md`, "Uitzonderingenscherm
(fase 5) concreet ontworpen"):**

- Eén rij per uniek onverklaard adres (niet per losse stop), met een teller en de
  betrokken monteur(en)/datum(s), gesorteerd op hoe vaak het voorkomt.
- `Tijdblok` krijgt twee nieuwe velden (`postcode`, `straat`), apart opgeslagen bij
  het matchen — in plaats van deze later kwetsbaar te herleiden uit de samengestelde
  adrestekst.
- Het koppel-formulier hergebruikt het bestaande `BekendeLocatie`-model: adres-
  precisie (straat of postcode, straat als voorkeur), SOORT (K/L/C), omschrijving.
  Geen `is_depot`-optie — een depot blijft admin-beheer.
- Na bevestigen wordt de matching direct herdraaid en toont het scherm de
  bijgewerkte lijst.
- Geen "Negeren"-actie in deze fase, alleen "Koppelen".
- Rechten: dezelfde permissie als een bekende locatie aanmaken in de admin.
- Eerste scherm buiten de admin — krijgt een minimale gedeelde basispagina
  (header/logo/navy balk, zie `docs/ui-spec.md`) die fase 6 hergebruikt.

**Gebouwd (03-09-2026, commit `b6cf401`, 195 tests groen):** precies zoals hierboven
ontworpen. `/uitzonderingen/` toont de gegroepeerde lijst, `/uitzonderingen/
koppelen/<precisie>/<waarde>/` het bevestigingsformulier. Bereikbaar via een link
op het matchmotor-statusscherm in de admin.

**Uitbreiding gebouwd (07-09-2026, zie `docs/decisions.md`).** Naast K/L/C is er
een vierde keuze op `BekendeLocatie.soort`: **P (Privé)**, voor onverklaarde
stops die overduidelijk privé zijn. Zelfde koppelformulier, zelfde mechanisme en
beperking als K/L/C (adres-classificatie, geldt voor elke monteur die er stopt) —
geen nieuw scherm, geen wijziging aan de tolerantielogica voor kortere
(?)-stops, en geen nieuwe stap in de prioriteitsvolgorde: P valt in de bestaande
"overige `BekendeLocatie`"-stap. Kleur `#C2185B` (`docs/ui-spec.md`).

**Vijfde keuze T (Thuis), gebouwd 07-09-2026.** Naast K/L/C/P is ook **T** via
dit formulier te koppelen. T heeft twee bronnen: primair het `thuisadres`-veld op
`Monteur` (zie §4 en `docs/database.md`), en daarnaast dit koppelformulier — voor
het geval dat de bus om de hoek staat en dat adres dus nooit gelijk is aan het
opgegeven huisadres. Zoals bij elke `BekendeLocatie` geldt zo'n koppeling voor
elke monteur die daar stopt.

**Gebouwd (08-09-2026) — suggestie op basis van `Relatie`.** Wim heeft een
aangepaste Relaties.xlsx aangeleverd met een nieuwe kolom "Klant of
leverancier" (K/L). Het koppelformulier doet daar een suggestie mee, geen
automatische classificatie: de gebruiker bevestigt nog steeds zelf, net als
bij K/L/C/P/T. Matching kan alleen op postcode — RouteVision-adressen
bevatten geen betrouwbaar huisnummer (`matching/timeline/normalize.py` knipt
het bewust af, een al gevalideerde PoC-regel), dus `Relatie.postcode` wordt
op dezelfde manier genormaliseerd en vergeleken als de rest van de app.
Precies één ondubbelzinnige relatie op die postcode → soort en label
voorgevuld; meerdere verschillende relaties op dezelfde postcode → een
keuzelijst met de kandidaten (gewone GET-links `?suggestie=<code>`, geen
JavaScript), waarna het formulier met die keuze wordt opgebouwd; geen relatie
→ formulier blijft leeg zoals voorheen. **Let op de lettermapping:** Relatie
gebruikt K/L (Klant/Leverancier), `BekendeLocatie.soort` gebruikt K/C
(Klant/Crediteur) — een Leverancier ("L") in Relatie wordt als SOORT **C**
voorgesteld, nooit als "L" (dat betekent in `BekendeLocatie.soort` "Locatie",
iets heel anders). Zie `docs/decisions.md` (08-09-2026).

Concreet gebouwd: `Relatie.klant_of_leverancier` (migratie `0009`, blank
toegestaan zodat een oudere export zonder die kolom gewoon blijft importeren),
`_relatie_suggesties()` en `_beginwaarden(groep, request)` in
`matching/views.py`, en de keuzelijst in `koppelen.html`. De poort staat op
`groep.postcode` en niet op `groep.precisie`: een op straat gegroepeerde
uitzondering draagt de postcode van zijn stops mee zodra RouteVision er één
gaf, en die is even goed te matchen. 15 nieuwe tests, 364 totaal groen (was
349).

Eén bewuste afwijking van de instructie: de gekozen kandidaat krijgt zijn
`.actief`-opmaak uit een eigen `{% block stijl %}` in `koppelen.html`. De
bestaande `.actief`-regel in `basis.html` is gescoped op `header.balk` en
raakt deze lijst dus niet — zonder eigen regel zou de gemaakte keuze er
identiek uitzien als de andere kandidaten, terwijl het ingevulde formulier pas
verderop op het scherm staat.

## 6. Weekoverzicht (roadmap-fase 6)

Het eindresultaat per monteur, beschikbaar als webpagina én als Excel-export, in de
layout die de klant zelf al in Excel had ontworpen (met de SOORT-codes uit §3b).
Bouwt voort op het HTML-prototype uit de eerdere validatie.

**Gebouwd (05-09-2026, 240 tests groen).** `/weekoverzicht/` toont één monteur-week:
een legenda, het weektotaal per SOORT, en per dag een inklapbare tabel (aankomst,
vertrek, duur, SOORT, omschrijving, adres) met daaronder de dagtotalen. Monteur en
week worden gekozen bovenaan de pagina en staan in de URL
(`?monteur=<id>&week=<jaar>-W<nr>`), met vorige/volgende week-links.
`/weekoverzicht/excel/` levert dezelfde week als .xlsx met dezelfde SOORT-celkleuren.

Twee bewuste afwijkingen van het prototype:

- **Geen WB-kolom en geen ⚑-signaal.** Die vergeleken de handmatig ingevulde
  werkbontijd met de RouteVision-tijd — het WB-vs-SYS-signaal dat volgens §3b bewust
  niet gebouwd is. Het prototype-uiterlijk mag dat signaal niet alsnog terugbrengen.
- **Wél de "gefactureerd vs. op locatie"-vergelijking**, per dag én als weektotaal:
  de som van `Uren.Aantal` tegenover de opgetelde duur van de SOORT=W-tijdblokken.
  Anders dan WB-vs-SYS vergelijkt dit twee bronnen die allebei betrouwbaar zijn
  (geboekte uren en gereconstrueerde ritdata).

Verder: een SOORT O-blok linkt rechtstreeks naar het koppelformulier van §5, en een
onvolledige week toont de dagen die er wél zijn plus een melding welke werkdagen
ontbreken — die ontbrekende dagen blijven buiten het weektotaal, zodat er nooit een
stil onvolledig totaal ontstaat.

**Landingspagina (06-09-2026).** Het weekoverzicht is de startpagina van de app.
De root-URL (`/`) stuurt door naar `/weekoverzicht/` (tijdelijke redirect, geen
301) in plaats van naar de admin; wie niet is ingelogd gaat via `/weekoverzicht/`
naar `/admin/login/?next=/weekoverzicht/` en komt ná het inloggen dus op het
weekoverzicht terug, niet in de admin. De admin blijft het enige inlogscherm van
de app en de "Beheer"-link in de navigatiebalk blijft naar `/admin/` wijzen.
`/weekoverzicht/` zonder `?monteur=` en `?week=` toont de eerste actieve monteur
alfabetisch en diens meest recent verwerkte week — bewust níét de huidige week:
op een maandagochtend of na een vakantie zou dat een leeg scherm opleveren, en de
standaardweergave is juist wat iedereen via `/` en via de navigatiebalk te zien
krijgt. Een monteur of week die wél in de URL staat maar niet bestaat blijft een
404, geen stille terugval.

**Testbevindingen (07-09-2026, avond, zie `docs/decisions.md`), beide gebouwd op
07-09-2026.** Tijdens een uitgebreide testronde na de "Data resetten"-functie
(zie §4) kwamen twee punten naar boven:

- Het label "Gefactureerd" hierboven heet nu "Totaal (excl. reistijd)", op de
  pagina en in de Excel-export. De berekening (som van `Uren.Aantal` tegenover
  de SOORT=W-duur) is ongewijzigd; alleen de naam klopte niet, omdat lang niet
  elk geboekt uur ook doorbelast wordt.
- Bug, bevestigd bij meerdere monteurs: alleen het middenstuk van de dag kwam in
  de tijdlijn terecht; zowel het ochtenddeel (rit naar het depot + verblijf) als
  het einde van de dag (verblijf bij het depot + rit naar huis) ontbrak
  structureel. Oorzaak bleek het afleiden van het thuisadres: het depot belandde
  tussen de "thuisstraten", waarna elke rit van huis naar depot, depot naar
  depot en depot naar huis werd weggegooid als ritje om het eigen huis. Het
  depot wordt nu uitgesloten bij die detectie. Zie `docs/changelog.md` en
  `docs/business-rules.md` (07-09-2026). Het restpunt uit diezelfde analyse — de
  detectie kende geen frequentiedrempel, waardoor een straat waar toevallig één
  dag begon of eindigde ook als thuis gold — is later die dag opgelost door de
  detectie helemaal te vervangen door een ingevuld `thuisadres` op `Monteur` en
  de nieuwe SOORT-code T. Sindsdien komt elke rit uit `Rit` in de tijdlijn
  terecht: op de juni-dataset 782 van 782.

**Aansluiting per werkbon — gebouwd 07-09-2026** (`docs/decisions.md`). Onder elk
dagoverzicht staat een tabel met één regel per werkbon die die dag voorkomt,
náást de bestaande dag-vergelijking en niet in plaats daarvan. Kolommen: Op
locatie (opgetelde SOORT=W-duur voor die werkbon die dag), Gedeclareerd (som van
`Uren.Aantal`), Verschil. Altijd alle werkbonnen van de dag, ook de kloppende.
Daaronder twee regels die geen werkbon zijn: "Klant (niet aan werkbon gekoppeld)"
met de SOORT=K-duur, en "Zonder werkbonnummer (indirect)" met de geboekte uren
die geen werkbonnummer dragen. Het dagtotaal telt W én K tegenover alle geboekte
uren; L en C blijven er bewust buiten. Alleen per dag — een weekversie was
expliciet geen onderdeel van het besluit. Zie `docs/business-rules.md` voor de
regels en `docs/changelog.md` (07-09-2026) voor de bouwverantwoording.

**Uitbreiding gebouwd (07-09-2026).** T (Thuis, zie §5) krijgt in het
weekoverzicht bewust géén eigen regel: T-blokken staan gewoon in de dagtabel en
tellen mee in het SOORT-totaal, meer niet — thuis-tijd is minder een getal dat je
wil optellen dan privé-tijd. P (Privé,
zie §5) heeft in het weekoverzicht wél een eigen, zichtbare regel naast het
weektotaal én per dag — net als de vergelijking hierboven een apart getal, geen
aftrek op "Totaal (excl. reistijd)". De regel verschijnt alleen wanneer er
privé-tijd is, zodat een week zonder privé-stops er onveranderd uitziet.

**Besloten (07-09-2026), nog niet gebouwd — "Aansluiting per werkbon".** De
bestaande "Totaal (excl. reistijd)" vs. "op locatie"-vergelijking hierboven is
één geblendet cijfer per dag; Wim kan er niet uit afleiden of er, per specifieke
werkbon, tijd is besteed die niet gedeclareerd is — en dat was feitelijk het doel
van de app (zie `docs/decisions.md`, 07-09-2026). Nieuw, onder elk dagoverzicht,
náást de bestaande regel:

- Eén rij per werkbon die die dag voorkomt (in `Uren.xlsx` en/of als een
  SOORT=W-tijdblok), altijd alle werkbonnen — ook zonder verschil, zodat een
  ontbrekende koppeling in beide richtingen opvalt: Gedeclareerd (`Uren.Aantal`)
  — Op locatie (SOORT=W-duur) — Verschil.
- Eén losse regel "Klant (niet aan werkbon gekoppeld)" met de totale SOORT=K-duur
  die dag — een K-adres heeft geen koppeling met een werkbonnummer, dus dit kan
  niet per werkbon, maar telt wel mee in het dagtotaal onderaan.
- Bewust buiten scope: SOORT L en C (Roger sprak specifiek over klant-tijd), en
  een weekniveau-versie van deze tabel — alleen per dag, zoals gevraagd.

Andere vraag dan de bestaande volledigheidscontrole (Werkbonnen.xlsx-check, §3b):
die beoordeelt een werkbon over zijn hele levensduur ("ooit afgerond zonder
uren"), deze aansluiting vergelijkt per dag twee al aanwezige bronnen, nu per
werkbon in plaats van geblendet.

**Gebouwd (08-09-2026) — Klantnaam bij "Aansluiting per werkbon".** De
tabel heeft een extra kolom **Klant**, direct naast de werkbonnummer-
kolom, met `Uren.project_opdrachtgever_naam` voor die werkbon/datum.
Alleen de werkbon-rijen krijgen een naam; de regels "Klant (niet aan
werkbon gekoppeld)", "Zonder werkbonnummer (indirect)" en de totaalregel
tonen een streepje. Is er voor die specifieke werkbon/datum geen
Uren-regel met een naam (bijv. een werkbon die alleen via de
Werkbonnen.xlsx-postcode-vangnet is gematcht), dan toont de cel eveneens
een streepje — geen opzoekactie bij een andere datum van dezelfde werkbon.
Op zowel de pagina als in de Excel-export. 349 tests groen (was 343).

Aandachtspunt (nog open): op echte data kan de vangnet-situatie hierboven
vaker voorkomen dan gedacht, waardoor een merkbaar deel van de rijen een
streepje bij Klant toont. Bewust voorlopig zo gelaten — pas op echte data
opnieuw bekijken. Zie `docs/decisions.md` (08-09-2026).

## 7. Oplevering en acceptatie (roadmap-fase 7 en 8)

Oplevering als lichte, zelfstandige Docker-container, samen met Stric geplaatst in een
bestaande Proxmox-/VM-omgeving (of anders een kleine VPS). Vóór elke nieuwe versie
wordt een back-up van de koppeltabellen gemaakt, zodat een rollback mogelijk is.
Daarna testen Roger en Wim samen; Wim heeft 30 werkdagen na oplevering om te testen,
anders geldt de oplevering automatisch als geaccepteerd. Bij oplevering hoort een
korte samenvatting van het gebouwde plus een instructie voor de beheerschermen en het
uitzonderingenscherm.

Vastgelegd (03-09-2026, zie `docs/decisions.md`, "Foutherstel bij het
uitzonderingenscherm — verplicht onderdeel van de opleverinstructie"): die instructie
moet expliciet uitleggen hoe een per ongeluk verkeerd gelegde koppeling hersteld
wordt — niet alleen hoe je een adres koppelt. Kort samengevat, voor die latere
instructie: een koppeling wijzigen of verwijderen kan altijd via "Bekende locaties"
in de admin (dat scherm is, anders dan bijvoorbeeld de tijdblokken, gewoon
bewerkbaar); de correctie wordt pas zichtbaar nadat de matching opnieuw is
gedraaid (de knop "Matching nu draaien", fase 4); en verwijderen is altijd veilig,
omdat een dag bij elke herberekening helemaal opnieuw beoordeeld wordt.

Vastgelegd (08-09-2026, zie `docs/decisions.md`, "Thuisadres invullen bij de
eerste inrichting"): bij diezelfde eerste inrichting moet voor elke monteur
het veld `thuisadres` (zie §4) worden ingevuld. Zonder dit veld wordt een
stop bij een monteur thuis niet als SOORT T herkend, maar blijft hij als
onverklaarde (O) stop in het uitzonderingenscherm staan.

## 8. Wat bewust buiten scope valt

Apart te offreren als vervolgstap, niet onderdeel van deze eerste werkende versie:

- Een uitgebreider dashboard of managementrapportage.
- Een directe API-koppeling met Syntess en/of RouteVision (in plaats van
  bestandsuitwisseling).
- Automatische signalering (bijv. een dagelijkse/wekelijkse e-mail met afwijkingen).
- Een optioneel serviceabonnement voor ondersteuning en kleine aanpassingen.
- Het snelheidscontrole-meerwerk (RouteVision-snelheid vs. maximumsnelheid per
  locatie) — **vastgelegd (05-09-2026): een aparte fase, later apart te offreren.**
  Het is dus geen openstaande ja/nee-vraag meer binnen deze roadmap en wordt nu niet
  opgepakt. Raakt bovendien AVG/medewerkersmonitoring en vereist een juridisch/
  HR-traject naast de techniek. Zie `docs/decisions.md` (05-09-2026).

## 9. Openstaande beslissingen — overzicht

Verzameld uit de secties hierboven, zodat ze niet uit het oog raken:

1. Bestandsnaam-conventie van de automatische Syntess/RouteVision-export (§2) — te
   bevestigen met Stric/RVS Solutions/RouteVision.
2. Exacte drempelwaarden van de tolerantietabel per activiteit (§3b) — te bevestigen
   met de klant.

_Opgelost op 2026-09-02: "monteur meegereden" (verfijnd 03-09-2026 tot een
instelbare 3-standen toggle, zie §3b/§4 en `docs/decisions.md`), de databronnen voor
de matching (Uren.xlsx + RouteVision leidend, Werkbonnen.xlsx alleen als
volledigheidscontrole, zie §2/§3b), het WB-vs-SYS-tijdsignaal (bewust niet gebouwd,
zie §3b), de onafhankelijke bestandsstatus per bron (zie §3a), het polling-/
stabiliteitsinterval (los instelbaar, zie §3a), de controlegranulariteit van de
volledigheidscontrole (per werkbon, zie §3b), en het AVG-beleid dat (ook
geanonimiseerde) klantdata nooit in git komt (zie `docs/decisions.md`) — zie
`docs/decisions.md` voor de volledige onderbouwing. Roadmap-fase 2 is gebouwd
(02-09-2026)._

_Opgelost op 2026-09-05: het snelheidscontrole-meerwerk. Dit is geen openstaande
ja/nee-vraag meer binnen deze roadmap, maar een aparte, later apart te offreren fase
— niet iets om nu op te pakken (zie §8 en `docs/decisions.md`)._


_Opgelost op 2026-09-08: het klant/leverancier-onderscheid (§9, punt 3).
Wim heeft een aangepaste Relaties.xlsx aangeleverd met de kolom "Klant of
leverancier" (K/L). De app blijft de SOORT-classificatie zelf handmatig doen
via `BekendeLocatie` (§5) — dat is niet vervangen — maar de nieuwe kolom
wordt gebruikt om die handmatige stap te versnellen: een voorstel op basis
van `Relatie` in het koppelformulier, zie §5 en `docs/decisions.md`
(08-09-2026)._
