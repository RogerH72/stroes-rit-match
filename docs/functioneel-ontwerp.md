# Functioneel Ontwerp — Stroes-Rit-Match (RMW)

_Vastgelegd: 2026-09-02_

Dit document beschrijft hoe RMW straks functioneel werkt — niet hoe het technisch
gebouwd wordt (zie `docs/architecture.md`) en niet in de precieze, terse regel-vorm van
`docs/business-rules.md`. Het is bedoeld als leesbaar naslagwerk: wat doet de app, voor
wie, en wat gebeurt er stap voor stap. Waar een onderdeel nog niet is uitontworpen,
staat dat expliciet vermeld — er wordt hier niets verzonnen.

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
koppeling (API) met Syntess of RouteVision in deze versie:

- **3 dagelijkse Syntess Excel-exports.** De exacte inhoud/structuur van elke export
  staat niet in dit document uitgewerkt (zie `docs/business-rules.md` /
  `docs/database.md` voor wat daar al over bekend is); functioneel gaat het om
  werkbon-, klant/leverancier- en relatiegegevens.
- **RouteVision-download** (rit-, tijd- en locatiegegevens per monteur/voertuig). Het
  dagelijks plaatsen van dit bestand in de servermap is een taak van SBTT/Stric, niet
  van de app of van Roger.

Servermap (bevestigd): `\\stroes-1909\atrium\Autoprint\RUUDS`. De exacte
bestandsnaam-conventie van de automatische export is nog niet bevestigd met
Stric/RVS Solutions/RouteVision — dit moet nog rond zijn vóór de bestandsherkenning
definitief wordt vastgelegd.

## 3. Verwerking

### 3a. Bestandsdetectie (roadmap-fase 2, eerstvolgende bouwstap)

De app controleert de servermap elke 30 minuten (polling, geen filesystem-events —
onbetrouwbaar op een netwerkshare). Een bestand wordt pas verwerkt als de
bestandsgrootte over twee metingen op rij (dus 30 minuten) ongewijzigd is gebleven —
dit voorkomt dat een nog niet volledig weggeschreven bestand wordt ingelezen.

Wat er is verwerkt, wordt uitsluitend bijgehouden via de database (de matchresultaten
zelf) — er komt geen aparte "verwerkt"-map en bestanden worden nooit verplaatst of
verwijderd op de servermap. Ontbreken bestanden aan het eind van de dag, dan wordt dat
gelogd en getoond via een statusveld ("laatste succesvolle run") in het beheerscherm —
er gaat geen automatische e-mail uit. Herverwerken van een dag kan alleen handmatig via
een knop in het beheerscherm; het weekoverzicht verandert nooit stilletjes vanzelf.

### 3b. Tijdlijnreconstructie + matching (roadmap-fase 3)

Per monteur per dag wordt uit de RouteVision-ritgegevens een tijdlijn opgebouwd.
Belangrijk uitgangspunt: de werktijd wordt afgeleid uit de ritgegevens (wanneer
stopt/vertrekt de monteur bij een klantadres), niet uit de Werktijd/Reistijd-velden die
de monteur zelf in de werkbon invult — omdat die niet consequent worden ingevuld.
Werktijd begint zodra de monteur bij een klantadres stopt en eindigt zodra hij daar
wegrijdt; een tussentijds bezoek aan een leverancier of de eigen zaak beëindigt de
werkdag niet zolang de monteur diezelfde dag nog terugkeert naar de klant — pas het
laatste vertrek bij de klant die dag telt als einde werktijd.

Voor het matchen van locaties geldt: een exacte postcode-match is niet voldoende, er is
een straatnaam-fallback nodig. Een bezoek aan het depot vóór het werk wordt herkend als
zodanig. Bekende adres-afwijkingen (bijvoorbeeld werkbonadres wijkt af van busadres)
worden getoond als aandachtspunt, niet automatisch weggematcht.

Elk tijdblok in de tijdlijn krijgt een SOORT-code:

| Code | Betekenis   |
| ---- | ----------- |
| K    | Klant       |
| L    | Locatie     |
| C    | Crediteur   |
| W    | Werkbon     |
| ?    | Onbekend    |
| O    | Onverklaard |
| R    | Reistijd    |

Deze indeling is exact het eindresultaat dat de klant zelf al in Excel had ontworpen.

Afwijkingen worden beoordeeld tegen een tolerantietabel per activiteit (instelbare
drempel voor wat nog telt als een "onverklaarde" stop). De exacte drempelwaarden liggen
nog niet vast — die moeten nog met de klant worden bevestigd.

**Nog geen keuze gemaakt — "monteur meegereden":** wanneer een junior monteur meerijdt
met een senior, zijn er twee opties besproken met Wim, maar nog niet gekozen: (A) de
junior in de beheerschermen hard koppelen aan de senior, zodat hij automatisch dezelfde
rittijden krijgt toegewezen, of (B) onderzoeken of Syntess dit zelf al automatisch kan
aangeven in de Werkbonnen-export (functioneel de nettere oplossing, technisch nog niet
getest).

**Nog te bevestigen — klant/leverancier-onderscheid:** dit was een open datavraag, maar
wordt mogelijk bij de bron opgelost doordat RVS Solutions dit onderscheid zelf aan de
Relaties-export toevoegt — dan hoeft de app het niet meer zelf af te leiden. Te
bevestigen zodra die aangepaste export er is.

## 4. Beheerschermen (roadmap-fase 4)

Via Django-admin worden de koppeltabellen onderhouden:

- Bekende locaties (met marge/tolerantie).
- Monteur–voertuig (inclusief de "meegereden"-koppeling, zodra daarvoor gekozen is).
- Personeelsnummer–naam.
- Klant/leverancier-relaties (mogelijk overbodig zodra RVS Solutions dit oplost, zie
  hierboven).
- De tolerantietabel per activiteit.
- Het statusveld "laatste succesvolle run" (zie §3a).

De precieze schermindeling is nog niet uitgewerkt.

## 5. Uitzonderingenscherm (roadmap-fase 5)

Onbekende of afwijkende adressen kunnen in één klik gekoppeld worden aan een bekende
locatie. Eenmaal bevestigde koppelingen worden onthouden (opgeslagen in de
"bekende-locaties"-koppeltabel), zodat de lijst met openstaande uitzonderingen elke week
vanzelf korter wordt. Verdere schermdetails zijn nog niet uitgewerkt.

## 6. Weekoverzicht (roadmap-fase 6)

Het eindresultaat per monteur, beschikbaar als webpagina én als Excel-export, in de
layout die de klant zelf al in Excel had ontworpen (met de SOORT-codes uit §3b). Bouwt
voort op het HTML-prototype uit de eerdere validatie.

## 7. Oplevering en acceptatie (roadmap-fase 7 en 8)

Oplevering als lichte, zelfstandige Docker-container, samen met Stric geplaatst in een
bestaande Proxmox-/VM-omgeving (of anders een kleine VPS). Vóór elke nieuwe versie wordt
een back-up van de koppeltabellen gemaakt, zodat een rollback mogelijk is. Daarna testen
Roger en Wim samen; Wim heeft 30 werkdagen na oplevering om te testen, anders geldt de
oplevering automatisch als geaccepteerd. Bij oplevering hoort een korte samenvatting van
het gebouwde plus een instructie voor de beheerschermen en het uitzonderingenscherm.

## 8. Wat bewust buiten scope valt

Apart te offreren als vervolgstap, niet onderdeel van deze eerste werkende versie:

- Een uitgebreider dashboard of managementrapportage.
- Een directe API-koppeling met Syntess en/of RouteVision (in plaats van
  bestandsuitwisseling).
- Automatische signalering (bijv. een dagelijkse/wekelijkse e-mail met afwijkingen).
- Een optioneel serviceabonnement voor ondersteuning en kleine aanpassingen.
- Het snelheidscontrole-meerwerk (RouteVision-snelheid vs. maximumsnelheid per locatie)
  — nog geen besluit; raakt bovendien AVG/medewerkersmonitoring en vereist een
  juridisch/HR-traject naast de techniek.

## 9. Openstaande beslissingen — overzicht

Verzameld uit de secties hierboven, zodat ze niet uit het oog raken:

- Bestandsnaam-conventie van de automatische Syntess/RouteVision-export (§2) — te
  bevestigen met Stric/RVS Solutions/RouteVision.
- Exacte drempelwaarden van de tolerantietabel per activiteit (§3b) — te bevestigen met
  de klant.
- Oplossingsrichting voor "monteur meegereden": optie A (hard koppelen) of optie B
  (Syntess-export) (§3b).
- Klant/leverancier-onderscheid: blijft dit een koppeltabel in de app, of lost RVS
  Solutions dit op in de Relaties-export (§3b/§4)?
- Snelheidscontrole-meerwerk: wel of niet oppakken, en zo ja, hoe met de
  AVG/medewerkersmonitoring-vraag om te gaan (§8).
