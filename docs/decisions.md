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
(elke 30 min, vanuit een ingebakken scheduler in de Docker-container), met een
stabiliteitscheck (bestandsgrootte twee checks op rij ongewijzigd) voordat een bestand
als compleet geldt. Wat al verwerkt is, wordt bijgehouden via de database
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
