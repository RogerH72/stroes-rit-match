"""Tests for reading the four source files."""

from __future__ import annotations

import datetime as dt
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase, TestCase

from matching.ingest.parsers import relaties, ritten, uren, werkbonnen
from matching.ingest.parsers.base import (
    ParseError,
    read_excel_rows,
    to_date,
    to_decimal,
    to_duration,
    to_time,
)
from matching.models import FaseStatus, ImportedFile, ImportStatus, SourceKind
from matching.tests import factories


class ValueConversionTests(SimpleTestCase):
    def test_dutch_decimal_comma(self):
        self.assertEqual(to_decimal("6,89"), Decimal("6.89"))
        self.assertEqual(to_decimal("0,6"), Decimal("0.6"))

    def test_thousands_separator_is_not_read_as_a_decimal_point(self):
        self.assertEqual(to_decimal("1.234,56"), Decimal("1234.56"))

    def test_whole_number_without_a_comma(self):
        self.assertEqual(to_decimal("12"), Decimal("12"))

    def test_empty_numbers_become_none(self):
        self.assertIsNone(to_decimal(""))
        self.assertIsNone(to_decimal(None))

    def test_rubbish_number_is_reported(self):
        with self.assertRaises(ParseError):
            to_decimal("n.v.t.")

    def test_dutch_date(self):
        self.assertEqual(to_date("3-8-2026"), dt.date(2026, 8, 3))
        self.assertEqual(to_date(dt.datetime(2026, 8, 3, 0, 0)), dt.date(2026, 8, 3))
        self.assertIsNone(to_date(""))

    def test_unrecognised_date_is_reported(self):
        with self.assertRaises(ParseError):
            to_date("08/03/2026 (week 32)")

    def test_clock_time(self):
        self.assertEqual(to_time("06:17:29"), dt.time(6, 17, 29))
        self.assertEqual(to_time("06:17"), dt.time(6, 17))
        self.assertIsNone(to_time(""))

    def test_duration_keeps_seconds_and_survives_over_24_hours(self):
        self.assertEqual(to_duration("00:10:07"), dt.timedelta(minutes=10, seconds=7))
        self.assertEqual(to_duration("26:30:00"), dt.timedelta(hours=26, minutes=30))
        self.assertIsNone(to_duration(""))


class ExcelReaderTests(SimpleTestCase):
    def test_reads_the_atrium_sheet_not_the_first_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = factories.uren_file(Path(tmp))
            rows = list(read_excel_rows(path))
        # Two data rows; the blank row in between is dropped.
        self.assertEqual([row_number for row_number, _ in rows], [2, 4])

    def test_missing_atrium_sheet_is_reported_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = factories.write_workbook(
                Path(tmp) / "Uren.xlsx",
                factories.UREN_COLUMNS,
                [],
                sheet_name="Blad1",
                extra_sheet_first=False,
            )
            with self.assertRaises(ParseError) as caught:
                list(read_excel_rows(path))
        self.assertIn("Atrium", str(caught.exception))

    def test_missing_column_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = factories.write_workbook(
                Path(tmp) / "Uren.xlsx", ["Medewerker", "Naam"], []
            )
            with self.assertRaises(ParseError) as caught:
                list(read_excel_rows(path, required_columns=("Werkbon",)))
        self.assertIn("Werkbon", str(caught.exception))


class ParserTestCase(TestCase):
    """Parsers need an ImportedFile to hang their rows on."""

    source_kind = SourceKind.UREN

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.imported_file = ImportedFile.objects.create(
            filename="test-source-file",
            source_kind=self.source_kind,
            size_bytes=1,
            last_measured_at=dt.datetime(2026, 8, 26, tzinfo=dt.timezone.utc),
            status=ImportStatus.STABIEL,
        )


class UrenParserTests(ParserTestCase):
    source_kind = SourceKind.UREN

    def test_reads_rows_and_skips_blanks(self):
        path = factories.uren_file(self.directory)
        rows = uren.build_rows(path, self.imported_file)

        self.assertEqual(len(rows), 2)
        first, second = rows
        self.assertEqual(first.medewerker, "001")
        self.assertEqual(first.werkbon, "WB261195")
        self.assertEqual(first.datum, dt.date(2026, 8, 3))
        self.assertEqual(first.aantal, Decimal("1"))
        self.assertEqual(first.plaats, "CULEMBORG")
        self.assertEqual(first.adres, "Floraliaweg 84")
        # Not filled in the real exports either.
        self.assertIsNone(first.begintijd)
        self.assertIsNone(first.eindtijd)

        self.assertEqual(second.aantal, Decimal("1.75"))
        self.assertEqual(second.begintijd, dt.time(8, 0))

    def test_keeps_accented_characters(self):
        path = factories.uren_file(self.directory)
        rows = uren.build_rows(path, self.imported_file)
        self.assertEqual(rows[0].project_opdrachtgever_naam, "Daniël Beuker")

    def test_row_number_points_at_the_source_row(self):
        path = factories.uren_file(self.directory)
        rows = uren.build_rows(path, self.imported_file)
        self.assertEqual([row.row_number for row in rows], [2, 4])


class RittenParserTests(ParserTestCase):
    source_kind = SourceKind.RIT

    def test_reads_cp1252_semicolon_csv_with_decimal_commas(self):
        path = factories.ritten_file(self.directory)
        rows = ritten.build_rows(path, self.imported_file)

        self.assertEqual(len(rows), 2)
        first = rows[0]
        self.assertEqual(first.kenteken, "V-31-JRT")
        self.assertEqual(first.bestuurder, "M5")
        self.assertEqual(first.reis_van_de_dag, 1)
        self.assertEqual(first.vertrekdatum, dt.date(2026, 8, 3))
        self.assertEqual(first.vertrektijd, dt.time(6, 17, 29))
        self.assertEqual(first.aankomsttijd, dt.time(6, 27, 36))
        self.assertEqual(first.duur, dt.timedelta(minutes=10, seconds=7))
        self.assertEqual(first.km_zakelijk, Decimal("6.89"))
        self.assertEqual(first.km_totaal, Decimal("6.89"))
        self.assertEqual(first.max_snelheid, 99)
        self.assertEqual(first.eindstand_km, Decimal("19596"))

    def test_empty_numeric_cells_become_null(self):
        path = factories.ritten_file(self.directory)
        second = ritten.build_rows(path, self.imported_file)[1]

        self.assertIsNone(second.km_prive)
        self.assertIsNone(second.km_woonwerk)
        self.assertIsNone(second.max_snelheid)
        self.assertIsNone(second.max_snelheid_datum)
        self.assertIsNone(second.eindstand_km)
        self.assertEqual(second.opmerking, "")

    def test_thousands_separator_and_accented_address(self):
        path = factories.ritten_file(self.directory)
        second = ritten.build_rows(path, self.imported_file)[1]
        self.assertEqual(second.km_totaal, Decimal("1234.56"))
        self.assertEqual(second.vertrekadres, "Küsterstraat 3")


class RelatiesParserTests(ParserTestCase):
    source_kind = SourceKind.RELATIE

    def test_trailing_empty_rows_are_dropped(self):
        path = factories.relaties_file(self.directory)
        rows = relaties.build_rows(path, self.imported_file)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].code, "0000")
        self.assertEqual(rows[0].relatienaam, "Stroes Bouw- & Techniek Team")
        self.assertEqual(rows[1].email, "syntess@x.nl")


class FaseStatusResolutionTests(SimpleTestCase):
    def test_any_finished_fase_wins(self):
        self.assertEqual(
            werkbonnen.resolve_fase_status(["Uitgevoerd", "Afgehandeld"]),
            FaseStatus.AFGEROND,
        )
        self.assertEqual(
            werkbonnen.resolve_fase_status(["Uitgevoerd", "Gereed"]),
            FaseStatus.AFGEROND,
        )

    def test_order_does_not_matter(self):
        self.assertEqual(
            werkbonnen.resolve_fase_status(["Afgehandeld", "Uitgevoerd"]),
            FaseStatus.AFGEROND,
        )

    def test_without_a_finished_fase_the_werkbon_has_not_started(self):
        self.assertEqual(
            werkbonnen.resolve_fase_status(["Gestopt", "Gestopt"]),
            FaseStatus.NIET_GESTART,
        )
        self.assertEqual(
            werkbonnen.resolve_fase_status(["Uitgevoerd"]), FaseStatus.NIET_GESTART
        )

    def test_case_and_spacing_are_ignored(self):
        self.assertEqual(
            werkbonnen.resolve_fase_status([" afgehandeld "]), FaseStatus.AFGEROND
        )

    def test_no_rows_at_all_is_not_started(self):
        self.assertEqual(werkbonnen.resolve_fase_status([]), FaseStatus.NIET_GESTART)


class WerkbonnenParserTests(ParserTestCase):
    source_kind = SourceKind.WERKBON_CONTROLE

    def test_fase_rows_collapse_into_one_row_per_werkbon_medewerker_date(self):
        path = factories.werkbonnen_file(self.directory)
        rows = werkbonnen.build_rows(path, self.imported_file)

        # 6 Fase rows -> 4 (werkbon, medewerker, datum) combinations.
        self.assertEqual(len(rows), 4)
        resolved = {(row.werkbon, row.datum): row.fase_status for row in rows}
        self.assertEqual(
            resolved,
            {
                ("WB260908", dt.date(2026, 8, 3)): FaseStatus.AFGEROND,
                ("WB261151", dt.date(2026, 8, 4)): FaseStatus.NIET_GESTART,
                ("WB260986", dt.date(2026, 8, 6)): FaseStatus.AFGEROND,
                ("WB260986", dt.date(2026, 8, 7)): FaseStatus.AFGEROND,
            },
        )

    def test_status_is_resolved_across_all_dates_of_one_werkbon(self):
        # WB260986 is only "Uitgevoerd" on 6 August and "Gereed" on 7 August;
        # the Werkbon as a whole is finished, so both rows say so.
        path = factories.werkbonnen_file(self.directory)
        rows = werkbonnen.build_rows(path, self.imported_file)
        statuses = {
            row.fase_status for row in rows if row.werkbon == "WB260986"
        }
        self.assertEqual(statuses, {FaseStatus.AFGEROND})

    def test_unused_columns_are_not_stored(self):
        # Reistijd, Werktijd, Titel and "Monteur meegereden" are deliberately
        # dropped (docs/database.md, docs/business-rules.md).
        field_names = {field.name for field in rows_model_fields()}
        for unwanted in ("reistijd", "werktijd", "titel", "monteur_meegereden"):
            self.assertNotIn(unwanted, field_names)


def rows_model_fields():
    from matching.models import WerkbonControle

    return WerkbonControle._meta.get_fields()
