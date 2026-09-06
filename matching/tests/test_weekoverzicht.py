"""Tests for the phase 6 weekoverzicht.

Four things are being protected. First, that a week is assembled from the stored
Tijdblok rows the way the SBTT format expects: one entry per day, totals per
SOORT, a week total. Second, the two instructed differences from the prototype —
no WB column or ⚑ signal anywhere, and a gefactureerd/op-locatie comparison that
really compares Uren.xlsx against the W-blocks. Third, that an incomplete week
says so instead of quietly showing a short week total. Fourth, that the screen
and the Excel export stay two renderings of the same numbers, and that an O
block links to the exact group the uitzonderingenscherm shows.
"""

from __future__ import annotations

import datetime as dt
import io
from decimal import Decimal

import openpyxl
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from matching import weekoverzicht as week
from matching.models import LocatieType, Soort
from matching.tests import factories
from matching.timeline.runner import run_matching
from matching.weekoverzicht_excel import bestandsnaam, bouw_werkboek

# Week 32 of 2026 runs from Monday 3 to Sunday 9 August — the week the PoC and
# the validation runs both used, so these dates line up with docs/demo.md.
MAANDAG = dt.date(2026, 8, 3)
DINSDAG = dt.date(2026, 8, 4)
WEEK = (2026, 32)

THUIS = ("J. Bosschaartstraat 22", "4112 LN Beusichem")
KLANT = ("Lingedijk 65", "4196 HB Tricht")
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


def _werkdag(bestuurder: str, datum: dt.date) -> None:
    """Home -> customer (2 hours) -> unknown address (1 hour) -> home."""
    _rit(bestuurder, datum, "07:00", "07:30", THUIS, KLANT)
    _rit(bestuurder, datum, "09:30", "09:45", KLANT, VREEMD)
    _rit(bestuurder, datum, "10:45", "11:15", VREEMD, THUIS)


class WeekParsingTests(TestCase):
    """The week value the URL and <input type="week"> both carry."""

    def test_parses_the_iso_week_format(self):
        self.assertEqual(week.parse_week("2026-W32"), (2026, 32))

    def test_rejects_a_week_the_year_does_not_have(self):
        # 2026 has 53 ISO weeks, 2027 does not — the shape alone is not enough.
        self.assertEqual(week.parse_week("2026-W53"), (2026, 53))
        self.assertIsNone(week.parse_week("2027-W53"))

    def test_rejects_nonsense(self):
        for waarde in ("", None, "2026", "week 32", "2026-W", "2026-W99"):
            self.assertIsNone(week.parse_week(waarde), waarde)

    def test_format_round_trips(self):
        self.assertEqual(week.format_week(2026, 32), "2026-W32")
        self.assertEqual(week.parse_week(week.format_week(2026, 7)), (2026, 7))

    def test_week_van_uses_the_iso_year(self):
        # 1 January 2027 is a Friday in week 53 of 2026; the calendar year would
        # point at a week 53 that 2027 does not have.
        self.assertEqual(week.week_van(dt.date(2027, 1, 1)), (2026, 53))


class WeekOpbouwTests(TestCase):
    """§the week itself: days, totals, and the hours comparison."""

    def setUp(self):
        self.monteur = factories.monteur("Jesse", "005", "M5")
        factories.bekende_locatie(
            LocatieType.POSTCODE, "4104 AC", Soort.LOCATIE, "Magazijn", is_depot=True
        )
        _werkdag("M5", MAANDAG)
        _werkdag("M5", DINSDAG)
        factories.urenregel(
            "005",
            MAANDAG,
            "WB260908",
            adres=KLANT[0],
            postcode="4196 HB",
            plaats="TRICHT",
            aantal="2.50",
        )
        # Two lines on one day: the comparison is per day, not per werkbon.
        factories.urenregel(
            "005",
            DINSDAG,
            "WB260908",
            adres=KLANT[0],
            postcode="4196 HB",
            plaats="TRICHT",
            aantal="1.00",
        )
        factories.urenregel(
            "005",
            DINSDAG,
            "WB261000",
            adres=KLANT[0],
            postcode="4196 HB",
            plaats="TRICHT",
            aantal="0.75",
        )
        run_matching()
        self.overzicht = week.bouw_weekoverzicht(self.monteur, *WEEK)

    def test_only_days_with_a_timeline_become_a_day(self):
        self.assertEqual(
            [dag.datum for dag in self.overzicht.dagen], [MAANDAG, DINSDAG]
        )

    def test_day_holds_every_block_in_order(self):
        maandag = self.overzicht.dagen[0]
        self.assertEqual(
            [regel.blok.soort for regel in maandag.regels],
            [
                Soort.REISTIJD,
                Soort.WERKBON,
                Soort.REISTIJD,
                Soort.ONVERKLAARD,
                Soort.REISTIJD,
            ],
        )

    def test_soort_totals_cover_every_code_including_the_empty_ones(self):
        totalen = {t.code: t.minuten for t in self.overzicht.dagen[0].totalen}
        self.assertEqual(set(totalen), {s.value for s in Soort})
        self.assertEqual(totalen[Soort.WERKBON], 120)  # 07:30 -> 09:30
        self.assertEqual(totalen[Soort.ONVERKLAARD], 60)  # 09:45 -> 10:45
        self.assertEqual(totalen[Soort.REISTIJD], 30 + 15 + 30)
        self.assertEqual(totalen[Soort.KLANT], 0)

    def test_empty_soort_shows_a_dash_not_a_zero_time(self):
        totalen = {t.code: t.tijd for t in self.overzicht.dagen[0].totalen}
        self.assertEqual(totalen[Soort.WERKBON], "2:00")
        self.assertEqual(totalen[Soort.KLANT], "–")

    def test_day_total_is_every_block_together(self):
        self.assertEqual(self.overzicht.dagen[0].totaal, "4:15")

    def test_week_total_adds_the_days_up(self):
        self.assertEqual(self.overzicht.totaal_minuten, 2 * 255)
        werkbon = next(
            t for t in self.overzicht.totalen if t.code == Soort.WERKBON
        )
        self.assertEqual(werkbon.minuten, 240)

    def test_booked_hours_come_from_uren_per_day(self):
        self.assertEqual(self.overzicht.dagen[0].gefactureerde_uren, Decimal("2.50"))
        # Both lines of Tuesday, added up.
        self.assertEqual(self.overzicht.dagen[1].gefactureerde_uren, Decimal("1.75"))

    def test_hours_on_location_are_the_werkbon_blocks(self):
        # Two hours at the customer; the unexplained hour does not count.
        self.assertEqual(self.overzicht.dagen[0].uren_op_locatie, Decimal("2.00"))
        self.assertEqual(self.overzicht.dagen[0].verschil, Decimal("0.50"))

    def test_week_comparison_totals_both_sides(self):
        self.assertEqual(self.overzicht.gefactureerde_uren, Decimal("4.25"))
        self.assertEqual(self.overzicht.uren_op_locatie, Decimal("4.00"))
        self.assertEqual(self.overzicht.verschil, Decimal("0.25"))

    def test_unexplained_block_carries_the_koppel_key_of_its_group(self):
        onverklaard = next(
            regel
            for regel in self.overzicht.dagen[0].regels
            if regel.blok.soort == Soort.ONVERKLAARD
        )
        self.assertTrue(onverklaard.koppelbaar)
        self.assertEqual(onverklaard.koppel_precisie, LocatieType.POSTCODE)
        self.assertEqual(onverklaard.koppel_sleutel, "4104AR")

    def test_other_blocks_are_not_koppelbaar(self):
        # Only an O is unresolved; offering "koppelen" on a matched werkbon
        # would invite users to link an address that is already explained.
        werkbon = next(
            regel
            for regel in self.overzicht.dagen[0].regels
            if regel.blok.soort == Soort.WERKBON
        )
        self.assertFalse(werkbon.koppelbaar)

    def test_neighbouring_weeks_are_offered(self):
        self.assertEqual(self.overzicht.vorige_week, "2026-W31")
        self.assertEqual(self.overzicht.volgende_week, "2026-W33")

    def test_another_week_is_empty_rather_than_wrong(self):
        leeg = week.bouw_weekoverzicht(self.monteur, 2026, 33)
        self.assertTrue(leeg.leeg)
        self.assertEqual(leeg.totaal_minuten, 0)


class OnvolledigeWeekTests(TestCase):
    """§incomplete week: which days are missing, and never a silent total."""

    def setUp(self):
        self.monteur = factories.monteur("Jesse", "005", "M5")
        _werkdag("M5", MAANDAG)
        # Booked hours on a day that has no ride data at all — the case that
        # points at a missing RouteVision export rather than at leave.
        factories.urenregel(
            "005", DINSDAG, "WB260908", adres=KLANT[0], postcode="4196 HB", aantal="8.00"
        )
        run_matching()

    def test_missing_working_days_are_reported(self):
        overzicht = week.bouw_weekoverzicht(self.monteur, *WEEK)
        self.assertEqual(
            [dag.datum for dag in overzicht.ontbrekende_dagen],
            [
                dt.date(2026, 8, 4),
                dt.date(2026, 8, 5),
                dt.date(2026, 8, 6),
                dt.date(2026, 8, 7),
            ],
        )

    def test_weekend_is_not_missing(self):
        overzicht = week.bouw_weekoverzicht(self.monteur, *WEEK)
        datums = [dag.datum for dag in overzicht.ontbrekende_dagen]
        self.assertNotIn(dt.date(2026, 8, 8), datums)
        self.assertNotIn(dt.date(2026, 8, 9), datums)

    def test_missing_day_carries_the_hours_booked_on_it(self):
        overzicht = week.bouw_weekoverzicht(self.monteur, *WEEK)
        dinsdag = overzicht.ontbrekende_dagen[0]
        self.assertEqual(dinsdag.gefactureerde_uren, Decimal("8.00"))

    def test_hours_of_a_missing_day_stay_out_of_the_week_total(self):
        # Counting Tuesday's 8 hours against a Tuesday that has no W-blocks
        # would read as a discrepancy in the work, while it is a gap in the data.
        overzicht = week.bouw_weekoverzicht(self.monteur, *WEEK)
        self.assertEqual(overzicht.gefactureerde_uren, Decimal("0.00"))

    def test_future_days_are_not_missing(self):
        # The current week, halfway through: the days still to come are not a
        # gap. Nothing is processed for this monteur in it, so every day that
        # has already passed is missing and none of the later ones are.
        vandaag = dt.date.today()
        overzicht = week.bouw_weekoverzicht(self.monteur, *week.week_van(vandaag))
        for dag in overzicht.ontbrekende_dagen:
            self.assertLessEqual(dag.datum, vandaag)


class WeekoverzichtSchermTests(TestCase):
    """§the page: navigation, the two dropped columns, and the O link."""

    def setUp(self):
        self.monteur = factories.monteur("Jesse", "005", "M5")
        self.collega = factories.monteur("Dennis", "001", "M1")
        _werkdag("M5", MAANDAG)
        _werkdag("M1", MAANDAG)
        factories.urenregel(
            "005", MAANDAG, "WB260908", adres=KLANT[0], postcode="4196 HB", aantal="2.50"
        )
        run_matching()

        self.gebruiker = User.objects.create_user("wim", password="geheim")
        self.gebruiker.user_permissions.add(
            Permission.objects.get(codename="add_bekendelocatie")
        )
        self.client.force_login(self.gebruiker)
        self.url = reverse("weekoverzicht")

    def _pagina(self, **params) -> str:
        antwoord = self.client.get(self.url, params)
        self.assertEqual(antwoord.status_code, 200)
        return antwoord.content.decode()

    def test_login_is_required(self):
        self.client.logout()
        antwoord = self.client.get(self.url)
        self.assertEqual(antwoord.status_code, 302)
        self.assertIn("/admin/login/", antwoord["Location"])

    def test_defaults_to_the_last_processed_week(self):
        # No parameters at all: the screen opens on a week that has content
        # rather than on an empty current week. This is the default the root
        # URL and the navigation link both land on, so it must never be blank
        # (see week.laatste_week_met_data for why it is not "this week").
        inhoud = self._pagina()
        self.assertIn("2026-W32", inhoud)
        self.assertIn("Jesse", inhoud)

    def test_defaults_to_the_first_monteur_alphabetically(self):
        # Dennis before Jesse, whatever order they were created in — "the first
        # one alphabetically" is the defined default of a bare /weekoverzicht/.
        self.assertIn("Weekoverzicht — Dennis", self._pagina())

    def test_the_default_page_is_not_empty(self):
        # The whole point of the two defaults above: someone arriving through /
        # or through the navigation bar sees a filled week, not a blank shell
        # with two dropdowns.
        inhoud = self._pagina()
        self.assertNotIn("is nog geen dag berekend", inhoud)
        self.assertIn("Maandag 3 augustus", inhoud)

    def test_selects_the_monteur_from_the_url(self):
        inhoud = self._pagina(monteur=self.collega.pk, week="2026-W32")
        self.assertIn("Weekoverzicht — Dennis", inhoud)

    def test_unknown_monteur_is_a_404_not_a_silent_fallback(self):
        antwoord = self.client.get(self.url, {"monteur": 9999})
        self.assertEqual(antwoord.status_code, 404)

    def test_impossible_week_is_a_404(self):
        antwoord = self.client.get(self.url, {"week": "2027-W53"})
        self.assertEqual(antwoord.status_code, 404)

    def test_no_wb_column_and_no_flag_signal(self):
        # The instructed omission: the WB-vs-SYS comparison is not built, so it
        # must not reappear here through the prototype's layout.
        inhoud = self._pagina(week="2026-W32")
        self.assertNotIn("⚑", inhoud)
        self.assertNotIn("<th>WB</th>", inhoud)
        self.assertNotIn("SYS aank", inhoud)

    def test_shows_the_hours_comparison(self):
        inhoud = self._pagina(week="2026-W32")
        self.assertIn("Gefactureerd", inhoud)
        self.assertIn("op locatie", inhoud)

    def test_unexplained_block_links_to_the_koppel_form(self):
        inhoud = self._pagina(week="2026-W32")
        verwacht = reverse(
            "uitzonderingen_koppelen", args=[LocatieType.POSTCODE, "4104AR"]
        )
        self.assertIn(verwacht, inhoud)

    def test_koppel_link_hidden_without_the_permission(self):
        kijker = User.objects.create_user("kijker", password="geheim")
        self.client.force_login(kijker)
        inhoud = self._pagina(week="2026-W32")
        self.assertNotIn("koppelen/", inhoud)

    def test_koppel_link_opens_the_group_the_list_shows(self):
        # The link is only useful if it lands on a real group; phase 5 answers
        # a 404 for a group that is not in the list.
        doel = reverse("uitzonderingen_koppelen", args=[LocatieType.POSTCODE, "4104AR"])
        self.assertEqual(self.client.get(doel).status_code, 200)

    def test_incomplete_week_warns_on_screen(self):
        inhoud = self._pagina(week="2026-W32")
        self.assertIn("Onvolledige week", inhoud)

    def test_empty_week_says_so_instead_of_showing_zero_totals(self):
        inhoud = self._pagina(week="2026-W20")
        self.assertIn("nog geen dag berekend", inhoud)


class WeekoverzichtExcelTests(TestCase):
    """§the export: same numbers, same colours, as a real workbook."""

    def setUp(self):
        self.monteur = factories.monteur("Jesse Verkerk", "005", "M5")
        _werkdag("M5", MAANDAG)
        factories.urenregel(
            "005", MAANDAG, "WB260908", adres=KLANT[0], postcode="4196 HB", aantal="2.50"
        )
        run_matching()
        self.overzicht = week.bouw_weekoverzicht(self.monteur, *WEEK)

    def _blad(self):
        werkboek = openpyxl.load_workbook(io.BytesIO(bouw_werkboek(self.overzicht)))
        return werkboek[werkboek.sheetnames[0]]

    def _cellen(self, blad) -> list[str]:
        return [
            str(cel.value)
            for rij in blad.iter_rows()
            for cel in rij
            if cel.value is not None
        ]

    def test_filename_names_monteur_and_week(self):
        self.assertEqual(
            bestandsnaam(self.overzicht),
            "RMW-weekoverzicht-2026-W32-Jesse-Verkerk.xlsx",
        )

    def test_sheet_holds_the_days_and_their_blocks(self):
        cellen = self._cellen(self._blad())
        self.assertIn("Maandag 03-08-2026 · totaal 4:15", cellen)
        self.assertIn("WB260908", cellen)
        self.assertIn("Onverklaarde stop", cellen)

    def test_soort_cells_carry_the_screen_colour(self):
        blad = self._blad()
        gekleurd = {
            cel.value: cel.fill.fgColor.rgb
            for rij in blad.iter_rows()
            for cel in rij
            if cel.value in {Soort.WERKBON.value, Soort.ONVERKLAARD.value}
            and cel.fill.fgColor.rgb not in (None, "00000000")
        }
        # openpyxl prefixes the alpha channel; the colour itself is the one the
        # page paints the pill with.
        self.assertTrue(gekleurd[Soort.WERKBON].endswith("1F8A4C"))
        self.assertTrue(gekleurd[Soort.ONVERKLAARD].endswith("D97706"))

    def test_hours_are_written_as_numbers_not_as_text(self):
        blad = self._blad()
        # A whole number of hours comes back as an int, so both types count:
        # what matters is that the cell holds a number a user can total further,
        # not the text "2,00 u".
        getallen = [
            cel.value
            for rij in blad.iter_rows()
            for cel in rij
            if isinstance(cel.value, (int, float)) and not isinstance(cel.value, bool)
        ]
        self.assertIn(2.5, getallen)  # gefactureerd
        self.assertIn(2, getallen)  # op locatie
        self.assertIn(0.5, getallen)  # verschil

    def test_no_wb_column_and_no_flag_signal(self):
        cellen = self._cellen(self._blad())
        self.assertNotIn("WB", cellen)
        self.assertNotIn("⚑", cellen)

    def test_incomplete_week_is_stated_in_the_sheet(self):
        cellen = " ".join(self._cellen(self._blad()))
        self.assertIn("onvolledige week", cellen.lower())

    def test_download_serves_a_workbook(self):
        gebruiker = User.objects.create_user("wim", password="geheim")
        self.client.force_login(gebruiker)
        antwoord = self.client.get(
            reverse("weekoverzicht_excel"),
            {"monteur": self.monteur.pk, "week": "2026-W32"},
        )
        self.assertEqual(antwoord.status_code, 200)
        self.assertIn("spreadsheetml", antwoord["Content-Type"])
        self.assertIn(
            "RMW-weekoverzicht-2026-W32-Jesse-Verkerk.xlsx",
            antwoord["Content-Disposition"],
        )
        # A real workbook, not an error page with the right header on it.
        openpyxl.load_workbook(io.BytesIO(antwoord.content))

    def test_download_requires_login(self):
        antwoord = self.client.get(reverse("weekoverzicht_excel"))
        self.assertEqual(antwoord.status_code, 302)


class LegeInrichtingTests(TestCase):
    """The state before anything is set up: no monteurs at all."""

    def setUp(self):
        gebruiker = User.objects.create_user("wim", password="geheim")
        self.client.force_login(gebruiker)

    def test_page_explains_what_is_missing(self):
        antwoord = self.client.get(reverse("weekoverzicht"))
        self.assertEqual(antwoord.status_code, 200)
        self.assertIn("nog geen monteurs", antwoord.content.decode())

    def test_export_has_nothing_to_export(self):
        antwoord = self.client.get(reverse("weekoverzicht_excel"))
        self.assertEqual(antwoord.status_code, 404)
