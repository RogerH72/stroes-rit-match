"""Tests for the run_matching command and the runner behind it.

The behaviour that matters here is not the classification (test_timeline.py) but
what a run does to what is already stored: a computed day is what the later
screens build on, so it never changes by itself.
"""

from __future__ import annotations

import datetime as dt
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from matching.models import Instelling, MeegeredenKoppeling, MeegeredenModus, Soort, Tijdblok
from matching.tests import factories
from matching.timeline.runner import run_matching

DAG = dt.date(2026, 8, 3)
VOLGENDE_DAG = dt.date(2026, 8, 4)

THUIS = ("J. Bosschaartstraat 22", "4112 LN Beusichem")
KLANT = ("Lingedijk 65", "4196 HB Tricht")


def _werkdag(bestuurder: str, datum: dt.date) -> None:
    """Home -> customer -> home, with an hour at the customer in between."""
    factories.rit(
        bestuurder, datum, "07:30", "08:00",
        vertrekadres=THUIS[0], vertrekplaats=THUIS[1],
        aankomstadres=KLANT[0], aankomstplaats=KLANT[1],
    )
    factories.rit(
        bestuurder, datum, "09:00", "09:30",
        vertrekadres=KLANT[0], vertrekplaats=KLANT[1],
        aankomstadres=THUIS[0], aankomstplaats=THUIS[1],
    )


class RunMatchingTests(TestCase):
    def setUp(self):
        self.monteur = factories.monteur("M5", "005", "M5")
        _werkdag("M5", DAG)
        _werkdag("M5", VOLGENDE_DAG)
        factories.urenregel(
            "005", DAG, "WB260908",
            adres=KLANT[0], postcode="4196 HB", plaats="TRICHT",
        )

    def test_a_run_stores_the_blocks_of_every_day_with_ride_data(self):
        result = run_matching()
        self.assertEqual(len(result.dagen), 2)
        self.assertEqual(Tijdblok.objects.filter(datum=DAG).count(), 3)
        self.assertEqual(
            set(Tijdblok.objects.filter(datum=DAG).values_list("soort", flat=True)),
            {Soort.REISTIJD, Soort.WERKBON},
        )

    def test_a_dry_run_writes_nothing(self):
        result = run_matching(dry_run=True)
        self.assertEqual(len(result.dagen), 2)
        self.assertEqual(Tijdblok.objects.count(), 0)

    def test_a_second_run_leaves_an_existing_day_alone(self):
        run_matching()
        berekend_op = Tijdblok.objects.earliest("id").berekend_op

        result = run_matching()
        self.assertEqual(result.dagen, [])
        self.assertEqual(len(result.overgeslagen), 2)
        self.assertEqual(Tijdblok.objects.earliest("id").berekend_op, berekend_op)

    def test_force_recomputes_a_day_without_duplicating_it(self):
        run_matching()
        before = Tijdblok.objects.count()

        # A koppeltabel change is exactly why --force exists: the same day now
        # classifies differently.
        factories.bekende_locatie("straat", "Lingedijk", Soort.LOCATIE, "Magazijn 2",
                                  is_depot=True)
        result = run_matching(force=True)

        self.assertEqual(len(result.dagen), 2)
        self.assertEqual(Tijdblok.objects.count(), before)
        self.assertEqual(
            Tijdblok.objects.filter(datum=DAG, soort=Soort.WERKBON).count(), 0
        )
        self.assertEqual(
            Tijdblok.objects.filter(datum=DAG, soort=Soort.LOCATIE).count(), 1
        )

    def test_a_date_range_limits_the_run(self):
        result = run_matching(van=VOLGENDE_DAG, tot=VOLGENDE_DAG)
        self.assertEqual([dag.datum for dag in result.dagen], [VOLGENDE_DAG])

    def test_selecting_one_monteur_skips_the_others(self):
        factories.monteur("M1", "001", "M1")
        _werkdag("M1", DAG)
        result = run_matching(medewerker_nummer="005")
        self.assertEqual({dag.monteur for dag in result.dagen}, {self.monteur})

    def test_inactive_monteurs_are_skipped_by_default(self):
        self.monteur.actief = False
        self.monteur.save()
        self.assertEqual(run_matching().dagen, [])

    def test_an_inactive_monteur_can_still_be_named_explicitly(self):
        self.monteur.actief = False
        self.monteur.save()
        self.assertEqual(len(run_matching(medewerker_nummer="005").dagen), 2)

    def test_a_junior_gets_the_days_of_the_senior_he_rides_with(self):
        # He has no ride data of his own, so without the koppeling there would be
        # no dates to process at all.
        junior = factories.monteur("Junior", "009", vaste_meerijder=self.monteur)
        result = run_matching(medewerker_nummer="009")
        self.assertEqual([dag.datum for dag in result.dagen], [DAG, VOLGENDE_DAG])
        self.assertTrue(all(dag.meegereden for dag in result.dagen))
        self.assertEqual(Tijdblok.objects.filter(monteur=junior).count(), 6)

    def test_a_junior_gets_the_days_of_a_period_koppeling(self):
        Instelling.objects.update_or_create(
            pk=Instelling.SINGLETON_PK,
            defaults={"meegereden_modus": MeegeredenModus.PERIODE},
        )
        junior = factories.monteur("Junior", "009")
        MeegeredenKoppeling.objects.create(
            junior=junior, senior=self.monteur, datum_van=DAG, datum_tot=DAG
        )
        result = run_matching(medewerker_nummer="009")
        self.assertEqual([dag.datum for dag in result.dagen], [DAG])


class RunMatchingCommandTests(TestCase):
    """The command wrapper: arguments in, a readable day summary out."""

    def setUp(self):
        self.monteur = factories.monteur("M5", "005", "M5")
        _werkdag("M5", DAG)

    def _call(self, *args) -> str:
        out = StringIO()
        call_command("run_matching", *args, stdout=out)
        return out.getvalue()

    def test_it_prints_a_per_day_soort_summary(self):
        output = self._call()
        self.assertIn("2026-08-03", output)
        self.assertIn("M5", output)
        self.assertIn("R 1:00", output)  # two rides of 30 minutes
        self.assertIn("O 1:00", output)  # the unexplained hour in between
        self.assertIn("totaal 2:00", output)
        self.assertIn("1 dag(en) berekend, 3 tijdblok(ken)", output)

    def test_dry_run_says_so_and_stores_nothing(self):
        output = self._call("--dry-run")
        self.assertIn("Dry run", output)
        self.assertEqual(Tijdblok.objects.count(), 0)

    def test_an_already_computed_day_is_reported_as_skipped(self):
        self._call()
        self.assertIn("al berekend (gebruik --force)", self._call())

    def test_force_recomputes(self):
        self._call()
        self.assertIn("1 dag(en) berekend", self._call("--force"))

    def test_a_monteur_without_ride_data_is_reported(self):
        factories.monteur("Nieuw", "007", "M7")
        self.assertIn("geen ritdata", self._call())

    def test_an_invalid_date_is_rejected_with_a_clear_message(self):
        with self.assertRaises(CommandError):
            self._call("--van", "03-08-2026")

    def test_an_inverted_date_range_is_rejected(self):
        with self.assertRaises(CommandError):
            self._call("--van", "2026-08-04", "--tot", "2026-08-03")
