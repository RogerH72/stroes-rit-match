"""Parser for Werkbonnen.xlsx — the completeness check, plus one fallback match key.

Werkbonnen.xlsx holds one row per Fase transition (Uitgevoerd, Gestopt, Gereed,
Afgehandeld), so a single Werkbon appears several times, and the same Werkbon can
also appear on more than one date. Rows collapse to one per (Werkbon, Medewerker,
Datum), carrying a Fase-status resolved across all of that Werkbon's rows.

Every remaining column is stored as well (docs/decisions.md, 2026-09-03). Only
Postcode is actually read by the matching, as a fallback key; Titel is display
text, and Tijd/Reistijd/Werktijd/"Monteur meegereden" are kept unused — see the
WerkbonControle docstring in matching/models.py for why storing them now was the
cheaper option.
"""

from __future__ import annotations

from pathlib import Path

from matching.ingest.parsers.base import read_excel_rows, text, to_date, to_time
from matching.models import FaseStatus, ImportedFile, WerkbonControle

REQUIRED_COLUMNS = ("Werkbon", "Medewerker", "Datum", "Fase")

# A Werkbon that reached any of these is finished; anything else (Uitgevoerd,
# Gestopt) counts as not started for the completeness check.
FINISHED_FASES = {"afgehandeld", "gereed"}


def resolve_fase_status(fases: list[str]) -> str:
    """Resolve one Fase-status from all the Fase rows of a single Werkbon.

    There is no ordering or timestamp column to pick a "last" row with, so the
    rule is a priority one: any finished Fase wins.
    """
    if any(text(fase).lower() in FINISHED_FASES for fase in fases):
        return FaseStatus.AFGEROND
    return FaseStatus.NIET_GESTART


def build_rows(path: Path, source_file: ImportedFile) -> list[WerkbonControle]:
    """Read Werkbonnen.xlsx into unsaved WerkbonControle instances.

    Two passes over the parsed rows: first collect every Fase per Werkbon, then
    emit one row per (Werkbon, Medewerker, Datum) carrying the status resolved
    across *all* of that Werkbon's rows. The status is a property of the Werkbon
    as a whole, while the date grain is what the completeness check needs to line
    up against Uren.
    """
    fases_per_werkbon: dict[str, list[str]] = {}
    # Keyed on (werkbon, medewerker, datum) so repeated Fase rows collapse into
    # one. The first row seen for a key supplies both its row_number and the
    # values of the columns outside the key, so a row and the line it is traced
    # back to always describe the same source line.
    seen: dict[tuple[str, str, object], tuple[int, dict]] = {}

    for row_number, values in read_excel_rows(path, required_columns=REQUIRED_COLUMNS):
        werkbon = text(values.get("Werkbon"), max_length=32)
        medewerker = text(values.get("Medewerker"), max_length=32)
        datum = to_date(values.get("Datum"))
        if not werkbon or datum is None:
            continue

        fases_per_werkbon.setdefault(werkbon, []).append(text(values.get("Fase")))
        seen.setdefault((werkbon, medewerker, datum), (row_number, values))

    return [
        WerkbonControle(
            source_file=source_file,
            row_number=row_number,
            werkbon=werkbon,
            medewerker=medewerker,
            datum=datum,
            fase_status=resolve_fase_status(fases_per_werkbon[werkbon]),
            postcode=text(values.get("Postcode"), max_length=10),
            titel=text(values.get("Titel"), max_length=255),
            tijd=to_time(values.get("Tijd")),
            reistijd=text(values.get("Reistijd"), max_length=32),
            werktijd=text(values.get("Werktijd"), max_length=32),
            monteur_meegereden=text(
                values.get("Monteur meegereden"), max_length=16
            ),
        )
        for (werkbon, medewerker, datum), (row_number, values) in seen.items()
    ]
