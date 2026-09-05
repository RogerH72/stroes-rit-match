"""Building one monteur-week for the weekoverzicht (roadmap phase 6).

The web page and the Excel export are two renderings of the same thing, so a
week is assembled here once and both read the result: `matching/views.py`
renders it as HTML, `matching/weekoverzicht_excel.py` writes the same numbers
into a workbook. Nothing here knows about the request or about URLs — it only
reads the Tijdblok rows the matchmotor already wrote (phase 3).

The layout follows the prototype SBTT worked with
(D:/STROES/PoC-demo/RMW_SBTT_week_M5.html) — SOORT colours, a legend, a
collapsible table per day with a SOORT-total, and a week-total bar — with two
deliberate differences:

1. **No WB column and no ⚑ signal.** Those compared the werkbon time a monteur
   typed in himself with the RouteVision time. That WB-vs-SYS signal was
   deliberately not built (docs/functioneel-ontwerp.md §3b), so reproducing it
   here would put a signal on screen that the rest of the app does not stand
   behind.
2. **The "gefactureerd vs. op locatie" comparison is kept**, per day and per
   week: the hours booked in Uren.xlsx against the time the monteur actually
   stood at a werkbon address (the SOORT=W blocks). Unlike WB-vs-SYS this
   compares two sources that are both trusted — booked hours and reconstructed
   ride data — which is exactly the discrepancy this whole tool exists to
   surface.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from matching.models import Monteur, Soort, Tijdblok, Uren
from matching.timeline import normalize

#: Colour per SOORT-code, used by the web page and the Excel export alike.
#:
#: Taken from the prototype (rmw_sbtt.py), because these are the colours SBTT
#: has been reading the overview in — a functional code palette, not a brand
#: palette. One change: O uses the warning colour phase 5 settled on
#: (docs/ui-spec.md) instead of the prototype's red, so an onverklaarde stop
#: looks the same on both screens.
SOORT_KLEUREN = {
    Soort.KLANT: "#0E7C86",
    Soort.LOCATIE: "#2563B0",
    Soort.CREDITEUR: "#8250B5",
    Soort.WERKBON: "#1F8A4C",
    Soort.ONBEKEND: "#8A94A2",
    Soort.ONVERKLAARD: "#D97706",
    Soort.REISTIJD: "#9AA4B2",
}

#: Fixed order of the codes wherever they are totalled or listed — the order of
#: the SOORT table in docs/functioneel-ontwerp.md §3b.
SOORT_VOLGORDE = [soort.value for soort in Soort]

#: "2026-W32", the value <input type="week"> produces and the URL carries.
_WEEK_PATROON = re.compile(r"^(\d{4})-W(\d{1,2})$")


# --- the week as a value ----------------------------------------------------


def parse_week(waarde: str | None) -> tuple[int, int] | None:
    """"2026-W32" -> (2026, 32), or None when that is not a real ISO week.

    Both halves are validated, not just the shape: "2026-W53" parses fine but
    2026 has no 53rd week, and a page built on it would silently show something
    else than the URL says.
    """
    match = _WEEK_PATROON.match((waarde or "").strip().upper())
    if not match:
        return None
    jaar, week = int(match.group(1)), int(match.group(2))
    try:
        dt.date.fromisocalendar(jaar, week, 1)
    except ValueError:
        return None
    return jaar, week


def format_week(jaar: int, week: int) -> str:
    """(2026, 32) -> "2026-W32"."""
    return f"{jaar}-W{week:02d}"


def week_van(datum: dt.date) -> tuple[int, int]:
    """The ISO year and week a date falls in.

    The ISO *year* is not always the calendar year: 1 January 2027 belongs to
    week 53 of 2026, and using the calendar year there would point at a week
    that does not exist.
    """
    iso = datum.isocalendar()
    return iso.year, iso.week


def laatste_week_met_data(monteur: Monteur) -> tuple[int, int]:
    """The most recent week this monteur has a reconstructed day in.

    The default when no week was asked for: opening the screen on the current
    week would show an empty page for most of Monday morning, and after a
    holiday it would show one for days. Falls back to the current week for a
    monteur who has never been processed.
    """
    laatste = (
        Tijdblok.objects.filter(monteur=monteur)
        .order_by("-datum")
        .values_list("datum", flat=True)
        .first()
    )
    return week_van(laatste or timezone.localdate())


# --- one week, assembled ----------------------------------------------------


@dataclass
class SoortTotaal:
    """Minutes on one SOORT-code, for a day or for the whole week."""

    code: str
    label: str
    kleur: str
    minuten: int

    @property
    def tijd(self) -> str:
        """h:mm, or a dash when the code did not occur — as in the prototype."""
        return normalize.minutes_to_hhmm(self.minuten) if self.minuten else "–"


@dataclass
class WeekRegel:
    """One row of a day table: a Tijdblok plus what it takes to show it."""

    blok: Tijdblok
    kleur: str
    #: Set on an onverklaarde stop only: the key the uitzonderingenscherm's
    #: confirm form is addressed by, so O can be resolved straight from here.
    koppel_precisie: str = ""
    koppel_sleutel: str = ""

    @property
    def koppelbaar(self) -> bool:
        return bool(self.koppel_sleutel)

    @property
    def is_reistijd(self) -> bool:
        """Travel rows are dimmed: they are context, not something to check."""
        return self.blok.soort == Soort.REISTIJD

    @property
    def start(self) -> dt.datetime:
        return timezone.localtime(self.blok.start_tijd)

    @property
    def eind(self) -> dt.datetime:
        return timezone.localtime(self.blok.eind_tijd)

    @property
    def duur(self) -> str:
        return normalize.minutes_to_hhmm(self.blok.duur_minuten)


@dataclass
class DagOverzicht:
    """One reconstructed day, with its totals."""

    datum: dt.date
    regels: list[WeekRegel] = field(default_factory=list)
    #: Hours booked in Uren.xlsx on this date — the "gefactureerd" side.
    gefactureerde_uren: Decimal = Decimal("0.00")

    @property
    def totalen(self) -> list[SoortTotaal]:
        return _soort_totalen(_minuten_per_soort(self.regels))

    @property
    def totaal_minuten(self) -> int:
        return sum(regel.blok.duur_minuten for regel in self.regels)

    @property
    def totaal(self) -> str:
        return normalize.minutes_to_hhmm(self.totaal_minuten)

    @property
    def uren_op_locatie(self) -> Decimal:
        """Time actually spent at a werkbon address, in hours."""
        return _naar_uren(
            sum(
                regel.blok.duur_minuten
                for regel in self.regels
                if regel.blok.soort == Soort.WERKBON
            )
        )

    @property
    def verschil(self) -> Decimal:
        """Booked minus on-location. Positive: more booked than driven to."""
        return self.gefactureerde_uren - self.uren_op_locatie


@dataclass
class OntbrekendeDag:
    """A working day of this week without a reconstructed timeline.

    Carries the hours booked on it, because those two facts together say what
    kind of gap it is: no hours either is most likely leave or a day off, while
    booked hours without any ride data points at a missing or unprocessed
    RouteVision export.
    """

    datum: dt.date
    gefactureerde_uren: Decimal = Decimal("0.00")


@dataclass
class WeekOverzicht:
    """Everything one monteur-week shows, in one object."""

    monteur: Monteur
    jaar: int
    week: int
    maandag: dt.date
    dagen: list[DagOverzicht] = field(default_factory=list)
    ontbrekende_dagen: list[OntbrekendeDag] = field(default_factory=list)

    @property
    def zondag(self) -> dt.date:
        return self.maandag + dt.timedelta(days=6)

    @property
    def vrijdag(self) -> dt.date:
        return self.maandag + dt.timedelta(days=4)

    @property
    def leeg(self) -> bool:
        return not self.dagen

    @property
    def totalen(self) -> list[SoortTotaal]:
        minuten: dict[str, int] = {}
        for dag in self.dagen:
            for code, aantal in _minuten_per_soort(dag.regels).items():
                minuten[code] = minuten.get(code, 0) + aantal
        return _soort_totalen(minuten)

    @property
    def totaal_minuten(self) -> int:
        return sum(dag.totaal_minuten for dag in self.dagen)

    @property
    def totaal(self) -> str:
        return normalize.minutes_to_hhmm(self.totaal_minuten)

    # The three week figures below deliberately only add up the days that are
    # actually shown. Counting the hours booked on a day that has no timeline
    # would compare them against W-blocks that do not exist, which reads as a
    # discrepancy in the work while it is really a gap in the data — the
    # ontbrekende_dagen list carries those hours separately instead.
    @property
    def gefactureerde_uren(self) -> Decimal:
        return sum(
            (dag.gefactureerde_uren for dag in self.dagen), start=Decimal("0.00")
        )

    @property
    def uren_op_locatie(self) -> Decimal:
        return sum((dag.uren_op_locatie for dag in self.dagen), start=Decimal("0.00"))

    @property
    def verschil(self) -> Decimal:
        return self.gefactureerde_uren - self.uren_op_locatie

    @property
    def vorige_week(self) -> str:
        return format_week(*week_van(self.maandag - dt.timedelta(days=7)))

    @property
    def volgende_week(self) -> str:
        return format_week(*week_van(self.maandag + dt.timedelta(days=7)))

    @property
    def waarde(self) -> str:
        """This week as "2026-W32" — what the form field and the URL carry."""
        return format_week(self.jaar, self.week)


def bouw_weekoverzicht(monteur: Monteur, jaar: int, week: int) -> WeekOverzicht:
    """Assemble one monteur-week from the stored Tijdblok rows.

    Only days that have a reconstructed timeline become a DagOverzicht; the
    working days that do not are reported separately, so an incomplete week can
    never pass for a complete one (the week total is the number a planner
    compares against a contract, so it has to say what it is missing).
    """
    maandag = dt.date.fromisocalendar(jaar, week, 1)
    zondag = maandag + dt.timedelta(days=6)

    uren_per_dag = _geboekte_uren(monteur, maandag, zondag)

    dagen: dict[dt.date, DagOverzicht] = {}
    blokken = Tijdblok.objects.filter(
        monteur=monteur, datum__range=(maandag, zondag)
    ).order_by("datum", "volgorde")
    for blok in blokken:
        dag = dagen.get(blok.datum)
        if dag is None:
            dag = dagen[blok.datum] = DagOverzicht(
                datum=blok.datum,
                gefactureerde_uren=uren_per_dag.get(blok.datum, Decimal("0.00")),
            )
        dag.regels.append(_regel(blok))

    return WeekOverzicht(
        monteur=monteur,
        jaar=jaar,
        week=week,
        maandag=maandag,
        dagen=[dagen[datum] for datum in sorted(dagen)],
        ontbrekende_dagen=_ontbrekende_dagen(maandag, set(dagen), uren_per_dag),
    )


def _regel(blok: Tijdblok) -> WeekRegel:
    """One block as a row, with its colour and — for O — its koppel-key.

    The key comes from the model rather than from a rule of this module, so a
    row here always addresses exactly the group the uitzonderingenscherm shows.
    """
    regel = WeekRegel(blok=blok, kleur=SOORT_KLEUREN.get(blok.soort, "#8A94A2"))
    if blok.soort == Soort.ONVERKLAARD:
        sleutel = blok.koppelsleutel
        if sleutel:
            regel.koppel_precisie, regel.koppel_sleutel = sleutel
    return regel


def _geboekte_uren(
    monteur: Monteur, van: dt.date, tot: dt.date
) -> dict[dt.date, Decimal]:
    """Hours booked per date, from Uren.xlsx — the "gefactureerd" side.

    Summed per date rather than per werkbon: the comparison is about the day as
    a whole, and a monteur regularly books several werkbonnen on one day.
    """
    rijen = (
        Uren.objects.filter(
            medewerker=monteur.medewerker_nummer, datum__range=(van, tot)
        )
        .values("datum")
        .annotate(totaal=Sum("aantal"))
    )
    # `aantal` is nullable, so a date whose rows are all empty sums to None.
    # Quantised so both sides of the comparison read the same: a sum that comes
    # back as Decimal("6") would otherwise print as "6 → 5,73 u".
    return {
        rij["datum"]: (rij["totaal"] or Decimal(0)).quantize(Decimal("0.01"))
        for rij in rijen
    }


def _ontbrekende_dagen(
    maandag: dt.date, aanwezig: set[dt.date], uren_per_dag: dict[dt.date, Decimal]
) -> list[OntbrekendeDag]:
    """The Monday-to-Friday days of this week without a reconstructed timeline.

    Weekend days are not reported: a monteur is not expected to have driven on
    Saturday, and a Saturday that does have rides simply shows up as a day.
    Days that have not happened yet are not reported either — on Wednesday,
    Thursday and Friday are not missing, they are still coming.
    """
    vandaag = timezone.localdate()
    ontbrekend = []
    for dagnummer in range(5):
        datum = maandag + dt.timedelta(days=dagnummer)
        if datum > vandaag or datum in aanwezig:
            continue
        ontbrekend.append(
            OntbrekendeDag(
                datum=datum, gefactureerde_uren=uren_per_dag.get(datum, Decimal("0.00"))
            )
        )
    return ontbrekend


def _minuten_per_soort(regels: list[WeekRegel]) -> dict[str, int]:
    minuten: dict[str, int] = {}
    for regel in regels:
        minuten[regel.blok.soort] = (
            minuten.get(regel.blok.soort, 0) + regel.blok.duur_minuten
        )
    return minuten


def _soort_totalen(minuten: dict[str, int]) -> list[SoortTotaal]:
    """Every code in the fixed order, including the ones that stayed at zero.

    Zeroes are kept on purpose: "O 0:00" is the reassuring line on this
    overview, and dropping it would leave the reader unsure whether there were
    no unexplained stops or the column was simply not shown.
    """
    return [
        SoortTotaal(
            code=code,
            label=Soort(code).label,
            kleur=SOORT_KLEUREN.get(code, "#8A94A2"),
            minuten=minuten.get(code, 0),
        )
        for code in SOORT_VOLGORDE
    ]


def _naar_uren(minuten: int) -> Decimal:
    """Minutes as hours with two decimals, the unit Uren.xlsx books in."""
    return (Decimal(minuten) / Decimal(60)).quantize(Decimal("0.01"))
