"""Tests for the completeness check: finished werkbonnen without booked hours."""

from __future__ import annotations

import datetime as dt

from django.test import TestCase

from matching.models import FaseStatus
from matching.tests import factories
from matching.timeline.volledigheidscontrole import werkbonnen_zonder_uren

DAG = dt.date(2026, 8, 3)
VOLGENDE_DAG = dt.date(2026, 8, 4)


class VolledigheidscontroleTests(TestCase):
    def test_a_finished_werkbon_without_hours_is_reported(self):
        factories.werkbon_controle("WB260908", "005", DAG, FaseStatus.AFGEROND)
        resultaat = werkbonnen_zonder_uren()
        self.assertTrue(resultaat.uitgevoerd)
        self.assertEqual(resultaat.werkbonnen, ["WB260908"])
        self.assertTrue(resultaat)

    def test_a_finished_werkbon_with_hours_is_not_reported(self):
        factories.werkbon_controle("WB260908", "005", DAG, FaseStatus.AFGEROND)
        factories.urenregel("005", DAG, "WB260908")
        self.assertEqual(werkbonnen_zonder_uren().werkbonnen, [])

    def test_a_werkbon_that_never_started_is_not_a_signal(self):
        # Expected to have no hours yet — that is not an anomaly.
        factories.werkbon_controle("WB261151", "001", DAG, FaseStatus.NIET_GESTART)
        self.assertEqual(werkbonnen_zonder_uren().werkbonnen, [])

    def test_hours_on_another_date_still_count(self):
        # The check judges the werkbon as a whole, not per date: a werkbon can be
        # finished on one day and have its hours booked on another
        # (docs/functioneel-ontwerp.md §3b).
        factories.werkbon_controle("WB260986", "005", VOLGENDE_DAG, FaseStatus.AFGEROND)
        factories.urenregel("005", DAG, "WB260986")
        self.assertEqual(werkbonnen_zonder_uren().werkbonnen, [])

    def test_hours_booked_by_someone_else_still_count(self):
        factories.werkbon_controle("WB260986", "005", DAG, FaseStatus.AFGEROND)
        factories.urenregel("002", DAG, "WB260986")
        self.assertEqual(werkbonnen_zonder_uren().werkbonnen, [])

    def test_a_date_range_narrows_which_werkbonnen_are_looked_at(self):
        factories.werkbon_controle("WB260908", "005", DAG, FaseStatus.AFGEROND)
        factories.werkbon_controle("WB260986", "005", VOLGENDE_DAG, FaseStatus.AFGEROND)
        resultaat = werkbonnen_zonder_uren(van=VOLGENDE_DAG)
        self.assertEqual(resultaat.werkbonnen, ["WB260986"])

    def test_without_the_source_file_the_check_reports_it_did_not_run(self):
        # A missing Werkbonnen.xlsx blocks only its own purpose, never the
        # matching (docs/business-rules.md, 02-09-2026).
        resultaat = werkbonnen_zonder_uren()
        self.assertFalse(resultaat.uitgevoerd)
        self.assertEqual(resultaat.werkbonnen, [])
        self.assertIn("niet ingelezen", resultaat.reden)
        self.assertFalse(resultaat)
