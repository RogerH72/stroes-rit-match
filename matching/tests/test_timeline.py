"""Tests for the matching engine: how a day is rebuilt and how stops are classified.

Every fixture here is built by hand, small enough to reason about, and states the
one rule it is about — see matching/tests/factories.py. The real sample exports
are covered separately by matching/tests/test_sample_data.py.
"""

from __future__ import annotations

import datetime as dt

from django.core.exceptions import ValidationError
from django.test import TestCase

from matching.models import (
    BekendeLocatie,
    FaseStatus,
    Instelling,
    LocatieType,
    MeegeredenKoppeling,
    MeegeredenModus,
    Monteur,
    Soort,
    ToleranceRegel,
)
from matching.tests import factories
from matching.timeline import normalize
from matching.timeline.engine import Thuisadres, build_day, drempel_minuten
from matching.timeline.meegereden import resolve_bronmonteur

DAG = dt.date(2026, 8, 3)

# Two addresses used throughout: the depot, and a customer with work booked on it.
DEPOT_ADRES = "Randweg 1b"
DEPOT_PLAATS = "4104 AC Culemborg"
KLANT_ADRES = "Lingedijk 65"
KLANT_PLAATS = "4196 HB Tricht"
THUIS_ADRES = "J. Bosschaartstraat 22"
THUIS_PLAATS = "4112 LN Beusichem"


class NormalizeTests(TestCase):
    """The address keys everything else compares on."""

    def test_street_drops_the_house_number_and_lowercases(self):
        self.assertEqual(normalize.street("Randweg 6A"), "randweg")
        self.assertEqual(normalize.street("J. Bosschaartstraat 22"), "j. bosschaartstraat")

    def test_postcode_loses_its_space_and_its_town(self):
        self.assertEqual(normalize.postcode("4104 AC Culemborg"), "4104AC")
        self.assertEqual(normalize.postcode("4104AC"), "4104AC")

    def test_a_value_without_a_postcode_yields_no_key(self):
        self.assertEqual(normalize.postcode("Culemborg"), "")
        self.assertEqual(normalize.postcode(None), "")


class BekendeLocatieTests(TestCase):
    """A koppeltabel row has to be stored the way the matching looks it up."""

    def test_a_typed_in_value_is_normalised_on_save(self):
        locatie = factories.bekende_locatie(
            LocatieType.STRAAT, "Randweg 6A", Soort.LOCATIE, "Magazijn"
        )
        locatie.refresh_from_db()
        self.assertEqual(locatie.waarde, "randweg")

    def test_a_postcode_is_stored_without_its_space(self):
        locatie = factories.bekende_locatie(
            LocatieType.POSTCODE, "4104 ac", Soort.LOCATIE, "Magazijn"
        )
        locatie.refresh_from_db()
        self.assertEqual(locatie.waarde, "4104AC")


class ThuisadresTests(TestCase):
    """Where a monteur lives is entered on his record, no longer detected.

    Detection was retired on 07-09-2026: it could not tell an occasional day edge
    apart from a real home, and every wrong guess silently dropped rides
    (docs/decisions.md). What is left is a plain field, normalised the same way a
    BekendeLocatie is.
    """

    def test_a_street_is_normalised_like_any_other_address_key(self):
        monteur = factories.monteur("M5", "005", "M5", thuisadres="J. Bosschaartstraat 22")
        self.assertEqual(monteur.thuisadres, "j. bosschaartstraat")
        self.assertEqual(Thuisadres.van(monteur), Thuisadres(straat="j. bosschaartstraat"))

    def test_a_postcode_home_address_is_normalised_as_a_postcode(self):
        monteur = factories.monteur(
            "M5", "005", "M5",
            thuisadres_type=LocatieType.POSTCODE, thuisadres="4112 LN Beusichem",
        )
        self.assertEqual(monteur.thuisadres, "4112LN")
        self.assertEqual(Thuisadres.van(monteur), Thuisadres(postcode="4112LN"))

    def test_an_empty_home_address_matches_nothing(self):
        # Most monteurs will have none filled in right after this ships, and an
        # empty field must never match a stop by accident.
        monteur = factories.monteur("M5", "005", "M5")
        thuis = Thuisadres.van(monteur)

        self.assertEqual(thuis, Thuisadres())
        self.assertFalse(thuis.matcht("4112LN", "j. bosschaartstraat"))
        self.assertFalse(thuis.matcht("", ""))

    def test_an_unusable_home_address_is_refused_rather_than_blanked(self):
        # Silently emptying it would leave a field that looks filled in on screen
        # and matches nothing at all.
        monteur = Monteur(
            naam="M5", medewerker_nummer="005",
            thuisadres_type=LocatieType.POSTCODE, thuisadres="geen postcode",
        )
        with self.assertRaises(ValidationError) as fout:
            monteur.clean()
        self.assertIn("thuisadres", fout.exception.error_dict)

    def test_only_the_chosen_precision_is_compared(self):
        # A street home address must not match a stop that only shares a
        # postcode, or the address precision would mean nothing.
        thuis = Thuisadres(straat="j. bosschaartstraat")

        self.assertTrue(thuis.matcht("9999ZZ", "j. bosschaartstraat"))
        self.assertFalse(thuis.matcht("4112LN", "andere straat"))


class ClassificatieTests(TestCase):
    """The priority order of §3b.

    Depot, own booked hours, the Werkbonnen.xlsx postcode fallback, the rest of
    the koppeltabel, home, and finally the tolerance check.
    """

    def setUp(self):
        self.monteur = factories.monteur("M5", "005", "M5")
        self.depot = factories.bekende_locatie(
            LocatieType.STRAAT, "Randweg", Soort.LOCATIE, "SBTT-Magazijn",
            is_depot=True,
        )

    def _day_with_one_stop(self, *, stop_adres, stop_plaats, stop_minuten=60):
        """A day of two rides, so there is exactly one stop between them."""
        aankomst = dt.time(8, 0)
        vertrek = (
            dt.datetime.combine(DAG, aankomst) + dt.timedelta(minutes=stop_minuten)
        ).time()
        factories.rit(
            "M5", DAG, "07:30", aankomst.strftime("%H:%M"),
            vertrekadres=THUIS_ADRES, vertrekplaats=THUIS_PLAATS,
            aankomstadres=stop_adres, aankomstplaats=stop_plaats,
        )
        factories.rit(
            "M5", DAG, vertrek.strftime("%H:%M"), "17:00",
            vertrekadres=stop_adres, vertrekplaats=stop_plaats,
            aankomstadres=THUIS_ADRES, aankomstplaats=THUIS_PLAATS,
        )
        return build_day(self.monteur, DAG)

    def _stop(self, tijdlijn):
        """The single non-reistijd block of a day built by _day_with_one_stop."""
        stops = [b for b in tijdlijn.blokken if b.soort != Soort.REISTIJD]
        self.assertEqual(len(stops), 1, "expected exactly one stop")
        return stops[0]

    def test_the_depot_wins_from_a_werkbon_at_the_same_address(self):
        # The company's own address is also a customer address in the real data;
        # a stop there must read as a depot visit, not as work at that customer.
        factories.urenregel(
            "005", DAG, "WB261206",
            adres="Randweg 6A", postcode="4104 AC", plaats="CULEMBORG",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=DEPOT_ADRES, stop_plaats=DEPOT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.LOCATIE)
        self.assertEqual(stop.omschrijving, "SBTT-Magazijn")
        self.assertEqual(stop.werkbon, "")

    def test_a_werkbon_wins_from_the_rest_of_the_koppeltabel(self):
        factories.bekende_locatie(
            LocatieType.STRAAT, "Lingedijk", Soort.KLANT, "Oude klantnotitie"
        )
        factories.urenregel(
            "005", DAG, "WB260908",
            adres=KLANT_ADRES, postcode="4196 HB", plaats="TRICHT",
            opdrachtgever="Gijs van Velzen",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.WERKBON)
        self.assertEqual(stop.werkbon, "WB260908")
        self.assertEqual(stop.omschrijving, "WB260908 · Gijs van Velzen")

    def test_a_werkbon_matches_on_postcode_when_the_street_differs(self):
        # docs/business-rules.md: an exact postcode match is not enough on its
        # own, but it is still the first thing tried.
        factories.urenregel(
            "005", DAG, "WB260908",
            adres="Heel andere straat 1", postcode="4196 HB", plaats="TRICHT",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.WERKBON)

    def test_a_werkbon_matches_on_street_when_the_postcode_differs(self):
        factories.urenregel(
            "005", DAG, "WB260908",
            adres="Lingedijk 67", postcode="9999 ZZ", plaats="ELDERS",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.WERKBON)

    def test_hours_booked_at_the_depot_do_not_turn_depot_stops_into_werkbonnen(self):
        # The depot street is left out of the street index on purpose; without
        # that, every visit to the magazijn would match this row.
        factories.urenregel(
            "005", DAG, "WB261206",
            adres="Randweg 6A", postcode="9999 ZZ", plaats="ELDERS",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres="Randweg 20", stop_plaats=DEPOT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.LOCATIE)

    def test_the_werkbonnen_postcode_rescues_a_stop_the_hours_do_not_cover(self):
        """The fallback that closed the gap with the PoC's recovery rate.

        A monteur types the address into his Uren booking by hand, so it can be
        wrong or simply different from where the van actually stopped. The
        postcode in Werkbonnen.xlsx comes from the office planning instead, so it
        still matches when the Uren address does not — which is why the PoC found
        werkbonnen this app was missing (docs/decisions.md, 2026-09-03).
        """
        factories.urenregel(
            "005", DAG, "WB260908",
            adres="Heel andere straat 1", postcode="9999 ZZ", plaats="ELDERS",
        )
        factories.werkbon_controle(
            "WB260908", "005", DAG, FaseStatus.AFGEROND,
            postcode="4196 HB", titel="TRICHT - E-werkzaamheden",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.WERKBON)
        self.assertEqual(stop.werkbon, "WB260908")
        # Titel is display text here, never a matching key of its own.
        self.assertEqual(stop.omschrijving, "WB260908 · TRICHT - E-werkzaamheden")

    def test_the_own_booked_hours_still_win_from_the_werkbonnen_postcode(self):
        # The fallback is second-best on purpose: it only fires where the
        # monteur's own booking does not already explain the stop.
        factories.urenregel(
            "005", DAG, "WB260908",
            adres=KLANT_ADRES, postcode="4196 HB", plaats="TRICHT",
            opdrachtgever="Gijs van Velzen",
        )
        factories.werkbon_controle(
            "WB999999", "005", DAG, FaseStatus.AFGEROND,
            postcode="4196 HB", titel="Andere werkbon",
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.werkbon, "WB260908")

    def test_the_werkbonnen_postcode_wins_from_the_koppeltabel(self):
        # A recognised werkbon says more than a label on an address, so the
        # fallback sits above the koppeltabel in the order.
        factories.bekende_locatie(
            LocatieType.STRAAT, "Lingedijk", Soort.CREDITEUR, "Groothandel"
        )
        factories.werkbon_controle(
            "WB260908", "005", DAG, FaseStatus.AFGEROND, postcode="4196 HB"
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.WERKBON)

    def test_the_depot_still_wins_from_the_werkbonnen_postcode(self):
        # The fallback is inserted below the depot check, so a werkbon planned at
        # the company's own address does not turn a depot stop into work.
        factories.werkbon_controle(
            "WB261206", "005", DAG, FaseStatus.AFGEROND, postcode="4104 AC"
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=DEPOT_ADRES, stop_plaats=DEPOT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.LOCATIE)

    def test_a_werkbonnen_row_of_another_monteur_does_not_match(self):
        factories.werkbon_controle(
            "WB260908", "001", DAG, FaseStatus.AFGEROND, postcode="4196 HB"
        )
        stop = self._stop(
            self._day_with_one_stop(
                stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS, stop_minuten=45
            )
        )
        self.assertEqual(stop.soort, Soort.ONVERKLAARD)

    def test_the_koppeltabel_labels_a_stop_that_has_no_werkbon(self):
        factories.bekende_locatie(
            LocatieType.STRAAT, "Lingedijk", Soort.CREDITEUR, "Groothandel"
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.soort, Soort.CREDITEUR)
        self.assertEqual(stop.omschrijving, "Groothandel")

    def test_a_street_entry_wins_from_a_postcode_entry(self):
        factories.bekende_locatie(
            LocatieType.POSTCODE, "4196 HB", Soort.KLANT, "Via postcode"
        )
        factories.bekende_locatie(
            LocatieType.STRAAT, "Lingedijk", Soort.CREDITEUR, "Via straat"
        )
        stop = self._stop(
            self._day_with_one_stop(stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS)
        )
        self.assertEqual(stop.omschrijving, "Via straat")

    def test_an_unexplained_stop_above_the_threshold_is_onverklaard(self):
        tijdlijn = self._day_with_one_stop(
            stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS, stop_minuten=45
        )
        stop = self._stop(tijdlijn)
        self.assertEqual(stop.soort, Soort.ONVERKLAARD)
        self.assertEqual(stop.duur_minuten, 45)

    def test_an_unexplained_stop_below_the_threshold_is_onbekend(self):
        stop = self._stop(
            self._day_with_one_stop(
                stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS, stop_minuten=5
            )
        )
        self.assertEqual(stop.soort, Soort.ONBEKEND)

    def test_a_stop_shorter_than_a_minute_is_dropped(self):
        factories.rit(
            "M5", DAG, "07:30", "08:00",
            vertrekadres=THUIS_ADRES, aankomstadres=KLANT_ADRES,
            aankomstplaats=KLANT_PLAATS,
        )
        factories.rit(
            "M5", DAG, "08:00", "08:30",
            vertrekadres=KLANT_ADRES, aankomstadres=THUIS_ADRES,
        )
        tijdlijn = build_day(self.monteur, DAG)
        self.assertEqual([b.soort for b in tijdlijn.blokken], [Soort.REISTIJD] * 2)

    def _dag_die_tussendoor_thuiskomt(self):
        factories.bekende_locatie(
            LocatieType.STRAAT, "Lingedijk", Soort.KLANT, "Klant zonder werkbon"
        )
        for vertrek, aankomst, van, naar in [
            ("07:00", "07:30", THUIS_ADRES, KLANT_ADRES),
            ("09:00", "09:30", KLANT_ADRES, THUIS_ADRES),
            ("12:00", "12:30", THUIS_ADRES, KLANT_ADRES),
            ("16:00", "16:30", KLANT_ADRES, THUIS_ADRES),
        ]:
            factories.rit(
                "M5", DAG, vertrek, aankomst,
                vertrekadres=van,
                vertrekplaats=THUIS_PLAATS if van == THUIS_ADRES else KLANT_PLAATS,
                aankomstadres=naar,
                aankomstplaats=THUIS_PLAATS if naar == THUIS_ADRES else KLANT_PLAATS,
            )

    def test_a_stop_at_the_home_address_is_reported_as_thuis(self):
        # Until 07-09-2026 this stop was dropped instead of stored. A day that
        # visibly starts and ends somewhere is easier to check than one that just
        # begins in the middle (docs/decisions.md).
        self.monteur.thuisadres = THUIS_ADRES
        self.monteur.save()
        self._dag_die_tussendoor_thuiskomt()

        tijdlijn = build_day(self.monteur, DAG)

        self.assertEqual(
            [b.soort for b in tijdlijn.blokken],
            [
                Soort.REISTIJD,
                Soort.KLANT,  # stop at the customer
                Soort.REISTIJD,
                Soort.THUIS,  # 09:30-12:00 at home, now a block of its own
                Soort.REISTIJD,
                Soort.KLANT,
                Soort.REISTIJD,
            ],
        )

    def test_without_a_home_address_that_same_stop_is_simply_unexplained(self):
        # No fallback to the old detection: a monteur whose home address is not
        # filled in gets an ordinary O, visible and correctable in the
        # uitzonderingenscherm, rather than a silent guess.
        self._dag_die_tussendoor_thuiskomt()

        tijdlijn = build_day(self.monteur, DAG)

        thuisstop = tijdlijn.blokken[3]
        self.assertEqual(thuisstop.soort, Soort.ONVERKLAARD)
        self.assertEqual(thuisstop.straat, "j. bosschaartstraat")

    def test_a_hand_linked_address_outranks_the_home_address(self):
        # Roger's own case: the van is parked around the corner. That address can
        # be linked as T by hand, and a link always wins from the field — step 4
        # sits above step 5.
        self.monteur.thuisadres = THUIS_ADRES
        self.monteur.save()
        factories.bekende_locatie(
            LocatieType.STRAAT, "J. Bosschaartstraat", Soort.KLANT, "Toch een klant"
        )
        self._dag_die_tussendoor_thuiskomt()

        self.assertEqual(build_day(self.monteur, DAG).blokken[3].soort, Soort.KLANT)

    def test_every_ride_becomes_a_reistijd_block(self):
        tijdlijn = self._day_with_one_stop(
            stop_adres=KLANT_ADRES, stop_plaats=KLANT_PLAATS
        )
        reistijd = [b for b in tijdlijn.blokken if b.soort == Soort.REISTIJD]
        self.assertEqual(len(reistijd), 2)
        self.assertEqual(reistijd[0].duur_minuten, 30)
        self.assertEqual([b.volgorde for b in tijdlijn.blokken], [1, 2, 3])

    def test_a_hop_around_the_house_is_kept_as_an_ordinary_ride(self):
        # It used to be dropped, together with everything else whose two ends
        # both looked like home — which is exactly how whole days disappeared
        # (docs/decisions.md, 07-09-2026). Now it is simply the short ride it is.
        self.monteur.thuisadres = THUIS_ADRES
        self.monteur.save()
        factories.rit(
            "M5", DAG, "07:30", "08:00",
            vertrekadres=THUIS_ADRES, vertrekplaats=THUIS_PLAATS,
            aankomstadres=KLANT_ADRES, aankomstplaats=KLANT_PLAATS,
        )
        factories.rit(
            "M5", DAG, "16:00", "16:30",
            vertrekadres=KLANT_ADRES, vertrekplaats=KLANT_PLAATS,
            aankomstadres=THUIS_ADRES, aankomstplaats=THUIS_PLAATS,
        )
        factories.rit(
            "M5", DAG, "19:00", "19:05",
            vertrekadres="J. Bosschaartstraat 22", vertrekplaats=THUIS_PLAATS,
            aankomstadres="J. Bosschaartstraat 40", aankomstplaats=THUIS_PLAATS,
        )
        tijdlijn = build_day(self.monteur, DAG)

        # 3 rides, the stop at the customer, and the evening stop at home.
        self.assertEqual(
            [b.soort for b in tijdlijn.blokken],
            [
                Soort.REISTIJD,
                Soort.ONVERKLAARD,
                Soort.REISTIJD,
                Soort.THUIS,
                Soort.REISTIJD,
            ],
        )

    def test_a_day_without_rides_yields_nothing(self):
        self.assertIsNone(build_day(self.monteur, DAG))


class TolerantieTests(TestCase):
    """The threshold comes from the tolerantietabel, not from a constant."""

    def test_the_seeded_algemeen_rule_is_the_default(self):
        self.assertEqual(drempel_minuten(), 15)

    def test_an_unknown_activity_falls_back_on_algemeen(self):
        self.assertEqual(drempel_minuten("montage"), 15)

    def test_a_specific_rule_wins_from_the_fallback(self):
        ToleranceRegel.objects.create(activiteit="montage", drempel_minuten=45)
        self.assertEqual(drempel_minuten("montage"), 45)
        self.assertEqual(drempel_minuten(), 15)

    def test_changing_the_algemeen_rule_changes_the_classification(self):
        monteur = factories.monteur("M5", "005", "M5")
        factories.rit(
            "M5", DAG, "07:30", "08:00",
            vertrekadres=THUIS_ADRES, aankomstadres=KLANT_ADRES,
            aankomstplaats=KLANT_PLAATS,
        )
        factories.rit(
            "M5", DAG, "08:20", "09:00",
            vertrekadres=KLANT_ADRES, vertrekplaats=KLANT_PLAATS,
            aankomstadres=THUIS_ADRES,
        )
        # 20 minutes: onverklaard at the default of 15...
        stop = [b for b in build_day(monteur, DAG).blokken if b.soort != Soort.REISTIJD]
        self.assertEqual(stop[0].soort, Soort.ONVERKLAARD)

        # ...and merely unknown once SBTT raises the tolerance.
        ToleranceRegel.objects.filter(activiteit=ToleranceRegel.ALGEMEEN).update(
            drempel_minuten=30
        )
        stop = [b for b in build_day(monteur, DAG).blokken if b.soort != Soort.REISTIJD]
        self.assertEqual(stop[0].soort, Soort.ONBEKEND)


class InstellingTests(TestCase):
    """One row, and one mode that must stay unreachable."""

    def test_load_creates_the_single_row_with_the_vast_default(self):
        instelling = Instelling.load()
        self.assertEqual(instelling.pk, Instelling.SINGLETON_PK)
        self.assertEqual(instelling.meegereden_modus, MeegeredenModus.VAST)
        self.assertEqual(Instelling.objects.count(), 1)

    def test_saving_a_second_row_overwrites_the_first_one(self):
        Instelling.load()
        Instelling(meegereden_modus=MeegeredenModus.PERIODE).save()
        self.assertEqual(Instelling.objects.count(), 1)
        self.assertEqual(Instelling.load().meegereden_modus, MeegeredenModus.PERIODE)

    def test_the_syntess_mode_cannot_be_saved(self):
        # Syntess does not fill "Monteur meegereden" reliably, so the mode is
        # reserved but disabled (docs/decisions.md, 03-09-2026). save() rejects
        # it too, not only the admin form.
        instelling = Instelling.load()
        instelling.meegereden_modus = MeegeredenModus.SYNTESS
        with self.assertRaises(ValidationError):
            instelling.save()
        with self.assertRaises(ValidationError):
            instelling.clean()
        self.assertEqual(Instelling.load().meegereden_modus, MeegeredenModus.VAST)


class MeegeredenTests(TestCase):
    """Whose rides describe a junior's day, per mode."""

    def setUp(self):
        self.senior = factories.monteur("Senior", "002", "M2")
        self.junior = factories.monteur("Junior", "009")
        factories.rit(
            "M2", DAG, "07:30", "08:00",
            vertrekadres=THUIS_ADRES, vertrekplaats=THUIS_PLAATS,
            aankomstadres=KLANT_ADRES, aankomstplaats=KLANT_PLAATS,
        )
        factories.rit(
            "M2", DAG, "16:00", "16:30",
            vertrekadres=KLANT_ADRES, vertrekplaats=KLANT_PLAATS,
            aankomstadres=THUIS_ADRES, aankomstplaats=THUIS_PLAATS,
        )

    def test_without_a_koppeling_a_monteur_is_his_own_source(self):
        self.assertEqual(resolve_bronmonteur(self.senior, DAG), self.senior)

    def test_vast_mode_uses_the_permanently_linked_senior(self):
        self.junior.vaste_meerijder = self.senior
        self.junior.save()
        self.assertEqual(resolve_bronmonteur(self.junior, DAG), self.senior)

    def test_vast_mode_ignores_a_period_koppeling(self):
        # The mode decides which koppeling is consulted; a leftover row from the
        # other mode must not leak into this one.
        MeegeredenKoppeling.objects.create(
            junior=self.junior, senior=self.senior, datum_van=DAG
        )
        self.assertEqual(resolve_bronmonteur(self.junior, DAG), self.junior)

    def test_periode_mode_uses_a_koppeling_covering_the_date(self):
        Instelling.objects.update_or_create(
            pk=Instelling.SINGLETON_PK,
            defaults={"meegereden_modus": MeegeredenModus.PERIODE},
        )
        MeegeredenKoppeling.objects.create(
            junior=self.junior,
            senior=self.senior,
            datum_van=DAG,
            datum_tot=DAG + dt.timedelta(days=7),
        )
        self.assertEqual(resolve_bronmonteur(self.junior, DAG), self.senior)

    def test_periode_mode_ignores_a_koppeling_outside_its_period(self):
        Instelling.objects.update_or_create(
            pk=Instelling.SINGLETON_PK,
            defaults={"meegereden_modus": MeegeredenModus.PERIODE},
        )
        MeegeredenKoppeling.objects.create(
            junior=self.junior,
            senior=self.senior,
            datum_van=DAG - dt.timedelta(days=30),
            datum_tot=DAG - dt.timedelta(days=1),
        )
        self.assertEqual(resolve_bronmonteur(self.junior, DAG), self.junior)

    def test_an_open_ended_koppeling_keeps_applying(self):
        Instelling.objects.update_or_create(
            pk=Instelling.SINGLETON_PK,
            defaults={"meegereden_modus": MeegeredenModus.PERIODE},
        )
        MeegeredenKoppeling.objects.create(
            junior=self.junior,
            senior=self.senior,
            datum_van=DAG - dt.timedelta(days=30),
            datum_tot=None,
        )
        self.assertEqual(resolve_bronmonteur(self.junior, DAG), self.senior)

    def test_a_junior_day_matches_his_own_hours_on_the_senior_rides(self):
        # The point of the whole construction: the senior's rides, the junior's
        # werkbonnen.
        self.junior.vaste_meerijder = self.senior
        self.junior.save()
        factories.urenregel(
            "009", DAG, "WB260908",
            adres=KLANT_ADRES, postcode="4196 HB", plaats="TRICHT",
        )
        # The senior booked nothing that day, so this can only come from the junior.
        tijdlijn = build_day(self.junior, DAG)
        self.assertTrue(tijdlijn.meegereden)
        self.assertEqual(tijdlijn.bronmonteur, self.senior)
        werkbonnen = [b.werkbon for b in tijdlijn.blokken if b.soort == Soort.WERKBON]
        self.assertEqual(werkbonnen, ["WB260908"])

    def test_a_monteur_who_never_drives_and_has_no_koppeling_has_no_day(self):
        self.assertIsNone(build_day(self.junior, DAG))

    def test_a_koppeling_to_yourself_is_rejected(self):
        koppeling = MeegeredenKoppeling(
            junior=self.senior, senior=self.senior, datum_van=DAG
        )
        with self.assertRaises(ValidationError):
            koppeling.clean()

    def test_an_end_date_before_the_start_date_is_rejected(self):
        koppeling = MeegeredenKoppeling(
            junior=self.junior,
            senior=self.senior,
            datum_van=DAG,
            datum_tot=DAG - dt.timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            koppeling.clean()


class MeegeredenOverlapTests(TestCase):
    """A junior rides along with one senior at a time.

    Two koppelingen covering the same day would make the resolution arbitrary:
    matching/timeline/meegereden.py picks the most recently started one, which is
    a tie-breaker for bad data, not an intention. Rejecting the overlap at entry
    keeps that tie-breaker from ever deciding anything.
    """

    def setUp(self):
        self.junior = factories.monteur("Junior", "009")
        self.senior_a = factories.monteur("Senior A", "002", "M2")
        self.senior_b = factories.monteur("Senior B", "003", "M3")

    def _koppeling(self, senior, van, tot, junior=None):
        return MeegeredenKoppeling(
            junior=junior or self.junior, senior=senior, datum_van=van, datum_tot=tot
        )

    def _bestaand(self, senior, van, tot, junior=None):
        koppeling = self._koppeling(senior, van, tot, junior)
        koppeling.save()
        return koppeling

    def test_two_periods_that_do_not_touch_are_both_allowed(self):
        self._bestaand(self.senior_a, dt.date(2026, 8, 1), dt.date(2026, 8, 9))
        volgende = self._koppeling(
            self.senior_b, dt.date(2026, 8, 10), dt.date(2026, 8, 20)
        )
        volgende.clean()  # does not raise

    def test_two_overlapping_periods_are_rejected(self):
        self._bestaand(self.senior_a, dt.date(2026, 8, 1), dt.date(2026, 8, 14))
        overlappend = self._koppeling(
            self.senior_b, dt.date(2026, 8, 10), dt.date(2026, 8, 20)
        )
        with self.assertRaises(ValidationError) as ctx:
            overlappend.clean()
        self.assertIn("datum_van", ctx.exception.message_dict)

    def test_periods_sharing_one_boundary_day_are_rejected(self):
        # Both ends are inclusive (as in geldt_op()), so 10 August belongs to
        # both periods — a junior cannot be reassigned mid-day.
        self._bestaand(self.senior_a, dt.date(2026, 8, 1), dt.date(2026, 8, 10))
        aansluitend = self._koppeling(
            self.senior_b, dt.date(2026, 8, 10), dt.date(2026, 8, 20)
        )
        with self.assertRaises(ValidationError):
            aansluitend.clean()

    def test_an_open_ended_period_blocks_every_later_one(self):
        # datum_tot=None means "still running", so it reaches into the future
        # rather than covering nothing.
        self._bestaand(self.senior_a, dt.date(2026, 8, 1), None)
        later = self._koppeling(self.senior_b, dt.date(2026, 12, 1), None)
        with self.assertRaises(ValidationError):
            later.clean()

    def test_a_new_open_ended_period_cannot_swallow_an_existing_one(self):
        self._bestaand(self.senior_a, dt.date(2026, 12, 1), dt.date(2026, 12, 31))
        eerder = self._koppeling(self.senior_b, dt.date(2026, 8, 1), None)
        with self.assertRaises(ValidationError):
            eerder.clean()

    def test_an_existing_row_does_not_clash_with_itself(self):
        koppeling = self._bestaand(
            self.senior_a, dt.date(2026, 8, 1), dt.date(2026, 8, 9)
        )
        koppeling.clean()  # re-saving an unchanged row must stay valid

        koppeling.datum_tot = dt.date(2026, 8, 12)
        koppeling.clean()  # and so must extending it

    def test_another_juniors_period_is_irrelevant(self):
        andere_junior = factories.monteur("Junior 2", "010")
        self._bestaand(
            self.senior_a, dt.date(2026, 8, 1), dt.date(2026, 8, 20),
            junior=andere_junior,
        )
        eigen = self._koppeling(
            self.senior_a, dt.date(2026, 8, 1), dt.date(2026, 8, 20)
        )
        eigen.clean()  # does not raise



class DagrandenTests(TestCase):
    """The whole start and end of a day must reach the timeline.

    Reproduces the real case that exposed the original bug: Dennis van de Berg
    (002) on 2026-06-02, whose day arrived with only its middle two rides left.
    That was caused twice over — first by the depot counting as a home street
    (fixed 07-09-2026, commit 4d219c2), then by the detection at large, which had
    no way of telling an occasional day edge from a real home.

    Both are gone now: nothing is filtered out before the day is built, so every
    ride is a block by construction. This class stays as the guard on that, and
    on what the day edges are classified as once they arrive.
    """

    THUIS = ("Beesdseweg 3a-18", "4116 GE Buren")
    THUIS_TERUG = ("Beesdseweg 3a-20", "4116 GE Buren")
    DEPOT_1B = ("Randweg 1b", "4104 AC Culemborg")
    DEPOT_6 = ("Randweg 6", "4104 AC Culemborg")
    DEPOT_6D = ("Randweg 6d", "4104 AC Culemborg")
    KLANT = ("Kruiwiel 18", "4126 RH Hei- en Boeicop")

    def setUp(self):
        self.monteur = factories.monteur(
            "Berg D", "002", "Dennis van de Berg", thuisadres="Beesdseweg"
        )
        factories.bekende_locatie(
            LocatieType.STRAAT, "Randweg", Soort.LOCATIE, "SBTT-Magazijn",
            is_depot=True,
        )

    def _rit(self, datum, vertrek, aankomst, van, naar):
        factories.rit(
            "Dennis van de Berg", datum, vertrek, aankomst,
            vertrekadres=van[0], vertrekplaats=van[1],
            aankomstadres=naar[0], aankomstplaats=naar[1],
        )

    def _de_zes_ritten(self):
        """2026-06-02: home -> depot -> customer -> depot -> home."""
        self._rit(DAG, "06:49", "06:52", self.THUIS, self.DEPOT_1B)
        self._rit(DAG, "12:01", "12:10", self.DEPOT_1B, self.DEPOT_6)
        self._rit(DAG, "12:10", "12:27", self.DEPOT_6, self.KLANT)
        self._rit(DAG, "17:11", "17:29", self.KLANT, self.DEPOT_6D)
        self._rit(DAG, "17:31", "17:33", self.DEPOT_6D, self.DEPOT_6)
        self._rit(DAG, "22:15", "22:19", self.DEPOT_6, self.THUIS_TERUG)

    def test_every_ride_of_the_day_ends_up_in_the_timeline(self):
        self._de_zes_ritten()

        tijdlijn = build_day(self.monteur, DAG)

        reistijden = [b for b in tijdlijn.blokken if b.soort == Soort.REISTIJD]
        self.assertEqual(
            [(b.start_tijd.strftime("%H:%M"), b.eind_tijd.strftime("%H:%M"))
             for b in reistijden],
            [
                ("06:49", "06:52"),
                ("12:01", "12:10"),
                ("12:10", "12:27"),
                ("17:11", "17:29"),
                ("17:31", "17:33"),
                ("22:15", "22:19"),
            ],
        )

    def test_the_day_runs_from_the_first_departure_to_the_last_arrival(self):
        self._de_zes_ritten()

        blokken = build_day(self.monteur, DAG).blokken

        self.assertEqual(blokken[0].start_tijd.strftime("%H:%M"), "06:49")
        self.assertEqual(blokken[-1].eind_tijd.strftime("%H:%M"), "22:19")

    def test_the_stays_at_the_depot_are_reported_as_depot_time(self):
        # The morning stay (06:52-12:01) and the evening one (17:33-22:15) were
        # both lost together with their rides; they are depot visits, not work.
        self._de_zes_ritten()

        blokken = build_day(self.monteur, DAG).blokken
        depot = [
            (b.start_tijd.strftime("%H:%M"), b.eind_tijd.strftime("%H:%M"))
            for b in blokken
            if b.omschrijving == "SBTT-Magazijn"
        ]

        # Four, not three: the 12:10 turnaround between the two depot addresses
        # is a zero-minute stop, and the depot branch has no minimum duration.
        self.assertEqual(len(depot), 4)
        self.assertIn(("06:52", "12:01"), depot)
        self.assertIn(("17:33", "22:15"), depot)

    def test_a_hop_between_two_addresses_on_his_own_street_is_kept(self):
        # The case that used to remove entire days: on 24 and 25 June every ride
        # Dennis drove ran between two addresses that both counted as "home", so
        # his day came out empty while he had booked 8 hours.
        self._rit(DAG, "11:08", "11:10", self.THUIS, self.THUIS_TERUG)
        self._rit(DAG, "11:10", "11:25", self.THUIS_TERUG, self.THUIS)
        self._rit(DAG, "16:45", "17:24", self.THUIS, self.THUIS_TERUG)

        blokken = build_day(self.monteur, DAG).blokken

        self.assertEqual(len([b for b in blokken if b.soort == Soort.REISTIJD]), 3)
        self.assertEqual(
            [b.soort for b in blokken],
            [
                Soort.REISTIJD,
                # The 11:10 turnaround is a zero-minute stop. Like the depot and
                # the koppeltabel branches, a named classification has no minimum
                # duration; only an unexplained stop needs a minute to earn a row.
                Soort.THUIS,
                Soort.REISTIJD,
                Soort.THUIS,
                Soort.REISTIJD,
            ],
        )
