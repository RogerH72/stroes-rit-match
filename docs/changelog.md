# Changelog — Stroes-Rit-Match (RMW)

## 2026-08-31 — Project aangemaakt

Project `stroes-rit-match` opgezet in `D:\PROJECTS\stroes-rit-match`, naar aanleiding
van het officiële akkoord van Wim Stroes. Voortbouwend op de brainstorm-sessie
`D:\AI\brainstorm-sessies\stroes-rit-match-werkbon`.

## 2026-08-31 — Documentatiestructuur gecorrigeerd

`docs/demo.md` alsnog toegevoegd (PoC-scope, doelgroep, scenario, prioriteiten,
blockers) en de documentatiekaart in `GUIDELINES.md` en de documentenlijst in
`CLAUDE.md` bijgewerkt, zodat de structuur volledig aansluit bij de AI-Efficient
Project Documentation Architecture.

## 2026-09-01 — Statuscorrectie: akkoord betrof volledige offerte, live-PoC vervallen

De documentatie beschreef eerder een gefaseerde aanpak (eerst een live-PoC met 1-2
monteurs bij de klant, dan pas een onderbouwde offerte). In werkelijkheid was het
akkoord van Wim (31-08-2026) al akkoord op de volledige offerte voor de complete app;
de live-PoC-met-klant-stap is niet uitgevoerd en vervallen. `GUIDELINES.md`,
`project-context.md`, `docs/demo.md` en `docs/decisions.md` zijn bijgewerkt om dit te
reflecteren. Eerstvolgende stap: een bredere eigen technische validatie (meer
weken/monteurs dan de eerdere test op monteur M5) vóór de bouw van de volledige app
start.

## 2026-09-01 — Bredere technische validatie afgerond (positief)

De bredere technische validatie (2 monteurs, 4 weken: W30 t/m W33) is uitgevoerd en
positief afgerond — 78% resp. 93% van de werkbonnen automatisch teruggevonden, met
verklaarbare afwijkingen, vergelijkbaar met of beter dan de eerdere validatie op
monteur M5. Zie `docs/decisions.md` en `docs/demo.md` voor de details. Dit was de
laatste stap vóór de bouw; `GUIDELINES.md` en `project-context.md` zijn bijgewerkt.
Eerstvolgende stap: de bouw van de volledige app.

## 2026-09-01 — Roadmap toegevoegd, stack-tekst gecorrigeerd naar OvO-scope

`docs/roadmap.md` toegevoegd: de bouwvolgorde voor de eerste werkende versie,
gebaseerd op de scope-opsomming uit het geaccordeerde OvO (v1.8, 31-08-2026).
`GUIDELINES.md`, `docs/architecture.md` en `CLAUDE.md` bijgewerkt (documentatiekaart
+ documentenlijst) en de stack-tekst gecorrigeerd: die zei nog "richting nog niet
vastgelegd", terwijl het OvO de stack al vastlegt (Python/Django, bestandsgebaseerd,
Docker-container). Zie `docs/decisions.md` voor de volledige toelichting.

## 2026-09-01 — Werkwijze bouwfase vastgelegd: Claude Code + Git/GitHub vanaf fase 1

Vastgelegd dat het bouwen van de webapp in een aparte Claude Code-sessie gebeurt
(niet in Cowork), en dat fase 1 van de roadmap een lokale Git-repo + GitHub-repo
opzet. `project-context.md`, `docs/decisions.md` en `docs/roadmap.md` bijgewerkt.

## 2026-09-01 — Taalconventie vastgelegd: code/instructies Engels, UI/docs Nederlands

Op basis van het ReplayCalcTool-precedent vastgelegd dat code, commit-messages en
instructies naar een code tool vanaf nu Engels zijn; UI en klantcommunicatie blijven
Nederlands; de al bestaande Nederlandstalige projectdocumentatie blijft staan.
`CLAUDE.md`, `GUIDELINES.md` en `docs/decisions.md` bijgewerkt.

## 2026-09-01 — Taalconventie aangevuld: Nederlandse domeintermen blijven staan

Verduidelijkt dat Nederlandse domeintermen uit het door SBTT ontworpen format
(Werkbon, Monteur, Rit, SOORT-codes, koppeltabel, tolerantietabel) letterlijk
Nederlands blijven in modelnamen/velden, ook al is de rest van de code Engels — zelfde
principe als "Totaal Montage" bij ReplayCalcTool. `CLAUDE.md`, `GUIDELINES.md` en
`docs/decisions.md` bijgewerkt.
