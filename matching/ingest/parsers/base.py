"""Reading the source files and converting their values.

Two readers, because the sources come in two shapes:

* The three Syntess exports are .xlsx workbooks whose data lives on a sheet named
  "Atrium" — not necessarily the first or active sheet, so it is addressed by name.
* The RouteVision export is a semicolon-separated CSV in cp1252, not UTF-8, with
  Dutch decimal commas in its numeric columns.

Both readers yield (row_number, {column: value}) and skip blank rows: Relaties.xlsx
in particular carries a couple of thousand entirely empty rows after its data.

openpyxl is the only added dependency; pandas would be far heavier than a handful
of columns warrants for a container that has to stay light (GUIDELINES.md).
"""

from __future__ import annotations

import csv
import datetime as dt
from collections.abc import Iterator
from decimal import Decimal, InvalidOperation
from pathlib import Path

import openpyxl

# The sheet every Syntess export puts its data on.
SHEET_NAME = "Atrium"

# RouteVision writes Windows-1252, semicolon-separated.
CSV_ENCODING = "cp1252"
CSV_DELIMITER = ";"


class ParseError(Exception):
    """A source file could not be read — wrong sheet, missing columns, bad values."""


# --- value conversion -------------------------------------------------------


def text(value: object, *, max_length: int | None = None) -> str:
    """A trimmed string for a text column; empty string when there is no value.

    Numbers are stringified rather than dropped: codes such as Medewerker "001"
    are text in the sample exports but could arrive as numbers from another export.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    result = str(value).strip()
    return result[:max_length] if max_length else result


def optional_text(value: object) -> str | None:
    """Like `text`, but None for an empty value — for nullable columns."""
    result = text(value)
    return result or None


def to_date(value: object) -> dt.date | None:
    """A date from an Excel datetime or a Dutch d-m-yyyy string."""
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ParseError(f"Unrecognised date value: {value!r}")


def to_time(value: object) -> dt.time | None:
    """A clock time from an Excel time or an HH:MM(:SS) string."""
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.time()
    if isinstance(value, dt.time):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return dt.datetime.strptime(raw, fmt).time()
        except ValueError:
            continue
    raise ParseError(f"Unrecognised time value: {value!r}")


def to_duration(value: object) -> dt.timedelta | None:
    """A duration from RouteVision's "Duur" column.

    The header says uu:mm but the values are HH:MM:SS. Stored as a real duration
    rather than a clock time, so a trip longer than a day cannot silently wrap.
    """
    if value is None or value == "":
        return None
    if isinstance(value, dt.timedelta):
        return value
    if isinstance(value, dt.time):
        return dt.timedelta(hours=value.hour, minutes=value.minute, seconds=value.second)
    raw = str(value).strip()
    if not raw:
        return None
    parts = raw.split(":")
    if len(parts) not in (2, 3):
        raise ParseError(f"Unrecognised duration value: {value!r}")
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        raise ParseError(f"Unrecognised duration value: {value!r}") from None
    hours, minutes = numbers[0], numbers[1]
    seconds = numbers[2] if len(numbers) == 3 else 0
    return dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)


def to_decimal(value: object) -> Decimal | None:
    """A decimal from a Dutch-formatted number such as "6,89" or "1.234,56".

    Conversion is explicit because a plain float() would reject the comma, and a
    thousands separator would otherwise be read as a decimal point.
    """
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    raw = str(value).strip()
    if not raw:
        return None
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        raise ParseError(f"Unrecognised number: {value!r}") from None


def to_int(value: object) -> int | None:
    """A whole number, accepting the decimal forms above."""
    number = to_decimal(value)
    return int(number) if number is not None else None


# --- readers ----------------------------------------------------------------


def _is_blank(values: dict[str, object]) -> bool:
    return all(value is None or str(value).strip() == "" for value in values.values())


def read_excel_rows(
    path: Path,
    *,
    sheet_name: str = SHEET_NAME,
    required_columns: tuple[str, ...] = (),
) -> Iterator[tuple[int, dict[str, object]]]:
    """Yield (row_number, values) for every non-blank data row of a Syntess export.

    `row_number` is the 1-based row in the sheet, header included, so it points at
    the line a value actually came from.
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            raise ParseError(
                f"{path.name}: sheet {sheet_name!r} not found "
                f"(sheets: {', '.join(workbook.sheetnames)})"
            )
        sheet = workbook[sheet_name]
        rows = sheet.iter_rows(values_only=True)

        try:
            header = next(rows)
        except StopIteration:
            raise ParseError(f"{path.name}: sheet {sheet_name!r} is empty") from None

        columns = [text(cell) for cell in header]
        missing = [column for column in required_columns if column not in columns]
        if missing:
            raise ParseError(
                f"{path.name}: missing column(s) {', '.join(missing)} "
                f"(found: {', '.join(c for c in columns if c)})"
            )

        for offset, row in enumerate(rows, start=2):
            values = {
                column: value
                for column, value in zip(columns, row)
                if column
            }
            if _is_blank(values):
                continue
            yield offset, values
    finally:
        workbook.close()


def read_csv_rows(
    path: Path,
    *,
    required_columns: tuple[str, ...] = (),
) -> Iterator[tuple[int, dict[str, str]]]:
    """Yield (row_number, values) for every non-blank data row of the RouteVision CSV."""
    with path.open("r", encoding=CSV_ENCODING, newline="") as handle:
        reader = csv.reader(handle, delimiter=CSV_DELIMITER)
        try:
            header = next(reader)
        except StopIteration:
            raise ParseError(f"{path.name}: file is empty") from None

        # Tolerate a byte order mark if the export ever switches to UTF-8-with-BOM.
        columns = [column.strip().lstrip("﻿") for column in header]
        missing = [column for column in required_columns if column not in columns]
        if missing:
            raise ParseError(
                f"{path.name}: missing column(s) {', '.join(missing)} "
                f"(found: {', '.join(c for c in columns if c)})"
            )

        for offset, row in enumerate(reader, start=2):
            values = {column: value for column, value in zip(columns, row) if column}
            if _is_blank(values):
                continue
            yield offset, values
