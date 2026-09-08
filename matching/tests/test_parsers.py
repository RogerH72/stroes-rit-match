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
    _gerepareerd_workbook_bestand,
    _KolomWaarden,
    read_csv_rows,
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


class RuweAtriumExportTests(ParserTestCase):
    """Reading an Atrium export that never passed through Excel (08-09-2026).

    Wim's Relaties.xlsx of that date was the first such file this project read,
    and openpyxl refused it outright: Atrium spells a few XML attribute names
    with the wrong capitalisation, and its column header reads "klant of
    leverancier" with a lower-case k. Every earlier fixture had been through
    Excel at some point, which silently repairs the XML — which is exactly why
    this stayed invisible until it hit a real import (docs/decisions.md).

    The defect is reproduced by `factories.ruwe_atrium_workbook` rather than by
    committing the customer's own file: no workbook belongs in this repository
    (.gitignore, "Client data ... personal data, AVG").
    """

    source_kind = SourceKind.RELATIE

    def _bestand(self, kolommen=None, rijen=None):
        return factories.ruwe_atrium_workbook(
            self.directory / "ruwe-atrium-export.xlsx",
            kolommen
            or ["Code", "Relatienaam", "Postcode", "klant of leverancier"],
            rijen
            or [
                ["0000", "Stroes Bouw- & Techniek Team", "4104 AC", "K"],
                ["0001", "Syntess Software", "4301 RZ", "L"],
            ],
        )

    def test_openpyxl_alone_cannot_read_it(self):
        # The fixture's reason for existing: without the repair in
        # read_excel_rows, this file does not open at all. If this ever stops
        # raising, the tests below would pass for the wrong reason.
        import openpyxl

        with self.assertRaises(TypeError):
            openpyxl.load_workbook(self._bestand(), read_only=True, data_only=True)

    def test_the_reader_opens_it_anyway(self):
        rijen = list(read_excel_rows(self._bestand(), required_columns=("Code",)))

        self.assertEqual(len(rijen), 2)
        self.assertEqual(rijen[0][1].get("Relatienaam"), "Stroes Bouw- & Techniek Team")

    def test_the_source_file_itself_is_never_rewritten(self):
        # The repair lives in memory: the inbox is read-only, and a repaired file
        # must not quietly replace what the customer's system delivered.
        pad = self._bestand()
        voor = pad.read_bytes()

        list(read_excel_rows(pad, required_columns=("Code",)))

        self.assertEqual(pad.read_bytes(), voor)

    def test_a_required_column_is_found_despite_its_letter_case(self):
        # "klant of leverancier" in the file, "Klant of leverancier" here.
        rijen = list(
            read_excel_rows(
                self._bestand(), required_columns=("Klant of leverancier",)
            )
        )

        self.assertEqual(len(rijen), 2)

    def test_a_genuinely_missing_column_is_still_reported(self):
        # Tolerance about capitalisation is not tolerance about absence.
        with self.assertRaises(ParseError):
            list(read_excel_rows(self._bestand(), required_columns=("Huisnr",)))

    def test_the_relaties_parser_reads_the_klant_of_leverancier_column(self):
        # The end-to-end point of both fixes: this column drives the suggestion
        # in the koppelformulier, and it arrived empty before.
        rijen = relaties.build_rows(self._bestand(), self.imported_file)

        self.assertEqual([rij.klant_of_leverancier for rij in rijen], ["K", "L"])
        self.assertEqual(rijen[0].code, "0000")


class KolomWaardenTests(SimpleTestCase):
    """The case-insensitive column lookup every parser row goes through."""

    def test_an_exact_name_is_answered_exactly(self):
        waarden = _KolomWaarden({"Postcode": "4104 AC"})

        self.assertEqual(waarden.get("Postcode"), "4104 AC")

    def test_a_differently_cased_name_still_finds_the_column(self):
        waarden = _KolomWaarden({"klant of leverancier": "L"})

        self.assertEqual(waarden.get("Klant of leverancier"), "L")

    def test_a_column_that_is_not_there_returns_the_default(self):
        waarden = _KolomWaarden({"Postcode": "4104 AC"})

        self.assertIsNone(waarden.get("Huisnr"))
        self.assertEqual(waarden.get("Huisnr", "leeg"), "leeg")

    def test_the_exact_spelling_wins_over_the_case_insensitive_one(self):
        # Two columns differing only in case: the exact name resolves exactly,
        # so a file like this cannot shift what an existing parser reads.
        waarden = _KolomWaarden({"Postcode": "exact", "POSTCODE": "afwijkend"})

        self.assertEqual(waarden.get("Postcode"), "exact")

    def test_two_columns_differing_only_in_case_do_not_crash(self):
        # Malformed, and not something this reader can sensibly arbitrate: the
        # last one wins in the fallback. Pinned down so it is not a surprise.
        waarden = _KolomWaarden({"POSTCODE": "eerste", "postcode": "tweede"})

        self.assertEqual(waarden.get("Postcode"), "tweede")


class HoofdletterOngevoeligeKolommenTests(ParserTestCase):
    """The same tolerance, through both readers rather than on the dict."""

    source_kind = SourceKind.RELATIE

    def test_an_excel_column_in_different_case_is_required_and_read(self):
        pad = factories.write_workbook(
            self.directory / "afwijkend.xlsx",
            ["code", "RELATIENAAM"],
            [["0000", "Stroes"]],
        )

        rijen = list(read_excel_rows(pad, required_columns=("Code", "Relatienaam")))

        self.assertEqual(len(rijen), 1)
        self.assertEqual(rijen[0][1].get("Relatienaam"), "Stroes")

    def test_a_csv_column_in_different_case_is_required_and_read(self):
        # No such file has turned up, but the RouteVision export is written by a
        # system outside our control too, so the two readers behave alike.
        pad = factories.write_csv(
            self.directory / "afwijkend.csv",
            ["KENTEKEN", "bestuurder"],
            [["V-31-JRT", "M5"]],
        )

        rijen = list(read_csv_rows(pad, required_columns=("Kenteken", "Bestuurder")))

        self.assertEqual(len(rijen), 1)
        self.assertEqual(rijen[0][1].get("Bestuurder"), "M5")


class ConformBestandOngemoeidTests(ParserTestCase):
    """The repair step must be a no-op on a file that is already conformant."""

    source_kind = SourceKind.RELATIE

    def test_a_conforming_workbook_is_handed_to_openpyxl_untouched(self):
        # Not merely "reads the same": the file itself is passed through, so a
        # conforming export never pays for the repair beyond one pass over its
        # zip directory.
        pad = factories.relaties_file(self.directory)

        self.assertIs(_gerepareerd_workbook_bestand(pad), pad)

    def test_a_conforming_workbook_reads_exactly_as_before(self):
        pad = factories.relaties_file(self.directory)

        rijen = list(read_excel_rows(pad, required_columns=("Code", "Relatienaam")))

        self.assertEqual(len(rijen), 2)
        self.assertEqual(rijen[0][1].get("Relatienaam"), "Stroes Bouw- & Techniek Team")
        self.assertEqual(rijen[1][1].get("Klant of leverancier"), "l")


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

    def test_the_klant_of_leverancier_letter_is_read_and_uppercased(self):
        # A lower-case "l" in Excel must not end up as an unrecognised value:
        # the suggestion in the koppelformulier looks the letter up as-is.
        path = factories.relaties_file(self.directory)
        rows = relaties.build_rows(path, self.imported_file)

        self.assertEqual(rows[0].klant_of_leverancier, "K")
        self.assertEqual(rows[1].klant_of_leverancier, "L")

    def test_an_export_without_the_klant_of_leverancier_column_still_imports(self):
        # Wim added that column on 08-09-2026; an older file has to keep working,
        # with the letter simply empty (docs/decisions.md, 08-09-2026).
        path = factories.relaties_file_zonder_soort(self.directory)
        rows = relaties.build_rows(path, self.imported_file)

        self.assertEqual(len(rows), 2)
        self.assertEqual([rij.klant_of_leverancier for rij in rows], ["", ""])


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

    def test_every_remaining_column_is_stored_verbatim(self):
        """The columns the matching does not read are captured all the same.

        Only Postcode is ever read (as a fallback matching key); the rest are
        stored because the source files are never deleted, so capturing them now
        beats building a second read-through later (docs/decisions.md,
        2026-09-03). This guards the parser side of that independently of what
        the matching does with any of it.
        """
        path = factories.werkbonnen_file(self.directory)
        rows = {
            (row.werkbon, row.datum): row
            for row in werkbonnen.build_rows(path, self.imported_file)
        }

        row = rows[("WB260908", dt.date(2026, 8, 3))]
        self.assertEqual(row.postcode, "4196 HB")  # raw, normalised at match time
        self.assertEqual(row.titel, "TRICHT - E-werkzaamheden")
        self.assertEqual(row.tijd, dt.time(7, 30))
        # Reistijd/Werktijd stay text: their unit is not confirmed and nothing
        # reads them, so a numeric type would only risk failing an import.
        self.assertEqual(row.reistijd, "0")
        self.assertEqual(row.werktijd, "0")
        self.assertEqual(row.monteur_meegereden, "Nee")

    def test_the_stored_values_come_from_the_row_the_row_number_points_at(self):
        # Fase rows for one key are collapsed to the first one seen; its values
        # and its row_number have to describe the same source line, or a value
        # would be traced back to a line it never came from.
        path = factories.werkbonnen_file(self.directory)
        rows = werkbonnen.build_rows(path, self.imported_file)

        # WB260986 appears on two dates with different Fase rows; each date keeps
        # its own Tijd/Postcode rather than borrowing the other's.
        per_datum = {row.datum: row for row in rows if row.werkbon == "WB260986"}
        self.assertEqual(per_datum[dt.date(2026, 8, 6)].row_number, 6)
        self.assertEqual(per_datum[dt.date(2026, 8, 7)].row_number, 7)
        for row in per_datum.values():
            self.assertEqual(row.postcode, "4021 JP")
            self.assertEqual(row.tijd, dt.time(8, 0))
