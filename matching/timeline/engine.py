"""Reconstructing one monteur's day from his rides, and classifying the stops.

This is the heuristic that was validated on real data before anything was built:
the PoC (D:/STROES/PoC-demo/rmw_sbtt.py) and its generalised form
(D:/STROES/Validatie-W30-W33/geanonimiseerd/validatie_2monteurs_4weken.py),
which recovered 78% resp. 93% of the werkbonnen automatically. The rules here are
the same; what changed is that every constant the scripts hardcoded — the depot,
the koppeltabel, the 15-minute threshold — now comes out of a koppeltabel that
SBTT maintains itself.

The shape of a day: each ride becomes an R (reistijd) block, and the gap between
two consecutive rides is a stop that gets classified. Work time therefore follows
from the ride data, never from the Werktijd/Reistijd fields on the werkbon —
monteurs do not fill those in consistently (docs/business-rules.md). Those fields
of Werkbonnen.xlsx (Werktijd/Reistijd/Titel/Tijd) are still never used for that;
only its Postcode is read here, as a fallback matching key
(docs/decisions.md, 2026-09-03).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.utils import timezone

from matching.models import (
    BekendeLocatie,
    LocatieType,
    Monteur,
    Rit,
    Soort,
    Tijdblok,
    ToleranceRegel,
    Uren,
    WerkbonControle,
)
from matching.timeline import normalize
from matching.timeline.meegereden import resolve_bronmonteur


@dataclass
class DagTijdlijn:
    """The reconstructed day for one monteur, before it is written to the database."""

    monteur: Monteur
    bronmonteur: Monteur
    datum: dt.date
    blokken: list[Tijdblok] = field(default_factory=list)

    @property
    def meegereden(self) -> bool:
        """Whether this day was reconstructed from someone else's rides."""
        return self.bronmonteur.pk != self.monteur.pk

    def totalen(self) -> dict[str, int]:
        """Minutes per SOORT-code, the summary the PoC printed per day."""
        totals = {soort.value: 0 for soort in Soort}
        for blok in self.blokken:
            totals[blok.soort] += blok.duur_minuten
        return totals


# --- home address detection -------------------------------------------------


def home_streets_for(
    monteur: Monteur,
    upto_date: dt.date | None = None,
    *,
    koppeltabellen: "Koppeltabellen | None" = None,
) -> set[str]:
    """The streets where this monteur's days start and end — his home address.

    Nobody registers where a monteur lives, so it is derived: take the first
    departure and the last arrival of every day he drove, and the street that
    keeps coming back is his own. Detection, not configuration, exactly as in the
    validation script's `home_streets_for`.

    The depot is the one place that has to be kept out of that. A monteur who
    picks up his van at the magazijn starts and ends those days there, so the
    depot street lands in this set alongside his real street — and from then on
    `_trim_home_hops` reads every home->depot, depot->depot and depot->home ride
    as "moving the van around at home" and drops it, taking the whole start and
    end of such a day out of the timeline (docs/changelog.md, 07-09-2026). A
    depot is configured, and it is by definition nobody's home, so it is excluded
    here rather than guessed around. Both keys are checked, because a depot may
    be configured on street or on postcode.

    Returns an empty set for a monteur without a driver code (he never drove).
    """
    if not monteur.bestuurder_code:
        return set()

    ritten = Rit.objects.filter(
        bestuurder=monteur.bestuurder_code, vertrekdatum__isnull=False
    )
    if upto_date is not None:
        ritten = ritten.filter(vertrekdatum__lte=upto_date)

    per_day: dict[dt.date, list[Rit]] = {}
    for rit in ritten.order_by("vertrekdatum", "vertrektijd", "row_number"):
        per_day.setdefault(rit.vertrekdatum, []).append(rit)

    if koppeltabellen is None:
        koppeltabellen = Koppeltabellen.load()

    streets = set()
    for dag_ritten in per_day.values():
        eerste, laatste = dag_ritten[0], dag_ritten[-1]
        streets.add(
            _home_edge(eerste.vertrekadres, eerste.vertrekplaats, koppeltabellen)
        )
        streets.add(
            _home_edge(laatste.aankomstadres, laatste.aankomstplaats, koppeltabellen)
        )
    streets.discard("")
    return streets


def _home_edge(adres: str, plaats: str, koppeltabellen: "Koppeltabellen") -> str:
    """The street of one day edge, or "" when that edge cannot be someone's home.

    Returning the empty string rather than filtering afterwards keeps the caller
    simple: "" is discarded there anyway, together with the edges that have no
    usable address at all.

    Two edges are refused. A depot, because it is configured and is by definition
    nobody's home. And a "street" without a single letter in it — RouteVision
    writes "-" for a stop it could not resolve, and that placeholder was becoming
    a home street of its own, after which every ride between two unresolved
    addresses was dropped as a hop around the house.
    """
    straat = normalize.street(adres)
    if not any(teken.isalpha() for teken in straat):
        return ""

    postcode = normalize.postcode(plaats)
    if straat in koppeltabellen.depot_per_straat or (
        postcode in koppeltabellen.depot_per_postcode
    ):
        return ""
    return straat


# --- the lookup tables one day is classified against ------------------------


@dataclass
class Koppeltabellen:
    """The koppeltabel content one classification pass needs, read once.

    Split by is_depot because a depot visit outranks everything else: the
    company's own address is often also a customer address, and a stop at the
    magazijn must not be read as work at that customer.
    """

    depot_per_postcode: dict[str, BekendeLocatie]
    depot_per_straat: dict[str, BekendeLocatie]
    locatie_per_postcode: dict[str, BekendeLocatie]
    locatie_per_straat: dict[str, BekendeLocatie]

    @classmethod
    def load(cls) -> "Koppeltabellen":
        tabellen = cls({}, {}, {}, {})
        for locatie in BekendeLocatie.objects.all():
            if not locatie.waarde:
                continue  # a row without a key can never match anything
            op_postcode = locatie.type == LocatieType.POSTCODE
            if op_postcode:
                tabellen.locatie_per_postcode[locatie.waarde] = locatie
                if locatie.is_depot:
                    tabellen.depot_per_postcode[locatie.waarde] = locatie
            else:
                tabellen.locatie_per_straat[locatie.waarde] = locatie
                if locatie.is_depot:
                    tabellen.depot_per_straat[locatie.waarde] = locatie
        return tabellen

    @property
    def depot_streets(self) -> set[str]:
        """Street names of the depot(s) — needed when indexing the booked hours."""
        return set(self.depot_per_straat)


@dataclass
class DagUren:
    """The hours this monteur booked on this date, indexed the way stops arrive.

    Both indexes point at an Uren row, so a matched stop can carry that row's
    werkbon number and customer name into the Tijdblok.
    """

    per_postcode: dict[str, Uren]
    per_straat: dict[str, Uren]

    @classmethod
    def load(
        cls, monteur: Monteur, datum: dt.date, depot_streets: set[str]
    ) -> "DagUren":
        per_postcode, per_straat = {}, {}
        for regel in Uren.objects.filter(
            medewerker=monteur.medewerker_nummer, datum=datum
        ).order_by("row_number"):
            postcode = normalize.postcode(regel.postcode)
            if postcode:
                per_postcode.setdefault(postcode, regel)
            straat = normalize.street(regel.adres)
            # The depot street is left out on purpose (the PoC does the same when
            # it builds wb_street): hours booked at the company's own address
            # would otherwise turn every depot stop into a werkbon match.
            if straat and straat not in depot_streets:
                per_straat.setdefault(straat, regel)
        return cls(per_postcode, per_straat)


@dataclass
class WerkbonPostcodes:
    """Fallback postcode index from Werkbonnen.xlsx.

    Used only when the monteur's own booked hours (DagUren) do not cover a
    stop's postcode or street. Werkbonnen.xlsx is still not a general matching
    source — Titel/Tijd/Reistijd/Werktijd from it are never read here — but its
    Postcode comes from the office planning rather than what a monteur typed
    into Uren.xlsx by hand, so it recovers matches the PoC also found this way
    (docs/decisions.md, 2026-09-03).
    """

    per_postcode: dict[str, WerkbonControle]

    @classmethod
    def load(cls, monteur: Monteur, datum: dt.date) -> "WerkbonPostcodes":
        per_postcode: dict[str, WerkbonControle] = {}
        for regel in WerkbonControle.objects.filter(
            medewerker=monteur.medewerker_nummer, datum=datum
        ).order_by("row_number"):
            postcode = normalize.postcode(regel.postcode)
            if postcode:
                per_postcode.setdefault(postcode, regel)
        return cls(per_postcode)


def drempel_minuten(activiteit: str | None = None) -> int:
    """The tolerance above which an unexplained stop counts as onverklaard (O).

    Looks up the rule for `activiteit` and falls back on the seeded "algemeen"
    row. There is no per-activity rule yet — the values still have to be
    confirmed with the customer (docs/functioneel-ontwerp.md §9, point 2) — so in
    practice every lookup lands on the fallback today. The signature already
    takes the activity so that adding rules later needs no call-site changes.
    """
    regels = ToleranceRegel.objects
    if activiteit:
        regel = regels.filter(activiteit=activiteit).first()
        if regel:
            return regel.drempel_minuten
    regel = regels.filter(activiteit=ToleranceRegel.ALGEMEEN).first()
    # The seed migration creates the "algemeen" row; the constant is only a
    # last-resort guard for a database where it was deleted by hand.
    return regel.drempel_minuten if regel else 15


# --- the day itself ---------------------------------------------------------


def build_day(
    monteur: Monteur,
    datum: dt.date,
    *,
    koppeltabellen: Koppeltabellen | None = None,
    home_streets: set[str] | None = None,
    bronmonteur: Monteur | None = None,
) -> DagTijdlijn | None:
    """Reconstruct one monteur-day; None when there are no rides to build it from.

    The optional arguments let a caller processing many days load the shared
    lookups once instead of per day; they change nothing about the result.
    """
    bronmonteur = bronmonteur or resolve_bronmonteur(monteur, datum)
    if not bronmonteur.bestuurder_code:
        return None

    ritten = _day_rides(bronmonteur, datum)
    if koppeltabellen is None:
        koppeltabellen = Koppeltabellen.load()
    if home_streets is None:
        # Needs the koppeltabellen, to keep the depot out of the home streets.
        home_streets = home_streets_for(bronmonteur, koppeltabellen=koppeltabellen)
    ritten = _trim_home_hops(ritten, home_streets)
    if not ritten:
        return None

    uren = DagUren.load(monteur, datum, koppeltabellen.depot_streets)
    werkbonnen = WerkbonPostcodes.load(monteur, datum)

    # One lookup per day rather than per stop: the tolerance cannot change
    # halfway through a day.
    drempel = drempel_minuten()

    tijdlijn = DagTijdlijn(monteur=monteur, bronmonteur=bronmonteur, datum=datum)
    for index, rit in enumerate(ritten):
        vertrek, aankomst = _ride_moments(rit)
        _add(
            tijdlijn,
            soort=Soort.REISTIJD,
            start=vertrek,
            eind=aankomst,
            omschrijving="Reistijd",
            adres=(
                f"{rit.vertrekadres} → {rit.aankomstadres}, "
                f"{normalize.plaatsnaam(rit.aankomstplaats)}"
            ),
        )

        # The last arrival of the day is where the day ends; there is no stop
        # after it to measure.
        if index == len(ritten) - 1:
            continue

        volgende_vertrek, _ = _ride_moments(ritten[index + 1])
        _classify_stop(
            tijdlijn,
            rit=rit,
            start=aankomst,
            eind=volgende_vertrek,
            koppeltabellen=koppeltabellen,
            uren=uren,
            werkbonnen=werkbonnen,
            home_streets=home_streets,
            drempel=drempel,
        )
    return tijdlijn


def _classify_stop(
    tijdlijn: DagTijdlijn,
    *,
    rit: Rit,
    start: dt.datetime,
    eind: dt.datetime,
    koppeltabellen: Koppeltabellen,
    uren: DagUren,
    werkbonnen: WerkbonPostcodes,
    home_streets: set[str],
    drempel: int,
) -> None:
    """Give one stop its SOORT, in the priority order validated by the PoC.

    The order matters and is not arbitrary:

    1. Depot first — the company's own address doubles as a customer address, so
       a depot stop must never be read as work there.
    2. Then the monteur's own booked hours (Uren.xlsx) — the actual matching: a
       stop at an address he booked hours on that day is that werkbon (W).
    3. Then Werkbonnen.xlsx's own Postcode, as a fallback for when Uren.xlsx's
       address doesn't cover the stop — still W, just a second-best source
       (docs/decisions.md, 2026-09-03).
    4. Then the rest of the koppeltabel (K/L/C) — addresses a user recognised
       once and never has to explain again.
    5. Then home — the day's own edges, dropped rather than shown.
    6. Otherwise unexplained: above the tolerance it is a real signal (O), below
       it is short noise (?), and under a minute it is not worth a row at all.

    Within 2, postcode wins over street; within 4, street wins over postcode —
    both exactly as the PoC ordered its lookups.
    """
    postcode = normalize.postcode(rit.aankomstplaats)
    straat = normalize.street(rit.aankomstadres)
    adres = f"{rit.aankomstadres}, {rit.aankomstplaats}"
    # Every branch below stores these two on its Tijdblok, not just the O one the
    # uitzonderingenscherm reads: they are already computed here, so keeping all
    # stop rows consistent costs nothing and saves a second migration later.
    gap = _minutes_between(start, eind)

    depot = koppeltabellen.depot_per_straat.get(
        straat
    ) or koppeltabellen.depot_per_postcode.get(postcode)
    if depot:
        _add(
            tijdlijn,
            soort=depot.soort,
            start=start,
            eind=eind,
            omschrijving=depot.label,
            adres=adres,
            postcode=postcode,
            straat=straat,
        )
        return

    urenregel = uren.per_postcode.get(postcode) or uren.per_straat.get(straat)
    if urenregel:
        omschrijving = urenregel.project_opdrachtgever_naam or urenregel.taak_omschrijving
        _add(
            tijdlijn,
            soort=Soort.WERKBON,
            start=start,
            eind=eind,
            omschrijving=f"{urenregel.werkbon} · {omschrijving}".strip(" ·"),
            adres=adres,
            postcode=postcode,
            straat=straat,
            werkbon=urenregel.werkbon,
        )
        return

    # The depot does not have to be excluded here the way DagUren.load() excludes
    # the depot street: a depot stop already returned above.
    controleregel = werkbonnen.per_postcode.get(postcode)
    if controleregel:
        omschrijving = f"{controleregel.werkbon} · {controleregel.titel}".strip(" ·")
        _add(
            tijdlijn,
            soort=Soort.WERKBON,
            start=start,
            eind=eind,
            omschrijving=omschrijving,
            adres=adres,
            postcode=postcode,
            straat=straat,
            werkbon=controleregel.werkbon,
        )
        return

    locatie = koppeltabellen.locatie_per_straat.get(
        straat
    ) or koppeltabellen.locatie_per_postcode.get(postcode)
    if locatie:
        _add(
            tijdlijn,
            soort=locatie.soort,
            start=start,
            eind=eind,
            omschrijving=locatie.label,
            adres=adres,
            postcode=postcode,
            straat=straat,
        )
        return

    if straat in home_streets:
        # Home is where the day starts and ends, not a stop to report — the PoC
        # drops these rows from its output too.
        return

    if gap >= drempel:
        _add(
            tijdlijn,
            soort=Soort.ONVERKLAARD,
            start=start,
            eind=eind,
            omschrijving="Onverklaarde stop",
            adres=adres,
            postcode=postcode,
            straat=straat,
        )
    elif gap >= 1:
        _add(
            tijdlijn,
            soort=Soort.ONBEKEND,
            start=start,
            eind=eind,
            omschrijving="Korte onbekende stop",
            adres=adres,
            postcode=postcode,
            straat=straat,
        )
    # Under a minute: too short to matter, no row at all.


def _add(
    tijdlijn: DagTijdlijn,
    *,
    soort: str,
    start: dt.datetime,
    eind: dt.datetime,
    omschrijving: str = "",
    adres: str = "",
    postcode: str = "",
    straat: str = "",
    werkbon: str = "",
) -> None:
    """Append one unsaved Tijdblok, numbering it as the next block of the day.

    `postcode`/`straat` are the normalised matching keys of the stop, stored
    alongside the composed `adres` display text so the uitzonderingenscherm can
    group on them without re-parsing that text (docs/decisions.md, 2026-09-03).
    They default to blank for a block that has no single address of its own — an
    R (reistijd) block runs between two addresses, not at one.
    """
    tijdlijn.blokken.append(
        Tijdblok(
            monteur=tijdlijn.monteur,
            datum=tijdlijn.datum,
            volgorde=len(tijdlijn.blokken) + 1,
            soort=soort,
            start_tijd=start,
            eind_tijd=eind,
            duur_minuten=_minutes_between(start, eind),
            omschrijving=omschrijving[:255],
            adres=adres[:512],
            postcode=postcode[:6],
            straat=straat[:255],
            werkbon=werkbon[:32],
        )
    )


# --- rides ------------------------------------------------------------------


def _day_rides(bronmonteur: Monteur, datum: dt.date) -> list[Rit]:
    """This driver's rides on this date, in the order they were driven.

    Grouped by departure date, as the PoC does: a ride belongs to the day it
    started on, even if it arrives after midnight.
    """
    return list(
        Rit.objects.filter(
            bestuurder=bronmonteur.bestuurder_code,
            vertrekdatum=datum,
            vertrektijd__isnull=False,
            aankomsttijd__isnull=False,
        ).order_by("vertrektijd", "row_number")
    )


def _trim_home_hops(ritten: list[Rit], home_streets: set[str]) -> list[Rit]:
    """Drop rides that go from home to home.

    Moving the van around the neighbourhood in the evening is not work, and
    leaving those rides in would put a bogus stop between them.
    """
    return [
        rit
        for rit in ritten
        if not (
            normalize.street(rit.vertrekadres) in home_streets
            and normalize.street(rit.aankomstadres) in home_streets
        )
    ]


def _ride_moments(rit: Rit) -> tuple[dt.datetime, dt.datetime]:
    """Departure and arrival as aware datetimes in the app's timezone.

    The arrival takes its own date when RouteVision filled one in, so a ride that
    runs past midnight does not come out as a negative duration.
    """
    vertrek = _aware(rit.vertrekdatum, rit.vertrektijd)
    aankomst = _aware(rit.aankomstdatum or rit.vertrekdatum, rit.aankomsttijd)
    return vertrek, aankomst


def _aware(datum: dt.date, tijd: dt.time) -> dt.datetime:
    naive = dt.datetime.combine(datum, tijd)
    return timezone.make_aware(naive) if timezone.is_naive(naive) else naive


def _minutes_between(start: dt.datetime, eind: dt.datetime) -> int:
    """Whole minutes between two moments, never negative.

    Rounded the way the PoC rounded its durations. Overlapping rides (the same
    van leaving before the previous ride's arrival) would otherwise produce a
    negative duration, which a PositiveIntegerField cannot hold; clamping keeps
    one odd source row from failing the whole day.
    """
    return max(0, int(round((eind - start).total_seconds() / 60)))
