"""Parser for Relaties.xlsx — customer/supplier master data."""

from __future__ import annotations

from pathlib import Path

from matching.ingest.parsers.base import read_excel_rows, text
from matching.models import ImportedFile, Relatie

REQUIRED_COLUMNS = ("Code", "Relatienaam")


def build_rows(path: Path, source_file: ImportedFile) -> list[Relatie]:
    """Read Relaties.xlsx into unsaved Relatie instances.

    The export carries a long tail of entirely empty rows after its data; those
    are dropped by the reader, so only real relations end up in the table.
    """
    rows = []
    for row_number, values in read_excel_rows(path, required_columns=REQUIRED_COLUMNS):
        rows.append(
            Relatie(
                source_file=source_file,
                row_number=row_number,
                code=text(values.get("Code"), max_length=32),
                relatienaam=text(values.get("Relatienaam"), max_length=255),
                postcode=text(values.get("Postcode"), max_length=16),
                huisnr=text(values.get("Huisnr"), max_length=32),
                email=text(values.get("E-mail"), max_length=255),
                telefoon=text(values.get("Telefoon"), max_length=64),
            )
        )
    return rows
