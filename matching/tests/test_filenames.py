"""Tests for recognising which source file is which."""

from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from matching.ingest.filenames import classify_filename
from matching.models import SourceKind


class ClassifyFilenameTests(SimpleTestCase):
    def test_recognises_the_poc_sample_names(self):
        cases = {
            "20260826 Download uit Syntess Uren  26 8 2026.xlsx": SourceKind.UREN,
            "20260826 Download uit Syntess Relaties  26 8 2026.xlsx": SourceKind.RELATIE,
            "20260826 Download uit Syntess Werkbonnen  26 8 2026.xlsx": (
                SourceKind.WERKBON_CONTROLE
            ),
            "20260826 Ritten_Alle_voertuigen aug 26 (CSV uit Syntess).csv": (
                SourceKind.RIT
            ),
        }
        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(classify_filename(filename), expected)

    def test_matching_is_loose_enough_for_a_different_convention(self):
        # The real export convention is not confirmed yet (functioneel-ontwerp §9),
        # so a different prefix, date format or separator must still be recognised.
        cases = {
            "uren.xlsx": SourceKind.UREN,
            "SYNTESS_UREN_20260826.xlsx": SourceKind.UREN,
            "export-relaties-2026-08-26.xlsx": SourceKind.RELATIE,
            "Werkbonnen_20260826.xlsx": SourceKind.WERKBON_CONTROLE,
            "ritten_20260826.csv": SourceKind.RIT,
        }
        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(classify_filename(filename), expected)

    def test_extension_has_to_match_too(self):
        self.assertIsNone(classify_filename("Uren.csv"))
        self.assertIsNone(classify_filename("Ritten.xlsx"))

    def test_unrelated_files_are_ignored(self):
        for filename in (
            "readme.txt",
            "~$Uren.xlsx.tmp",
            "Facturen 2026.xlsx",
            "thumbs.db",
        ):
            with self.subTest(filename=filename):
                self.assertIsNone(classify_filename(filename))

    def test_a_full_path_is_classified_on_its_filename(self):
        self.assertEqual(
            classify_filename(r"\\stroes-1909\atrium\Autoprint\RUUDS\Uren.xlsx"),
            SourceKind.UREN,
        )

    @override_settings(
        RMW_FILE_PATTERNS={SourceKind.UREN: (r"^HOURS_\d+$|HOURS", (".xlsx",))}
    )
    def test_patterns_can_be_replaced_per_deployment(self):
        # Once the real convention is confirmed, only this table has to change.
        self.assertEqual(classify_filename("HOURS_20260826.xlsx"), SourceKind.UREN)
        self.assertIsNone(classify_filename("Uren.xlsx"))
