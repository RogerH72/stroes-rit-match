"""Tests for where the application drops you: the root URL and the login.

Three things are being protected. The root URL opens the weekoverzicht, not the
admin — the overview is the screen SBTT staff work in, the beheerschermen are
occasional. An anonymous visitor who asks for either of those two URLs comes
back to the weekoverzicht after signing in, instead of being dumped in the
admin index he did not ask for. And the "Beheer" link in the navigation bar
still goes to the admin, because that redirect must not swallow the one route
that is supposed to end up there.
"""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RootUrlTests(TestCase):
    """§/ — the front door of the application, not of the admin."""

    def test_root_redirects_to_the_weekoverzicht(self):
        antwoord = self.client.get("/")
        self.assertRedirects(
            antwoord, "/weekoverzicht/", fetch_redirect_response=False
        )

    def test_the_redirect_is_temporary(self):
        # Not a 301: which screen is the landing page is a product decision that
        # may change again, and a permanent redirect stays in browser caches
        # long after the URL configuration has moved on.
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_root_does_not_require_a_login_of_its_own(self):
        # The redirect target does the gating. Sending an anonymous visitor
        # straight to the login page from / would lose the ?next=, which is
        # exactly what carries him back to the weekoverzicht afterwards.
        antwoord = self.client.get("/")
        self.assertEqual(antwoord["Location"], "/weekoverzicht/")

    def test_the_admin_is_still_reachable(self):
        # The "Beheer" link in the navigation bar points here; the new root
        # redirect must not have taken that route over.
        antwoord = self.client.get(reverse("admin:index"))
        self.assertEqual(antwoord.status_code, 302)
        self.assertIn("/admin/login/", antwoord["Location"])


class InloggenLandtOpHetWeekoverzichtTests(TestCase):
    """§the login — where you end up after signing in."""

    WACHTWOORD = "geheim-genoeg-voor-een-test"

    def setUp(self):
        # is_staff is required: the admin's own AdminAuthenticationForm refuses
        # a non-staff account, and the admin login is the only login this app
        # has (docs/decisions.md, 2026-09-03).
        self.gebruiker = User.objects.create_user(
            "wim", password=self.WACHTWOORD, is_staff=True
        )

    def _log_in(self, next_url: str) -> "object":
        return self.client.post(
            f"/admin/login/?next={next_url}",
            {
                "username": "wim",
                "password": self.WACHTWOORD,
                "next": next_url,
            },
        )

    def test_anonymous_visitor_is_sent_to_the_login_with_a_way_back(self):
        antwoord = self.client.get("/weekoverzicht/")
        self.assertRedirects(
            antwoord,
            "/admin/login/?next=/weekoverzicht/",
            fetch_redirect_response=False,
        )

    def test_login_lands_on_the_weekoverzicht(self):
        antwoord = self._log_in("/weekoverzicht/")
        self.assertRedirects(
            antwoord, "/weekoverzicht/", fetch_redirect_response=False
        )

    def test_the_whole_route_from_the_root_url_ends_on_the_weekoverzicht(self):
        # The path a user actually walks: type the bare host, get bounced to the
        # login, sign in, and arrive on the overview rather than in the admin.
        naar_overzicht = self.client.get("/")
        naar_login = self.client.get(naar_overzicht["Location"])
        self.assertIn("next=/weekoverzicht/", naar_login["Location"])

        na_inloggen = self._log_in("/weekoverzicht/")
        self.assertEqual(na_inloggen["Location"], "/weekoverzicht/")

    def test_a_login_without_a_destination_falls_back_to_the_weekoverzicht(self):
        # LOGIN_REDIRECT_URL. The admin's login form fills in its own index as
        # `next` when opened through the "Beheer" link, so this covers the
        # remaining case: a POST that carries no destination at all.
        antwoord = self.client.post(
            "/admin/login/", {"username": "wim", "password": self.WACHTWOORD}
        )
        self.assertRedirects(
            antwoord, "/weekoverzicht/", fetch_redirect_response=False
        )
