# Hoe de app de dag van een monteur herkent

Een uitleg zonder technisch jargon — bedoeld om te delen met Wim.

_Laatst bijgewerkt: 05-09-2026, na het gereedkomen van het weekoverzicht (zie
"Wat je hiervan te zien krijgt"). Zie de onderhoudsafspraak onderaan dit
document._

## Het probleem waar dit voor is bedacht

Monteurs vullen op de werkbon niet altijd nauwkeurig in hoe laat ze ergens
aankwamen of vertrokken. Dat is begrijpelijk — het is niet hun hoofdtaak, en
het schiet er in de praktijk bij in. Daardoor kun je op basis van de werkbon
zelf niet betrouwbaar zien hoe een werkdag er echt uitzag.

Wat wél heel precies bekend is: waar en wanneer de bus reed, dankzij de
ritregistratie (RouteVision). Die gegevens liegen niet — ze komen automatisch
uit het voertuig. Daarom is dat het uitgangspunt van de app: niet wat een
monteur zelf invulde, maar waar hij daadwerkelijk was.

## Hoe een werkdag wordt opgebouwd

De app legt voor elke monteur, voor elke dag, alle ritten van die dag achter
elkaar. Tussen twee ritten in zit altijd een moment dat de bus stilstond —
dat is een stop. Zo'n stop is waar gewerkt is, geleverd is, of iets anders
gebeurde. De app probeert van elke stop te herkennen wát daar gebeurde.

## Hoe een stop herkend wordt

Voor elke stop doorloopt de app een aantal vragen, in deze volgorde — zodra
er een antwoord "ja" is, staat het vast en stopt de app met verder zoeken:

1. **Is dit het eigen bedrijfspand (het magazijn/depot)?** Zo ja, dan is dit
   geen klantbezoek maar een bezoek aan de eigen zaak. Dit wordt als eerste
   gecheckt, want het kan voorkomen dat het eigen adres toevallig dicht bij
   een klant ligt — die verwarring wordt zo voorkomen.
2. **Komt dit adres overeen met een werkbon waar de monteur die dag zelf uren
   op heeft geboekt?** Zo ja, dan is dit die werkbon — het eigenlijke werk.
   Dit is de kern van de herkenning.
3. **Zo niet: komt het overeen met het adres dat in de planning bij die
   werkbon staat?** Soms wijkt wat een monteur zelf intypt net iets af van
   wat er in het systeem staat gepland. Voor dat geval is er een extra
   vangnet: als het niet lukt via wat de monteur zelf invulde, wordt ook
   gekeken naar het adres uit de planning. Dit vangnet hebben we onlangs
   toegevoegd, juist om dit soort gemiste gevallen alsnog automatisch te
   herkennen.
4. **Is het een ander bekend adres** — een klant, een leverancier, nog een
   eigen locatie die niet het hoofddepot is, of een privé-adres? Die adressen
   worden één keer handmatig aangewezen en onthoudt de app daarna vanzelf.

   "Privé" (code **P**) is op 07-09-2026 toegevoegd. Daarvóór bleef een stop
   die duidelijk privé was als "onverklaard" in de lijst staan, omdat er geen
   manier was om hem als privé af te handelen. Privé-tijd telt niet mee als
   werktijd; ze wordt apart getoond, als een eigen getal naast de totalen —
   niet ervan afgetrokken. Let op: een adres krijgt één classificatie voor
   iedereen, net als bij klant, locatie en leverancier. Merk je een adres als
   privé aan, dan geldt dat dus voor elke monteur die daar ooit stopt.
5. **Is dit het huisadres van de monteur?** Dan telt dat niet mee als
   werktijd — dat is gewoon het begin of einde van de dag.

   Het huisadres staat nergens ingevuld; de app leidt het af uit waar de
   dagen van die monteur beginnen en eindigen. Het magazijn telt daarbij
   bewust niet mee: wie zijn bus bij de zaak ophaalt begint en eindigt daar
   ook, maar het magazijn is natuurlijk niemands huis. Ging dat mis, dan
   werden de rit naar het magazijn, de tijd daar en de rit naar huis gezien
   als "rondje om het huis" en verdwenen ze uit het dagoverzicht. Dat is op
   07-09-2026 verholpen.
6. **Niets van dit alles:** dan blijft de stop onverklaard. Duurde de stop
   langer dan de ingestelde grens (nu 15 minuten), dan wordt hij zichtbaar
   gemaakt als "onverklaard", zodat iemand het kan uitzoeken. Was de stop
   heel kort, dan wordt hij als onopvallend "onbekend" gemarkeerd — te kort
   om ergens voor te staan.

## Het resultaat

Per monteur, per dag, ontstaat zo een overzicht van de hele werkdag met een
label per moment — precies de indeling die Wim zelf al in Excel had bedacht:

| Code | Betekenis |
|---|---|
| **K** | Klantbezoek |
| **L** | Bezoek aan een eigen locatie (bijv. het depot) |
| **C** | Bezoek aan een leverancier |
| **P** | Privé — geen werktijd (sinds 07-09-2026) |
| **W** | Werk op een specifieke werkbon |
| **R** | Onderweg (reistijd) |
| **O** | Onverklaarde stop — de moeite waard om te bekijken |
| **?** | Korte, onbekende stop |

## Wat je hiervan te zien krijgt

Per monteur kun je een week opvragen. Bovenaan staat het weektotaal: hoeveel
tijd er die week in elk van bovenstaande categorieën zat. Daaronder staat elke
dag apart, met alle momenten op een rij — hoe laat de bus ergens aankwam en
weer wegreed, hoe lang dat duurde, welk label erbij hoort en om welk adres het
gaat. Je kunt een dag dichtklappen als je hem niet nodig hebt. Dezelfde week is
te downloaden als Excel-bestand, met dezelfde kleuren, zodat je hem kunt
bewaren of doorsturen.

Staat er een onverklaarde stop tussen, dan kun je die daar meteen koppelen —
je hoeft daar geen apart scherm voor op te zoeken.

Per dag en per week staat er één extra vergelijking bij: **de uren die de
monteur in Syntess heeft geboekt, naast de tijd dat hij volgens de
ritregistratie daadwerkelijk op een werkbon-adres stond.** Dat is bedoeld als
signaal om even naar te kijken, niet als beschuldiging — er zijn twee
verklaringen die vaak voorkomen en die geen enkel probleem zijn:

- Uren die op het eigen bedrijfsadres worden geboekt tellen niet mee aan de
  rechterkant. Een stop op het eigen terrein wordt namelijk herkend als "eigen
  locatie", niet als werk op een werkbon.
- Als één iemand de uren van een heel team op zijn eigen naam boekt, staat aan
  de linkerkant het werk van meerdere mensen, en aan de rechterkant alleen zijn
  eigen bus.

Is een week niet compleet — bijvoorbeeld omdat de ritgegevens van een dag nog
niet binnen zijn — dan zegt het scherm dat er met zoveel woorden bij, met welke
dagen het betreft. Er verschijnt dus nooit stilzwijgend een weektotaal dat
eigenlijk over minder dagen gaat dan je denkt.

## Waarom dit betrouwbaar genoeg is om op te bouwen

Deze aanpak is niet nieuw bedacht en dan pas getest — het is precies andersom
gegaan. Eerst is deze manier van herkennen uitgeprobeerd op echte,
geanonimiseerde ritdata van meerdere monteurs over meerdere weken. Daaruit
kwam dat 78 tot 93% van alle werkbonnen automatisch en correct herkend werd,
puur op basis van rit- en adresgegevens. Pas nadat dat resultaat er stond, is
besloten dit als app te gaan bouwen.

Wat er niet automatisch herkend wordt, verdwijnt niet stilletjes — dat blijft
zichtbaar als "onverklaard" of "onbekend", zodat het in één oogopslag
opvalt. Zo'n onverklaard adres kan met één klik handmatig gekoppeld worden aan
een bekende locatie — en die koppeling onthoudt de app daarna voor altijd,
zodat de lijst met openstaande gevallen vanzelf steeds korter wordt (ook voor
dagen die daarna nog volgen). Gebeurt dat per ongeluk verkeerd, dan is dat
altijd terug te draaien — dat hoort bij de instructie die je bij oplevering
krijgt.

---

_Onderhoudsafspraak: dit document wordt bijgewerkt zodra de matchlogica
wijzigt, en zodra een hier genoemd onderdeel dat nu nog "niet klaar" heet
daadwerkelijk gereed komt. Zie `CLAUDE.md`._
