"""The read-only admin screens must refuse deletion, not just editing.

The import tables and the computed timeline were registered read-only from the
start, but only add and change were turned off. "Delete selected" therefore
stayed in the actions dropdown of Urenregels, Ritten, Relaties, Werkbon-
controles and Tijdblokken — and picking it on a full table posts one hidden
field per selected row, which trips Django's DATA_UPLOAD_MAX_NUMBER_FIELDS and
comes back as a bare 400. These tests pin down that the action is gone.
"""

from __future__ import annotations

import datetime as dt

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from matching.models import Relatie, Rit, Tijdblok, Uren, WerkbonControle
from matching.tests import factories

# Every model whose admin is a report of data owned elsewhere: the four raw
# import tables (owned by the share) and the timeline (owned by run_matching).
READ_ONLY_MODELS = (Uren, Rit, Relatie, WerkbonControle, Tijdblok)


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
