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
