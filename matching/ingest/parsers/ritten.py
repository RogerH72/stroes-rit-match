"""Parser for the RouteVision CSV — trips, the main matching source.

cp1252 rather than UTF-8, semicolon separated, and every numeric column uses a
Dutch decimal comma; see matching/ingest/parsers/base.py for the conversions.
"""

from __future__ import annotations

from pathlib import Path

from matching.ingest.parsers.base import (
    read_csv_rows,
    text,
    to_date,
    to_decimal,
    to_duration,
    to_int,
    to_time,
)
from matching.models import ImportedFile, Rit

REQUIRED_COLUMNS = ("Kenteken", "Vertrekdatum", "Vertrektijd")


def build_rows(path: Path, source_file: ImportedFile) -> list[Rit]:
    """Read the RouteVision CSV into unsaved Rit instances, 1-to-1 with its rows."""
    rows = []
    for row_number, values in read_csv_rows(path, required_columns=REQUIRED_COLUMNS):
        rows.append(
            Rit(
                source_file=source_file,
                row_number=row_number,
                kenteken=text(values.get("Kenteken"), max_length=32),
                bestuurder=text(values.get("Bestuurder"), max_length=128),
                reis_van_de_dag=to_int(values.get("Reis van de dag")),
                reistype=text(values.get("Reistype"), max_length=8),
                vertrekdatum=to_date(values.get("Vertrekdatum")),
                vertrektijd=to_time(values.get("Vertrektijd")),
                vertrekadres=text(values.get("Vertrekadres"), max_length=255),
                vertrekplaats=text(values.get("Vertrekplaats"), max_length=128),
                aankomstdatum=to_date(values.get("Aankomstdatum")),
                aankomsttijd=to_time(values.get("Aankomsttijd")),
                aankomstadres=text(values.get("Aankomstadres"), max_length=255),
                aankomstplaats=text(values.get("Aankomstplaats"), max_length=128),
                duur=to_duration(values.get("Duur (uu:mm)")),
                km_prive=to_decimal(values.get("Privé (km)")),
                co2_prive=to_decimal(values.get("Privé CO2 (kg)")),
                km_zakelijk=to_decimal(values.get("Zakelijke (km)")),
                co2_zakelijk=to_decimal(values.get("Zakelijk CO2 (kg)")),
                km_woonwerk=to_decimal(values.get("Woonwerk (km)")),
                co2_woonwerk=to_decimal(values.get("Woonwerk CO2 (kg)")),
                km_totaal=to_decimal(values.get("Totaal (km)")),
                co2_totaal=to_decimal(values.get("Totaal CO2 (kg)")),
                max_snelheid=to_int(values.get("Maximum (km/u)")),
                max_snelheid_datum=to_date(values.get("Max. snelheid datum")),
                max_snelheid_tijd=to_time(values.get("Max. snelheid tijd")),
                max_snelheid_adres=text(values.get("Max. snelheid adres"), max_length=255),
                max_snelheid_plaats=text(values.get("Max. snelheid stad"), max_length=128),
                eindstand_km=to_decimal(values.get("Eindstand (km)")),
                opmerking=text(values.get("Opmerking"), max_length=255),
            )
        )
    return rows
