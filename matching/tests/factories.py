"""Building source files for the tests.

The tests write their own miniature exports rather than leaning on the real
sample files: that keeps them runnable anywhere (the anonymised customer exports
in voorbeeld-data/ are not in version control) and lets each test state exactly
the quirk it is about. matching/tests/test_sample_data.py covers the real files
when they happen to be present.

The shapes here mirror the real exports: sheet "Atrium" for the Syntess
workbooks, cp1252 + semicolons + decimal commas for the RouteVision CSV.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
from pathlib import Path

import openpyxl

from matching.ingest.parsers.base import CSV_DELIMITER, CSV_ENCODING, SHEET_NAME

UREN_COLUMNS = [
    "Medewerker",
    "Naam",
    "Werkbon",
    "Datum",
    "Aantal",
    "Taak code",
    "Taak omschrijving",
    "Project opdrachtgever naam",
    "Postcode",
    "Plaats",
    "Adres",
    "Begintijd",
    "Eindtijd",
]

WERKBON_COLUMNS = [
    "Werkbon",
    "Titel",
    "Postcode",
    "Huisnr",
    "Datum",
    "Tijd",
    "Medewerker",
    "Naam",
    "Reistijd",
    "Werktijd",
    "Fase",
    "Monteur meegereden",
]

RELATIE_COLUMNS = ["Code", "Relatienaam", "Postcode", "Huisnr", "E-mail", "Telefoon"]

RIT_COLUMNS = [
    "Kenteken",
    "Bestuurder",
    "Reis van de dag",
    "Reistype",
    "Vertrekdatum",
    "Vertrektijd",
    "Vertrekadres",
    "Vertrekplaats",
    "Aankomstdatum",
    "Aankomsttijd",
    "Aankomstadres",
    "Aankomstplaats",
    "Duur (uu:mm)",
    "Privé (km)",
    "Privé CO2 (kg)",
    "Zakelijke (km)",
    "Zakelijk CO2 (kg)",
    "Woonwerk (km)",
    "Woonwerk CO2 (kg)",
    "Totaal (km)",
    "Totaal CO2 (kg)",
    "Maximum (km/u)",
    "Max. snelheid datum",
    "Max. snelheid tijd",
    "Max. snelheid adres",
    "Max. snelheid stad",
    "Eindstand (km)",
    "Opmerking",
]


def write_workbook(
    path: Path,
    columns: list[str],
    rows: list[list],
    *,
    sheet_name: str = SHEET_NAME,
    extra_sheet_first: bool = True,
) -> Path:
    """Write a Syntess-shaped workbook.

    By default a decoy sheet is added *before* the data sheet, so a parser that
    reads the first or active sheet instead of "Atrium" fails the test.
    """
    workbook = openpyxl.Workbook()
    default_sheet = workbook.active
    if extra_sheet_first:
        default_sheet.title = "Blad1"
        default_sheet["A1"] = "not the data"
        sheet = workbook.create_sheet(sheet_name)
    else:
        default_sheet.title = sheet_name
        sheet = default_sheet

    sheet.append(columns)
    for row in rows:
        sheet.append(row)
    workbook.save(path)
    workbook.close()
    return path


def write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> Path:
    """Write a RouteVision-shaped CSV: cp1252, semicolon separated."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=CSV_DELIMITER, lineterminator="\r\n")
    writer.writerow(columns)
    writer.writerows(rows)
    path.write_bytes(buffer.getvalue().encode(CSV_ENCODING))
    return path


def uren_file(directory: Path, name: str = "Download uit Syntess Uren.xlsx") -> Path:
    """A small Uren.xlsx, including a blank row and empty Begin-/Eindtijd."""
    return write_workbook(
        directory / name,
        UREN_COLUMNS,
        [
            [
                "001",
                "M1",
                "WB261195",
                dt.datetime(2026, 8, 3),
                1,
                "101",
                "Arbeidsloon Regie",
                "Daniël Beuker",
                "4101 GD",
                "CULEMBORG",
                "Floraliaweg 84",
                None,
                None,
            ],
            [None] * len(UREN_COLUMNS),
            [
                "005",
                "M5",
                "WB260908",
                dt.datetime(2026, 8, 3),
                1.75,
                "100",
                "Arbeidsloon",
                "Gijs van Velzen",
                "4196 HB",
                "TRICHT",
                "Lingedijk 67",
                dt.time(8, 0),
                dt.time(9, 45),
            ],
        ],
    )


def werkbonnen_file(
    directory: Path, name: str = "Download uit Syntess Werkbonnen.xlsx"
) -> Path:
    """A small Werkbonnen.xlsx with several Fase rows per Werkbon.

    WB260908 finishes (Afgehandeld), WB261151 never gets past Gestopt, and
    WB260986 runs across two dates.
    """
    return write_workbook(
        directory / name,
        WERKBON_COLUMNS,
        [
            [
                "WB260908",
                "TRICHT - E-werkzaamheden",
                "4196 HB",
                "67",
                dt.datetime(2026, 8, 3),
                dt.time(7, 30),
                "005",
                "M5",
                0,
                0,
                "Afgehandeld",
                "Nee",
            ],
            [
                "WB260908",
                "TRICHT - E-werkzaamheden",
                "4196 HB",
                "67",
                dt.datetime(2026, 8, 3),
                dt.time(7, 30),
                "005",
                "M5",
                None,
                None,
                "Uitgevoerd",
                "Nee",
            ],
            [
                "WB261151",
                "CULEMBORG - Onderhoud",
                "4104 AC",
                "20",
                dt.datetime(2026, 8, 4),
                dt.time(8, 0),
                "001",
                "M1",
                None,
                None,
                "Gestopt",
                "Nee",
            ],
            [
                "WB261151",
                "CULEMBORG - Onderhoud",
                "4104 AC",
                "20",
                dt.datetime(2026, 8, 4),
                dt.time(8, 0),
                "001",
                "M1",
                None,
                None,
                "Gestopt",
                "Nee",
            ],
            [
                "WB260986",
                "MAURIK - Airco installatie",
                "4021 JP",
                "14",
                dt.datetime(2026, 8, 6),
                dt.time(8, 0),
                "005",
                "M5",
                None,
                None,
                "Uitgevoerd",
                "Nee",
            ],
            [
                "WB260986",
                "MAURIK - Airco installatie",
                "4021 JP",
                "14",
                dt.datetime(2026, 8, 7),
                dt.time(8, 0),
                "005",
                "M5",
                0,
                0,
                "Gereed",
                "Nee",
            ],
        ],
    )


def relaties_file(
    directory: Path, name: str = "Download uit Syntess Relaties.xlsx"
) -> Path:
    """A small Relaties.xlsx with the trailing block of empty rows the real one has."""
    rows = [
        ["0000", "Stroes Bouw- & Techniek Team", "4104 AC", "6A", "info@x.nl", "0345-1"],
        ["0001", "Syntess Software", "4301 RZ", "2", "syntess@x.nl", "088-2 (alg)"],
    ]
    rows += [[None] * len(RELATIE_COLUMNS) for _ in range(25)]
    return write_workbook(directory / name, RELATIE_COLUMNS, rows)


def ritten_file(directory: Path, name: str = "Ritten_Alle_voertuigen.csv") -> Path:
    """A small RouteVision CSV: decimal commas, empty numeric cells, accented text."""
    return write_csv(
        directory / name,
        RIT_COLUMNS,
        [
            [
                "V-31-JRT",
                "M5",
                "1",
                "Z",
                "3-8-2026",
                "06:17:29",
                "J. Bosschaartstraat 22",
                "4112 LN Beusichem",
                "3-8-2026",
                "06:27:36",
                "Wethouder Schoutenweg 1a",
                "4105 LH Culemborg",
                "00:10:07",
                "",
                "",
                "6,89",
                "1,38",
                "",
                "",
                "6,89",
                "1,38",
                "99",
                "3-8-2026",
                "04:20:47",
                "Provincialeweg",
                "Beusichem",
                "19596",
                "",
            ],
            [
                "VKV-60-T",
                "M1",
                "12",
                "Z",
                "4-8-2026",
                "16:02:15",
                "Küsterstraat 3",
                "4101 KA Culemborg",
                "4-8-2026",
                "16:20:00",
                "Randweg 1b",
                "4104 AC Culemborg",
                "00:17:45",
                "",
                "",
                "12",
                "2,41",
                "",
                "",
                "1.234,56",
                "2,41",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
        ],
    )


def all_source_files(directory: Path) -> dict[str, Path]:
    """Write one of each source file into `directory`."""
    return {
        "uren": uren_file(directory),
        "werkbon": werkbonnen_file(directory),
        "relatie": relaties_file(directory),
        "rit": ritten_file(directory),
    }
