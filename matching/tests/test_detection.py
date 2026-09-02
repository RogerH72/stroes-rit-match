"""Tests for detecting and importing the files on the server share."""

from __future__ import annotations

import datetime as dt
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from matching.ingest.detection import scan_share
from matching.models import (
    ImportedFile,
    ImportStatus,
    Relatie,
    Rit,
    SourceKind,
    Uren,
    WerkbonControle,
)
from matching.tests import factories


class DetectionTestCase(TestCase):
    """Every test gets its own throwaway share folder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.share = Path(self.tmp.name)

    def poll(self, times: int = 1, **kwargs):
        """Run the share check `times` times, as the scheduler would."""
        for _ in range(times):
            result = scan_share(path=self.share, **kwargs)
        return result


@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class StabilityCycleTests(DetectionTestCase):
    def test_a_file_is_only_imported_after_six_unchanged_polls(self):
        factories.uren_file(self.share)

        for poll_number in range(1, 6):
            result = self.poll()
            self.assertEqual(result.imported, {}, f"imported too early at poll {poll_number}")
            record = ImportedFile.objects.get()
            self.assertEqual(record.status, ImportStatus.WACHTEND)
            self.assertEqual(record.unchanged_polls, poll_number)

        result = self.poll()
        self.assertEqual(list(result.imported), [record.filename])
        record.refresh_from_db()
        self.assertEqual(record.status, ImportStatus.VERWERKT)
        self.assertEqual(record.row_count, 2)
        self.assertIsNotNone(record.processed_at)
        self.assertEqual(Uren.objects.count(), 2)

    def test_a_growing_file_restarts_the_stability_run(self):
        path = factories.uren_file(self.share)
        self.poll(times=5)
        self.assertEqual(ImportedFile.objects.get().unchanged_polls, 5)

        # The export is still being written: the file changes size.
        factories.write_workbook(
            path,
            factories.UREN_COLUMNS,
            [["001", "M1", "WB1", dt.datetime(2026, 8, 3), 1, "", "", "", "", "", "", None, None]]
            * 40,
        )
        self.poll()

        record = ImportedFile.objects.get()
        self.assertEqual(record.unchanged_polls, 1)
        self.assertEqual(record.status, ImportStatus.WACHTEND)
        self.assertEqual(Uren.objects.count(), 0)

    def test_force_imports_without_waiting(self):
        factories.uren_file(self.share)
        result = self.poll(force=True)

        self.assertEqual(len(result.imported), 1)
        self.assertEqual(ImportedFile.objects.get().status, ImportStatus.VERWERKT)

    def test_dry_run_writes_nothing(self):
        factories.uren_file(self.share)
        result = self.poll(force=True, dry_run=True)

        self.assertEqual(len(result.imported), 1)
        self.assertEqual(ImportedFile.objects.count(), 0)
        self.assertEqual(Uren.objects.count(), 0)

    def test_required_measurements_follow_the_two_settings_independently(self):
        factories.uren_file(self.share)
        with override_settings(POLL_INTERVAL_MINUTES=10, STABILITY_MINUTES=30):
            result = self.poll(times=3)
        self.assertEqual(result.required_consecutive, 3)
        self.assertEqual(len(result.imported), 1)


@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class IndependentTrackingTests(DetectionTestCase):
    def test_every_source_file_gets_its_own_row(self):
        factories.all_source_files(self.share)
        self.poll(force=True)

        kinds = set(ImportedFile.objects.values_list("source_kind", flat=True))
        self.assertEqual(
            kinds,
            {
                SourceKind.UREN,
                SourceKind.RIT,
                SourceKind.RELATIE,
                SourceKind.WERKBON_CONTROLE,
            },
        )
        self.assertEqual(Uren.objects.count(), 2)
        self.assertEqual(Rit.objects.count(), 2)
        self.assertEqual(Relatie.objects.count(), 2)
        self.assertEqual(WerkbonControle.objects.count(), 4)

    def test_a_missing_werkbonnen_file_does_not_block_the_others(self):
        # Werkbonnen.xlsx feeds only the completeness check, so its absence must
        # never hold up the matching sources (functioneel-ontwerp §3a).
        factories.uren_file(self.share)
        factories.ritten_file(self.share)
        factories.relaties_file(self.share)

        result = self.poll(force=True)

        self.assertEqual(len(result.imported), 3)
        self.assertEqual(Uren.objects.count(), 2)
        self.assertEqual(Rit.objects.count(), 2)
        self.assertEqual(WerkbonControle.objects.count(), 0)

    def test_a_file_still_being_written_does_not_hold_up_the_rest(self):
        factories.uren_file(self.share)
        factories.ritten_file(self.share)
        werkbon_path = factories.werkbonnen_file(self.share)

        # Uren and Ritten sit still for six polls; Werkbonnen keeps growing.
        for size in range(6):
            factories.write_workbook(
                werkbon_path,
                factories.WERKBON_COLUMNS,
                [
                    [
                        "WB1", "", "", "", dt.datetime(2026, 8, 3), None,
                        "001", "M1", None, None, "Gestopt", "Nee",
                    ]
                ]
                * (size + 1),
            )
            result = self.poll()

        self.assertEqual(set(result.imported), {"Download uit Syntess Uren.xlsx",
                                                "Ritten_Alle_voertuigen.csv"})
        self.assertIn("Download uit Syntess Werkbonnen.xlsx", result.waiting)
        self.assertEqual(WerkbonControle.objects.count(), 0)

    def test_a_broken_file_does_not_stop_the_others(self):
        factories.uren_file(self.share)
        (self.share / "Ritten_kapot.csv").write_bytes(b"not;a;routevision;export\r\n")

        result = self.poll(force=True)

        self.assertEqual(len(result.imported), 1)
        self.assertEqual(list(result.failed), ["Ritten_kapot.csv"])
        self.assertEqual(Uren.objects.count(), 2)

        broken = ImportedFile.objects.get(filename="Ritten_kapot.csv")
        # Stays stabiel with the error recorded, so the next run retries it.
        self.assertEqual(broken.status, ImportStatus.STABIEL)
        self.assertTrue(broken.last_error)


@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class ProcessedFileTests(DetectionTestCase):
    def test_a_processed_file_is_not_imported_twice(self):
        factories.uren_file(self.share)
        self.poll(force=True)
        result = self.poll(force=True)

        self.assertEqual(result.imported, {})
        self.assertEqual(result.skipped_processed, ["Download uit Syntess Uren.xlsx"])
        self.assertEqual(Uren.objects.count(), 2)

    def test_a_changed_processed_file_is_not_reprocessed_automatically(self):
        # Reprocessing is a manual action only (docs/architecture.md).
        path = factories.uren_file(self.share)
        self.poll(force=True)

        factories.write_workbook(
            path,
            factories.UREN_COLUMNS,
            [["009", "M9", "WB999", dt.datetime(2026, 8, 4), 3, "", "", "", "", "", "", None, None]]
            * 12,
        )
        result = self.poll(force=True)

        self.assertEqual(result.imported, {})
        self.assertEqual(Uren.objects.count(), 2)
        self.assertEqual(ImportedFile.objects.get().status, ImportStatus.VERWERKT)

    def test_manual_reprocess_replaces_only_that_files_rows(self):
        path = factories.uren_file(self.share)
        factories.ritten_file(self.share)
        self.poll(force=True)
        self.assertEqual(Uren.objects.count(), 2)

        factories.write_workbook(
            path,
            factories.UREN_COLUMNS,
            [["009", "M9", "WB999", dt.datetime(2026, 8, 4), 3, "", "", "", "", "", "", None, None]]
            * 5,
        )
        self.poll(force=True, reprocess=True)

        self.assertEqual(Uren.objects.count(), 5)
        self.assertEqual(Rit.objects.count(), 2)
        self.assertEqual(ImportedFile.objects.get(source_kind=SourceKind.UREN).row_count, 5)


@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class ShareHandlingTests(DetectionTestCase):
    def test_unrecognised_files_are_ignored_not_failed(self):
        factories.uren_file(self.share)
        (self.share / "readme.txt").write_text("nothing to see", encoding="utf-8")
        (self.share / "Facturen 2026.xlsx").write_bytes(b"whatever")

        result = self.poll(force=True)

        self.assertEqual(len(result.imported), 1)
        self.assertEqual(result.failed, {})
        self.assertEqual(sorted(result.ignored), ["Facturen 2026.xlsx", "readme.txt"])

    def test_source_files_are_never_moved_or_deleted(self):
        before = factories.all_source_files(self.share)
        self.poll(force=True)

        for path in before.values():
            self.assertTrue(path.exists(), f"{path.name} disappeared from the share")
        self.assertEqual(len(list(self.share.iterdir())), len(before))

    def test_an_unavailable_share_is_logged_not_crashed(self):
        result = scan_share(path=self.share / "does-not-exist")
        self.assertEqual(result.seen, [])
        self.assertEqual(result.failed, {})

    def test_subdirectories_are_skipped(self):
        (self.share / "archief").mkdir()
        factories.uren_file(self.share)
        result = self.poll(force=True)
        self.assertEqual(len(result.imported), 1)


@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class ManagementCommandTests(DetectionTestCase):
    def test_command_runs_the_check_and_reports(self):
        factories.uren_file(self.share)
        out = StringIO()

        call_command("check_imports", "--path", str(self.share), "--force", stdout=out)

        output = out.getvalue()
        self.assertIn("imported", output)
        self.assertIn("Download uit Syntess Uren.xlsx", output)
        self.assertEqual(Uren.objects.count(), 2)

    def test_command_without_force_waits_for_stability(self):
        factories.uren_file(self.share)
        out = StringIO()

        call_command("check_imports", "--path", str(self.share), stdout=out)

        self.assertIn("waiting", out.getvalue())
        self.assertEqual(Uren.objects.count(), 0)

    def test_command_reports_an_empty_share(self):
        out = StringIO()
        call_command("check_imports", "--path", str(self.share), stdout=out)
        self.assertIn("no recognised source files found", out.getvalue())
