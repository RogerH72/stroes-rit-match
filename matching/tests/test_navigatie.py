"""Tests for the way out: who am I, and how do I log out or get back.

Two headers are covered, because RMW has two of them. The application's own
screens share matching/templates/matching/basis.html, and its navigation bar now
names the signed-in user and holds the logout button. The Django admin has its
own header, overridden in templates/admin/base_site.html — relabelled, not
rebuilt: Django already rendered both links, but under "Afmelden" and "Website
bekijken", which is a third and a fourth word for what the rest of the app calls
"Uitloggen" and "Weekoverzicht".

The override lives in the project-level templates/ directory rather than in
matching/templates/, because django.contrib.admin precedes matching in
INSTALLED_APPS and would otherwise win. That is easy to undo by accident, so
OverridePaktTests asserts the override is really the one being rendered.

Both headers log out through the same route and land on the same screen; that
symmetry is what SymmetrischUitloggenTests is for. Worth knowing while reading
it: the two would land on the same screen even without the shared route, because
AdminSite.logout is a LogoutView with no next_page and so inherits
settings.LOGOUT_REDIRECT_URL. These tests pin the route, not just the
destination, so the agreement does not depend on that fallback.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

WACHTWOORD = "geheim-genoeg-voor-een-test"


class NavigatiebalkTests(TestCase):
    """§basis.html — the header of the screens outside the admin."""

    def setUp(self):
        self.gebruiker = User.objects.create_user("wim", password=WACHTWOORD)
        self.client.force_login(self.gebruiker)

    def _header(self, naam: str) -> str:
        antwoord = self.client.get(reverse(naam))
        self.assertEqual(antwoord.status_code, 200)
        return antwoord.content.decode()

    def test_weekoverzicht_names_the_user_and_offers_a_way_out(self):
        inhoud = self._header("weekoverzicht")
        self.assertIn("wim", inhoud)
        self.assertIn("Uitloggen", inhoud)

    def test_uitzonderingen_shows_the_same_header(self):
        # Both screens extend basis.html, so "how do I log out" must never
        # depend on which of them you happen to be looking at.
        inhoud = self._header("uitzonderingen")
        self.assertIn("wim", inhoud)
        self.assertIn("Uitloggen", inhoud)

    def test_the_logout_button_posts_to_the_logout_route(self):
        self.assertIn(
            f'action="{reverse("uitloggen")}"', self._header("weekoverzicht")
        )

    def test_a_full_name_is_preferred_over_the_username(self):
        self.gebruiker.first_name = "Wim"
        self.gebruiker.save()
        self.assertIn("Wim", self._header("weekoverzicht"))

    def test_the_admin_link_is_still_there(self):
        # The session block was added next to the screen links, not in place of
        # them: "Beheer" still has to reach the admin.
        self.assertIn('href="/admin/"', self._header("weekoverzicht"))


class UitloggenTests(TestCase):
    """§/uitloggen/ — the app's own logout, and where it drops you."""

    def setUp(self):
        User.objects.create_user("wim", password=WACHTWOORD)
        self.client.force_login(User.objects.get(username="wim"))

    def test_logging_out_ends_the_session(self):
        self.client.post(reverse("uitloggen"))
        antwoord = self.client.get(reverse("weekoverzicht"))
        self.assertEqual(antwoord.status_code, 302)
        self.assertIn("/admin/login/", antwoord["Location"])

    def test_logging_out_returns_to_the_login_screen(self):
        # LOGOUT_REDIRECT_URL. The ?next= is filled in already, so signing back
        # in lands on the weekoverzicht instead of in the admin index.
        antwoord = self.client.post(reverse("uitloggen"))
        self.assertRedirects(
            antwoord,
            "/admin/login/?next=/weekoverzicht/",
            fetch_redirect_response=False,
        )

    def test_a_get_cannot_log_you_out(self):
        # The reason the header holds a form and not a link: a GET logout is
        # followed by link-prefetchers and mail scanners.
        self.assertEqual(self.client.get(reverse("uitloggen")).status_code, 405)
        self.assertEqual(self.client.get(reverse("weekoverzicht")).status_code, 200)


class AdminHeaderTests(TestCase):
    """§templates/admin/base_site.html — the header of every admin screen."""

    def setUp(self):
        self.gebruiker = User.objects.create_superuser(
            "beheerder", "beheer@example.com", WACHTWOORD
        )
        self.client.force_login(self.gebruiker)

    def _header(self, url: str) -> str:
        antwoord = self.client.get(url)
        self.assertEqual(antwoord.status_code, 200)
        return antwoord.content.decode()

    def test_site_url_points_straight_at_the_weekoverzicht(self):
        # Not the default "/": that reaches the weekoverzicht too, but only
        # through a redirect, so the browser's status bar would show "/".
        self.assertEqual(str(admin.site.site_url), reverse("weekoverzicht"))

    def test_index_offers_logging_out_and_the_way_back(self):
        inhoud = self._header(reverse("admin:index"))
        self.assertIn("Uitloggen", inhoud)
        self.assertIn("Naar het weekoverzicht", inhoud)
        self.assertIn(f'href="{reverse("weekoverzicht")}"', inhoud)

    def test_every_admin_screen_offers_them_not_just_the_index(self):
        # "Vanuit elk admin-scherm met één klik": a list, a form, and the one
        # admin template this project overrides itself.
        schermen = [
            reverse("admin:matching_monteur_changelist"),
            reverse("admin:matching_monteur_add"),
            reverse("admin:matching_matchmotorstatus_changelist"),
        ]
        for url in schermen:
            with self.subTest(scherm=url):
                inhoud = self._header(url)
                self.assertIn("Uitloggen", inhoud)
                self.assertIn("Naar het weekoverzicht", inhoud)

    def test_logging_out_is_a_post_form(self):
        # Django 5 refuses a GET logout; the header must carry the form that
        # goes with it, not a bare link.
        inhoud = self._header(reverse("admin:index"))
        self.assertIn("csrfmiddlewaretoken", inhoud)
        self.assertIn("<button type=\"submit\" class=\"rmw-actie\">Uitloggen", inhoud)

    def test_the_admin_logs_out_through_the_apps_own_route(self):
        # One logout route for the whole app, rather than two that agree by
        # accident: admin:logout lands on the same screen only because it
        # inherits LOGOUT_REDIRECT_URL from a LogoutView fallback.
        inhoud = self._header(reverse("admin:index"))
        self.assertIn(f'action="{reverse("uitloggen")}"', inhoud)
        self.assertNotIn(f'action="{reverse("admin:logout")}"', inhoud)


class OverridePaktTests(TestCase):
    """§the override wins — django.contrib.admin precedes matching."""

    def setUp(self):
        User.objects.create_superuser("beheerder", "b@example.com", WACHTWOORD)
        self.client.force_login(User.objects.get(username="beheerder"))

    def test_djangos_own_wording_is_gone(self):
        # If templates/ ever drops out of TEMPLATES["DIRS"], or the file is
        # moved into matching/templates/, Django's base_site.html takes over
        # again and these two Dutch translations come back. That is exactly the
        # state Roger reported, so it gets a test rather than a comment.
        inhoud = self.client.get(reverse("admin:index")).content.decode()
        self.assertNotIn("Afmelden", inhoud)
        self.assertNotIn("Website bekijken", inhoud)

    def test_the_branding_block_survived_the_override(self):
        # base_site.html has to re-supply the blocks it inherited; forgetting
        # one silently drops the site header.
        inhoud = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("RMW — Ritten Match Werkbon", inhoud)


class SymmetrischUitloggenTests(TestCase):
    """§one word, one behaviour — both headers end on the same screen.

    RMW has two headers and therefore two "Uitloggen" buttons: one in the
    application's own navigation bar, one in the admin. They used to part ways
    at the last step — the admin's went to Django's logged-out page — which made
    the same label mean two things depending on which screen you happened to be
    on. These tests pin them together.
    """

    def setUp(self):
        User.objects.create_superuser("beheerder", "b@example.com", WACHTWOORD)

    def _log_in(self):
        self.client.force_login(User.objects.get(username="beheerder"))

    def _uitloggen_vanaf(self, pagina_url: str):
        """Press the "Uitloggen" button that `pagina_url` renders, for real.

        Scraping the action= rather than posting to a hard-coded route is the
        whole point: if the admin's form is ever pointed back at admin:logout,
        this follows it there and sees a rendered page instead of a redirect to
        the login screen.
        """
        actie = self._knop_in(pagina_url)
        return self.client.post(actie)

    #: The form that holds an "Uitloggen" button, whichever header rendered it.
    UITLOGFORM = re.compile(
        r'<form[^>]*action="([^"]+)"[^>]*>(?:(?!</form>).)*?Uitloggen', re.S
    )

    def _knop_in(self, pagina_url: str) -> str:
        """The action= of the "Uitloggen" button on that page."""
        self._log_in()
        inhoud = self.client.get(pagina_url).content.decode()
        treffer = self.UITLOGFORM.search(inhoud)
        self.assertIsNotNone(treffer, f"geen uitlogknop op {pagina_url}")
        return treffer.group(1)

    def test_both_headers_point_at_the_same_route(self):
        self.assertEqual(
            self._knop_in(reverse("admin:index")),
            self._knop_in(reverse("weekoverzicht")),
        )

    def test_both_routes_end_on_the_same_login_screen(self):
        vanuit_app = self._uitloggen_vanaf(reverse("weekoverzicht"))
        vanuit_admin = self._uitloggen_vanaf(reverse("admin:index"))
        for antwoord in (vanuit_app, vanuit_admin):
            self.assertEqual(antwoord.status_code, 302)
        self.assertEqual(vanuit_app["Location"], vanuit_admin["Location"])
        self.assertEqual(vanuit_app["Location"], settings.LOGOUT_REDIRECT_URL)

    def test_the_shared_destination_is_the_login_screen(self):
        antwoord = self._uitloggen_vanaf(reverse("admin:index"))
        self.assertRedirects(
            antwoord,
            "/admin/login/?next=/weekoverzicht/",
            fetch_redirect_response=False,
        )

    def test_logging_out_from_the_admin_really_ends_the_session(self):
        self._uitloggen_vanaf(reverse("admin:index"))
        antwoord = self.client.get(reverse("admin:index"))
        self.assertEqual(antwoord.status_code, 302)
        self.assertIn("/admin/login/", antwoord["Location"])

    def test_nothing_links_to_the_admins_own_logout_any_more(self):
        # admin:logout still exists — Django registers it — but no admin screen
        # points at it, so there is one route to maintain instead of two.
        self._log_in()
        schermen = [
            reverse("admin:index"),
            reverse("admin:matching_monteur_changelist"),
            reverse("admin:matching_matchmotorstatus_changelist"),
        ]
        for url in schermen:
            with self.subTest(scherm=url):
                inhoud = self.client.get(url).content.decode()
                self.assertNotIn(reverse("admin:logout"), inhoud)

