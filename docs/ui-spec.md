# UI Specification — Stroes-Rit-Match (RMW)

_Vastgelegd: 2026-09-03. Eerste invulling van dit document, besloten in de Cowork-
sessie bij de start van roadmap-fase 5 (uitzonderingenscherm) — zie `docs/decisions.md`,
"Lichte visuele stijl vastgelegd voor fase 5". De PoC had geen UI (output was een
Excel/HTML-weekoverzicht), en fase 3/4 zijn Django-admin-schermen zonder eigen
styling. Dit is de eerste keer dat RMW een schil krijgt buiten de Django-admin om, dus
de eerste keer dat een visuele stijl nodig is. Bedoeld als lichte basis — geen volledig
design system, maar genoeg om het uitzonderingenscherm (fase 5) en het weekoverzicht
(fase 6) er als één samenhangende applicatie uit te laten zien._

## Visual tone

Rustig en zakelijk, aansluitend bij SBTT's eigen huisstijl (zie hieronder) — geen
eigen "look" voor RMW los van de klant. RMW is een intern werkinstrument voor SBTT-
medewerkers, geen consumentenproduct: duidelijkheid en snelheid staan voorop, niet
visueel vertoon. Ruime witruimte, platte vormen (geen schaduwen/verlopen), afgeronde
labels voor status.

## Kleuren en huisstijl-bron

SBTT heeft geen apart merk-/stijldocument (nagekeken in `D:\STROES` — niet aanwezig).
Op verzoek is daarom gekeken naar het logo (`D:\STROES\ChatGPT Image 31 aug 2026,
18_09_13.png` — de eigen RMW-logo-afbeelding, gebruikt als grafisch beeldmerk, **niet**
als kleurbron) en naar SBTT's eigen websites. Twee sites zijn bekeken:

- `https://stroesteam.nl/` — dit is SBTT zelf (Bouw / Techniek / Klimaat, komt overeen
  met de klant van dit project). Kleuren hieronder komen hier vandaan.
- `https://www.stroes.nl/` — bleek bij inspectie een ander bedrijf te zijn ("Stroes
  Vastgoed" / "Stroes Onroerend Goed", vastgoedverhuur, `backoffice@stroes.nl`), niet
  SBTT. Deze site is **niet** gebruikt als stijlbron.

De kleuren hieronder zijn overgenomen uit de daadwerkelijke CSS van stroesteam.nl
(niet van een screenshot afgeschat):

| Naam | Hex | Herkomst op stroesteam.nl | Gebruik in RMW |
|---|---|---|---|
| Navy | `#133B78` | Kleur van het "Bouw"-label | Hoofdkleur: koptekst, hoofdnavigatie, primaire knoppen |
| Oranje | `#FF6B24` | Kleur van het "Techniek"-label en van alle "Bekijk ons aanbod"-links | Actiekleur: links, bevestig-knoppen (bijv. "Koppelen") |
| Groen | `#80BB45` | Kleur van het "Klimaat"-label | Positieve status (bijv. "al gekoppeld" / bevestigd) |
| Achtergrond | `#F6F6F6` | Pagina-achtergrond | Achtergrond buiten kaarten/panelen |
| Kaarten | `#FFFFFF` | Kaart-achtergrond | Panelen, formulieren, tabelrijen |
| Tekst | `#000000` (of een net iets zachtere donkere tint indien nodig voor leesbaarheid) | Hoofdtekstkleur | Lopende tekst |

**Waarschuwingskleur (los van het SBTT-palet):** voor SOORT O ("onverklaarde stop" —
de kern van het uitzonderingenscherm) wordt bewust géén kleur uit het SBTT-palet
gebruikt. Oranje is op dit scherm al de actieknop-kleur (Koppelen/Negeren); een
onverklaarde stop in diezelfde kleur tonen zou een waarschuwing en een actieknop
visueel door elkaar laten lopen. In plaats daarvan een neutrale amber/rode
waarschuwingskleur (exacte tint bij de bouw van fase 5 te kiezen, bijv. een
standaard amber `#D97706`-achtige tint), uitsluitend voor "dit heeft aandacht nodig".

## Typografie

stroesteam.nl gebruikt het lettertype "Satoshi" (licentiegebonden, niet zomaar in te
laden). RMW gebruikt in plaats daarvan de standaard systeem-sans-serif-stack (bijv.
`-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`) — voor een intern
beheerscherm visueel nauwelijks te onderscheiden van Satoshi, zonder licentie- of
laad-gedoe.

## Componenten en conventies

- **Status-labels**: volledig afgeronde ("pil"-vormige") labels met witte tekst op
  een gekleurde achtergrond — rechtstreeks overgenomen van de "Bouw / Techniek /
  Klimaat"-labels op stroesteam.nl. Gebruikt voor SOORT-codes en voor status
  ("onverklaard" / "al gekoppeld" / etc.).
- **Kaarten**: witte panelen met ruime binnenruimte op een lichtgrijze pagina-
  achtergrond, geen schaduw of alleen een zeer lichte schaduw — vlakke, rustige
  vormtaal.
- **Primaire actie**: oranje knop/link, zoals SBTT's eigen "Bekijk ons aanbod".
- **Logo**: het bestaande RMW-logo (`D:\STROES\ChatGPT Image 31 aug 2026,
  18_09_13.png`) wordt als beeldmerk gebruikt zoals het is — de kleuren in dat logo
  zelf zijn niet de bron voor dit kleurenschema (zie hierboven).

## SOORT-kleuren (vastgelegd bij de bouw van fase 6, 05-09-2026)

De zeven SOORT-codes hebben een eigen kleurenset, los van het SBTT-palet hierboven.
Reden: dit is een **functioneel codepalet**, geen merkpalet — de codes moeten in een
dichte tabel van elkaar te onderscheiden zijn, en zeven codes passen niet in drie
huisstijlkleuren. De waarden komen uit het prototype waar SBTT het overzicht al in
las (`D:\STROES\PoC-demo\rmw_sbtt.py`), zodat het scherm er voor Wim hetzelfde
uitziet als wat hij kent. Eén afwijking: **O gebruikt de waarschuwingskleur van fase
5** (`#D97706`) in plaats van het rood uit het prototype, zodat een onverklaarde stop
er op beide schermen hetzelfde uitziet.

| Code | Betekenis | Hex |
|---|---|---|
| K | Klant | `#0E7C86` |
| L | Locatie | `#2563B0` |
| C | Crediteur | `#8250B5` |
| W | Werkbon | `#1F8A4C` |
| ? | Onbekend | `#8A94A2` |
| O | Onverklaard | `#D97706` |
| R | Reistijd | `#9AA4B2` |

Deze tabel staat één keer in code (`SOORT_KLEUREN` in `matching/weekoverzicht.py`) en
wordt door zowel de webpagina als de Excel-export gebruikt, zodat een gedownloade week
dezelfde kleuren heeft als het scherm.

**Componenten die fase 6 toevoegde** aan de gedeelde basispagina: een navigatie in de
kopbalk (Weekoverzicht · Uitzonderingen · Beheer, met het actieve scherm onderstreept)
en een `stijl`-block waarin een scherm zijn eigen CSS kwijt kan. De SOORT-code zelf
wordt getoond als een klein vierkant "chip" (`.code`), niet als de ronde status-pil:
in een tabelrij moet een code niet breder zijn dan de letter die erin staat.

## Reikwijdte van dit document

Dit is een lichte basisstijl, geen uitgebreid design system — dat past bij de
contractueel afgesproken scope (`GUIDELINES.md`, "Technology stack": Django-admin
voor koppeltabellen/tolerantietabel; geen uitgebreid dashboard). Het
uitzonderingenscherm (fase 5) en het weekoverzicht (fase 6) zijn de eerste twee
schermen die deze stijl gebruiken; wijzigt de stijl bij de bouw van fase 5, dan wordt
dit document bijgewerkt vóór fase 6 begint, zodat beide schermen er als één
applicatie uitzien.
