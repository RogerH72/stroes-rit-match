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

## 2026-09-01 — Taalconventie: code/instructies Engels, UI/documentatie Nederlands (Current)

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

## Meerwerk snelheidscontrole (Deferred)

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
