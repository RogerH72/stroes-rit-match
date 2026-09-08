"""Tests for the phase 4 admin: the status record and the two manual buttons.

Three things are being protected here. First, that the status row tells the truth
whichever way a run was triggered — that is the whole reason the wrapper exists.
Second, that neither button can fire on a GET: one rewrites every Tijdblok, the
other imports rows. Third, that "Bestanden nu inlezen" only imports — it must not
quietly recompute as well, because importing and recomputing are deliberately two
separate steps (docs/decisions.md, 08-09-2026).
"""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from matching.admin import MatchmotorStatusAdmin
from matching.models import (
    ImportedFile,
    ImportStatus,
    MatchmotorStatus,
    Rit,
    Tijdblok,
    Uren,
)
from matching.tests import factories
from matching.timeline.runner import run_matching_and_record_status

DAG = dt.date(2026, 8, 3)

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


class MatchmotorStatusModelTests(TestCase):
    """Singleton behaviour, same as Instelling."""

    def test_load_creates_the_single_row(self):
        status = MatchmotorStatus.load()
        self.assertEqual(status.pk, MatchmotorStatus.SINGLETON_PK)
        self.assertEqual(MatchmotorStatus.objects.count(), 1)

    def test_a_fresh_row_says_never_run_rather_than_failed(self):
        # None and False are different signals: nothing has happened yet versus
        # the last attempt went wrong.
        status = MatchmotorStatus.load()
        self.assertIsNone(status.succes)
        self.assertIsNone(status.laatste_run_gestart_op)
        self.assertEqual(status.dagen_verwerkt, 0)

    def test_saving_a_second_row_overwrites_the_first_one(self):
        MatchmotorStatus.load()
        MatchmotorStatus(dagen_verwerkt=7).save()
        self.assertEqual(MatchmotorStatus.objects.count(), 1)
        self.assertEqual(MatchmotorStatus.load().dagen_verwerkt, 7)

    def test_it_cannot_be_deleted(self):
        with self.assertRaises(ValidationError):
            MatchmotorStatus.load().delete()
        self.assertEqual(MatchmotorStatus.objects.count(), 1)


class RecordStatusTests(TestCase):
    """The wrapper both trigger paths go through."""

    def setUp(self):
        self.monteur = factories.monteur("M5", "005", "M5")
        _werkdag("M5", DAG)

    def test_a_successful_run_is_recorded(self):
        result = run_matching_and_record_status()

        status = MatchmotorStatus.load()
        self.assertTrue(status.succes)
        self.assertEqual(status.dagen_verwerkt, len(result.dagen))
        self.assertEqual(status.foutmelding, "")
        self.assertIsNotNone(status.laatste_run_gestart_op)
        self.assertIsNotNone(status.laatste_run_afgerond_op)
        self.assertLessEqual(
            status.laatste_run_gestart_op, status.laatste_run_afgerond_op
        )

    def test_a_failing_run_is_recorded_and_still_raises(self):
        # The caller has to keep seeing the failure — recording it must not
        # swallow it.
        with mock.patch(
            "matching.timeline.runner.run_matching",
            side_effect=RuntimeError("ritdata onleesbaar"),
        ):
            with self.assertRaises(RuntimeError):
                run_matching_and_record_status()

        status = MatchmotorStatus.load()
        self.assertIs(status.succes, False)
        self.assertIn("ritdata onleesbaar", status.foutmelding)
        self.assertIsNotNone(status.laatste_run_afgerond_op)

    def test_a_later_success_clears_the_previous_error(self):
        with mock.patch(
            "matching.timeline.runner.run_matching",
            side_effect=RuntimeError("even mis"),
        ):
            with self.assertRaises(RuntimeError):
                run_matching_and_record_status()

        run_matching_and_record_status(force=True)
        status = MatchmotorStatus.load()
        self.assertTrue(status.succes)
        self.assertEqual(status.foutmelding, "")

    def test_a_dry_run_is_not_recorded_as_a_run(self):
        # It writes no Tijdblok rows, so calling it "de laatste run" would make
        # the status claim work that never happened.
        run_matching_and_record_status(dry_run=True)
        status = MatchmotorStatus.load()
        self.assertIsNone(status.succes)
        self.assertIsNone(status.laatste_run_gestart_op)

    def test_the_command_records_status_too(self):
        from django.core.management import call_command
        from io import StringIO

        call_command("run_matching", stdout=StringIO())
        self.assertTrue(MatchmotorStatus.load().succes)


# The project serves static files with WhiteNoise's manifest storage, which
# needs a collectstatic run. These tests render real admin pages, so they fall
# back on plain storage rather than requiring a build step before `manage.py test`.
@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class RunNowButtonTests(TestCase):
    """The admin endpoint behind the "Matching nu draaien" button."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("beheer", "b@sbtt.nl", "geheim")
        cls.url = reverse("admin:matching_matchmotorstatus_run")
        cls.changelist = reverse("admin:matching_matchmotorstatus_changelist")

    def setUp(self):
        self.monteur = factories.monteur("M5", "005", "M5")
        _werkdag("M5", DAG)
        self.client.force_login(self.staff)

    def test_the_button_is_on_the_changelist(self):
        response = self.client.get(self.changelist)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Matching nu draaien")
        self.assertContains(response, self.url)

    def test_posting_runs_the_matching_and_redirects_back(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, self.changelist)
        self.assertEqual(Tijdblok.objects.filter(monteur=self.monteur).count(), 3)
        self.assertTrue(MatchmotorStatus.load().succes)

    def test_it_reports_what_it_did(self):
        response = self.client.post(self.url, follow=True)
        messages = [str(m) for m in response.context["messages"]]
        self.assertTrue(
            any("1 dag(en) herberekend" in message for message in messages), messages
        )

    def test_a_get_does_not_run_anything(self):
        # POST-only: a refreshed tab or a link preview must not be able to
        # rewrite every Tijdblok.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Tijdblok.objects.count(), 0)
        self.assertIsNone(MatchmotorStatus.load().succes)

    def test_it_recomputes_days_that_were_already_computed(self):
        # The button is for "I changed a koppeltabel, redo everything", so it
        # must not skip days that already have a result the way a plain run does.
        self.client.post(self.url)
        self.client.post(self.url)
        self.assertEqual(MatchmotorStatus.load().dagen_verwerkt, 1)

    def test_a_failure_is_shown_instead_of_a_traceback(self):
        with mock.patch(
            "matching.admin.run_matching_and_record_status",
            side_effect=RuntimeError("ritdata onleesbaar"),
        ):
            response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, self.changelist)
        messages = [str(m) for m in response.context["messages"]]
        self.assertTrue(
            any("mislukt" in message for message in messages), messages
        )

    def test_a_non_staff_user_cannot_reach_it(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Tijdblok.objects.count(), 0)

    def test_adding_and_deleting_the_status_row_are_not_offered(self):
        response = self.client.get(self.changelist)
        self.assertNotContains(response, "Matchmotor-status toevoegen")

    def test_the_row_cannot_be_edited_by_hand(self):
        # The row reports what a run did; the change form must not be a way to
        # rewrite that report.
        MatchmotorStatus.load()
        change_url = reverse(
            "admin:matching_matchmotorstatus_change",
            args=[MatchmotorStatus.SINGLETON_PK],
        )
        # assertLogs only to keep Django's 403 traceback out of the test output.
        with self.assertLogs("django.request", "WARNING"):
            response = self.client.post(change_url, {"dagen_verwerkt": 99})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(MatchmotorStatus.load().dagen_verwerkt, 0)

    def test_the_button_still_works_with_the_form_read_only(self):
        # The two live together on purpose: the run writes the row through
        # save(), not through the admin form, so switching the form off must not
        # switch the button off with it.
        self.assertFalse(
            MatchmotorStatusAdmin(MatchmotorStatus, admin.site).has_change_permission(
                None
            )
        )
        response = self.client.post(self.url)
        self.assertRedirects(response, self.changelist)
        self.assertTrue(MatchmotorStatus.load().succes)

    def test_a_staff_user_without_the_permission_cannot_press_it(self):
        # has_change_permission() is False for everyone now, so the endpoint
        # checks the underlying Django permission instead — it must still say no
        # to staff who do not have it.
        kijker = User.objects.create_user(
            "kijker", "k@sbtt.nl", "geheim", is_staff=True
        )
        self.client.force_login(kijker)
        with self.assertLogs("django.request", "WARNING"):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Tijdblok.objects.count(), 0)


class BestandenInlezenButtonTests(TestCase):
    """The admin endpoint behind the "Bestanden nu inlezen" button (08-09-2026).

    SBTT staff have no shell to run `check_imports` in, so the share can hold a
    file nobody has read in yet. This button is that command, minus the two
    options that stay deliberate manual steps: no reprocess, and no matching run
    afterwards.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("beheer", "b@sbtt.nl", "geheim")
        cls.url = reverse("admin:matching_bestanden_inlezen")
        cls.changelist = reverse("admin:matching_matchmotorstatus_changelist")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.share = Path(self.tmp.name)
        self.instellingen = override_settings(SERVERMAP_PATH=str(self.share))
        self.instellingen.enable()
        self.addCleanup(self.instellingen.disable)
        self.client.force_login(self.staff)

    def _berichten(self, response):
        return [str(bericht) for bericht in response.context["messages"]]

    def test_the_button_is_on_the_changelist(self):
        response = self.client.get(self.changelist)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bestanden nu inlezen")
        self.assertContains(response, self.url)

    def test_posting_imports_what_is_on_the_share(self):
        factories.uren_file(self.share)

        response = self.client.post(self.url)

        self.assertRedirects(response, self.changelist)
        self.assertEqual(Uren.objects.count(), 2)
        self.assertEqual(ImportedFile.objects.get().status, ImportStatus.VERWERKT)

    def test_it_does_not_wait_out_the_stability_margin(self):
        # force=True: the margin exists for the unattended scheduler, not for
        # someone standing at the screen asking for it now. A plain poll would
        # need six unchanged measurements before importing this file.
        factories.uren_file(self.share)

        with override_settings(POLL_INTERVAL_MINUTES=5, STABILITY_MINUTES=30):
            self.client.post(self.url)

        self.assertEqual(Uren.objects.count(), 2)

    def test_it_reports_what_it_read_in(self):
        factories.uren_file(self.share)

        berichten = self._berichten(self.client.post(self.url, follow=True))

        self.assertTrue(any("Ingelezen: 1 bestand(en)" in b for b in berichten), berichten)
        self.assertTrue(any("2 rij(en)" in b for b in berichten), berichten)

    def test_it_does_not_run_the_matching_as_a_side_effect(self):
        # The whole point of keeping this a separate button: importing must not
        # silently change what the weekoverzicht shows.
        factories.uren_file(self.share)
        factories.ritten_file(self.share)
        factories.monteur("M5", "005", "M5")

        with mock.patch("matching.admin.run_matching_and_record_status") as gedraaid:
            berichten = self._berichten(self.client.post(self.url, follow=True))

        gedraaid.assert_not_called()
        self.assertEqual(Rit.objects.count(), 2)
        self.assertEqual(Tijdblok.objects.count(), 0)
        self.assertIsNone(MatchmotorStatus.load().succes)
        self.assertTrue(
            any("niet automatisch herberekend" in b for b in berichten), berichten
        )

    def test_an_empty_share_says_so_instead_of_failing(self):
        berichten = self._berichten(self.client.post(self.url, follow=True))

        self.assertTrue(
            any("Geen herkende bronbestanden" in b for b in berichten), berichten
        )
        self.assertEqual(ImportedFile.objects.count(), 0)

    def test_a_file_that_was_already_read_in_is_left_alone(self):
        # No reprocess from this button: pressing it twice must not import the
        # same file again (docs/architecture.md).
        factories.uren_file(self.share)
        self.client.post(self.url)

        berichten = self._berichten(self.client.post(self.url, follow=True))

        self.assertEqual(Uren.objects.count(), 2)
        self.assertTrue(any("Niets nieuws" in b for b in berichten), berichten)

    def test_a_failing_file_is_reported_without_stopping_the_others(self):
        factories.uren_file(self.share)
        stuk = self.share / "Download uit Syntess Relaties.xlsx"
        stuk.write_bytes(b"dit is geen xlsx")

        berichten = self._berichten(self.client.post(self.url, follow=True))

        self.assertEqual(Uren.objects.count(), 2)  # the good one still went in
        self.assertTrue(any("Ingelezen: 1 bestand(en)" in b for b in berichten), berichten)
        self.assertTrue(any("Mislukt" in b for b in berichten), berichten)

    def test_a_run_where_only_the_failure_happened_does_not_also_say_niets_nieuws(self):
        # "Niets nieuws om in te lezen" next to an error would read as a
        # contradiction: something did happen, it just went wrong.
        stuk = self.share / "Download uit Syntess Relaties.xlsx"
        stuk.write_bytes(b"dit is geen xlsx")

        berichten = self._berichten(self.client.post(self.url, follow=True))

        self.assertTrue(any("Mislukt" in b for b in berichten), berichten)
        self.assertFalse(any("Niets nieuws" in b for b in berichten), berichten)

    def test_a_get_does_not_import_anything(self):
        factories.uren_file(self.share)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Uren.objects.count(), 0)

    def test_a_user_without_the_permission_cannot_use_it(self):
        kijker = User.objects.create_user(
            "kijker", "k@sbtt.nl", "geheim", is_staff=True
        )
        kijker.user_permissions.add(
            Permission.objects.get(codename="view_matchmotorstatus")
        )
        self.client.force_login(kijker)
        factories.uren_file(self.share)

        # assertLogs only to keep Django's 403 traceback out of the test output.
        with self.assertLogs("django.request", "WARNING"):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Uren.objects.count(), 0)

    def test_a_logged_out_user_cannot_reach_it(self):
        self.client.logout()
        factories.uren_file(self.share)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Uren.objects.count(), 0)
