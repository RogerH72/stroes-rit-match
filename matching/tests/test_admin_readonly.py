"""The read-only admin screens must refuse adding, editing and deleting.

The import tables and the computed timeline were registered read-only from the
start, but only add and change were turned off. "Delete selected" therefore
stayed in the actions dropdown of Urenregels, Ritten, Relaties, Werkbon-
controles and Tijdblokken — and picking it on a full table posts one hidden
field per selected row, which trips Django's DATA_UPLOAD_MAX_NUMBER_FIELDS and
comes back as a bare 400. These tests pin down that the action is gone.

Importbestanden joined the group on 09-09-2026 and is the one that could do the
most damage: it is not a copy of anything, it is the record scan_share() and the
matching believe about what has already been read in. All three permissions are
therefore checked for every model here, not just deletion.
"""

from __future__ import annotations

import datetime as dt

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from matching.models import (
    ImportedFile,
    ImportStatus,
    Relatie,
    Rit,
    SourceKind,
    Tijdblok,
    Uren,
    WerkbonControle,
)
from matching.tests import factories

# Every model whose admin is a report of data owned elsewhere: the four raw
# import tables (owned by the share), the timeline (owned by run_matching) and
# the import bookkeeping (owned by scan_share).
READ_ONLY_MODELS = (Uren, Rit, Relatie, WerkbonControle, Tijdblok, ImportedFile)


class ReadOnlyAdminDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("beheer", "b@sbtt.nl", "geheim")

    def setUp(self):
        self.client.force_login(self.staff)

    def _request(self):
        request = RequestFactory().get("/")
        request.user = self.staff
        return request

    def test_adding_is_refused_for_every_read_only_model(self):
        # Nothing here is data a person enters; every row arrives through an
        # import or a run.
        for model in READ_ONLY_MODELS:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertFalse(model_admin.has_add_permission(self._request()))

    def test_changing_is_refused_for_every_read_only_model(self):
        for model in READ_ONLY_MODELS:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertFalse(model_admin.has_change_permission(self._request()))

    def test_deletion_is_refused_for_every_read_only_model(self):
        for model in READ_ONLY_MODELS:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertFalse(model_admin.has_delete_permission(self._request()))

    def test_delete_selected_is_not_offered_as_an_action(self):
        # Django filters the actions dropdown on has_delete_permission, so the
        # refusal above is what keeps the option off the screen entirely.
        for model in READ_ONLY_MODELS:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertNotIn(
                    "delete_selected", model_admin.get_actions(self._request())
                )

    def test_the_delete_url_is_refused_for_a_single_row(self):
        # Even hand-typed: a superuser has the Django-level delete permission,
        # so only the admin class stands between him and a missing row.
        regel = factories.urenregel("002", dt.date(2026, 8, 3), "W1000")
        url = reverse("admin:matching_uren_delete", args=[regel.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
        self.assertTrue(Uren.objects.filter(pk=regel.pk).exists())

    def test_the_changelist_still_opens(self):
        # Turning the permission off must not take the screen itself away —
        # looking at what was imported is the whole point of these admins.
        factories.urenregel("002", dt.date(2026, 8, 3), "W1000")
        response = self.client.get(reverse("admin:matching_uren_changelist"))
        self.assertEqual(response.status_code, 200)


class ImportbestandAdminTests(TestCase):
    """Importbestanden, locked down on 09-09-2026.

    Checked through the screens rather than only through the permission methods,
    because what was reported was what the screen offered: an "Add" button, and a
    change form that saved. A hand-made row here is worse than a hand-made import
    row — set a status to "verwerkt" and the app stops reading a file it never
    read, without anything looking wrong.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("beheer", "b@sbtt.nl", "geheim")

    def setUp(self):
        self.client.force_login(self.staff)
        self.bestand = ImportedFile.objects.create(
            filename="Download uit Syntess Uren.xlsx",
            source_kind=SourceKind.UREN,
            size_bytes=4096,
            last_measured_at=timezone.now(),
            status=ImportStatus.WACHTEND,
        )

    def test_the_changelist_offers_no_add_button(self):
        response = self.client.get(reverse("admin:matching_importedfile_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("admin:matching_importedfile_add"))
        self.assertNotContains(response, "Importbestand toevoegen")

    def test_the_add_screen_is_refused(self):
        url = reverse("admin:matching_importedfile_add")

        # assertLogs only to keep Django's 403 traceback out of the test output.
        with self.assertLogs("django.request", "WARNING"):
            self.assertEqual(self.client.get(url).status_code, 403)
        with self.assertLogs("django.request", "WARNING"):
            self.assertEqual(self.client.post(url, {"filename": "x.xlsx"}).status_code, 403)
        self.assertEqual(ImportedFile.objects.count(), 1)

    def test_a_status_cannot_be_set_to_verwerkt_by_hand(self):
        # The hole this closes: the app would then skip a file it never read.
        url = reverse("admin:matching_importedfile_change", args=[self.bestand.pk])

        with self.assertLogs("django.request", "WARNING"):
            response = self.client.post(
                url,
                {
                    "filename": self.bestand.filename,
                    "source_kind": SourceKind.UREN,
                    "status": ImportStatus.VERWERKT,
                },
            )

        self.assertEqual(response.status_code, 403)
        self.bestand.refresh_from_db()
        self.assertEqual(self.bestand.status, ImportStatus.WACHTEND)

    def test_the_delete_url_is_refused(self):
        url = reverse("admin:matching_importedfile_delete", args=[self.bestand.pk])

        with self.assertLogs("django.request", "WARNING"):
            self.assertEqual(self.client.get(url).status_code, 403)
        with self.assertLogs("django.request", "WARNING"):
            self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
        self.assertTrue(ImportedFile.objects.filter(pk=self.bestand.pk).exists())

    def test_the_row_is_still_readable(self):
        # The screen exists to show the status per file; locking it must not
        # take that away.
        response = self.client.get(
            reverse("admin:matching_importedfile_change", args=[self.bestand.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bestand.filename)
