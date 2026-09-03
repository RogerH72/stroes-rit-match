# Hoe de app de dag van een monteur herkent

Een uitleg zonder technisch jargon — bedoeld om te delen met Wim.

_Laatst bijgewerkt: 03-09-2026, na het toevoegen van het Werkbonnen-postcode-
vangnet (zie `docs/decisions.md`). Zie de onderhoudsafspraak onderaan dit
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
4. **Is het een ander bekend adres** — een klant, een leverancier, of nog een
   eigen locatie die niet het hoofddepot is? Die adressen worden één keer
   handmatig aangewezen en onthoudt de app daarna vanzelf.
5. **Is dit het huisadres van de monteur?** Dan telt dat niet mee als
   werktijd — dat is gewoon het begin of einde van de dag.
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
| **W** | Werk op een specifieke werkbon |
| **R** | Onderweg (reistijd) |
| **O** | Onverklaarde stop — de moeite waard om te bekijken |
| **?** | Korte, onbekende stop |

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
