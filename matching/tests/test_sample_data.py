"""Tests against the real anonymised sample exports in voorbeeld-data/.

These are structurally representative Syntess/RouteVision exports, so they catch
things a hand-written fixture cannot — the actual sheet names, the real column
spelling, the trailing empty rows in Relaties.xlsx.

The matching itself is exercised against them too, at the bottom of this file.

They are skipped when the folder is absent: it holds (anonymised) customer data
and is currently not in version control, so a fresh clone must still be able to
run the suite. The rest of matching/tests/ covers the same behaviour with its own
generated fixtures.
"""

from __future__ import annotations

import datetime as dt
import unittest

from django.conf import settings
from django.test import TestCase, override_settings

from matching.ingest.detection import scan_share
from matching.models import (
    BekendeLocatie,
    FaseStatus,
    ImportedFile,
    ImportStatus,
    LocatieType,
    Monteur,
    Relatie,
    Rit,
    Soort,
    SourceKind,
    Tijdblok,
    Uren,
    WerkbonControle,
)
from matching.timeline.runner import run_matching
from matching.timeline.volledigheidscontrole import werkbonnen_zonder_uren

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


@sample_data_required
@override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30)
class SampleDataMatchingTests(TestCase):
    """run_matching end-to-end on the real exports, checked against the PoC.

    The koppeltabel content is the same minimum the PoC hardcoded: the two
    monteurs in this export, and the depot at Randweg / 4104 AC. The point is a
    sanity check on the whole chain — import, meegereden resolution, day
    reconstruction, storage — plus a look at how many werkbonnen come back
    automatically, so a rule that silently stops working does not go unnoticed.
    """

    @classmethod
    def setUpTestData(cls):
        scan_share(path=SAMPLE_DIR, force=True)
        cls.m5 = Monteur.objects.create(
            naam="M5", medewerker_nummer="005", bestuurder_code="M5",
            kenteken="V-31-JRT",
        )
        cls.m1 = Monteur.objects.create(
            naam="M1", medewerker_nummer="001", bestuurder_code="M1",
            kenteken="VKV-60-T",
        )
        for locatie_type, waarde in (
            (LocatieType.POSTCODE, "4104 AC"),
            (LocatieType.STRAAT, "Randweg"),
        ):
            BekendeLocatie.objects.create(
                type=locatie_type,
                waarde=waarde,
                soort=Soort.LOCATIE,
                label="SBTT-Magazijn (Randweg, Culemborg)",
                is_depot=True,
            )
        cls.result = run_matching()

    def test_every_working_day_in_the_export_is_reconstructed(self):
        # Both monteurs drove Monday through Friday of the sample week.
        self.assertEqual(len(self.result.dagen), 10)
        self.assertEqual(
            sorted({dag.datum for dag in self.result.dagen}),
            [dt.date(2026, 8, day) for day in range(3, 8)],
        )
        self.assertEqual(Tijdblok.objects.count(), self.result.aantal_blokken)

    def test_a_day_is_a_chain_of_rides_and_stops(self):
        blokken = list(
            Tijdblok.objects.filter(monteur=self.m5, datum=dt.date(2026, 8, 3))
        )
        self.assertEqual([b.volgorde for b in blokken], list(range(1, len(blokken) + 1)))
        # A day starts and ends with a ride; stops only ever sit in between.
        self.assertEqual(blokken[0].soort, Soort.REISTIJD)
        self.assertEqual(blokken[-1].soort, Soort.REISTIJD)
        for blok in blokken:
            self.assertLessEqual(blok.start_tijd, blok.eind_tijd)

    def test_the_depot_is_recognised(self):
        self.assertTrue(
            Tijdblok.objects.filter(
                soort=Soort.LOCATIE, omschrijving__startswith="SBTT-Magazijn"
            ).exists()
        )

    def test_werkbon_recovery_is_in_the_range_the_poc_found(self):
        """Roughly what the PoC/validation script got — no wild divergence.

        The PoC reported 82% for M5 on this week and the broader validation 78%
        and 93% for two other monteurs over four weeks. This app scores a little
        lower on purpose: the PoC also matched on postcodes from Werkbonnen.xlsx,
        which is deliberately not a matching source here (docs/business-rules.md).
        The bound is loose because the exact figure depends on the koppeltabel;
        it is there to catch a rule that breaks, not to pin a number.
        """
        gevonden, totaal = self._werkbon_recovery(self.m5)
        self.assertGreaterEqual(totaal, 8, "sample data no longer holds M5's week")
        self.assertGreaterEqual(gevonden / totaal, 0.6)

    def test_m1_shows_the_depot_rule_outranking_a_werkbon(self):
        """M1 works at Randweg 20 — the depot street, so his stops read as L.

        Not a defect but the validated priority order at work (a stop at the
        company's own address is a depot visit, not work at the customer who
        shares that address). Asserted so the behaviour is visible rather than
        surprising, and so a change to the order shows up here.
        """
        gevonden, totaal = self._werkbon_recovery(self.m1)
        self.assertGreater(totaal, 0)
        self.assertEqual(gevonden, 0)
        self.assertTrue(
            Tijdblok.objects.filter(monteur=self.m1, soort=Soort.LOCATIE).exists()
        )

    def test_the_completeness_check_runs_on_the_real_werkbonnen(self):
        resultaat = werkbonnen_zonder_uren()
        self.assertTrue(resultaat.uitgevoerd)
        # Whatever it reports must be finished werkbonnen that really have no hours.
        geboekt = set(Uren.objects.values_list("werkbon", flat=True))
        for werkbon in resultaat.werkbonnen:
            self.assertNotIn(werkbon, geboekt)

    def _werkbon_recovery(self, monteur: Monteur) -> tuple[int, int]:
        """(recovered, total) werkbonnen this monteur booked hours on."""
        gevonden = totaal = 0
        for datum in sorted({dag.datum for dag in self.result.dagen}):
            geboekt = set(
                Uren.objects.filter(
                    medewerker=monteur.medewerker_nummer, datum=datum
                ).values_list("werkbon", flat=True)
            )
            teruggevonden = set(
                Tijdblok.objects.filter(
                    monteur=monteur, datum=datum, soort=Soort.WERKBON
                ).values_list("werkbon", flat=True)
            )
            totaal += len(geboekt)
            gevonden += len(geboekt & teruggevonden)
        return gevonden, totaal
