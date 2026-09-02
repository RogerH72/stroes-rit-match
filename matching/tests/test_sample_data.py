"""Tests against the real anonymised sample exports in voorbeeld-data/.

These are structurally representative Syntess/RouteVision exports, so they catch
things a hand-written fixture cannot — the actual sheet names, the real column
spelling, the trailing empty rows in Relaties.xlsx.

They are skipped when the folder is absent: it holds (anonymised) customer data
and is currently not in version control, so a fresh clone must still be able to
run the suite. The rest of matching/tests/ covers the same behaviour with its own
generated fixtures.
"""

from __future__ import annotations

import unittest

from django.conf import settings
from django.test import TestCase, override_settings

from matching.ingest.detection import scan_share
from matching.models import (
    FaseStatus,
    ImportedFile,
    ImportStatus,
    Relatie,
    Rit,
    SourceKind,
    Uren,
    WerkbonControle,
)

SAMPLE_DIR = settings.BASE_DIR / "voorbeeld-data"

sample_data_required = unittest.skipUnless(
    SAMPLE_DIR.is_dir() and any(SAMPLE_DIR.iterdir()),
    f"sample exports not present in {SAMPLE_DIR}",
)


@sample_data_required
@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class SampleDataImportTests(TestCase):
    """One forced pass over voorbeeld-data/, then check what landed."""

    @classmethod
    def setUpTestData(cls):
        cls.result = scan_share(path=SAMPLE_DIR, force=True)

    def test_all_four_sources_are_recognised_and_imported(self):
        self.assertEqual(self.result.failed, {})
        self.assertEqual(
            set(ImportedFile.objects.values_list("source_kind", flat=True)),
            {
                SourceKind.UREN,
                SourceKind.RIT,
                SourceKind.RELATIE,
                SourceKind.WERKBON_CONTROLE,
            },
        )
        self.assertTrue(
            all(
                record.status == ImportStatus.VERWERKT
                for record in ImportedFile.objects.all()
            )
        )

    def test_uren_rows_are_read(self):
        self.assertEqual(Uren.objects.count(), 31)
        row = Uren.objects.order_by("row_number").first()
        self.assertEqual(row.medewerker, "001")
        self.assertEqual(row.werkbon, "WB261195")
        # Anonymised names still carry their accents through the import.
        self.assertEqual(row.project_opdrachtgever_naam, "Daniël Beuker")

    def test_rit_rows_are_read_from_the_cp1252_csv(self):
        self.assertEqual(Rit.objects.count(), 92)
        first = Rit.objects.order_by("row_number").first()
        self.assertEqual(first.kenteken, "V-31-JRT")
        self.assertEqual(str(first.km_totaal), "6.89")
        self.assertEqual(first.duur.total_seconds(), 607)

    def test_relaties_drops_its_long_tail_of_empty_rows(self):
        # The sheet is ~2500 rows, of which only two hold data.
        self.assertEqual(Relatie.objects.count(), 2)
        self.assertEqual(
            set(Relatie.objects.values_list("code", flat=True)), {"0000", "0001"}
        )

    def test_werkbon_fase_rows_collapse_to_one_row_per_werkbon_medewerker_date(self):
        # 38 Fase rows in the export, 19 (werkbon, medewerker, datum) combinations.
        self.assertEqual(WerkbonControle.objects.count(), 19)
        self.assertEqual(
            WerkbonControle.objects.filter(fase_status=FaseStatus.AFGEROND).count(), 13
        )
        self.assertEqual(
            WerkbonControle.objects.filter(fase_status=FaseStatus.NIET_GESTART).count(), 6
        )

    def test_a_werkbon_that_never_got_past_gestopt_counts_as_not_started(self):
        statuses = set(
            WerkbonControle.objects.filter(werkbon="WB261151").values_list(
                "fase_status", flat=True
            )
        )
        self.assertEqual(statuses, {FaseStatus.NIET_GESTART})

    def test_the_sample_files_are_left_untouched(self):
        for record in ImportedFile.objects.all():
            self.assertTrue((SAMPLE_DIR / record.filename).exists())
