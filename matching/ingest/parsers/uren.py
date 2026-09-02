"""Parser for Uren.xlsx — booked hours, the main matching source."""

from __future__ import annotations

from pathlib import Path

from matching.ingest.parsers.base import (
    read_excel_rows,
    text,
    to_date,
    to_decimal,
    to_time,
)
from matching.models import ImportedFile, Uren

REQUIRED_COLUMNS = ("Medewerker", "Werkbon", "Datum")


def build_rows(path: Path, source_file: ImportedFile) -> list[Uren]:
    """Read Uren.xlsx into unsaved Uren instances, 1-to-1 with the source rows."""
    rows = []
    for row_number, values in read_excel_rows(path, required_columns=REQUIRED_COLUMNS):
        rows.append(
            Uren(
                source_file=source_file,
                row_number=row_number,
                medewerker=text(values.get("Medewerker"), max_length=32),
                naam=text(values.get("Naam"), max_length=128),
                werkbon=text(values.get("Werkbon"), max_length=32),
                datum=to_date(values.get("Datum")),
                aantal=to_decimal(values.get("Aantal")),
                taak_code=text(values.get("Taak code"), max_length=32),
                taak_omschrijving=text(values.get("Taak omschrijving"), max_length=255),
                project_opdrachtgever_naam=text(
                    values.get("Project opdrachtgever naam"), max_length=255
                ),
                postcode=text(values.get("Postcode"), max_length=16),
                plaats=text(values.get("Plaats"), max_length=128),
                adres=text(values.get("Adres"), max_length=255),
                begintijd=to_time(values.get("Begintijd")),
                eindtijd=to_time(values.get("Eindtijd")),
            )
        )
    return rows
