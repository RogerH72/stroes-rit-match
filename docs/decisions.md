# Decisions — Stroes-Rit-Match (RMW)

## 2026-08-31 — Officieel akkoord van de klant (Superseded — zie 2026-09-01 hieronder)

Decision: Wim Stroes heeft op 31-08-2026 officieel akkoord gegeven om verder te gaan,
na intern overleg met zijn IT-supportpartner. Het project gaat over van
brainstorm/verkenning naar een opgezet project met een PoC als eerste stap.

Reasoning: bevestigt de gefaseerde aanpak (eerst een kleine PoC met 1-2 monteurs over
~1 week, daarna pas een onderbouwde offerte voor de volledige app) die al intern was
gekozen en die Wim op 26-08-2026 zelf overnam.

## 2026-09-01 — Statuscorrectie: akkoord betrof volledige offerte, live-PoC-met-klant vervallen (Current, corrigeert eerder besluit)

Decision: het "officieel akkoord van de klant" op 31-08-2026 betrof akkoord op de
**volledige offerte voor de complete app** — niet, zoals hierboven vastgelegd, akkoord
om alleen een live-PoC-fase met 1-2 monteurs te starten. De geplande live-PoC-stap met
de klant (~1 week, in overleg met Wim) heeft niet plaatsgevonden en is ook niet meer
voorzien als aparte offerte-stap.

Reasoning: de enige validatie die aan de offerte ten grondslag ligt is Roger's eigen
technische testrun op bestaande data van monteur M5 (week 3–7 aug 2026, zie
`docs/demo.md`), niet een klant-gevalideerde live-PoC. Om het risico te beperken dat
tijdens de bouw blijkt dat het matchingsconcept niet robuust genoeg is — terwijl de
offerte al is geaccordeerd — voert Roger vóór de bouwstart eerst zelf een bredere
technische validatie uit (meer weken/monteurs dan alleen M5). Superseded: het besluit
"2026-08-31 — Officieel akkoord van de klant", voor zover dat de akkoord-scope
beschreef als (alleen) een PoC-fase.

## 2026-09-01 — Trigger-mechanisme servermap: polling + database-tracking, geen verwerkt-map (Current)

Decision: de productie-app detecteert nieuwe bestanden op de servermap via polling
(vanuit een ingebakken scheduler in de Docker-container), met een stabiliteitscheck
(bestandsgrootte een aantal checks op rij ongewijzigd) voordat een bestand als
compleet geldt. **Het exacte polling-interval en de stabiliteitsmarge zijn op
2026-09-02 losgekoppeld — zie het besluit hieronder.** Wat al verwerkt is, wordt bijgehouden via de database
(matchresultaten per dag/monteur) — er komt geen aparte "verwerkt"-map op de servermap
en er worden geen bronbestanden verplaatst of verwijderd. Herverwerken van een dag kan
alleen handmatig, via een knop in het beheerscherm.

Reasoning: event-gebaseerd bestandswatchen is onbetrouwbaar op de netwerkshare, dus
polling is de veiligere keuze. Het idee om verwerkte bestanden naar een aparte map te
verplaatsen (voor overzicht/zichtbaarheid voor Wim/Stric) is expliciet overwogen en
afgewezen: de database houdt "al verwerkt" toch al bij als bijproduct van het opslaan
van de resultaten, dus een verwerkt-map lost geen echt probleem op. Bovendien zou het
schrijfrechten op de servermap vereisen in plaats van de leesrechten die nu al in de
OvO staan (punt 5a) — een extra afstemming met Stric en een groter risico-oppervlak,
zonder compenserend voordeel.

Open actiepunt: de exacte bestandsnaam-conventie van de automatische productie-export
is nog niet bekend (de PoC-bestanden in `D:\STROES` zijn handmatig benoemd) — te
bevestigen met Stric/RVS Solutions/RouteVision.

## 2026-09-01 — Bredere technische validatie afgerond: positief, bouw kan beginnen (Current)

Decision: de bredere technische validatie (2 monteurs — Jesse Verkerk/M03 en Dennis
van de Berg/M02 — over 4 weken, W30 t/m W33 / 20 juli-16 aug 2026) die als vervolg op
de statuscorrectie van 01-09-2026 werd afgesproken, is uitgevoerd en positief
afgerond. Jesse Verkerk: 29 van de 37 werkbonnen automatisch teruggevonden (78%, 18
werkdagen). Dennis van de Berg: 28 van de 30 (93%, 16 werkdagen; W33 bleek een
vakantieweek zonder ritdata). Beide resultaten zijn vergelijkbaar met of beter dan de
eerdere validatie op alleen monteur M5 (82%, 1 week). De gemiste werkbonnen zijn
stuk voor stuk verklaarbaar via hetzelfde al bekende patroon (werkbon-adres wijkt af
van straat/postcode-suffix in de RouteVision-data); één recidiverende klant kwam twee
keer voor met exact dezelfde mismatch, wat bevestigt dat een koppeltabel-regel voor
zulke klanten dit structureel oplost. Nieuwe observatie: bij Jesse Verkerk is het
verschil tussen gefactureerde en "op locatie"-uren relatief groter (~37% over 4 weken)
dan in de eerdere validatie (~11%) — geen matchingprobleem, wel een aandachtspunt voor
de bouwfase (hoe om te gaan met onvolledige/niet-aansluitende GPS-tracks).

Uitvoering: nieuwe RouteVision-downloads per kenteken (V-31-JRT, V-43-FRH) gecombineerd
met de bestaande Syntess Werkbonnen/Uren-exports; geanonimiseerd via het bestaande
`D:\STROES\anonimiseer_stroes.py` (personeelsnummer → M-code; `overrides_namen.csv`
toegevoegd omdat de automatische naamherkenning faalde — het Naam-veld in
Werkbonnen/Uren gebruikt hier "Achternaam Voorletter." zonder komma, niet het
komma-formaat dat het script verwacht). Matchinglogica hergebruikt ongewijzigd uit
`D:\STROES\PoC-demo\rmw_sbtt.py`, generiek gemaakt over meerdere monteurs/weken in
`D:\STROES\Validatie-W30-W33\geanonimiseerd\validatie_2monteurs_4weken.py`.

Reasoning: dit was de laatste stap vóór de bouw van de reeds geaccordeerde volledige
app (zie de statuscorrectie van 01-09-2026 hierboven). Het kwalitatieve
succescriterium — afwijkingen blijven verklaarbaar en het patroon is consistent met
de eerdere validatie — is gehaald. Gevolg: de bouw van de volledige app kan beginnen.

## 2026-09-01 — Roadmap vastgelegd + stack-tekst gecorrigeerd naar OvO-scope (Current)

Decision: `docs/roadmap.md` toegevoegd met de bouwvolgorde voor "de eerste werkende
versie" (8 fases: projectopzet, data-inlezing, reken-/matchmotor, koppeltabellen +
beheerschermen, uitzonderingen-scherm, weekoverzicht, oplevering, acceptatie), plus
een expliciete lijst van wat bewust buiten deze eerste versie valt (dashboard, directe
API-koppeling, automatische signalering, serviceabonnement, snelheidscontrole).
Tegelijk zijn de stack-teksten in `GUIDELINES.md` en `docs/architecture.md`
gecorrigeerd: die zeiden nog "productierichting nog niet definitief vastgelegd",
terwijl het geaccordeerde OvO (v1.8, 31-08-2026) de stack al vastlegt op
Python/Django, bestandsgebaseerd, opgeleverd als Docker-container.

Reasoning: op verzoek van Roger is gecontroleerd of er al een roadmap bestond
(brainstorm-besluiten, projectvoorstel, OvO) voordat er één werd opgesteld. Het
getekende OvO (punt 2a) bleek de scope al concreet vast te leggen — dat is dus geen
open richting meer maar een contractuele opsomming, en de bestaande documentatie was
op dat punt verouderd. De roadmap volgt de scope-opsomming uit het OvO 1-op-1, in de
volgorde die technisch logisch is (motor vóór schermen, schermen vóór oplevering).

## 2026-09-01 — Bouwen in Claude Code, niet in Cowork; Git + GitHub vanaf fase 1 (Current)

Decision: het daadwerkelijke bouwen van de webapp (vanaf roadmap-fase 1) gebeurt in
een aparte Claude Code-sessie (los terminalvenster op Rogers computer), niet in deze
Cowork-sessie. Ontwerpbeslissingen, de roadmap en documentatie-onderhoud blijven wel
in Cowork/chat, conform `werkwijze-project`. Daarnaast: `D:\PROJECTS\stroes-rit-match`
krijgt in fase 1 een lokale Git-repository én een gekoppelde GitHub-repo (zoals bij
CamperWorks/View360), in plaats van dit uit te stellen.

Reasoning: Cowork's toegang tot Rogers computer werkt via kortlopende, op zichzelf
staande shell-opdrachten (elk opnieuw gestart, geen doorlopend proces, tijdslimiet
per opdracht) — prima gebleken voor het losse validatiescript, maar minder geschikt
voor het itererend bouwen van de webapp zelf: een Django-ontwikkelserver die moet
blijven draaien, Docker-builds/logs die je wilt volgen, migraties die je interactief
wilt debuggen. Een doorlopende Claude Code-terminalsessie geeft Roger bovendien live
zicht op elk commando en kan hij direct onderbreken. Git+GitHub meteen vanaf fase 1
voorkomt dat er een periode is waarin bouwwerk onbeheerd/onback-upt op de lokale
schijf staat.

## 2026-09-01 — Taalconventie: code/instructies Engels, UI/documentatie Nederlands (Current, commit-taal herzien op 2026-09-05 hieronder)

Decision: vanaf de bouw van de webapp zijn code (variabelen, comments),
commit-messages en instructies naar een code tool (Claude Code) in het Engels. De al
bestaande RMW-projectdocumentatie (`CLAUDE.md`, `GUIDELINES.md`, `project-context.md`,
`docs/*.md`) blijft Nederlands en wordt niet met terugwerkende kracht vertaald. UI en
klantcommunicatie richting SBTT/Wim blijven te allen tijde Nederlands.

Reasoning: Roger vroeg of de instructie voor Claude Code beter in het Engels gegeven
kan worden. Onderzoek van het vergelijkbare, bestaande Django-project ReplayCalcTool
(zelfde ontwikkelaar, ook een Nederlandse klant) liet een duidelijk precedent zien:
daar zijn documentatie én code in het Engels, met alleen expliciet "UI language:
Dutch" vastgelegd. RMW week hiervan af (alles Nederlands, incl. code), zonder dat dit
ooit bewust was gekozen — dat was een aanname bij het scaffolden van het project. Om
aan te sluiten bij de gangbare praktijk (Django-ecosysteem/documentatie is Engelstalig)
zonder de al geaccordeerde Nederlandse projectdocumentatie te moeten hervertalen, is
gekozen voor een gesplitste aanpak: code/instructies Engels vanaf nu, bestaande
documentatie blijft staan.

**Aanvulling (zelfde dag):** Roger vroeg terecht door of het Engels/Nederlands mixen
wel goed werkt. Technisch is dat geen risico (Claude Code leest Nederlandse context
en schrijft er probleemloos Engelse code bij — een standaardpatroon). Wel relevant
gemaakt: Nederlandse domeintermen die letterlijk uit het door SBTT ontworpen format
komen (Werkbon, Monteur, Rit, de SOORT-codes K/L/C/W/?/O/R, koppeltabel,
tolerantietabel) blijven ongewijzigd Nederlands in modelnamen/velden, net als "Totaal
Montage" bij ReplayCalcTool — dit matcht zowel de eigen vocabulaire van de klant als de
bestaande Nederlandse documentatie. Alleen generieke code/structuur/comments zijn
Engels.

## PoC bewust stack-agnostisch (Current)

Decision: de PoC gebruikt een kaal Python-script, bestand-in/bestand-uit, zonder
productiestack-keuze.

Reasoning: Syntess-ontsluiting was het grootste risico; dat is voor de PoC opgelost via
3 dagelijkse Excel-exports, dus is er geen dure/premature architectuurkeuze nodig om
het matchingsconcept te valideren.

## Meerwerk snelheidscontrole (Superseded — zie 2026-09-05 hieronder)

Decision: nog geen besluit over het bouwen van een snelheidscontrole
(RouteVision-snelheid vs. maximumsnelheid per locatie).

Reasoning: raakt AVG/medewerkersmonitoring en vereist een zorgvuldig juridisch/HR-
traject naast de techniek; wordt pas opgepakt als Wim dit expliciet als meerwerk wil
laten uitwerken, niet vooruitlopend op het hoofdtraject. Zie
`D:\AI\brainstorm-sessies\stroes-rit-match-werkbon\besluiten.md` voor de verkende
technische bronnen (OSM/Overpass, Mapbox, HERE/TomTom, NWB/WKD).

## 2026-08-31 — docs/demo.md alsnog toegevoegd (Current, corrigeert eerder besluit)

Decision: `docs/demo.md` is alsnog toegevoegd, in lijn met de documentatiestandaard
(AI-Efficient Project Documentation Architecture, §5): een demo/PoC-document hoort erbij
zodra een project een pilot of proof of concept heeft.

Reasoning: bij het aanmaken van het project is deze stap eerst overgeslagen. Dit project
is expliciet in PoC-fase (1-2 monteurs, ~1 week), dus hoort het volgens de eigen
standaard wél te bestaan. Superseded: het eerdere besluit om `docs/demo.md` niet aan te
maken.

## 2026-09-02 — Fase-2 databronnen en "monteur meegereden" vastgelegd, na inspectie voorbeelddata (Current)

Decision: de voorbeeld-databestanden in `voorbeeld-data/` (geanonimiseerde
Syntess-exports Relaties/Uren/Werkbonnen + een RouteVision-rit-CSV, peildatum
26-08-2026) zijn ingelezen en de structuur is gebruikt om twee openstaande punten af
te ronden. (1) De matching drijft op **Uren.xlsx** (wie, welke werkbon, welke datum,
hoeveel uur, welk adres/klant) en de RouteVision-rit-CSV, aangevuld met
**Relaties.xlsx** voor klant/leverancier-stamgegevens. **Werkbonnen.xlsx wordt niet
gebruikt voor de matching** (Reistijd/Werktijd/Titel/Fase/Monteur meegereden voegen
daar niets aan toe), maar wordt wél ingelezen voor een **volledigheidscontrole**:
signaleren of een werkbon bestaat zonder geboekte uren. Daarbij telt de
laatste/huidige Fase-status: "nog niet gestart" (geen signaal) versus "afgerond
zonder geboekte uren" (wél een afwijking). (2) **"Monteur meegereden"**: het
Syntess-veld hiervoor staat al in de Werkbonnen-export, maar wordt in de praktijk nog
niet gevuld (ligt bij Ruud/RVS Solutions, geen ETA) — dus wordt optie A gebouwd: in
de beheerschermen ("Instellingen") een junior monteur hard koppelen aan een senior
monteur, waarna de junior automatisch dezelfde rittijden krijgt toegewezen.

Reasoning: zonder de echte kolomstructuur te zien dreigde het datamodel voor
roadmap-fase 2 te worden gebaseerd op aannames. Bij inspectie bleek de Werkbonnen-
export een 1-op-meerdere relatie te hebben met Fase-overgangen (elke werkbon
meerdere rijen, één per statuswijziging) — structureel, niet een eigenaardigheid van
dit specifieke exportmoment. Omdat Reistijd/Werktijd uit Werkbonnen al niet leidend
zijn (zie het besluit over werktijd uit ritgegevens hierboven), en Fase niet nodig is
om te bepalen wélke uren-boekingen matchbaar zijn (dat is een dagelijks feit, los van
de voortgang van de hele werkbon), bleef er geen valide reden over om Werkbonnen.xlsx
als matching-input te gebruiken — wel als controle-input, om werkbonnen te signaleren
die überhaupt niet zijn terugverwerkt naar geboekte uren. Voor "monteur meegereden"
gold al langer twee opties (zie eerdere vastlegging in `docs/business-rules.md`);
omdat optie B (Syntess vult het veld zelf) in de praktijk nog niet werkt, is optie A
nu het besluit, niet langer "geen keuze gemaakt".

Ook is bij deze gelegenheid directe toegang tot `D:\PROJECTS\stroes-rit-match`
gekoppeld aan de Cowork-ontwerpsessie (voorheen alleen los-gekopieerde bestanden in
project knowledge). Documentatie-updates (`docs/*.md`) worden vanaf nu direct in de
canonieke map bijgewerkt vanuit die sessie — geen tussenstap meer via de Claude
Code-sessie voor pure documentatiewijzigingen (die blijft wel de route voor
daadwerkelijke code/Django/Docker-wijzigingen).

## 2026-09-02 — WB-vs-SYS-tijdsignaal: geen apart doel, al opgelost via "ritgegevens leidend"; actiepunt kloktijden afgerond (Current)

Decision: het oorspronkelijke wensdoel (a) uit het bronbestand van de klant
(`20260424 RMW-Overzicht RouteVision & Werkbon koppelen.xlsx`, tabblad "Omschrijving"):
"de aankomst- en vertrektijd die Monteur heeft ingevuld op de Werkbon en of deze
overeenkomt met de werkelijkheid" — wordt niet als apart signaal (WB-tijd vs SYS-tijd)
gebouwd. Werkbonnen.xlsx blijft zoals al vastgelegd: alleen voor de
volledigheidscontrole, geen input voor de matching. Het openstaande actiepunt uit de
brainstorm-sessie ("navragen bij Wim/Syntess-accountmanager of echte begin-/
eindtijden per werkbon beschikbaar te maken zijn") is hiermee afgerond: Wim heeft
expliciet geantwoord dat dit geen haalbare weg is ("Het zou een forse uitdaging
worden om de monteurs 'begin- en eindtijd' te laten invullen. We moeten hier niet
oprekenen.") en gevraagd om de Ritgegevens leidend te maken — (1) werktijd begint
zodra de monteur bij een klant stopt, (2) werktijd stopt zodra hij wegrijdt.

Reasoning: bij het doornemen van de brainstorm-sessie (op initiatief van Roger, vóór
de bouw van fase 2) leek er een gemiste functie van Werkbonnen.xlsx te zijn: een
WB-vs-SYS-tijdsignaal uit een vroege PoC-demo-verkenning, die teruggaat op
bovengenoemd wensdoel (a) uit het originele klantbestand. Bij nadere inspectie bleek
dit doel niet uitvoerbaar met de echte Syntess-data (geen aankomst-/vertrektijd-
velden die de monteur invult, alleen Reistijd/Werktijd-duur die maar ~45% gevuld is)
— en al eerder (mailwisseling 27/28-08-2026) én nu opnieuw expliciet door Wim
losgelaten ten gunste van "ritgegevens leidend", wat al exact de vastgelegde regel is
in `docs/business-rules.md`. Er was dus geen gemiste functie: de vroege
brainstorm-verkenning van wensdoel (a) is inmiddels achterhaald door deze latere,
explicietere beslissing. Geen wijziging nodig in `docs/business-rules.md`,
`docs/database.md` of `docs/functioneel-ontwerp.md` — die weerspiegelden dit al
correct.

## 2026-09-02 — Robuustheid bestandsdetectie: ontbrekend bronbestand blokkeert alleen zijn eigen doel (Current)

Decision: elk bronbestand (Uren, Rit, Relatie, WerkbonControle) wordt in de
ImportBestand-bijhoudtabel onafhankelijk gevolgd. Als Werkbonnen.xlsx voor een
periode ontbreekt terwijl Uren.xlsx er wel is, draait de matching/
tijdlijnreconstructie gewoon door — die leunt niet op Werkbonnen.xlsx (zie de
databronnen-beslissing hierboven). Alleen de volledigheidscontrole wordt voor die
periode overgeslagen, met status "niet uitgevoerd, bronbestand ontbrak". Het
weekoverzicht wordt dus niet geblokkeerd door een ontbrekend Werkbonnen-bestand.

Reasoning: Roger vroeg expliciet naar dit scenario voordat de bouw van fase 2 wordt
geïnstrueerd. Omdat Werkbonnen.xlsx al geen matching-input is (zie hierboven), is er
geen inhoudelijke reden om de matching te laten wachten op of falen door een
ontbrekend Werkbonnen-bestand — dat zou een onnodige, kunstmatige afhankelijkheid
tussen twee losstaande doelen (matching vs. volledigheidscontrole) introduceren.

## 2026-09-02 — Impact-analyse (geen besluit): als Wim de WB-vs-SYS-tijdvergelijking alsnog wil

Decision: geen — dit is een vastgelegde impact-analyse voor toekomstig gebruik, geen
wijziging van de huidige scope. Mocht Wim later alsnog de vergelijking "ingevulde
werkbon-tijd vs. GPS-werkelijkheid" willen (zie het besluit hierboven over waarom dit
nu niet gebouwd wordt), dan raakt dat vier plekken, telkens als toevoeging, niet als
herontwerp: (1) fase 2 — de WerkbonControle-tabel uitbreiden met het Tijd-veld (en
eventueel Reistijd/Werktijd) uit Werkbonnen.xlsx, een bestand dat al wordt ingelezen;
(2) fase 3 — een extra vergelijkingsstap: de tijdlijnreconstructie berekent de
daadwerkelijke aankomsttijd (SYS-tijd) al uit de ritgegevens, die wordt dan ook naast
de Werkbon.Tijd gelegd; (3) fase 4 — een aparte drempelwaarde voor dit signaal in de
tolerantietabel; (4) fase 6 — een extra kolom in het weekoverzicht.

Reasoning: Roger vroeg dit uit voorzorg na de eerdere verwarring over het
WB-vs-SYS-signaal, om te weten hoeveel werk een eventuele omkeer van Wim zou
betekenen. Omdat fase 2 (ruwe import) losstaat van fase 3 (matchlogica) en fase 6
(output), is de impact beperkt tot optelbare aanpassingen — geen reden om nu al
anders te bouwen dan vastgelegd.


## 2026-09-02 — Polling-interval en stabiliteitsmarge losgekoppeld, beide instelbaar (Current)

Decision: het polling-interval (hoe vaak de servermap wordt gecontroleerd) en de
stabiliteitsmarge (hoe lang een bestandsgrootte ongewijzigd moet blijven voordat een
bestand als compleet geldt) zijn twee losse instellingen, elk apart configureerbaar
(bv. via env-var), niet één hardcoded getal. Startwaarden: polling elke 5 minuten,
stabiliteitsmarge 30 minuten (dus 6 opeenvolgende checks op rij bij dit interval).

Reasoning: het besluit van 2026-09-01 ("Trigger-mechanisme servermap") ging uit van
één interval van 30 minuten voor zowel polling als stabiliteitscheck. Bij nader
inzien zijn dit twee verschillende doelen: de stabiliteitsmarge (30 minuten) is een
inhoudelijke garantie tegen het inlezen van een half weggeschreven bestand, en hoeft
niet te veranderen. Het polling-interval bepaalt alleen hoe snel de app een compleet
bestand signaleert nadat het klaar staat; dat mag korter (5 minuten) zonder de
stabiliteitsgarantie aan te tasten, en blijft zo ook makkelijk bij te stellen zonder
de stabiliteitslogica te raken. Beide instelbaar maken voorkomt dat een toekomstige
wijziging in code hoeft te worden aangepast.

Impact op eerdere vastlegging: verfijnt (zonder te herroepen) het 2026-09-01-besluit
"Trigger-mechanisme servermap: polling + database-tracking, geen verwerkt-map" — de
kern van dat besluit (polling i.p.v. filesystem-events, database-tracking, geen
verwerkt-map, alleen handmatig herverwerken) blijft onveranderd van kracht.


## 2026-09-02 — Roadmap-fase 2 (data-inlezing) gebouwd (Current)

Decision/vastlegging: fase 2 is gebouwd in de Claude Code-sessie, getest (74 tests
groen) en in twee commits vastgelegd (nog niet gepusht naar GitHub). Gebouwd:
bestandsdetectie met polling (5 min, instelbaar) + stabiliteitscheck (30 min,
instelbaar, los van elkaar), de vier ruwe importmodellen (Uren, Rit, Relatie,
WerkbonControle) en de `ImportedFile`-bijhoudtabel, plus handmatige triggers
(`--force`/`--dry-run`/`--reprocess`/`--path`). Zie `docs/changelog.md` voor de
volledige technische samenvatting.

Bijzonderheden/openstaande punten uit de bouw:
- De scheduler is gebouwd als een aparte compose-service met een simpele loop
  (`scripts/scheduler.sh`) in plaats van cron/supercronic — een gelijkwaardige
  invulling van hetzelfde ontwerp (`docs/architecture.md` noemde cron/supercronic
  als voorbeeld, niet als eis).
- De bijhoudtabel is in code `ImportedFile` genoemd (Engels) in plaats van
  `ImportBestand` (zoals in `docs/database.md`) — toegestaan binnen de taalconventie
  omdat het een generieke technische tabel is, geen SBTT-domeinterm. Functioneel
  hetzelfde ding.
- `db.sqlite3` (lokaal, gitignored) is verwijderd om een schone eind-tot-eind-test te
  draaien. Bevatte alleen fase-1-opzet (nog geen modellen); als daar een lokale
  Django-superuser in stond, moet die opnieuw aangemaakt worden (`createsuperuser`).
- De Docker-image-build is nog niet gecontroleerd (Docker Desktop stond niet aan
  tijdens het bouwen) — wel gevalideerd dat `docker compose config` klopt en beide
  services de juiste env meekrijgen.

Reasoning: dit zijn implementatiekeuzes binnen het al vastgelegde ontwerp
(`docs/architecture.md`), geen scope- of ontwerpwijziging, dus geen aparte
bevestiging per punt nodig — hier alleen vastgelegd zodat een volgende sessie niet
opnieuw hoeft te ontdekken waarom code en documentnamen op dit punt uiteenlopen.

## 2026-09-02 — Volledigheidscontrole beoordeelt de werkbon als geheel, niet per datum (Current)

Decision: de volledigheidscontrole (fase 3, "bestaat er een werkbon zonder geboekte
uren") kijkt naar de werkbon als geheel — "is deze werkbon ooit afgerond zonder dat
er ooit uren op zijn geboekt" — niet per specifieke datum van een fase-overgang.

Reasoning: een werkbon kan over meerdere data lopen (bijv. Fase Uitgevoerd op 6
augustus, Gereed op 7 augustus). Tijdens de bouw van fase 2 werd zichtbaar dat de
opgeslagen fase-status per datumregel de eindstatus van de hele werkbon is (met
terugwerkende kracht op elke datumregel gezet) — dit riep de vraag op of de controle
per datum of per werkbon moet oordelen. Per werkbon is gekozen omdat dat het
oorspronkelijke doel is (zie `docs/functioneel-ontwerp.md` §3b) en per-datum-oordelen
onnodig complex zou zijn zonder functionele meerwaarde. De ruwe opslag blijft wel per
(Werkbon, Medewerker, Datum) — dit besluit raakt alleen hoe de fase-3-controle die
opslag straks leest, niet hoe fase 2 importeert.

## 2026-09-02 — AVG-beleid: geen klantdata (ook niet geanonimiseerd) in git (Current)

Decision: de geanonimiseerde voorbeeld-databestanden (`voorbeeld-data/`) worden nooit
naar de git-repository gecommit, ook niet ter ontwikkelgemak. De map is gitignored;
testen draaien op zelf-gegenereerde synthetische fixtures en slaan de test tegen de
echte voorbeeldbestanden over als die map ontbreekt.

Reasoning: ook geanonimiseerde klantdata in een git-historie (die op GitHub komt te
staan, zie `docs/decisions.md` 01-09-2026) is een AVG-afweging die niet impliciet
door een code-tool gemaakt mag worden. Bij de bouw van fase 2 werd dit expliciet als
zodanig herkend en aan Roger voorgelegd in plaats van zelf besloten — hier bevestigd
als vast beleid voor de rest van het project.

## 2026-09-03 — Deployment volgt het ReplayCalcTool-patroon; productiedatabase blijft SQLite (Current)

Decision: RMW's oplevering (roadmap-fase 7) volgt dezelfde aanpak als
ReplayCalcTool: lokaal bouwen, verpakken als Docker-container, en door de
IT-supportpartner van de klant (Stric) op een eigen VM (bij voorkeur Proxmox,
anders een kleine VPS) geplaatst vanaf de private GitHub-repo. Geen tussenlaag
zoals Railway — bij Replay is dat destijds ook losgelaten ten gunste van
rechtstreeks een VM bij de IT-partner.

Daarnaast, expliciet nu al besloten in plaats van open te laten tot fase 7: de
**productiedatabase blijft SQLite** (niet PostgreSQL zoals bij Replay). Het
SQLite-bestand staat op een named Docker-volume, gedeeld door de `web`- en
`scheduler`-service. Back-up gebeurt via een nog te bouwen `backup_db`
management-command dat gebruikmaakt van SQLite's ingebouwde online-backup-API
(veilig bruikbaar terwijl de database in gebruik is), wegschrijvend naar een
aparte bind-mount op de VM (los van het databasevolume, zodat een
`docker compose down -v` de back-ups niet meeneemt), met een dagelijkse cron-job
en 30 dagen bewaartermijn — zelfde ritme als Replay's `pg_dump`-cron, andere
techniek.

Het volledige, uitvoerbare draaiboek staat in `DRAAIBOEK.md` (root van de
repository, zelfde plek/naam als bij ReplayCalcTool). Dat draaiboek is nu al
grotendeels geschreven, vooruitlopend op fase 7, met drie onderdelen expliciet
gemarkeerd als nog niet definitief: de VM-gegevens (in te vullen zodra Stric een
VM heeft klaargezet), het `backup_db`-commando + de bijbehorende volume in
`docker-compose.yml` (nog te bouwen), en §7 "eerste inrichting" (kan pas
ingevuld worden na de beheerschermen van fase 4/5).

Reasoning: Roger wil voor RMW dezelfde, inmiddels bewezen werkwijze als bij
Replay aanhouden — lokaal bouwen, dan containeriseren, dan bij de klant plaatsen
via de IT-partner, in plaats van een aparte demo-/staging-omgeving. Voor de
database is expliciet gekozen tussen SQLite en PostgreSQL (zie
`settings.py`-comment "de productiedatabase is bewust nog niet gekozen"): SQLite
past beter bij RMW's schaal (één klant, lage schrijffrequentie: de scheduler
draait elke 5 minuten, de admin-schermen worden incidenteel gebruikt) en bij de
in het OvO toegezegde "lichte, zelfstandige container" — een aparte
databaseservice zoals bij Replay zou dat uitgangspunt onnodig verzwaren. Het
draaiboek is nu al opgesteld (in plaats van te wachten tot fase 7) zodat de
oplevering straks een kwestie van uitvoeren is; de drie nog openstaande
onderdelen zijn expliciet gemarkeerd in plaats van als af voorgedaan.

## 2026-09-03 — "Monteur meegereden" verfijnd tot instelbare 3-standen toggle (Current, verfijnt eerder besluit)

Decision: het besluit van 02-09-2026 ("optie A": een junior monteur hard koppelen aan
een senior) wordt verfijnd tot één globale instelling (in het "Instellingen"-scherm,
fase 4) met drie standen:

1. **Vast** — een junior monteur is permanent gekoppeld aan één senior monteur (één
   veld op de monteur-koppeltabel); wijzigt alleen als iemand dat handmatig aanpast.
2. **Periode-/datumgebonden** — een aparte koppeltabel met een geldigheidsperiode
   (van–tot), zodat een junior op verschillende momenten met verschillende senioren
   kan meerijden.
3. **Uit Syntess** (de kolom "Monteur meegereden" in de Werkbonnen-export) — **staat
   nu uit** en kan niet gekozen worden, omdat Syntess dit veld in de praktijk nog niet
   betrouwbaar vult (ligt bij Ruud/RVS Solutions, geen ETA). Activeren is een apart,
   later te nemen besluit zodra RVS Solutions dit oplevert; het vereist bovendien een
   uitbreiding van de fase 2-importtabel `WerkbonControle`, die "Monteur meegereden"
   momenteel bewust niet opslaat (zie het besluit van 02-09-2026).

Voor de bouw (fase 3/4): standen 1 en 2 worden nu echt werkend gebouwd (model +
matchinglogica). Stand 3 wordt opgenomen als gereserveerde keuze in het model/de
instelling, zonder importlogica erachter — dat volgt pas bij een apart besluit om hem
te activeren.

Reasoning: bij het bespreken van de matchmotor (fase 3) bleek een vaste koppeling
alleen niet flexibel genoeg — een junior kan met verschillende senioren meerijden op
verschillende momenten — terwijl de oorspronkelijke wens (het Syntess-veld zelf
uitlezen, "optie B" uit de eerdere afweging in `docs/business-rules.md`) ooit weer
bruikbaar kan worden zodra RVS Solutions het veld gaat vullen. Een instelbare toggle
met drie standen dekt beide scenario's zonder dat de app later herbouwd hoeft te
worden: nu twee werkende, handmatige standen; een kant-en-klare, maar bewust
uitgeschakelde derde stand voor zodra de brondata het toelaat. Superseded: het besluit
"2026-09-02 — Fase-2 databronnen en 'monteur meegereden' vastgelegd", voor zover dat
"optie A" als enige/definitieve oplossing beschreef — de databronnen-keuzes in dat
besluit blijven ongewijzigd van kracht.

## 2026-09-03 — Fase 3 gebouwd: twee aandachtspunten voor de configuratie, geen bugs (Current)

Decision: bij het bouwen en testen van de reken-/matchmotor (fase 3, commit `eea759c`)
kwamen twee dingen naar boven die geen fouten in de motor zijn, maar bewust
vastgelegd worden als aandachtspunt voor de vervolgstappen:

1. **Straat-niveau depotrisico.** De depotprioriteitsregel (een `BekendeLocatie` met
   `is_depot=True` wint altijd van een werkbonmatch — de gevalideerde PoC-regel,
   nodig omdat het eigen depotadres van SBTT kan samenvallen met of dicht bij
   klantadressen kan liggen) werkt op straatniveau. Zodra in fase 4 het échte
   SBTT-depotadres wordt ingevoerd, claimt dat élk adres op diezelfde straat vóór een
   werkbonmatch — ook als dat andere adres feitelijk een klant is. Geen bug (dit is
   precies het gevalideerde PoC-gedrag), maar iets om bewust bij te houden bij het
   invoeren van het echte depotadres in fase 4: een depotadres met een postcode of
   huisnummer-precisie zou dit risico verkleinen, maar dat is nu geen doel op zich.
2. **Lager werkbon-hervindingspercentage dan de PoC.** Dit is het verwachte gevolg
   van het eerder genomen besluit (02-09-2026) om Werkbonnen.xlsx niet als matchbron
   te gebruiken (alleen voor de volledigheidscontrole) — de PoC gebruikte
   Werkbonnen-postcodes wél mee in de match. Geen motorfout; de tests bevestigen dat
   het hervindingspercentage binnen de op basis van dit besluit te verwachten
   bandbreedte valt.

Daarnaast een kleine, geaccepteerde beperking: `Instelling.delete()` is aan
modelniveau geblokkeerd (de singleton-instelling mag niet verwijderd worden), maar
een `Instelling.objects.all().delete()` op queryset-niveau omzeilt dat (Django roept
`delete()` op individuele instances niet aan bij een queryset-bulkdelete). Dit is een
bewust geaccepteerd, laag risico: er is geen UI-pad dat een bulkdelete op
`Instelling` aanbiedt, en de DB-`CheckConstraint` voorkomt in elk geval dat er ooit
meer dan één rij ontstaat.

Reasoning: beide bevindingen zijn eigenschappen van bewust eerder genomen besluiten
(de PoC-gevalideerde depotregel; het besluit om Werkbonnen.xlsx niet als matchbron te
gebruiken), geen nieuwe fouten — vastleggen voorkomt dat ze later als verrassing of
als "misschien een bug" opnieuw onderzocht moeten worden. Het depotrisico wordt
expliciet meegenomen als aandachtspunt bij de fase 4-bespreking (zie
`GUIDELINES.md`, "Current priorities", punt 6).

## 2026-09-03 — Werkbonnen.xlsx-postcode alsnog als matchvangnet; overige velden voortaan bewaard (Current, verfijnt eerder besluit)

Decision: naar aanleiding van het lagere werkbon-hervindingspercentage dat bij de
fase 3-bouw aan het licht kwam (zie het besluit hierboven, "Fase 3 gebouwd"), wordt
het besluit van 02-09-2026 ("Werkbonnen.xlsx is geen input voor de matching") op één
punt verfijnd:

1. **Postcode uit Werkbonnen.xlsx wordt alsnog een matchbron**, als vangnet ná de
   bestaande postcode/straat-match op de eigen geboekte uren (Uren.xlsx) en vóór de
   koppeltabel (K/L/C): als een rit-stop niet matcht op het adres dat de monteur zelf
   bij zijn uren invulde, wordt alsnog geprobeerd of de postcode uit Werkbonnen.xlsx
   voor die werkbon/datum matcht. Dit is exact wat de PoC ook deed (`wb_pc` in
   `rmw_sbtt.py`) en sluit het gat dat het 02-09-besluit had geopend.
2. **Werktijd, Reistijd, Titel en Tijd uit Werkbonnen.xlsx worden voortaan wél
   opgeslagen**, maar blijven ongebruikt in de matchlogica zelf (Titel uitgezonderd:
   die wordt als omschrijvingstekst getoond wanneer de postcode-vangnet-match
   raak is, puur ter leesbaarheid — geen matchsleutel). Reden: deze velden zijn
   structureel onbetrouwbaar (bevestigd door Wim, mailwisseling 27/28-08-2026), dus
   een concrete reden om ze wél te gebruiken is er niet — maar bronbestanden op de
   servermap worden nooit verwijderd (zie `matching/models.py`/`docs/architecture.md`),
   dus niets gaat verloren door ze nu alvast mee te lezen in plaats van later een hele
   nieuwe uitleesronde te bouwen.
3. **"Monteur meegereden" wordt ook nu al opgeslagen** (ongebruikt, gereserveerd) —
   niet om te gebruiken vóórdat stand 3 van de meegereden-toggle apart geactiveerd
   wordt (zie het besluit van 03-09-2026 hierboven), maar omdat deze wijziging toch al
   een migratie op `WerkbonControle` vereist: nu meenemen voorkomt een tweede migratie
   op dezelfde tabel zodra stand 3 ooit geactiveerd wordt.

Reasoning: bij het navragen waarom het hervindingspercentage lager uitviel dan de PoC
bleek de oorzaak concreet: de PoC had een tweede matchbron (Werkbonnen-postcode) die
deze app niet had. Die postcode komt uit de planning bij de klant, niet uit wat een
monteur handmatig intypt bij zijn uren, en is dus vaak preciezer juist wanneer de
Uren.xlsx-match faalt. Het overnemen van alleen dit ene veld verandert niets aan het
onderliggende besluit dat Werktijd/Reistijd (en het WB-vs-SYS-signaal dat daarop
gebaseerd zou zijn) niet betrouwbaar genoeg zijn om te gebruiken — dat blijft
ongewijzigd van kracht. Superseded: het besluit "2026-09-02 — Fase-2 databronnen en
'monteur meegereden' vastgelegd", uitsluitend voor zover dat beschreef dat
Werkbonnen.xlsx "geen enkele rol" in de matching speelt en dat Reistijd/Werktijd/
Titel/Monteur meegereden "niet opgeslagen" worden — de kern van dat besluit (deze
velden worden niet gebruikt om werktijd of aan/vertrektijden te bepalen) blijft
staan.

## 2026-09-03 — MatchmotorStatus wordt read-only in de admin (Current)

Decision: `MatchmotorStatus` (het statusscherm/de knop uit fase 4) krijgt
dezelfde read-only-behandeling in de admin als `Tijdblok` en de import-
tabellen: alleen bekijken, niet handmatig aanpassen. Bij het bouwen was dit
een openstaande keuze (Claude Code liet wijzigen expliciet aan, "add" en
"delete" uit) — nu gelijkgetrokken met het bestaande patroon.

Reasoning: `MatchmotorStatus` is systeem-berekende data (elke run overschrijft
de rij), geen door SBTT beheerde configuratie zoals `Instelling` of de
koppeltabellen. Een gebruiker die de statusrij handmatig aanpast, kan daarmee
geen kwaad (de eerstvolgende run overschrijft het toch), maar het is verwarrend
om iets bewerkbaar te tonen dat feitelijk alleen een uitleesvenster op een proces
is. Consistent met waarom `Tijdblok` al read-only is: "de manier om de uitkomst
te veranderen is een koppeltabel aan te passen en de matching opnieuw te
draaien", niet het resultaat zelf handmatig te bewerken.

Aanvulling 07-09-2026: "read-only" omvat ook verwijderen. Dat stond hier al
impliciet ("alleen bekijken"), maar was in de code alleen voor
`MatchmotorStatus` en `Instelling` waargemaakt — `Uren`, `Rit`, `Relatie`,
`WerkbonControle` en `Tijdblok` misten `has_delete_permission`, waardoor
"verwijder geselecteerde items" in de admin gewoon beschikbaar was. Dit is
gerepareerd als bug, niet als nieuw besluit; zie `docs/changelog.md`
(07-09-2026).

## 2026-09-03 — Lichte visuele stijl vastgelegd voor fase 5 (Current)

Decision: het uitzonderingenscherm (fase 5) wordt gebouwd als onderdeel van de
uiteindelijke webapplicatie, buiten de Django-admin om — niet als extra
admin-scherm. Reden: dit is een scherm dat SBTT-medewerkers vaak zullen
gebruiken, en dat verdient eigen ontwerpaandacht in plaats van de generieke
admin-uitstraling.

Bijbehorend besluit: nu al een lichte visuele basisstijl vastleggen in
`docs/ui-spec.md`, in plaats van dit tot fase 6 uit te stellen — het
uitzonderingenscherm zet zo het sjabloon voor het weekoverzicht (fase 6),
zodat beide er als één samenhangende applicatie uitzien in plaats van
achteraf te moeten harmoniseren.

De kleuren komen rechtstreeks uit de CSS van `https://stroesteam.nl/` (SBTT
zelf: Bouw/Techniek/Klimaat) — navy `#133B78`, oranje `#FF6B24`, groen
`#80BB45`. `https://www.stroes.nl/` bleek bij inspectie een ander bedrijf te
zijn (vastgoedverhuur, "Stroes Onroerend Goed") en is niet gebruikt. Het
bestaande RMW-logo (`D:\STROES\ChatGPT Image 31 aug 2026, 18_09_13.png`)
wordt als beeldmerk gebruikt zoals het is; de kleuren in dat logo zelf zijn
expliciet niet de bron voor het kleurenschema. Voor SOORT O ("onverklaard",
de kern van dit scherm) is bewust gekozen voor een aparte amber/rode
waarschuwingskleur buiten het SBTT-palet, omdat oranje op dit scherm al de
actieknop-kleur is — anders zouden waarschuwing en actieknop visueel door
elkaar lopen. Volledige uitwerking (tabel met exacte hex-waardes,
typografie, componenten): zie `docs/ui-spec.md`.

## 2026-09-03 — Uitzonderingenscherm (fase 5) concreet ontworpen (Current)

Decision: het uitzonderingenscherm toont één rij per uniek onverklaard adres
(postcode, straat als er geen postcode is) — niet één rij per losse
onverklaarde stop. Elke rij toont hoe vaak dat adres voorkomt en welke
monteur(en)/datum(s) het betreft, gesorteerd op frequentie (meest voorkomend
eerst). Reden: één koppeling lost in één keer alle onverklaarde stops op dat
adres op (nu én toekomstig, na een herberekening) — dat is het "de lijst
wordt vanzelf korter"-effect dat al in `voor-klant/hoe-werkt-de-matching.md`
staat.

`Tijdblok` krijgt twee nieuwe velden: `postcode` en `straat`, apart
opgeslagen op het moment dat een tijdblok ontstaat (naast de al bestaande
samengestelde `adres`-tekst, die blijft voor de weergave). Reden: zonder
deze velden zou het scherm de postcode/straat opnieuw uit de samengestelde
adrestekst moeten interpreteren ("Randweg 6a, 4104 AC Culemborg" uit elkaar
halen) — dat werkt vandaag, maar breekt stilzwijgend zodra het adresformaat
ooit verandert. Net als bij de Werkbonnen.xlsx-velden (besluit van
03-09-2026 hierboven) is de keuze: één keer goed opslaan in plaats van later
kwetsbaar herleiden. Kost een migratie en het eenmalig herverwerken van
bestaande dagen (`run_matching --force`, zelfde bekende stap als eerder).

Het bevestigingsformulier ("Koppelen") hergebruikt het bestaande
`BekendeLocatie`-model en zijn validatie rechtstreeks: adres-precisie
(straat of postcode — straat als voorkeursoptie, want straat wint ook al bij
de matching zelf voor K/L/C), SOORT (kan op het model toch alleen K/L/C
zijn) en een omschrijving/label. `is_depot` wordt in dit formulier niet
aangeboden — een depot blijft iets dat via de admin beheerd wordt, niet iets
dat per ongeluk vanuit dit scherm ontstaat.

Na bevestigen wordt de matching direct herdraaid (eerder al besloten) en
toont het scherm de bijgewerkte, kortere lijst.

Geen "Negeren"-actie in deze fase — alleen "Koppelen". Een eenmalige,
niet-koppelbare uitschieter blijft gewoon in de lijst staan; een aparte,
blijvende registratie van genegeerde adressen (nodig om te voorkomen dat zo'n
stop na elke herberekening terugkeert) is meer bouwwerk dan nu de moeite
waard is. Kan later alsnog toegevoegd worden.

Rechten: dezelfde permissie als het aanmaken van een bekende locatie in de
admin (`matching.add_bekendelocatie`) — geen apart rechtensysteem.

Dit is het eerste scherm buiten de Django-admin, dus er komt een minimale
gedeelde basispagina (header met het RMW-logo en de navy balk uit
`docs/ui-spec.md`) die fase 6 (weekoverzicht) hergebruikt.

## 2026-09-03 — Foutherstel bij het uitzonderingenscherm — verplicht onderdeel van de opleverinstructie (Current)

Decision: de gebruikersinstructie die bij oplevering aan Wim wordt meegegeven
(roadmap-fase 7/8, zie `docs/functioneel-ontwerp.md` §7) moet expliciet
uitleggen hoe een per ongeluk verkeerd gelegde koppeling in het
uitzonderingenscherm hersteld kan worden — niet alleen hoe je een adres
koppelt.

Aanleiding: het uitzonderingenscherm (fase 5, zie het ontwerp-besluit
hierboven) biedt bewust alleen "koppelen" aan, geen "verwijderen" — fouten
herstellen blijft admin-werk via "Bekende locaties". Zonder een expliciete
instructie zou een gebruiker die per ongeluk een verkeerde koppeling maakt,
niet weten hoe dat terug te draaien is.

Wat die instructie moet dekken (nu vastgelegd zodat het bij de daadwerkelijke
oplevering niet vergeten wordt — de tekst zelf wordt pas geschreven als het
scherm gebouwd en getest is):

1. Een koppeling wijzigen of verwijderen kan altijd via "Bekende locaties" in
   de admin — dat scherm is, anders dan bijvoorbeeld de tijdblokken of de
   matchmotor-status, gewoon volledig bewerkbaar.
2. De correctie wordt pas zichtbaar nadat de matching opnieuw is gedraaid
   (de knop "Matching nu draaien" uit fase 4) — het aanpassen van de
   koppeling zelf heeft geen direct effect op wat al berekend is.
3. Verwijderen is altijd veilig: een dag wordt bij elke herberekening
   helemaal opnieuw beoordeeld aan de hand van de op dat moment geldende
   koppeltabel, dus er is geen risico op een "kapotte" verwijzing.

Bewust niet nu al uitgeschreven als kant-en-klare instructietekst: het
uitzonderingenscherm is op het moment van dit besluit nog niet gebouwd (de
bouwinstructie is net verstuurd), en een instructietekst schrijven voor een
scherm dat tijdens de bouw nog kan afwijken zou voorbarig zijn.

## 2026-09-05 — Snelheidscontrole-meerwerk: aparte, later te offreren fase (Current, vervangt "Meerwerk snelheidscontrole")

Decision: het snelheidscontrole-meerwerk (RouteVision-snelheid vs. maximumsnelheid per
locatie) is geen openstaande ja/nee-vraag meer binnen deze roadmap, maar een aparte,
later apart te offreren fase — niet iets om nu op te pakken.

Reasoning: het punt stond tot nu toe als open beslissing in
`docs/functioneel-ontwerp.md` §9, waardoor het bij elke roadmap-stap opnieuw als
af te wegen keuze terugkwam terwijl het in de praktijk buiten het huidige traject
valt. Door het expliciet als aparte fase vast te leggen, is duidelijk dat het niet
vergeten is maar bewust naar een eigen offerte-moment is verplaatst; de inhoudelijke
zwaarte blijft ongewijzigd (het raakt AVG/medewerkersmonitoring en vereist een
zorgvuldig juridisch/HR-traject naast de techniek, en wordt pas uitgewerkt als Wim
dit expliciet als meerwerk wil laten offreren). De verkende technische bronnen
(OSM/Overpass, Mapbox, HERE/TomTom, NWB/WKD) staan in
`D:\AI\brainstorm-sessies\stroes-rit-match-werkbon\besluiten.md`.

Superseded: het besluit "Meerwerk snelheidscontrole" hierboven, voor zover dat de
status beschreef als "nog geen besluit".

Doorgevoerd in: `docs/functioneel-ontwerp.md` §8 (herformuleerd) en §9 (uit de
openstaande-beslissingen-lijst gehaald, toegevoegd aan de opgelost-regel),
`docs/roadmap.md` ("Expliciet buiten deze roadmap"), `GUIDELINES.md` ("Important
warnings" en "Current priorities"), `docs/business-rules.md` en `docs/demo.md`.
Geen codewijziging.

## 2026-09-05 — Commit-messages in het Nederlands (Current, herziet de commit-taal van 2026-09-01)

Decision: commit-messages zijn Nederlands. De rest van de taalconventie van
01-09-2026 blijft ongewijzigd: code (variabelen, comments) en instructies naar een
code tool blijven Engels, UI en klantcommunicatie blijven Nederlands, en de
bestaande projectdocumentatie blijft Nederlands.

Reasoning: een commit-message hoort bij de projectuitvoering, niet bij de code zelf
— hij wordt gelezen naast de changelog, de roadmap en de besluiten, en die zijn
allemaal Nederlands. Engelse commit-messages boven een volledig Nederlandstalig
project leverden een taalgrens midden in dezelfde gedachtegang op. Daarbij was de
Engelse regel in de praktijk al niet gevolgd: de commits van fase 5 en fase 6, en
de documentatiecommits daaromheen, zijn Nederlands geschreven. Deze bijstelling
maakt de vastgelegde conventie gelijk aan de feitelijke praktijk, in plaats van een
regel te laten staan die bij elke commit opnieuw wordt overtreden.

Superseded: het besluit "2026-09-01 — Taalconventie", uitsluitend voor zover dat
commit-messages als Engels aanwees. De motivering daarvan (aansluiten bij het
Engelstalige Django-ecosysteem) geldt voor code en tool-instructies, niet voor een
tekst die alleen door de projectbetrokkenen zelf gelezen wordt.

## 2026-09-07 — Lokaal testen met echte data: uitsluitend via Docker (Current)

Decision: bij het testen met échte (niet-geanonimiseerde) SBTT-data wordt voortaan
uitsluitend gebruikgemaakt van `docker compose up` — nooit meer van een losse
`manage.py runserver` tegen de host-`db.sqlite3`. Zo is er nog maar één database om
naar te kijken.

Reasoning: bij de eerste testrun met échte augustus-data (06-09-2026, avond, zie
`GUIDELINES.md`) bleek de container een eigen, vrijwel lege database te hebben
(Docker-volume), los van de host-`db.sqlite3` die een bare `runserver` gebruikt. Dit
zorgde tot twee keer toe voor verwarring: eerst geen account/koppeltabellen in de
container, later weer de oude testdata zodra juist de host-`runserver` werd gestart.
Overwogen alternatief: de database als bind-mount delen tussen host en container
(zoals nu al met `data/inbox`) — afgewezen omdat SQLite + bind-mounts op Docker
Desktop/Windows (WSL2) een bekende valkuil is: de bind-mount gedraagt zich voor
file-locking als een netwerkbestandssysteem, wat SQLite expliciet afraadt vanwege het
risico op databasecorruptie bij gelijktijdig schrijven vanuit host én container.
Bijkomend voordeel van uitsluitend-Docker: de app draait in productie sowieso in
Docker (roadmap-fase 7), dus dit brengt dev en productie al dichter bij elkaar vóór de
oplevering.

Dit geldt alleen voor testen met échte klantdata. De gewone ontwikkel-cyclus
(`manage.py test` op synthetische fixtures, `manage.py runserver` tijdens het bouwen
van een feature zonder échte data) verandert niet.

Expliciet vastgelegd op verzoek van Roger: mocht dit in de toekomst tóch geprobeerd
worden (een bare `runserver` tegen échte SBTT-data), dan hoort daarop gewezen te
worden dat dit zo is afgesproken — zie ook `CLAUDE.md`, "Development principles".

## 2026-09-07 — Beheeractie "Data resetten" toegevoegd: volledig leegmaken of periode verwijderen (Current)

Decision: er komt een aparte, bewuste beheeractie ("Data resetten") in de admin, los
van de generieke Django bulk-delete-acties op de importtabellen (die vandaag terecht
dichtgezet zijn, zie de aanvulling op het besluit "MatchmotorStatus wordt read-only
in de admin" hierboven). Twee modi:

1. **Volledig leegmaken** — verwijdert alle rijen uit Uren, Rit, Relatie,
   WerkbonControle, Tijdblok én ImportedFile (dezelfde 6 tabellen als bij de
   handmatige reset van vandaag, zie het besluit "Schone herimport +
   herberekening" hierboven). Koppeltabellen (Monteur, BekendeLocatie,
   Instelling, MeegeredenKoppeling, ToleranceRegel, MatchmotorStatus) blijven
   altijd ongemoeid.
2. **Periode verwijderen** (van–tot datum) — filtert en verwijdert Uren, Rit,
   WerkbonControle en Tijdblok op datum. Relatie (klant/leverancier-stamgegevens
   zonder periode-begrip) en ImportedFile (per bestand, niet per periode) blijven
   buiten deze modus: een periode-reset "vergeet" dus niet dat een bronbestand al
   verwerkt is, en een her-import van hetzelfde bestand voor die periode blijft de
   bestaande handmatige `--reprocess`-stap vereisen.

Beide modi tonen eerst een preview (aantal rijen per tabel dat verwijderd gaat
worden) en vereisen een expliciete bevestiging voordat er definitief iets
verdwijnt. Net als bij "Matching nu draaien" (fase 4) is herimporteren/
herberekenen na een reset een bewuste, aparte vervolgstap — geen automatisch
gevolg van de reset-actie zelf.

Toegang: alleen superusers (dus voorlopig alleen Roger), niet elke ingelogde
beheerder. Dit is bewust een technisch/troubleshooting-hulpmiddel, geen
SBTT-personeelsfunctie; mocht Wim dit ooit zelf nodig hebben, is dat een apart te
nemen besluit.

Reasoning: de bugfix van vandaag (`has_delete_permission` toevoegen) herstelde
terecht het bedoelde read-only-gedrag van deze tabellen, maar liet daarmee ook
geen enkele weg meer open om bewust een schone lei te maken — nodig voor testen
(zoals vandaag, waar een volledige reset nodig was om de twee bugs te kunnen
verifiëren) en potentieel voor het corrigeren van een foutief geïmporteerde
periode. De generieke Django `delete_selected`-actie is hiervoor sowieso
ongeschikt gebleken (de `DATA_UPLOAD_MAX_NUMBER_FIELDS`-limiet bij meer dan 1000
rijen, zie hierboven), dus een eigen, doelgerichte actie — met preview en
bevestiging in plaats van rij-voor-rij selecteren — is zowel veiliger als
bruikbaarder. Het periode-scherm sluit ImportedFile bewust uit om het principe
"nooit automatisch/stilletjes herverwerken" (besluit van 01-09-2026, "Trigger-
mechanisme servermap") niet te doorbreken.


## 2026-09-07 (avond) — Label "Gefactureerd" wordt "Totaal (excl. reistijd)" in het weekoverzicht (Current)

Decision: het label "Gefactureerd" in de dag- en weektotalen van het weekoverzicht
(web én Excel-export) wordt "Totaal (excl. reistijd)". De onderliggende berekening
verandert niet — nog steeds de som van `Uren.Aantal` per datum/week, tegenover de
opgetelde duur van de SOORT=W-tijdblokken (zie `docs/functioneel-ontwerp.md` §6,
besluit 05-09-2026). Nog niet gebouwd: wacht op een instructie naar de Claude
Code-sessie, samen met het bug-onderzoek hieronder, zodra Roger klaar is met de
huidige testronde.

Reasoning: tijdens een uitgebreide testronde op 2 juni-data (monteur Dennis van de
Berg) bleek het label misleidend voor uren die wel geboekt zijn maar nooit aan een
klant gefactureerd worden — met name een magazijnbezoek 's ochtends, dat wél in
Uren.xlsx staat maar nooit een werkbon-adres (SOORT W) oplevert. Het getal zelf
klopte al: dit is precies de op 05-09-2026 gedocumenteerde verklaring "uren geboekt
op het eigen bedrijfsadres" (zie `docs/business-rules.md`). Alleen de naam ervoor
was onjuist — "Gefactureerd" suggereert facturatie aan de klant, terwijl het feitelijk
alle geboekte uren van die dag zijn, ongeacht of ze declarabel zijn.

## 2026-09-07 (avond) — Bevinding: begin en einde van de dag ontbreken in de tijdlijn, bug zit in de tijdlijnreconstructie (Current, oorzaak nog niet gevonden)

Bevinding, geen besluit: bij dezelfde testronde bleek het patroon breder dan
aanvankelijk gedacht en dus structureel, niet incidenteel — Roger heeft dit bij
meerdere monteurs nagelopen en het is consistent. Concreet uitgewerkt op de dag
van monteur Dennis van de Berg (medewerkernr. 002), 2026-06-02, aan de hand van
de volledige RouteVision-ritdata voor die dag (6 ritten, `Reis van de dag`
2/11/13/28/30/33):

- Rit 2 (06:49–06:52, thuis → Randweg 1b) en het verblijf tot 12:01 op Randweg
  1b, en rit 11 (12:01–12:10, Randweg 1b → Randweg 6) — ontbreken (al eerder
  vastgelegd hierboven, zie de vorige bevinding).
- Rit 13 (12:10–12:27, Randweg 6 → Kruiwiel 18) en het verblijf bij de klant
  tot 17:11 — **komen wél goed in het weekoverzicht terecht** (Reistijd +
  W-blok WB260779).
- Rit 28 (17:11–17:29, Kruiwiel 18 → Randweg 6d) — **komt wél goed terecht**
  (laatste zichtbare regel: Reistijd 17:11–17:29).
- Rit 30 (17:31–17:32:54, Randweg 6d → Randweg 6), het verblijf op Randweg 6
  tot 22:15 (bijna 4 uur 43 min), en rit 33 (22:15:18–22:19:24, Randweg 6 →
  thuis) — **ontbreken**, net als het ochtenddeel.

Het patroon is dus symmetrisch: alleen het middenstuk van de dag — vanaf de
eerste rit naar een klant/werkbon-adres tot en met de laatste rit terug bij het
depotgebied — komt in de tijdlijn terecht. Alles ervoor (de ochtend bij het
depot) en alles erna (het depot-verblijf en de rit naar huis aan het eind van
de dag) ontbreekt, ongeacht of het om een korte rit of een verblijf van uren
gaat.

Correctie op een eerdere aanname (Roger, 07-09-2026): de `Rit`-tabel in Django-admin
(het ingelezen resultaat, niet de RouteVision-brondata zelf) bevat deze ritten wél —
de import verwerkt alle ritten correct. Het probleem zit dus aantoonbaar bij het
opbouwen van de tijdblokken (de tijdlijnreconstructie), niet bij het inlezen. In
principe zou elke rit die in `Rit` staat een plek moeten krijgen in het
weekoverzicht; dat gebeurt nu niet voor het begin- en eindstuk van de dag.

Nog niet onderzocht in code — deze Cowork-sessie heeft geen codetoegang. De precieze
oorzaak in de reconstructielogica moet Claude Code vaststellen. Wacht op een
instructie naar de Claude Code-sessie, nadat Roger de huidige testronde heeft
afgerond. Zie ook `docs/functioneel-ontwerp.md` §6.

## 2026-09-07 (avond) — Nieuwe SOORT-classificatie 'P' (privé) besloten, nog niet gebouwd (Current)

Decision: naast K (Klant), L (Locatie) en C (Crediteur) komt er een vierde
handmatige SOORT-classificatie: **P (Privé)**. Aanleiding (Roger): bij het achteraf
koppelen van onverklaarde stops (het uitzonderingenscherm, zie `docs/functioneel-
ontwerp.md` §5) is er nu geen manier om een stop die overduidelijk privé is aan te
merken — hij blijft dan als O (onverklaard) in de lijst staan.

Drie deelbeslissingen, bevestigd door Roger:

1. **Mechanisme: adres-classificatie, net als K/L/C.** P wordt een vierde keuze op
   `BekendeLocatie.soort`, gekoppeld via hetzelfde bestaande koppelformulier/
   uitzonderingenscherm uit §5 — geen nieuw scherm, geen monteur-specifieke
   koppeling. Eenmaal een adres als P gekoppeld, geldt dat voor elke monteur die
   daar ooit stopt — zelfde mechanisme en zelfde beperking als nu al geldt voor
   K/L/C (één adres, één classificatie, ongeacht wie er stopt).
2. **Alleen voor stops die nu al als O verschijnen.** Geen wijziging aan de
   tolerantielogica — kortere stops onder de drempel (SOORT ?) blijven
   ongewijzigd niet-koppelbaar, ook niet als P.
3. **P telt niet mee in "Totaal (excl. reistijd)", maar krijgt een eigen, zichtbare
   regel.** Net als de "gefactureerd vs. op locatie"-vergelijking (§6) is dit een
   apart getal naast het bestaande totaal, geen aftrek erop — zodat zichtbaar is
   hoeveel tijd een monteur die dag/week privé onderweg was, zonder dat het als
   werktijd meetelt.

De kleur van P in het codepalet (`docs/ui-spec.md`, `SOORT_KLEUREN`) laat Roger
bewust over aan Claude Code (07-09-2026, avond) — de bestaande zeven kleuren zijn
functioneel gekozen om in een dichte tabel goed van elkaar te onderscheiden te
zijn; P voegt daar een achtste kleur aan toe die net zo goed te onderscheiden moet
zijn, binnen diezelfde paletlogica.

Gebouwd 07-09-2026, commit `117a648` (zie `GUIDELINES.md` punt 20).

## 2026-09-07 — Bugfix en uitbreiding gebouwd; nieuwe restbevinding over thuisdetectie (Current)

De instructie op basis van de drie besluiten hierboven is uitgevoerd door de
Claude Code-sessie, in drie losse commits, elk met eigen tests en documentatie-
bijwerking, niet gepusht:

- `4d219c2` — de tijdlijnbug (begin/einde van de dag ontbrak): root cause was
  dat `home_streets_for()` het thuisadres afleidt uit elke dag-rand zonder
  frequentietoets, waardoor een depotstraat waar een monteur zijn bus ophaalt
  permanent als "thuis" meetelde. `_trim_home_hops()` gooide vervolgens elke
  rit tussen huis/depot weg. Fix: het depot (`is_depot`, op straat én
  postcode) wordt nu uitgesloten bij het afleiden van het thuisadres. Als
  bijvangst ook gefixt: een "straat" zonder letters (RouteVision schrijft `-`
  voor een onbepaalde stop) telde ook als thuisstraat en liet ritten tussen
  twee onbepaalde adressen verdwijnen (trof Jesse Verkerk, 5 ritten). 308
  tests groen. Op de echte juni-dataset: 1169 → 1356 tijdblokken; Dennis van
  de Berg (002), 02-06-2026 toont weer alle 6 ritten.
- `bf1c077` — label "Gefactureerd" → "Totaal (excl. reistijd)", op de pagina,
  in de Excel-export en in de dagregel. Berekening ongewijzigd. 309 tests
  groen.
- `117a648` — SOORT P (Privé): vierde keuze op `BekendeLocatie.soort`, geen
  wijziging aan `_classify_stop()` nodig (P valt vanzelf in de bestaande
  "overige BekendeLocatie"-stap), eigen regel per dag/week (verschijnt alleen
  bij privé-tijd), kleur `#C2185B` (karmijn, gekozen door Claude Code — bewust
  geen rood, dat zou naast het amberkleurige O lezen als "erger dan
  onverklaard"). Migratie 0007 bevestigd een no-op (`sqlmigrate` toont
  `-- (no-op)` voor beide `AlterField`-operaties). 320 tests groen.

**Restbevinding uit de `4d219c2`-analyse, nog niet gebouwd.** Dezelfde
detectie kent nog steeds geen frequentietoets: elke dag-rand, hoe zelden ook,
telt mee als kandidaat-thuisstraat. Bij Dennis van de Berg gelden zo ook
`rolweg` (6 van 50 dagranden) en `forêtweg` (2 van 50) als thuis, bij Maarten
Jaarsma `marsweg` (8 van 46). Over de juni-dataset vallen hierdoor nog 28
ritten over 12 dagen weg — deels terecht (echte ritjes in de eigen straat),
deels niet. Scherpste geval: Dennis van de Berg produceert op 24-06 en 25-06
nul tijdblokken terwijl hij beide dagen 8 uur boekte; alle ritten die dagen
lopen tussen Rolweg-adressen.

**Besluit (Roger, 07-09-2026):** in plaats van een frequentiedrempel te
raden, komt er een expliciet thuisadres-veld. Drie deelbeslissingen:

1. **Nieuwe SOORT-code T (Thuis), niet hergebruik van L.** Eigen kleur en rij
   in de legenda/het codepalet (`docs/ui-spec.md`), net als P een keuze op
   `BekendeLocatie.soort` — zodat het geval dat Roger zelf noemde ("de
   monteur zet zijn auto om de hoek") ook afgedekt is: zo'n nabijgelegen
   adres is dan alsnog als T te koppelen via het bestaande
   uitzonderingenscherm (§5), naast het nieuwe, primaire thuisadres-veld op
   `Monteur`.
2. **Geen terugval meer op de (inmiddels depot-gefixte) frequentiedetectie**
   zodra dit gebouwd is. Een monteur zonder ingevuld thuisadres krijgt zijn
   ochtend-/avondstops gewoon zichtbaar in de tijdlijn (waarschijnlijk als O,
   afhankelijk van de tolerantiedrempel) in plaats van dat het systeem stil
   blijft gokken of ze laat vallen — corrigeerbaar via het bestaande scherm,
   in plaats van onzichtbaar fout.
3. **Geen apart weektotaal voor T**, in tegenstelling tot P. De T-blokken
   staan gewoon in de dagtabel, zonder eigen samengevatte regel — thuis-tijd
   is minder een getal dat je wil optellen dan privé-tijd.

Uitgevoerd 07-09-2026, commit `67b6df4` (zie `GUIDELINES.md` punt 21).

## 2026-09-07 — Thuisadres en SOORT T gebouwd; meegereden-regel en een datavoorval (Current)

**Resultaat.** `Monteur` heeft nu `thuisadres` + `thuisadres_type` (straat/
postcode, beide optioneel, dezelfde precisie en normalisatie als
`BekendeLocatie`; een ingevulde waarde die niet normaliseert wordt geweigerd
in plaats van stilzwijgend leeggemaakt). SOORT T (Thuis) zit op precies de
plek in de prioriteitsvolgorde waar de oude, nu verwijderde thuisstraat-stap
zat — vlak vóór de tolerantiecheck — maar slaat het blok op in plaats van
het te laten vallen. T is daarnaast ook een koppelbare keuze op
`BekendeLocatie.soort` (koppeltabel-stap staat hoger in de volgorde, dus een
handmatige koppeling wint altijd van het veld) — dekt Rogers eigen
"auto om de hoek"-geval. Geen apart dag-/weektotaal voor T. Kleur `#6D4C41`
(bruin), door Claude Code gekozen. Migratie 0008: twee echte kolommen met
default (`''`/`straat`, geen handmatige databewerking nodig) plus twee
no-op-keuzewijzigingen. 327 tests groen.

De frequentiedetectie (`home_streets_for()`, `_home_edge()`,
`_trim_home_hops()`) is volledig verwijderd, geen terugval. Op de echte
juni-dataset komen nu **782 van 782 ritten** in de tijdlijn terecht (was
754 vóór `4d219c2`, 782 na deze stap) — de restbevinding uit de vorige
sessie is dus volledig opgelost, niet alleen voor het depot. Dennis van de
Berg's 24 en 25 juni geven nu 9 en 8 tijdblokken tegen nul voorheen.

**Nieuwe regel, door Claude Code toegevoegd en hier vastgelegd (niet
expliciet in de instructie gevraagd, wel een logische invulling):** op een
"meegereden"-dag (zie `Instelling.meegereden_modus`) telt voor de
thuisadres-herkenning het adres van de tijdlijn-monteur zelf, niet dat van
de senior/bestuurder wiens ritten die dag opbouwen — diens huis is niet het
huis van de meerijder. Zo'n stop komt dan gewoon als onverklaard (O) in de
tijdlijn, corrigeerbaar via het uitzonderingenscherm.

**Datavoorval tijdens het testen, geen bug in de bouwstap zelf.** Bij het
opruimen van een testadres filterde Claude Code op `label__startswith='TEST '`
— SQLite's `LIKE` is hoofdletterongevoelig voor ASCII, dus dit trof ook twee
bestaande, echte rijen (`test 4 klant` op postcode 4104AR en `Test klant` op
4105JC, beide SOORT K, geen depot) en verwijderde ze samen met de testdata.
Beide zijn direct daarna hersteld uit de waarden die eerder in dezelfde
sessie waren uitgelezen, en de matching is opnieuw gedraaid. Roger is
gevraagd deze twee rijen na te kijken voordat er verder gebouwd wordt — zie
`GUIDELINES.md` punt 21/22.

Gepusht en gecontroleerd door Roger — de twee rijen zijn in orde (zie
`GUIDELINES.md` punt 22).

## 2026-09-07 — Besluit: aansluiting per werkbon tussen RouteVision-tijd en Syntess-uren (Current)

**Aanleiding (Roger).** De bestaande dag-/weekvergelijking ("Totaal (excl.
reistijd)" vs. "op locatie", besluit 05-09-2026) is één geblendet cijfer per
dag — de som van alle `Uren.Aantal` die dag tegenover de som van alle
SOORT=W-tijdblokken die dag, ongeacht welke werkbon. Daarmee kan Wim niet
zien of er, per werkbon, tijd is doorgebracht die niet gedeclareerd is — en
dat was feitelijk het hele doel van de app.

**Besluit.** Onder elk dagoverzicht komt een nieuwe tabel, **"Aansluiting per
werkbon"**, náást de bestaande dag-/weekregel (niet ter vervanging — die
blijft als snel totaalcijfer bestaan):

1. **Eén rij per werkbon die die dag voorkomt** — in `Uren.xlsx` en/of als
   `Tijdblok`(SOORT=W) die dag, dus de vereniging van beide bronnen, niet het
   snijvlak. Kolommen: Gedeclareerd (som `Uren.Aantal` voor die werkbon/
   datum) — Op locatie (som duur van de SOORT=W-tijdblokken met die
   werkbon-referentie, die datum) — Verschil.
2. **Altijd alle werkbonnen van die dag, niet alleen de afwijkende.** Een
   werkbon die in `Uren.xlsx` staat maar geen enkel SOORT=W-tijdblok
   oplevert (of andersom: tijd op locatie zonder boeking) moet meteen
   opvallen, niet verborgen zijn omdat er toevallig "geen rij" stond.
3. **Klant-tijd (SOORT K) telt mee, als losse regel.** Een BekendeLocatie
   met SOORT K heeft geen koppeling met een werkbonnummer — die koppeling
   bestaat niet in de data (K komt uit de "overige BekendeLocatie"-stap,
   volledig los van `Uren.xlsx.Werkbon`). Daarom geen aparte "Gedeclareerd"-
   waarde bij K, maar wél een losse regel **"Klant (niet aan werkbon
   gekoppeld)"** onder de werkbon-rijen, met de totale SOORT=K-duur die dag.
   Deze regel telt mee in het dagtotaal onderaan de tabel (Gedeclareerd
   totaal vs. Op locatie totaal inclusief K) — dát dagtotaal is het
   eigenlijke antwoord op Rogers vraag: is er tijd besteed die nergens op
   gedeclareerd is.

**Bewust niet meegenomen (geen scope-uitbreiding zonder overleg):** SOORT L
(Locatie) en C (Crediteur) tellen niet mee — Roger sprak specifiek over
"uren die we aan een klant gekoppeld hebben", niet over locaties of
crediteuren. Ook geen weekniveau-versie van deze tabel — alleen "onder ieder
dagoverzicht", zoals gevraagd; een weektotaal kan later alsnog, als apart
besluit.

**Verhouding tot de bestaande volledigheidscontrole (Werkbonnen.xlsx-check,
besluit 02-09-2026).** Andere vraag, geen duplicaat: die controle signaleert
op werkbon-niveau (de hele levensduur van de werkbon) of een afgeronde
werkbon ooit uren heeft gekregen. Deze nieuwe aansluiting werkt per dag en
vergelijkt twee onafhankelijke, al aanwezige bronnen (geboekte uren vs.
gereconstrueerde ritdata) — precies zoals de bestaande dag-vergelijking al
deed, alleen nu per werkbon in plaats van geblendet.

Uitgevoerd 07-09-2026, commit `69c151b` (zie `GUIDELINES.md` punt 23).

## 2026-09-07 — Aansluiting per werkbon gebouwd; extra regel voor uren zonder werkbonnummer (Current)

**Resultaat.** Precies zoals besloten: de tabel "Aansluiting per werkbon"
staat nu onder elk dagoverzicht, náást de bestaande dag-vergelijking, op de
pagina én in de Excel-export. Alle werkbonnen van de dag krijgen een regel
(ook de kloppende), kolommen Op locatie / Gedeclareerd / Verschil, plus de
losse regel "Klant (niet aan werkbon gekoppeld)" met de SOORT=K-duur. Geen
migratie nodig — beide bronnen (`Uren.Werkbon`/`Aantal` en de werkbon-
referentie op SOORT=W `Tijdblok`-rijen) bestonden al, dit is aggregatie op
weergavemoment. 23 tests erbij, 343 groen.

**Eigen toevoeging van Claude Code, hier vastgelegd als regel.** Bij het
bouwen bleek dat 256 van de 462 urenregels in de juni-dataset géén
werkbonnummer dragen — Kantoor, Verlof, Reisuren, Magazijn onderhoud en
dergelijke. Zonder daar een regel voor toe te voegen, zou het totaal van de
nieuwe tabel niet aansluiten op de bestaande dagregel erboven (die wél al
deze uren meetelt). Er is daarom een tweede losse regel toegevoegd: **"Zonder
werkbonnummer (indirect)"**, met die geboekte-maar-ongekoppelde uren als
losse "Gedeclareerd"-waarde, geen "Op locatie"-kant (die kan er per
constructie niet zijn — geen werkbonnummer betekent geen W-blok om aan te
haken). Een logische, goed onderbouwde aanvulling, niet expliciet gevraagd
maar noodzakelijk om de tabel intern kloppend te maken — vastgelegd zodat het
niet als losse verrassing terugkomt.

**Twee kleine, eveneens niet vooraf besproken maar voor de hand liggende
keuzes:**

- **Een niet-toepasselijke kant toont een gedachtestreepje, nooit 0,00.**
  0,00 zou beweren dat er gemeten is en niets uitkwam; een streepje zegt dat
  de vraag hier niet gesteld wordt (bijv. geen "Op locatie" bij de indirecte
  regel, geen "Gedeclareerd" bij de klant-regel).
- **Geen nieuwe kleur.** Een werkelijk verschil krijgt de bestaande
  waarschuwingskleur (`#D97706`, dezelfde als SOORT O), maar bewust niet op
  de totaalregel — een gereconstrueerde dag heeft vrijwel altijd een verschil
  van een paar centen door afronding, en die zou anders de hele kolom laten
  oplichten zonder dat er iets aan de hand is.

**Geverifieerd op de echte juni-dataset (Docker).** Jesse Verkerk, 17 juni:
werkbon WB260917 toont 1,50 gedeclareerd tegen 0,00 op locatie. Dennis van de
Berg, 6 juni: 0,38 uur klant-tijd zonder enige boeking. Beide gevallen vielen
in de oude, geblendete dagregel volledig weg — precies het probleem dat deze
tabel moest oplossen.

Nog niet gepusht — zie `GUIDELINES.md` punt 24 voor de actuele prioritering
van openstaande punten.

## 2026-09-08 — Thuisadres invullen bij de eerste inrichting — toegevoegd aan de opleverinstructie (Current)

Decision: bij de eerste inrichting (roadmap-fase 7, samen met het echte
SBTT-depotadres) moet voor elke monteur het veld `Monteur.thuisadres`
(straatnaam of postcode) worden ingevuld. De opleverinstructie aan Wim
(zie `docs/functioneel-ontwerp.md` §7) krijgt dit als expliciet punt, naast
het al vastgelegde punt over foutherstel bij het uitzonderingenscherm
(besluit 03-09-2026).

Aanleiding: bij het navragen (08-09-2026) waarom SOORT T (Thuis) nog nergens
in het weekoverzicht verschijnt, bleek dat het testthuisadres dat tijdens de
bouw is gebruikt (Beesdseweg/4104AV bij Dennis van de Berg, zie het besluit
van 07-09-2026 "Thuisadres en SOORT T gebouwd") na verificatie weer is
verwijderd om de dataset niet te vervuilen met testgegevens (`GUIDELINES.md`,
punt 21). Voor de echte monteurs staat het veld dus nog overal leeg — geen
bug, maar een configuratiestap die nog moet gebeuren. Zonder een ingevuld
thuisadres blijft een stop bij een monteur thuis gewoon als onverklaarde (O)
stop in het uitzonderingenscherm staan (corrigeerbaar, maar onnodige ruis in
de eerste weken na oplevering).

Doorgevoerd in: `docs/functioneel-ontwerp.md` §7. Geen codewijziging.

## 2026-09-08 — Klantnaam toegevoegd aan "Aansluiting per werkbon" (Current, besloten, nog niet gebouwd)

Decision: de tabel "Aansluiting per werkbon" (besloten en gebouwd
07-09-2026) krijgt een extra kolom **Klant**, direct naast de
werkbonnummer-kolom, met de naam van de opdrachtgever van die werkbon. Bron:
`Uren.project_opdrachtgever_naam`, hetzelfde veld dat al bij elke Uren-regel
wordt ingelezen. Alleen de werkbon-rijen krijgen een klantnaam; de regels
"Klant (niet aan werkbon gekoppeld)", "Zonder werkbonnummer (indirect)" en
de totaalregel tonen een streepje (–), net als bij de bestaande
niet-van-toepassing-cellen — deze rijen zijn niet aan één specifieke
werkbon gekoppeld.

Aanleiding: Roger gaf aan dat de tabel op zich prima is, maar dat hij bij
het beoordelen van een afwijking niet zonder verder opzoekwerk ziet om welke
klant het gaat.

Fallback wanneer er voor die specifieke (datum, werkbon)-combinatie geen
Uren-regel met een naam is (bijvoorbeeld een werkbon die alleen via de
Werkbonnen.xlsx-postcode-vangnet is gematcht): toon een streepje (–), net
als bij elke andere niet-van-toepassing-cel in deze tabel — geen
opzoekactie in andere Uren-regels van dezelfde werkbon op een andere datum.
Consistent met het bestaande principe in deze tabel: een cel toont "–"
wanneer de vraag niet van toepassing is, nooit een gegokt of breder
opgezocht antwoord.

Wordt toegevoegd op zowel de pagina als in de Excel-export, net als de rest
van deze tabel.

Doorgevoerd in: `docs/functioneel-ontwerp.md` §6, `docs/business-rules.md`
("Designed but not implemented"). Nog niet gebouwd — instructie naar de
Claude Code-sessie volgt.

## 2026-09-08 — Klantnaam bij "Aansluiting per werkbon" gebouwd; aandachtspunt vangnet-rijen blijft openstaan (Current)

Resultaat: gebouwd zoals besloten (zie het besluit hierboven). 349 tests
groen (was 343). `AansluitingRegel.klantnaam` op de werkbon-rijen, gevuld
uit `Uren.project_opdrachtgever_naam` voor exact die (datum, werkbon)
combinatie; de KLANT/INDIRECT-regels en de totaalregel tonen een streepje.
Op de pagina en in de Excel-export (kolom 2, die in deze tabel al vrij
stond tussen Werkbon en Op locatie — KOL_TIJD is ongemoeid gebleven).

Aandachtspunt, gemeld door Claude Code tijdens de bouw: een werkbon die op
een dag alleen via de Werkbonnen.xlsx-postcode-vangnet wordt gematcht
(besluit 03-09-2026) kan zonder eigen `Uren.xlsx`-regel voor precies die
datum in de tijdlijn belanden — de vangnet leest immers `WerkbonControle`
(Werkbonnen.xlsx), niet `Uren`. In dat geval is er ook geen
`project_opdrachtgever_naam` om te tonen, ook al is de naam voor diezelfde
werkbon op een andere datum wel bekend. Dit is exact de bewust gekozen
"geen opzoekactie op een andere datum"-regel (zie het besluit hierboven),
maar kan op echte data een merkbaar deel van de rijen raken.

Besluit (Roger, 08-09-2026): voorlopig zo laten. Pas op echte data
opnieuw bekijken hoe vaak dit voorkomt, in plaats van nu al te verruimen
naar een bredere zoekactie over andere datums van dezelfde werkbon.

## 2026-09-08 — RouteVision-dekkingsgaten verklaard: vakantie, geen exportprobleem (Current)

Bevinding: de twee dekkingsgaten die bij het testen met echte augustus-data
naar boven kwamen (zie de bevinding van 07-09-2026, "Schone herimport +
herberekening", en `GUIDELINES.md` punt 17) zijn verklaard. Roger heeft
rechtstreeks toegang tot RouteVision gekregen: bij Maarten Jaarsma ontbreekt
data tussen 15-08 en 01-09-2026, waarna de data weer terugkomt; bij Dennis
van de Berg geldt hetzelfde patroon. Uit een eerder gesprek met Wim is
bekend dat zijn personeel in die periode met vakantie was.

Reasoning: geen structureel exportprobleem met RouteVision of Stric, dus
geen verdere actie nodig richting die partijen. De 8 uur die bij Dennis in
week 33 wél geboekt stonden in Syntess passen in dit beeld: verlofuren
worden daar gewoon als geboekte uren vastgelegd (dezelfde categorie als
kantoor/reisuren/magazijnonderhoud, zie `docs/business-rules.md`), ook al
is er die dag geen enkele rit. Het bestaande gedrag van de app — zo'n week
melden als "onvolledige week" omdat er geen ritdata is om een tijdlijn op
te bouwen, met de wél-geboekte (verlof)uren apart getoond — is precies het
bedoelde gedrag (`docs/business-rules.md`, "Een week is nooit stil
onvolledig"). Geen wijziging nodig aan de matchlogica, het weekoverzicht of
de tolerantielogica.

Doorgevoerd in: `GUIDELINES.md` (punt 27). Geen codewijziging.

## 2026-09-08 — Klant/leverancier-suggestie in het koppelformulier, op basis van Relatie (Current, besloten, nog niet gebouwd)

Decision: het koppelformulier van het uitzonderingenscherm (§5) krijgt een
suggestie op basis van `Relatie`, niet een automatische classificatie. Als
de postcode van een onverklaard adres matcht met precies één relatie in
`Relatie`, worden `soort` en `label` in het formulier voorgevuld (net als
`type`/`waarde` nu al gebeurt via `_beginwaarden()`); de gebruiker moet nog
steeds zelf op "Koppelen" klikken om dit te bevestigen, precies zoals bij
elke andere K/L/C/P/T-koppeling vandaag. Matcht de postcode met meerdere,
verschillende relaties, dan toont het scherm een keuzelijst van de
kandidaten (naam + K/L); kiest de gebruiker er geen, dan werkt het
formulier zoals vandaag (leeg, handmatig invullen).

Aanleiding: Wim heeft een aangepaste Relaties.xlsx aangeleverd met een
nieuwe kolom "Klant of leverancier" (K/L), naar aanleiding van de oude
openstaande vraag in `docs/functioneel-ontwerp.md` §9 (punt 3, vastgelegd
02-09-2026) of RVS Solutions dit onderscheid ooit aan de export zou
toevoegen. Roger vroeg terecht door of dit dan niet gebruikt zou moeten
worden om het handmatige koppelwerk in het uitzonderingenscherm te
verminderen, in plaats van de kolom ongebruikt te laten zoals `Relatie` nu
al is (alleen een read-only importtabel, nergens gelezen door de
matchmotor, zie `matching/admin.py`).

Twee technische beperkingen bepaalden de precieze invulling:

1. **Alleen op postcode te matchen, niet op huisnummer.** `Relatie` heeft
   Postcode en Huisnr als losse velden, maar
   `matching/timeline/normalize.py` knipt het huisnummer bewust af bij elk
   RouteVision-adres — een al in de PoC gevalideerde regel, omdat
   RouteVision en Syntess het vaker oneens zijn over huisnummers dan over
   straatnamen. Er is dus geen betrouwbaar huisnummer op stop-niveau om
   `Relatie.huisnr` tegen te leggen. Matchen op postcode alleen (dezelfde
   precisie als de rest van de app) brengt hetzelfde over-claim-risico mee
   als het straat-niveau depotrisico (`docs/decisions.md`, 03-09-2026) —
   een postcode kan meerdere panden dekken. Omdat dit een suggestie is en
   geen automatische classificatie, ziet de gebruiker de suggestie en kan
   hij afwijken; dat maakt dit risico acceptabel.
2. **Lettermapping K/L (Relatie) naar K/C (`BekendeLocatie.soort`).**
   Relatie gebruikt Klant/Leverancier (K/L); `BekendeLocatie.soort`
   gebruikt Klant/Locatie/Crediteur (K/L/C, plus P/T). Een Leverancier
   ("L" in Relatie) moet als SOORT **C** (Crediteur) voorgesteld worden —
   niet als "L", want dat betekent in `BekendeLocatie.soort` "Locatie",
   een heel ander begrip. Expliciet vastgelegd omdat een letterlijke
   1-op-1 kopie van de letter een stille misclassificatie zou zijn.

Reasoning voor "suggestie, geen automatisch" (Roger, 08-09-2026): de
bestaande K/L/C/P/T-koppelingen worden allemaal door een mens bevestigd —
dat is een bewuste kwaliteitscontrole (`docs/decisions.md`, 03-09-2026,
Uitzonderingenscherm-ontwerp). Een suggestie respecteert die controle en
lost toch het grootste deel van het typewerk op; volledig automatisch zou
het over-claim-risico van punt 1 hierboven zonder controle laten
doorwerken.

Timing: Roger wil dit vóór de oplevering meenemen, ook al stond het niet in
de oorspronkelijke OvO-scope — het is een kans die pas ontstond doordat Wim
deze aangepaste export nu aanleverde.

Doorgevoerd in: `docs/functioneel-ontwerp.md` §5/§9, `docs/business-rules.md`
("Designed but not implemented"), `GUIDELINES.md` (punt 28). Nog niet
gebouwd — instructie naar de Claude Code-sessie volgt.

## 2026-09-08 — Klant/leverancier-suggestie gebouwd (Current)

Resultaat: gebouwd zoals besloten (zie het besluit hierboven, "Klant/
leverancier-suggestie in het koppelformulier, op basis van Relatie"). 364
tests groen, 15 nieuwe (was 349). Concreet:
`Relatie.klant_of_leverancier` (migratie `0009`, blank toegestaan zodat een
oudere Relaties.xlsx zonder die kolom gewoon blijft importeren),
`_relatie_suggesties()` + `_beginwaarden(groep, request)` in
`matching/views.py`, en de keuzelijst in `koppelen.html` als gewone
GET-links (`?suggestie=<code>`), zonder JavaScript — hetzelfde
server-rendered patroon als de rest van dat scherm.

De lettermapping uit punt 2 van het besluit is vastgelegd in een test die
naast `assertEqual(..., Soort.CREDITEUR)` ook expliciet
`assertNotEqual(..., Soort.LOCATIE)` controleert. Die tweede assert is er
puur om een latere "versimpeling" naar een 1-op-1 lettercopy hard te laten
omvallen in plaats van stilzwijgend elke leverancier als Locatie weg te
zetten.

Drie tests die Claude Code er zelf bij heeft gezet, elk op een randgeval dat
tijdens de bouw opviel:

1. **Postcode-normalisatie aan beide kanten.** `Relatie.postcode` staat ruw
   uit Excel in de database (anders dan `BekendeLocatie.waarde`, die bij het
   opslaan wordt genormaliseerd), dus "4104 ar" en "4104AR" zijn hetzelfde
   adres in twee spellingen. Getest met spatie én kleine letters.
2. **Een onbekende `?suggestie=`-waarde vult niets voor.** Een oude of
   geknutselde URL mag geen willekeurige kandidaat voorinvullen; er gebeurt
   dan hetzelfde als bij "geen keuze gemaakt".
3. **Dezelfde relatie op meerdere rijen telt één keer.** Een relatie kan met
   een rij per contactpersoon in het bestand staan; drie keer dezelfde naam
   zou als drie verschillende kandidaten lezen en onnodig de keuzelijst
   oproepen.

Eén bewuste afwijking van de instructie, gemeld door Claude Code: het
`class="actief"` op de gekozen kandidaat deed niets, omdat de bestaande
`.actief`-regel in `basis.html` gescoped is op `header.balk`. Zonder eigen
opmaak zou de gemaakte keuze er identiek uitzien als de andere kandidaten,
terwijl de enige andere terugkoppeling (het ingevulde formulier) verderop op
de pagina staat. Opgelost met een klein eigen `{% block stijl %}` in
`koppelen.html`.

Eén implementatiedetail dat afwijkt van hoe de rest van de app matcht: de
vergelijking loopt in Python over de `Relatie`-rijen in plaats van in de
query, juist omdat `Relatie.postcode` niet genormaliseerd is opgeslagen. Bij
een stamtabel van enkele duizenden rijen is dat verwaarloosbaar; bewust niet
vooraf geoptimaliseerd met een extra genormaliseerde kolom, zolang dat niet
meetbaar knelt.

Doorgevoerd in: `docs/functioneel-ontwerp.md` §5, `docs/business-rules.md`
("Implemented"), `docs/changelog.md`, `GUIDELINES.md` (punt 29).

## 2026-09-08 — De ruwe Atrium-export is niet leesbaar zonder tussenkomst van Excel; ingest-laag tolerant gemaakt (Current)

Bevinding, aan het licht gekomen bij het importeren van de nieuwe
`Relaties.xlsx` van Wim (het bestand waarvoor de klant/leverancier-suggestie
hierboven juist was gebouwd): de import mislukte met
`TypeError: BookView.__init__() got an unexpected keyword argument
'WindowWidth'`.

Oorzaak: Atrium schrijft in `xl/workbook.xml` de attribuutnamen
`WindowWidth`/`WindowHeight` met een hoofdletter W, terwijl OOXML —  en dus
openpyxl — `windowWidth`/`windowHeight` voorschrijft. Dezelfde soort fout zit
in het werkblad: `firstPageNo` in plaats van `firstPageNumber`. Excel trekt
zich daar niets van aan en corrigeert het stilzwijgend bij het opslaan.

**Wat dit onthulde is groter dan dat ene bestand.** Elk voorbeeldbestand
waarmee tot nu toe getest is, is ooit door Microsoft Excel geopend en
opgeslagen — aantoonbaar aan de Excel-revisienamespaces (`xr`/`xr2`/`xr6`),
een `fileVersion`-tag met buildnummer, en in het oude Relaties-voorbeeld zelfs
een OneDrive-pad (`.../PRIVE/Desktop/STROES backup/`) in de XML. Die
Excel-tussenstap repareerde de afwijking, en maskeerde daarmee dat de app de
échte export helemaal niet kon lezen. Het nieuwe bestand van Wim was de eerste
volstrekt ongemoeide Atrium-export die dit project ooit heeft ingelezen, en
het brak meteen. Op de servermap komen bestanden rechtstreeks uit Atrium — daar
is geen Excel die eerst schoonpoetst.

Voorbehoud bij die conclusie: er is één ruwe export om op te baseren. Dat het
Uren/Werkbonnen even goed raakt is een sterke gevolgtrekking, geen bewijs.

Tweede, losstaand probleem in hetzelfde bestand: de kolomkop luidt
`klant of leverancier` met een kleine k, terwijl de parser exact op
`"Klant of leverancier"` zocht — `read_excel_rows()` matcht hoofdlettergevoelig.
Zonder fix zou de kolom als leeg zijn binnengekomen en had de suggestie die
hierboven net gebouwd is stilzwijgend niets gedaan.

Decision (Roger, 08-09-2026): beide problemen oplossen in de gedeelde
ingest-laag (`matching/ingest/parsers/base.py`), niet in `relaties.py` alleen.
De onderliggende oorzaak — een systeem buiten onze controle dat
niet-conforme XML en afwijkende hoofdletters schrijft — geldt voor Uren,
Werkbonnen en de RouteVision-CSV net zo goed.

1. **XML-reparatie vóór het inlezen.** `_gerepareerd_workbook_bestand()` opent
   het `.xlsx` als zip, corrigeert alleen de drie letterlijk aangetroffen
   tokens in de XML onder `xl/`, en geeft een kopie in het geheugen aan
   openpyxl. Bewust geen brede XML-normalisatie: alleen wat feitelijk is
   waargenomen, want gokken naar wat Atrium verder fout zou kunnen doen
   introduceert risico op bestanden die nu prima werken. Een conform bestand
   krijgt het pad zelf terug — de reparatie is dan een no-op, vastgelegd in een
   test. Het bronbestand op de share wordt nooit overschreven: dat is een
   inbox waar alleen uit gelezen wordt, en een gerepareerd bestand mag niet
   stilletjes vervangen wat het klantsysteem heeft aangeleverd.
2. **Hoofdletterongevoelige kolomnamen.** `_KolomWaarden` (een dict-variant)
   beantwoordt een exacte naam exact — dus niets verandert voor de kolommen
   die al werkten — en valt alleen terug op kleine letters als de exacte naam
   niet bestaat. Dezelfde tolerantie in de `required_columns`-check van beide
   readers. Geen enkele parser hoefde hierdoor aangepast te worden;
   `relaties.py` blijft letterlijk `values.get("Klant of leverancier")` doen.

Regressietest: `factories.ruwe_atrium_workbook()` maakt een workbook na met
exact dezelfde twee afwijkende XML-fragmenten als Wims bestand. Eerst is
geprobeerd het échte bestand uitgedund als binaire fixture bij te voegen, maar
dat botst met een expliciete projectregel: `.gitignore` weert álle workbooks
("Client data ... personal data, AVG") en er staat dan ook geen enkele .xlsx in
de repository — ook de voorbeelddata niet. Een klantbestand toevoegen zou die
regel doorbreken voor een testdoel dat net zo goed nagemaakt kan worden.

Dat namaken is geen zwakkere test: `test_openpyxl_alone_cannot_read_it`
controleert dat openpyxl het gegenereerde bestand wél degelijk weigert, dus als
de nagemaakte afwijking ooit niet meer klopt, valt die test om in plaats van de
rest stilzwijgend op de verkeerde gronden te laten slagen. Een tweede test
bewaakt dat het bronbestand na het inlezen byte-voor-byte onveranderd is.

Resultaat na de fix: 379 tests groen (was 364, 15 nieuw). Het bestand
importeert: 2561 relaties, 1826× "K", 715× "L", 20 leeg. Van de 61 openstaande
onverklaarde groepen in de juni-data krijgen er 23 een suggestie (9 met precies
één kandidaat, 14 met een keuzelijst) — samen 38 van de 103 onverklaarde stops.

Nog te doen, los hiervan en niet blokkerend: Wim/RVS Solutions melden dat de
Atrium-export niet-schemaconforme XML schrijft. De app heeft er geen last meer
van, maar elk ander programma dat deze bestanden leest wel.

Doorgevoerd in: `docs/architecture.md`, `docs/changelog.md`, `GUIDELINES.md`
(punt 30).

## 2026-09-08 — Knop "Bestanden nu inlezen" op het matchmotor-beheerscherm (Current, besloten; gebouwd — zie de entry onderaan)

Decision: er komt een derde knop op het bestaande matchmotor-beheerscherm
(`MatchmotorStatusAdmin`), naast de al bestaande "Matching nu draaien" en
"Data resetten": **"Bestanden nu inlezen"**. Deze roept `scan_share(force=True)`
aan — dezelfde functie die `check_imports --force` vanaf de command line al
aanroept — zonder de `--reprocess`-optie: alleen bestanden die nog niet als
verwerkt gemarkeerd staan worden ingelezen, precies zoals de achtergrondpoller
dat ook doet, alleen dan direct in plaats van na de stabiliteitsmarge. De knop
draait de matching niet automatisch mee — dat blijft een aparte, bewuste stap
via de bestaande "Matching nu draaien"-knop.

Aanleiding: bij het testen van de klant/leverancier-suggestie bleek dat een
nieuw bestand in de inbox zetten niet hetzelfde is als het importeren ervan —
Roger moest handmatig `docker compose exec web python manage.py check_imports
--path /app/data/inbox --force` draaien om het direct te zien. SBTT-staff heeft
geen shell, dus voor productiegebruik is dat sowieso geen optie.

Reasoning: dit is exact het patroon dat al bestaat voor "Matching nu
draaien", met dezelfde reden ("SBTT staff have no shell", zie de
docstring van `MatchmotorStatusAdmin`). Geen reprocess-optie in de knop:
het herimporteren van al-verwerkte bestanden is een zeldzaam, risicovol
geval (dubbele import) en blijft daarom bewust alleen via de command line
beschikbaar, zoals dat nu ook al zo vastligt. Geen automatische koppeling
met de matching: consistent met hoe deze app overal expliciete stappen
houdt in plaats van impliciete kettingreacties.

## 2026-09-08 — Ingest-laag tolerant gemaakt voor niet-schemaconforme Atrium-XML en kolomnaam-hoofdletters (Current, besloten; gebouwd — zie "De ruwe Atrium-export is niet leesbaar zonder tussenkomst van Excel" hierboven)

Decision: `matching/ingest/parsers/base.py` (de gedeelde lezer die alle vier
de parsers gebruiken) wordt op twee punten toleranter gemaakt:

1. **Niet-schemaconforme XML repareren vóór het inlezen.** Het nieuwe
   `Relaties.xlsx` van Wim schrijft `WindowWidth`/`WindowHeight` (met
   hoofdletter) in plaats van `windowWidth`/`windowHeight`, en
   `firstPageNo` in plaats van `firstPageNumber` — beide OOXML-attributen
   die de standaard met een kleine letter voorschrijft. `openpyxl` weigert
   het bestand daardoor met een `TypeError`. De drie bekende, exacte tokens
   worden voortaan in het geheugen gecorrigeerd vóór `openpyxl` het bestand
   ziet — geen brede XML-normalisatie, alleen deze specifieke, aangetoonde
   gevallen.
2. **Kolomnaam-matching hoofdletterongevoelig maken.** De nieuwe kolom heet
   in de praktijk `klant of leverancier` (kleine letter), terwijl de
   parser exact op `Klant of leverancier` zocht. Zowel de
   `required_columns`-check als de opgebouwde waarden per rij worden
   hoofdletterongevoelig, met voorrang voor een exacte match zodat niets
   verandert voor kolommen die nu al goed werken.

Aanleiding: bij het testen van de klant/leverancier-suggestie faalde de
import van het nieuwe Relaties.xlsx volledig (Relatie-tabel bleef leeg).
Onderzoek wees uit dat dit het eerste bestand is dat de app ooit onder ogen
kreeg zonder ooit door Excel geopend en opgeslagen te zijn — geverifieerd
door de workbook-XML van het oude testbestand (met Excel-revisienamespaces
en een `fileVersion`-buildnummer) te vergelijken met die van het nieuwe
bestand (kaal, zonder die Excel-toevoegingen). Excel repareert dit soort
afwijkingen stilzwijgend bij het opslaan, wat het probleem tot nu toe heeft
gemaskeerd in elk voorbeeld-/testbestand.

Reasoning: dit raakt de ingest-laag, niet de Relaties-parser alleen — Uren,
Werkbonnen en de RouteVision-CSV komen van hetzelfde systeem (Atrium/Syntess)
en zijn tot nu toe ook alleen ooit als door-Excel-behandeld bestand getest.
Op de productieserver komt straks alleen de ongemoeide vorm binnen. Niet
gewacht op een fix bij de bron (RVS Solutions, onbekende doorlooptijd) omdat
fase 7 (oplevering) er aan zit te komen; het melden bij Wim/RVS gebeurt wel,
los van en niet blokkerend op deze fix. Reparatie bewust minimaal gehouden
(drie exacte tokens, geen generieke normalisatie) om geen nieuwe risico's
te introduceren op basis van een aanname over wat Atrium verder nog fout
zou kunnen doen.

## 2026-09-08 — Knop "Bestanden nu inlezen" gebouwd (Current)

Resultaat: gebouwd zoals besloten (zie de besluit-entry van dezelfde dag).
391 tests groen (was 379). `bestanden_inlezen_view` in `matching/admin.py`,
naar het model van de bestaande `run_matching_view`: POST-only via
`require_POST`, gated op `matching.change_matchmotorstatus` (dezelfde
constructie als daar — `has_change_permission()` is voor iedereen False omdat
de rij niet bewerkbaar is, maar de knop indrukken *is* een wijziging), en een
redirect terug naar de changelist met een melding.

De knop staat boven "Matching nu draaien": dat is de volgorde waarin de twee
stappen gezet worden. In de container gecontroleerd op de echte data — knop
staat op het scherm, POST geeft "Niets nieuws om in te lezen" (alle vier de
bestanden stonden al op verwerkt) en het aantal tijdblokken bleef gelijk, dus
er draaide inderdaad geen matching mee.

Eén afwijking van de instructie, bewust: de melding "Niets nieuws om in te
lezen" verschijnt alleen als er ook niets is mislukt. Letterlijk uitgevoerd zou
een run waarin één bestand stukliep zowel "Niets nieuws om in te lezen" als
"Mislukt: …" tonen, en dat spreekt zichzelf tegen — er is dan wel degelijk iets
gebeurd, het ging alleen mis. Een test legt dat vast.

Doorgevoerd in: `docs/functioneel-ontwerp.md` §4, `docs/business-rules.md`
("Implemented"), `docs/changelog.md`, `GUIDELINES.md` (punt 33).

Terzijde, opgemerkt bij het bijwerken: `GUIDELINES.md` had twee punten met
nummer 30 en twee documenten droegen tegelijk een "nog niet gebouwd"-entry
voor de ingest-fix die al gebouwd én gepusht was. Dat komt doordat er die dag
vanuit twee sessies tegelijk aan dezelfde documenten is geschreven. De
nummering is rechtgezet (31/32 doorgeschoven) en de achterhaalde entries
verwijzen nu naar de gebouwd-entry, in plaats van ze te verwijderen — zoals
elders in dit bestand blijft een eerder besluit staan en haalt een latere
entry hem in.

## 2026-09-08 — Zelfkoppeling bij "vast meerijden" tegengaan; klacht over niet-verwijderbare koppeling nader te onderzoeken (Uitgevoerd)

Decision: `Monteur.vaste_meerijder` krijgt dezelfde zelfkoppeling-check als
`MeegeredenKoppeling` al heeft — een monteur mag zichzelf niet als eigen
vaste meerijder kiezen. Zowel een `clean()`-validatie met een Nederlandse
foutmelding als een databaseconstraint, zelfde patroon en bewoording als
`MeegeredenKoppeling.clean()`/`meegereden_junior_is_not_senior`.

Een tweede klacht — een vastgelegde vaste koppeling is in het
beheerscherm wel te wijzigen maar niet te verwijderen (leeg maken) — kon
niet in de code worden bevestigd: `vaste_meerijder` staat op
`null=True, blank=True` en `MonteurAdmin` heeft geen aangepast formulier
dat dit zou blokkeren. Besloten: eerst live natesten in de container
(zelfde aanpak als bij de importknop) voordat hier een fix voor bedacht
wordt — een gok zou het verkeerde probleem kunnen oplossen.

Aanleiding: Roger meldde beide bij het uitproberen van "monteur vast laten
meerijden" via het beheerscherm, en vroeg daarnaast of de
meegereden-functionaliteit (Vast/Periode) daadwerkelijk werkt en of een
vaste koppeling kan overlappen met een periode-koppeling.

Ter info, geen actie: de meegereden-functionaliteit werkt —
`resolve_bronmonteur()` wordt aangeroepen vanuit
`matching/timeline/engine.py` en beide standen hebben eigen testdekking
(`test_timeline.py`, `test_run_matching.py`). Een vaste koppeling kan niet
overlappen met een periode-koppeling: `Instelling.meegereden_modus` is één
globale instelling, dus de matching leest altijd maar één van de twee
bronnen; de andere staat stil in de database, ongebruikt maar niet gewist.
Er is wel al een overlap-check, maar alleen tussen twee
periode-koppelingen van dezelfde junior onderling
(`MeegeredenKoppeling._check_no_overlap`, 07-09-2026).

Reasoning: zelfde reden als bij `MeegeredenKoppeling` destijds — twee
monteurs (hier: één monteur met zichzelf) die aan elkaar gekoppeld zijn
maakt de matching-uitkomst zinloos/ongedefinieerd. Geen aanname over de
tweede klacht zonder het eerst te reproduceren: de code biedt geen enkele
aanwijzing voor een bug, dus eerst kijken wat er in de draaiende app
werkelijk gebeurt.

Uitkomst: beide punten zijn afgerond. De zelfkoppeling-check is gebouwd
(`CheckConstraint` + `clean()`-validatie, migratie `0010`). De tweede
klacht is live gereproduceerd in de container en bleek geen codefout —
leeg selecteren en opslaan wist het veld gewoon. Waarschijnlijke oorzaak:
Django's standaard leeg-label `---------` leest niet als "verwijderen".
Opgelost met een duidelijker label ("— geen vaste meerijder —") op
`MonteurAdmin`, in plaats van een codewijziging voor een niet-bestaande
bug. Het verouderde code-commentaar in
`matching/timeline/meegereden.py` (`_koppeling_op()`) is tegelijk
rechtgezet. 398 tests groen (was 391). Commit `bcd57af` op `main`.

## 2026-09-09 — Knop "Bestanden uploaden" als terugval voor de servermap (Current, gebouwd)

Decision: een vierde knop op het matchmotor-beheerscherm, onder "Matching nu
draaien", "Data resetten" en "Bestanden nu inlezen": **"Bestanden uploaden"**.
Een gewone `<input type="file" multiple accept=".xlsx,.csv">` in de browser,
waarmee Wim de Syntess- en RouteVision-bestanden zelf kan aanleveren. De
geüploade bestanden gaan onder hun eigen naam naar diezelfde inbox-map
(`SERVERMAP_PATH` / `RMW_INBOX_DIR`) die `scan_share()` al afloopt, waarna
direct `scan_share(force=True)` draait. Uitdrukkelijk een terugval, geen
vervanging van de share-route.

Reasoning: de netwerkshare (`\\stroes-1909\atrium\Autoprint\RUUDS`) is bij
Stric nog niet werkend, en fase 7 (oplevering) komt eraan. Zonder deze knop is
de app onbruikbaar zolang die share er niet is — met de knop kan SBTT
doorwerken. Bewust *dezelfde* map als bestemming en geen aparte uploadmap: dan
blijft er één inbox en één verhaal over wat er is ingelezen, en is een geüpload
bestand vanaf het moment dat het er staat niet meer te onderscheiden van een
bestand dat de export er zelf neerzette (zelfde `ImportedFile`-rij, zelfde
statusverloop). Een tweede map zou een tweede, half-parallelle importweg zijn
geworden.

Uploaden en inlezen zijn hier bewust één handeling, anders dan bij "Bestanden
nu inlezen": de stabiliteitsmarge bestaat om een bestand te vangen dat een
exportjob nog aan het schrijven is, en een bestand dat compleet over HTTP is
binnengekomen heeft niets meer om op te wachten. De matching draait er níét
achteraan — dat blijft overal in deze app een aparte, bewuste stap.

Twee weigeringen, allebei per bestand zodat één onbruikbaar bestand de rest van
de batch niet kost (zelfde redenering als de foutafhandeling per bestand in
`scan_share`):

- **Naam bestaat al op de servermap** — geweigerd, nooit overschreven. Het
  bestand dat er staat kan juist het al ingelezen bestand zijn; het vervangen
  zou zijn `ImportedFile`-rij iets anders laten beschrijven dan wat er op
  schijf ligt. Geïmplementeerd door te openen met `"xb"` in plaats van een
  `exists()`-controle gevolgd door `"wb"`, zodat controleren en schrijven één
  stap zijn.
- **Naam die `classify_filename()` niet herkent** — geweigerd in plaats van
  weggeschreven. Zou hij wél op de share belanden, dan negeert `scan_share()`
  hem stilzwijgend en denkt de uploader dat hij hem heeft aangeleverd.

Er wordt achteraf niets opgeruimd, om dezelfde reden als op de share: de
database alleen registreert wat er is gedaan, bestanden worden nooit verplaatst
of verwijderd (`docs/architecture.md`).

Eén afweging expliciet gemaakt: de instructie vroeg om een POST-only endpoint
én om "een klein uploadformulier". Die twee sluiten een apart GET-scherm uit,
dus het formulier staat inline op het beheerscherm zelf — één scherm, één POST,
zelfde patroon als de drie knoppen erboven.

Uitkomst: gebouwd. `bestanden_uploaden_view` plus de helpers `_bewaar_upload`
en `_meld_scanresultaat` in `matching/admin.py`; die laatste is uit
`bestanden_inlezen_view` getrokken en wordt nu door beide importknoppen
gebruikt, zodat een import in dezelfde bewoordingen wordt gemeld ongeacht hoe
het bestand op de servermap terecht is gekomen. 411 tests groen (was 398),
waarvan 13 nieuwe: permissie, POST-only, dubbele naam, onbekende naam, geen
automatische matching, en een geslaagde upload van meerdere bestanden. Commit
`72840db`.

Terzijde: het normaliseren van de aangeleverde bestandsnaam tot alleen de
laatste padcomponent is dubbelop — Django's `MultiPartParser` doet dat zelf al
(`sanitize_file_name`). Het staat er toch, omdat die naam hier een pad wordt
waarnaar geschreven wordt; de test die het afdekt legt de garantie vast, niet
die ene regel.

Doorgevoerd in: `docs/functioneel-ontwerp.md` §4, `docs/business-rules.md`
("Implemented"), `docs/changelog.md`, `GUIDELINES.md` (punt 35).

## 2026-09-09 — Importbestanden alleen-lezen; uploadblok bovenaan (Current, gebouwd)

Twee losse punten van dezelfde ronde.

**1. `ImportedFileAdmin` alleen-lezen.** Decision: `ImportedFile`
(schermnaam "Importbestanden") krijgt dezelfde `has_add_permission` /
`has_change_permission` / `has_delete_permission` op False als de andere
niet-bewerkbare tabellen, door van `ReadOnlyImportAdmin` te erven.

Let op de status van dit besluit: dit is een **nieuw** besluit, geen
achterstallige uitvoering van een oud besluit. Het besluit van 03-09-2026
("MatchmotorStatus wordt read-only", met de aanvulling van 07-09-2026 over
verwijderen) noemt `Uren`, `Rit`, `Relatie`, `WerkbonControle`, `Tijdblok`,
`MatchmotorStatus` en `Instelling` — `ImportedFile` stond daar niet bij en
werd in `docs/changelog.md` (02-09-2026) juist apart genoemd als het scherm
dat "de status per bestand toont". Er is dus niet eerder iets besloten en
vergeten te bouwen; de tabel is altijd bewerkbaar geweest.

Reasoning: van alle tabellen is dit de gevaarlijkste om open te laten staan.
De andere zijn een kopie van de servermap — een handmatige wijziging maakt de
database daar hooguit oneens mee, en de volgende import zet het recht. Deze is
geen kopie maar de eigen administratie waar zowel `scan_share()` als de
matching op afgaan. Een met de hand op "verwerkt" gezette status laat de app
een bestand overslaan dat nooit is ingelezen, en er is niets aan het scherm te
zien waaraan dat op te merken valt.

Bewust geaccepteerd gevolg: het verwijderen van één `ImportedFile`-rij was tot
nu toe de enige manier om via de admin één specifiek bestand opnieuw te laten
inlezen (zonder rij maakt `scan_share()` een nieuwe aan en importeert opnieuw).
Die weg is nu dicht. Dat sluit aan op wat `docs/architecture.md` al
voorschrijft — herverwerken is command-line-only — maar het is een echt
verschil: een gerichte herimport vraagt voortaan `check_imports --reprocess`,
of anders "Data resetten" (volledig, superuser-only). Voor SBTT zelf is dat
geen verlies, want herverwerken was voor hen sowieso geen bedoelde handeling.

**2. "Bestanden uploaden" bovenaan.** Decision: het uploadformulier verhuist
van de laatste naar de eerste sectie van het matchmotor-beheerscherm, in een
eigen `.module`-blok met een eigen koptekst en een accentrand, in plaats van
onderaan achter een kale `<hr>`.

Reasoning: de plaatsing onderaan volgde de gedachte "terugval, dus niet in de
weg lopen". Dat klopt niet zolang de netwerkshare van Stric nog niet werkt: dan
is dit niet de uitzondering maar de enige manier om data in de app te krijgen,
en dan hoort het niet onder drie secties te staan die allemaal aannemen dat die
servermap het wél doet. De werkvolgorde van de dagelijkse knoppen eronder
blijft ongewijzigd.

Puur een template-wijziging: `bestanden_uploaden_view` is niet aangeraakt en
houdt al zijn eigenschappen (POST-only, gated op
`matching.change_matchmotorstatus`, schrijven naar dezelfde inbox-map, daarna
`scan_share(force=True)`, weigering van een dubbele naam via `"xb"` en van een
onbekende naam per bestand).

Uitkomst: beide gebouwd. 419 tests groen (was 411): de bestaande
alleen-lezen-tests draaien nu over zes modellen en controleren alle drie de
rechten, met daarnaast een eigen testklasse die het importbestanden-scherm door
de schermen heen controleert, plus één test die de sectievolgorde op de pagina
vastlegt. Gecontroleerd op de gerenderde pagina `/admin/matching/importedfile/`:
statuscode 200, geen `.../importedfile/add/`-link, een leeg
`<ul class="object-tools">` (daar zou de knop staan) en een lege actielijst;
de enige `addlink`-elementen op die pagina horen bij andere modellen in de
zijbalk (Gebruikers, Groepen, Bekende locaties, Instellingen, Meegereden
koppelingen, Monteurs, Tolerantietabel). Commits `cad4165` en `4c273f2`.

Doorgevoerd in: `docs/business-rules.md`, `docs/functioneel-ontwerp.md` §4,
`docs/changelog.md`, `GUIDELINES.md` (punt 36).

## 2026-09-11 — Een herberekening ruimt vervallen dagen op binnen de eigen selectie (Current)

Decision: `run_matching(..., force=True)` — de "Matching nu draaien"-knop en
`python manage.py run_matching --force` — verwijdert voortaan ook de opgeslagen
`Tijdblok`-rijen van dagen die géén resultaat meer opleveren, binnen precies de
selectie die de run gevraagd kreeg (dezelfde monteur, dezelfde `--van`/`--tot`).
Geen modelwijziging, geen migratie: dit is logica in `matching/timeline/runner.py`.

Reasoning: de matchmotor verwijderde bestaande rijen alleen in `_store()`, en
`_store()` wordt uitsluitend aangeroepen voor een dag die daadwerkelijk opnieuw
is opgebouwd. Een dag wordt alleen opgebouwd als er nog ritdata achter zit. De
dagen die juist *vervallen* zijn — een junior die van zijn vaste meerijder is
losgekoppeld, een dag waarvan de ritten door een gecorrigeerde import zijn
verdwenen — waren dus precies de dagen die niemand meer aanraakte. Ze bleven met
hun oude tijdblokken in het weekoverzicht en het uitzonderingenscherm staan,
terwijl de run zichzelf als geslaagd rapporteerde. Dat is de gevaarlijkste vorm
van fout: de gebruiker heeft zijn koppeling gecorrigeerd, de app zegt "gelukt",
en het scherm laat nog steeds de oude werkelijkheid zien.

De opruiming hangt bewust aan `force` en niet aan elke run. Zonder `--force`
laat de matchmotor bestaande dagen juist met rust (dat is de hele betekenis van
de vlag); een run die dagen overslaat mag ze ook niet weggooien. `--force` is al
de stap die je draait ná een wijziging in een koppeltabel — precies het moment
waarop een dag kan vervallen.

De selectie is de grens, en is in de code met dezelfde argumenten uitgedrukt als
de run zelf: een herberekening voor monteur X raakt nooit monteur Y, een
herberekening over een datumrange raakt nooit een dag erbuiten. Een onbegrensde
`--force` ruimt wél alles vervallen op — dat is wat "reken alles opnieuw door"
betekent. Een dry run meldt de vervallen dagen en verwijdert niets.

Uitkomst: gebouwd. 424 tests groen (was 419), met vijf nieuwe tests in
`matching/tests/test_run_matching.py`: de twee scenario's uit het probleem (de
losgekoppelde junior, de dag zonder ritten) plus de drie grenzen (datumrange,
andere monteur, dry run). Beide scenario-tests falen aantoonbaar op de oude
code (6 != 0 resp. 3 != 0).

Doorgevoerd in: `matching/timeline/runner.py`,
`matching/management/commands/run_matching.py`,
`matching/tests/test_run_matching.py`, `docs/business-rules.md`,
`docs/changelog.md`, `GUIDELINES.md` (punt 37).

## 2026-09-11 — Urenregels zonder werkbonnummer blijven buiten de werkbon-matchindex (Current)

Decision: `DagUren.load()` in `matching/timeline/engine.py` indexeert alleen nog
`Uren`-regels die daadwerkelijk een werkbonnummer dragen. Een regel zonder
werkbonnummer kan een stop dus niet meer aan een werkbon koppelen; die stop valt
door naar de volgende stappen van de prioriteitsvolgorde (Werkbonnen-postcode,
koppeltabel, thuis, onverklaard). Geen modelwijziging, geen migratie.

Reasoning: ruim de helft van de urenregels in de juni-data is indirect —
kantoor, verlof, reisuren, magazijnonderhoud — en die dragen geen
werkbonnummer. Zo'n regel werd tot nu toe gewoon meegeïndexeerd, en een stop op
hetzelfde adres kwam er dan als SOORT W uit, met een leeg werkbonnummer. Dat
richtte twee soorten schade aan:

1. **Het dagtotaal en "Aansluiting per werkbon" spraken elkaar tegen.** Het
   dagcijfer "op locatie" telt álle W-blokken; de aansluitingstabel groepeert op
   werkbonnummer en kon een W-blok zonder nummer dus niet meetellen. Dezelfde
   dag liet daardoor twee verschillende totalen zien — precies het soort
   inconsistentie dat het vertrouwen in de hele tabel ondermijnt.
2. **De echte werkbon werd verdrongen.** De index houdt per sleutel de eerste
   regel (`setdefault` op rijvolgorde), dus een indirecte regel op dezelfde
   postcode of straat kon de plek innemen van de werkbon die daar wél geboekt
   was. Het werk kwam dan met een leeg nummer in beeld in plaats van met het
   juiste.

Dit is geen nieuwe regel maar het gelijktrekken van code en al vastgelegde
regel: `docs/business-rules.md` zei over de indirecte regel al "die kunnen per
definitie geen W-blok opleveren", en `weekoverzicht.py` hanteerde die aanname
ook (`AansluitingRegel` geeft de indirecte regel bewust geen `op_locatie`).
Alleen de matchmotor deed niet mee.

Bewust niet ook een tweede controle op de classificatieplek gezet: de index is
de enige bron van die match, dus één plek afsluiten is genoeg en een extra
`if` daar zou alleen suggereren dat het nog kon voorkomen. De aanname staat wel
als comment op de gebruiksplek.

Uitkomst: gebouwd. 428 tests groen (was 424), met vier nieuwe tests: drie in
`ClassificatieTests` (de verdringing, geen W zonder nummer, en het doorvallen
naar de koppeltabel) en één in `AansluitingPerWerkbonTests` die vastlegt dat
het dagtotaal en de aansluitingstabel weer hetzelfde cijfer geven. Alle vier
falen aantoonbaar op de oude code (de aansluitingstest met 1,00 tegen 2,00).

Doorgevoerd in: `matching/timeline/engine.py`,
`matching/tests/test_timeline.py`, `matching/tests/test_weekoverzicht.py`,
`docs/business-rules.md`, `docs/changelog.md`, `GUIDELINES.md` (punt 38),
`voor-klant/hoe-werkt-de-matching.md`.
