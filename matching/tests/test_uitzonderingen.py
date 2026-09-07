"""Tests for the phase 5 uitzonderingenscherm.

Three things are being protected. First, that the matching stores the postcode
and street of every stop, not only of the unexplained ones — the screen reads
them, but a half-populated column would be a trap for phase 6. Second, that the
list really groups per address (postcode first, street as fallback) and puts the
most frequent address on top. Third, that confirming a koppeling creates exactly
the BekendeLocatie the user asked for, recomputes, and shortens the list.
"""

from __future__ import annotations

import datetime as dt

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from matching.models import (
    BekendeLocatie,
    LocatieType,
    MatchmotorStatus,
    Soort,
    Tijdblok,
)
from matching.tests import factories
from matching.timeline.runner import run_matching

DAG = dt.date(2026, 8, 3)
DAG2 = dt.date(2026, 8, 4)

THUIS = ("J. Bosschaartstraat 22", "4112 LN Beusichem")
KLANT = ("Lingedijk 65", "4196 HB Tricht")
DEPOT = ("Randweg 6a", "4104 AC Culemborg")
VREEMD = ("Industrieweg 2", "4104 AR Culemborg")


def _rit(bestuurder, datum, vertrek, aankomst, van, naar):
    return factories.rit(
        bestuurder,
        datum,
        vertrek,
        aankomst,
        vertrekadres=van[0],
        vertrekplaats=van[1],
        aankomstadres=naar[0],
        aankomstplaats=naar[1],
    )


def _dag_met_onverklaarde_stop(bestuurder: str, datum: dt.date, stop=VREEMD) -> None:
    """Home -> unknown address (two hours) -> home."""
    _rit(bestuurder, datum, "07:30", "08:00", THUIS, stop)
    _rit(bestuurder, datum, "10:00", "10:30", stop, THUIS)


class TijdblokAdresveldenTests(TestCase):
    """§1/§2: postcode and straat are stored for every kind of block, not only O."""

    def setUp(self):
        self.monteur = factories.monteur("Jesse", "005", "M5")
        factories.bekende_locatie(
            LocatieType.POSTCODE, "4104 AC", Soort.LOCATIE, "Magazijn", is_depot=True
        )
        # A full day: depot (L), a werkbon stop (W) and an unexplained stop (O).
        _rit("M5", DAG, "07:00", "07:15", THUIS, DEPOT)
        _rit("M5", DAG, "07:45", "08:15", DEPOT, KLANT)
        _rit("M5", DAG, "10:00", "10:20", KLANT, VREEMD)
        _rit("M5", DAG, "12:00", "12:30", VREEMD, THUIS)
        factories.urenregel(
            "005", DAG, "WB260908", adres=KLANT[0], postcode="4196 HB", plaats="TRICHT"
        )
        run_matching()

    def _blok(self, soort: str) -> Tijdblok:
        return Tijdblok.objects.get(monteur=self.monteur, datum=DAG, soort=soort)

    def test_depot_block_stores_postcode_and_straat(self):
        blok = self._blok(Soort.LOCATIE)
        self.assertEqual(blok.postcode, "4104AC")
        self.assertEqual(blok.straat, "randweg")

    def test_werkbon_block_stores_postcode_and_straat(self):
        blok = self._blok(Soort.WERKBON)
        self.assertEqual(blok.postcode, "4196HB")
        self.assertEqual(blok.straat, "lingedijk")

    def test_onverklaard_block_stores_postcode_and_straat(self):
        blok = self._blok(Soort.ONVERKLAARD)
        self.assertEqual(blok.postcode, "4104AR")
        self.assertEqual(blok.straat, "industrieweg")

    def test_reistijd_block_has_no_single_address(self):
        # An R block runs between two addresses, so it has no key of its own —
        # the fields stay blank on purpose.
        reistijd = Tijdblok.objects.filter(soort=Soort.REISTIJD)
        self.assertTrue(reistijd.exists())
        for blok in reistijd:
            self.assertEqual(blok.postcode, "")
            self.assertEqual(blok.straat, "")


class UitzonderingenLijstTests(TestCase):
    """§3a: one row per address, with counts, monteurs and dates."""

    def setUp(self):
        self.gebruiker = User.objects.create_user(
            "beheerder", password="geheim", is_staff=True
        )
        self.client.force_login(self.gebruiker)

    def test_stops_sharing_a_postcode_become_one_row(self):
        monteur = factories.monteur("Jesse", "005", "M5")
        _dag_met_onverklaarde_stop("M5", DAG)
        _dag_met_onverklaarde_stop("M5", DAG2)
        run_matching()

        response = self.client.get(reverse("uitzonderingen"))
        groepen = response.context["groepen"]
        self.assertEqual(len(groepen), 1)
        groep = groepen[0]
        self.assertEqual(groep.precisie, LocatieType.POSTCODE)
        self.assertEqual(groep.sleutel, "4104AR")
        self.assertEqual(groep.aantal, 2)
        self.assertEqual(groep.monteurs, [monteur.naam])
        self.assertEqual(groep.datums, [DAG, DAG2])
        self.assertContains(response, "4104AR")
        self.assertContains(response, "industrieweg")

    def test_a_stop_without_a_postcode_falls_back_to_the_street(self):
        factories.monteur("Jesse", "005", "M5")
        # RouteVision sometimes leaves the place empty, so there is no postcode
        # to group on — only the street remains.
        _dag_met_onverklaarde_stop("M5", DAG, stop=("Industrieweg 2", ""))
        run_matching()

        groepen = self.client.get(reverse("uitzonderingen")).context["groepen"]
        self.assertEqual(len(groepen), 1)
        self.assertEqual(groepen[0].precisie, LocatieType.STRAAT)
        self.assertEqual(groepen[0].sleutel, "industrieweg")
        self.assertEqual(groepen[0].postcode, "")

    def test_the_list_is_sorted_by_count_descending(self):
        factories.monteur("Jesse", "005", "M5")
        ander = ("Zaanweg 2", "4105 GN Culemborg")
        _dag_met_onverklaarde_stop("M5", DAG)
        _dag_met_onverklaarde_stop("M5", DAG2)
        _dag_met_onverklaarde_stop("M5", dt.date(2026, 8, 5), stop=ander)
        run_matching()

        groepen = self.client.get(reverse("uitzonderingen")).context["groepen"]
        self.assertEqual([groep.aantal for groep in groepen], [2, 1])
        self.assertEqual(groepen[0].sleutel, "4104AR")

    def test_an_empty_list_says_so(self):
        response = self.client.get(reverse("uitzonderingen"))
        self.assertEqual(response.context["groepen"], [])
        self.assertContains(response, "Geen onverklaarde stops")

    def test_anonymous_visitors_are_sent_to_the_admin_login(self):
        self.client.logout()
        response = self.client.get(reverse("uitzonderingen"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])


class KoppelenTests(TestCase):
    """§3b: the confirm form creates the location and triggers a re-run."""

    def setUp(self):
        self.monteur = factories.monteur("Jesse", "005", "M5")
        _dag_met_onverklaarde_stop("M5", DAG)
        _dag_met_onverklaarde_stop("M5", DAG2)
        run_matching()

        self.gebruiker = User.objects.create_user(
            "beheerder", password="geheim", is_staff=True
        )
        self.gebruiker.user_permissions.add(
            Permission.objects.get(codename="add_bekendelocatie")
        )
        self.client.force_login(self.gebruiker)
        self.url = reverse(
            "uitzonderingen_koppelen", args=[LocatieType.POSTCODE, "4104AR"]
        )

    def test_get_shows_a_prefilled_form_without_creating_anything(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.initial["type"], LocatieType.POSTCODE)
        self.assertEqual(form.initial["waarde"], "4104AR")
        self.assertEqual(response.context["groep"].aantal, 2)
        self.assertEqual(BekendeLocatie.objects.count(), 0)

    def test_the_form_does_not_offer_is_depot(self):
        # A depot outranks every other matching rule, so it must not be
        # creatable in passing from this screen.
        form = self.client.get(self.url).context["form"]
        self.assertNotIn("is_depot", form.fields)

    def test_the_form_offers_every_hand_assigned_soort(self):
        # P and T were both added on 07-09-2026 so an obviously private or
        # at-home stop can be cleared from this list instead of staying an O
        # forever; both are assigned through this same form, with no screen of
        # their own. W/?/O/R never appear — those follow from the matching.
        form = self.client.get(self.url).context["form"]
        keuzes = [waarde for waarde, _ in form.fields["soort"].choices if waarde]

        self.assertEqual(
            keuzes,
            [Soort.KLANT, Soort.LOCATIE, Soort.CREDITEUR, Soort.PRIVE, Soort.THUIS],
        )

    def test_linking_an_address_as_thuis_clears_it_from_the_list(self):
        # Roger's case: the van is parked around the corner from the actual home
        # address, so it never matches Monteur.thuisadres — but it can be linked
        # here, and then it counts for every monteur who stops there.
        response = self.client.post(
            self.url,
            {
                "type": LocatieType.POSTCODE,
                "waarde": "4104AR",
                "soort": Soort.THUIS,
                "label": "Parkeerplek om de hoek",
            },
        )
        self.assertRedirects(response, reverse("uitzonderingen"))

        self.assertEqual(BekendeLocatie.objects.get().soort, Soort.THUIS)
        self.assertFalse(
            Tijdblok.objects.filter(soort=Soort.ONVERKLAARD, postcode="4104AR").exists()
        )
        self.assertEqual(
            Tijdblok.objects.filter(soort=Soort.THUIS, postcode="4104AR").count(), 2
        )

    def test_linking_an_address_as_prive_clears_it_from_the_list(self):
        response = self.client.post(
            self.url,
            {
                "type": LocatieType.POSTCODE,
                "waarde": "4104AR",
                "soort": Soort.PRIVE,
                "label": "Sportschool",
            },
        )
        self.assertRedirects(response, reverse("uitzonderingen"))

        self.assertEqual(BekendeLocatie.objects.get().soort, Soort.PRIVE)
        self.assertFalse(
            Tijdblok.objects.filter(soort=Soort.ONVERKLAARD, postcode="4104AR").exists()
        )
        self.assertEqual(
            Tijdblok.objects.filter(soort=Soort.PRIVE, postcode="4104AR").count(), 2
        )

    def test_a_successful_post_creates_the_location_and_recomputes(self):
        response = self.client.post(
            self.url,
            {
                "type": LocatieType.POSTCODE,
                "waarde": "4104AR",
                "soort": Soort.CREDITEUR,
                "label": "Groothandel Van Egmond",
            },
        )
        self.assertRedirects(response, reverse("uitzonderingen"))

        locatie = BekendeLocatie.objects.get()
        self.assertEqual(locatie.type, LocatieType.POSTCODE)
        self.assertEqual(locatie.waarde, "4104AR")
        self.assertEqual(locatie.soort, Soort.CREDITEUR)
        self.assertEqual(locatie.label, "Groothandel Van Egmond")
        self.assertFalse(locatie.is_depot)

        # The re-run happened: the status row was updated and the stops that
        # made up this group are now classified as C instead of O.
        self.assertTrue(MatchmotorStatus.load().succes)
        self.assertFalse(
            Tijdblok.objects.filter(soort=Soort.ONVERKLAARD, postcode="4104AR").exists()
        )
        self.assertEqual(
            Tijdblok.objects.filter(soort=Soort.CREDITEUR, postcode="4104AR").count(), 2
        )

    def test_the_list_is_shorter_afterwards(self):
        self.client.post(
            self.url,
            {
                "type": LocatieType.POSTCODE,
                "waarde": "4104AR",
                "soort": Soort.CREDITEUR,
                "label": "Groothandel Van Egmond",
            },
        )
        response = self.client.get(reverse("uitzonderingen"))
        self.assertEqual(response.context["groepen"], [])
        self.assertContains(response, "Groothandel Van Egmond")  # success message

    def test_the_street_value_can_be_chosen_instead_of_the_postcode(self):
        # The group was formed on postcode, but both keys are stored on every
        # Tijdblok, so switching precision is a matter of editing the value.
        self.client.post(
            self.url,
            {
                "type": LocatieType.STRAAT,
                "waarde": "Industrieweg",
                "soort": Soort.KLANT,
                "label": "Klant op de Industrieweg",
            },
        )
        locatie = BekendeLocatie.objects.get()
        self.assertEqual(locatie.type, LocatieType.STRAAT)
        self.assertEqual(locatie.waarde, "industrieweg")  # normalised by the model

    def test_an_invalid_form_creates_nothing(self):
        response = self.client.post(
            self.url,
            {"type": LocatieType.POSTCODE, "waarde": "4104AR", "soort": Soort.KLANT},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(BekendeLocatie.objects.count(), 0)
        self.assertIn("label", response.context["form"].errors)

    def test_a_user_without_the_permission_cannot_submit(self):
        self.gebruiker.user_permissions.clear()
        # Permissions are cached on the request user; a fresh login is the
        # cheapest way to drop that cache.
        self.client.force_login(User.objects.get(pk=self.gebruiker.pk))

        response = self.client.post(
            self.url,
            {
                "type": LocatieType.POSTCODE,
                "waarde": "4104AR",
                "soort": Soort.CREDITEUR,
                "label": "Groothandel Van Egmond",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(BekendeLocatie.objects.count(), 0)

    def test_an_address_that_is_no_longer_unexplained_gives_a_404(self):
        onbekend = reverse(
            "uitzonderingen_koppelen", args=[LocatieType.POSTCODE, "9999ZZ"]
        )
        self.assertEqual(self.client.get(onbekend).status_code, 404)

    def test_an_unknown_precision_gives_a_404(self):
        response = self.client.get("/uitzonderingen/koppelen/huisnummer/4104AR/")
        self.assertEqual(response.status_code, 404)


class AdminLinkTests(TestCase):
    """§5: the one way into the screen from the admin."""

    def setUp(self):
        self.gebruiker = User.objects.create_superuser("baas", password="geheim")
        self.client.force_login(self.gebruiker)

    def test_the_matchmotor_changelist_links_to_the_uitzonderingenscherm(self):
        response = self.client.get(
            reverse("admin:matching_matchmotorstatus_changelist")
        )
        self.assertContains(response, reverse("uitzonderingen"))
        self.assertContains(response, "Uitzonderingen bekijken")
