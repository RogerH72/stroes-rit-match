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
  §3b).
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
  `docs/business-rules.md` (07-09-2026). Eén punt uit dezelfde analyse staat nog
  open: de detectie kent nog steeds geen frequentiedrempel, waardoor een straat
  waar toevallig één dag begon of eindigde ook als thuis geldt — een
  business-rule-keuze die apart genomen moet worden.

**Uitbreiding gebouwd (07-09-2026).** De nieuwe SOORT-classificatie P (Privé,
zie §5) heeft in het weekoverzicht een eigen, zichtbare regel naast het
weektotaal én per dag — net als de vergelijking hierboven een apart getal, geen
aftrek op "Totaal (excl. reistijd)". De regel verschijnt alleen wanneer er
privé-tijd is, zodat een week zonder privé-stops er onveranderd uitziet.

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
3. Klant/leverancier-onderscheid: blijft dit een koppeltabel in de app, of lost RVS
   Solutions dit op in de Relaties-export (§3b/§4)?

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
