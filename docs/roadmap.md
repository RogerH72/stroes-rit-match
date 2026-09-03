# Roadmap — Stroes-Rit-Match (RMW)

_Vastgelegd: 2026-09-01_

## Doel van dit document

De bouwvolgorde voor "de eerste werkende versie (basisgedeelte)" zoals vastgelegd in
het OvO (v1.8, geaccordeerd door Wim Stroes op 31-08-2026) en het onderliggende
projectvoorstel (27-08-2026). Bij tegenstrijdigheid is de scope-beschrijving in het
OvO punt 2a leidend (zie `D:\STROES\OvO_Huijskens-Stroes_RMW_basisversie_v1_8.pdf`).

## Uitgangspunt

De bredere technische validatie (2 monteurs, 4 weken) heeft bevestigd dat de
matching-heuristiek robuust genoeg is (zie `docs/decisions.md`, 01-09-2026). Deze
roadmap gaat over het omzetten van die gevalideerde logica naar de contractueel
toegezegde applicatie — niet over het opnieuw bepalen van de matchinglogica zelf.

## Fasering

### 1. Projectopzet
Django-project + Docker-basis; lokale ontwikkelomgeving; lokale Git-repository +
gekoppelde GitHub-repo (zie `docs/decisions.md`, 01-09-2026). Uitgevoerd in een
aparte Claude Code-sessie (niet in Cowork), zie `docs/decisions.md`.

### 2. Data-inlezing
Bestandsgebaseerde inlezing van de servermap (Syntess-exports + RouteVision-download),
volgens het al ontworpen trigger-mechanisme: polling elke 5 minuten, stabiliteitscheck
van 30 minuten op bestandsgrootte (beide los instelbaar), bijhouden wat al verwerkt is
via de database (geen aparte "verwerkt"-map, geen bestanden die worden verplaatst/
verwijderd). **Gebouwd (02-09-2026), zie `docs/changelog.md`.** Zie
`docs/architecture.md` en `docs/decisions.md`.

### 3. Reken-/matchmotor
De gevalideerde matching-heuristiek (uit de PoC en de bredere validatie —
`D:\STROES\PoC-demo\rmw_sbtt.py`, gegeneraliseerd in
`D:\STROES\Validatie-W30-W33\geanonimiseerd\validatie_2monteurs_4weken.py`) overzetten
naar herbruikbare Django-logica: tijdlijnreconstructie per monteur per dag,
classificatie in soorten (werkbon/klant/leverancier/eigen locatie/reistijd/
onbekend/onverklaard), en het toepassen van de tolerantietabel per activiteit.
**Gebouwd (03-09-2026), inclusief de koppeltabellen die de motor nodig heeft
(`Monteur`, `BekendeLocatie`, `Instelling`, `MeegeredenKoppeling`, `ToleranceRegel`)
— op verzoek van Roger nu al als echte modellen, in plaats van pas in fase 4. 143
tests groen, commit `eea759c`. Zie `docs/changelog.md` en `docs/decisions.md`
(03-09-2026).**

### 4. Koppeltabellen + beheerschermen
De koppeltabellen zelf zijn al gebouwd in fase 3 (zie hierboven). Deze fase gaat nu
vooral over de admin-schermen zelf verfijnen (labels, filters, gebruiksgemak) en het
invoeren van de echte SBTT-stamgegevens (o.a. het echte depotadres — met het
aandachtspunt uit `docs/decisions.md`, 03-09-2026, over het straat-niveau
depotrisico).
**Gebouwd (03-09-2026), commit `989b6d3`, 173 tests groen:** een
`MatchmotorStatus`-tabel en een "Matching nu draaien"-knop in het beheerscherm,
zodat SBTT-personeel de matching zelf opnieuw kan laten draaien na het
aanpassen van een koppeltabel — zonder serverdoegang (de matching draait niet
automatisch op een schema, zie `docs/database.md`). Daarnaast een
overlap-validatie op `MeegeredenKoppeling`. Het invoeren van de échte
SBTT-stamgegevens (o.a. het depotadres) is een aparte, latere stap — zie
`docs/decisions.md` (03-09-2026).

### 5. Uitzonderingen-scherm
Onbekende of afwijkende adressen in één klik koppelen; bevestigde koppelingen worden
onthouden, zodat de lijst met uitzonderingen steeds korter wordt.

### 6. Weekoverzicht
Per monteur, als webpagina én als Excel-export, in de eigen lay-out van SBTT
(SOORT-codes K/L/C/W/?/O/R) — voortbouwend op het HTML-prototype uit de validatie.

### 7. Oplevering
Lichte, zelfstandige Docker-container, i.s.m. Stric geplaatst in een bestaande
Proxmox-/VM-omgeving (of anders een kleine VPS). Bij elke nieuwe versie eerst een
back-up van de koppeltabellen, zodat een rollback mogelijk is bij problemen (OvO
punt 3). Volgt dezelfde aanpak als ReplayCalcTool (zie `docs/decisions.md`,
03-09-2026). Het uitvoerbare draaiboek staat alvast klaar in `DRAAIBOEK.md`; drie
onderdelen daarin zijn nog niet definitief (VM-gegevens, het `backup_db`-commando,
§7 "eerste inrichting").

### 8. Acceptatie
Samen testen; Wim test binnen 30 werkdagen na oplevering, anders geldt de oplevering
als geaccepteerd (OvO 5b). Een korte samenvatting van het gebouwde + een instructie
voor de beheerschermen en het uitzonderingen-scherm (OvO punt 6).

## Expliciet buiten deze roadmap

Bewust buiten de eerste werkende versie gehouden (apart te offreren als vervolgstap,
per OvO punt 2a / projectvoorstel §6):

- Een uitgebreider dashboard of managementrapportage.
- Een directe API-koppeling met Syntess en/of RouteVision (i.p.v. bestandsuitwisseling).
- Automatische signalering (bijv. een dagelijkse/wekelijkse e-mail met afwijkingen).
- Een optioneel serviceabonnement voor ondersteuning en kleine aanpassingen.
- Het snelheidscontrole-meerwerk (zie `docs/decisions.md` — "Meerwerk snelheidscontrole", Deferred).

## Afhankelijkheden van derden

De planning is mede afhankelijk van tijdige medewerking van Stric (VPN,
Proxmox-omgeving, toegang tot de servermap `\\stroes-1909\atrium`), RVS Solutions
(leverancier van Syntess) en RouteVision. Vertraging of beperkingen vanuit deze
partijen zijn niet aan Roger toe te rekenen (OvO punt 4).
