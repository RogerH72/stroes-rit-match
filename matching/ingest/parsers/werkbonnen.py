"""Parser for Werkbonnen.xlsx — completeness check only, never matching input.

Werkbonnen.xlsx holds one row per Fase transition (Uitgevoerd, Gestopt, Gereed,
Afgehandeld), so a single Werkbon appears several times, and the same Werkbon can
also appear on more than one date. Only Werkbon, Medewerker, Datum and a single
resolved Fase-status are kept; Reistijd, Werktijd, Titel and "Monteur meegereden"
are deliberately dropped (docs/database.md, docs/business-rules.md).
"""

from __future__ import annotations

from pathlib import Path

from matching.ingest.parsers.base import read_excel_rows, text, to_date
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
    # Keyed on (werkbon, medewerker, datum) so repeated Fase rows collapse into one.
    seen: dict[tuple[str, str, object], int] = {}

    for row_number, values in read_excel_rows(path, required_columns=REQUIRED_COLUMNS):
        werkbon = text(values.get("Werkbon"), max_length=32)
        medewerker = text(values.get("Medewerker"), max_length=32)
        datum = to_date(values.get("Datum"))
        if not werkbon or datum is None:
            continue

        fases_per_werkbon.setdefault(werkbon, []).append(text(values.get("Fase")))
        seen.setdefault((werkbon, medewerker, datum), row_number)

    return [
        WerkbonControle(
            source_file=source_file,
            row_number=row_number,
            werkbon=werkbon,
            medewerker=medewerker,
            datum=datum,
            fase_status=resolve_fase_status(fases_per_werkbon[werkbon]),
        )
        for (werkbon, medewerker, datum), row_number in seen.items()
    ]
