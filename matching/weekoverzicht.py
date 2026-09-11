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
2. **The booked-hours vs. op-locatie comparison is kept**, per day and per
   week: the hours booked in Uren.xlsx against the time the monteur actually
   stood at a werkbon address (the SOORT=W blocks). Unlike WB-vs-SYS this
   compares two sources that are both trusted — booked hours and reconstructed
   ride data — which is exactly the discrepancy this whole tool exists to
   surface. On screen the left-hand side reads "Totaal (excl. reistijd)": not
   every booked hour is actually invoiced to a client — depot and magazijn time
   is booked but not billed — so the older "Gefactureerd" label claimed more
   than the number meant (docs/decisions.md, 07-09-2026 avond).
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
    # P (07-09-2026) fills the one gap left in the palette's hue circle: teal,
    # blue, violet, green, amber and two greys were taken, so the red half was
    # free. Crimson rather than a true red on purpose — red next to the amber O
    # would read as "worse than unexplained", while a P stop is the opposite, a
    # stop that has been explained away. Dark enough for the white code letter
    # (about 6:1 against white), and far enough from the violet C to stay apart
    # in a dense table.
    Soort.PRIVE: "#C2185B",
    # T (07-09-2026). Eight codes in, the hue circle is nearly full; what was
    # left unused is the desaturated warm-dark corner, so T is a brown. It reads
    # as quiet rather than as a signal, which is what a stop at home is, and its
    # low saturation and darkness keep it apart from the one neighbour it shares
    # a hue family with — the bright amber O.
    Soort.THUIS: "#6D4C41",
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


#: Label of the row that carries the K time — client time that no werkbon can
#: account for, because a BekendeLocatie(K) has no werkbon number anywhere in the
#: data (docs/decisions.md, 07-09-2026).
KLANT_LABEL = "Klant (niet aan werkbon gekoppeld)"

#: Label of the row that carries the booked hours with no werkbon number on them
#: — Kantoor, Verlof, Reisuren, Magazijn onderhoud and the like. Over half of the
#: urenregels in the June data are of this kind, so leaving them out would make
#: the table's own total disagree with the day figure right above it.
INDIRECT_LABEL = "Zonder werkbonnummer (indirect)"


@dataclass(frozen=True)
class AansluitingRegel:
    """One line of the per-werkbon reconciliation of a day.

    Either side can be absent rather than zero, and the difference is the two
    sides being genuinely comparable:

    - a K row has no `gedeclareerd`, because client time carries no werkbon
      number to book hours against;
    - the indirect row has no `op_locatie`, because hours without a werkbon
      number can never produce a W block to stand at.

    Absent is not zero: "–" says the question does not apply here, while 0,00
    would claim it was asked and came back empty.
    """

    label: str
    op_locatie: Decimal | None
    gedeclareerd: Decimal | None
    #: The client this werkbon was booked for, from Uren.xlsx. Only werkbon rows
    #: carry one: the K row, the indirect row and the total are not tied to a
    #: single werkbon, so they stay None and read as "–" like every other
    #: not-applicable cell here (docs/decisions.md, 08-09-2026).
    klantnaam: str | None = None

    @property
    def verschil(self) -> Decimal | None:
        """Declared minus on-site, or None when the two are not comparable.

        Same direction as the day comparison above this table, so a positive
        number means the same thing in both places: more booked than driven to.
        """
        if self.op_locatie is None or self.gedeclareerd is None:
            return None
        return self.gedeclareerd - self.op_locatie

    @property
    def sluit_aan(self) -> bool:
        return self.verschil == Decimal("0.00")


@dataclass
class DagOverzicht:
    """One reconstructed day, with its totals."""

    datum: dt.date
    regels: list[WeekRegel] = field(default_factory=list)
    #: Booked hours per werkbon number on this date, "" holding the ones with no
    #: werkbon number at all.
    gedeclareerd_per_werkbon: dict[str, Decimal] = field(default_factory=dict)
    #: Client name per werkbon number on this date, as booked in Uren.xlsx. Only
    #: what stands on this exact date: a werkbon that has no Uren row today has
    #: no entry here, and gets a "–" rather than a name borrowed from another day
    #: (docs/decisions.md, 08-09-2026).
    klantnaam_per_werkbon: dict[str, str] = field(default_factory=dict)
    #: Hours booked in Uren.xlsx on this date — the left-hand side of the
    #: comparison. On screen this is labelled "Totaal (excl. reistijd)" since
    #: 07-09-2026; the field keeps its original name because the value is
    #: unchanged and renaming it would touch the Excel export and every test for
    #: a label change (docs/decisions.md, 07-09-2026 avond).
    gefactureerde_uren: Decimal = Decimal("0.00")

    @property
    def zichtbare_regels(self) -> list[WeekRegel]:
        """The rows of the day table: everything except the zero-minute blocks.

        A block of start == eind is a real row in the database and stays there —
        it is what the reconstruction found — but on screen it says that a stop
        or a ride happened and took no time, which tells a reader nothing while
        pushing the rows that do matter off the page.

        Display only, and deliberately *not* applied to `regels`: every total on
        this class is a sum over `regels`, and the aansluiting table derives its
        set of werkbon rows from them too. A zero-minute block adds nothing to
        any sum, but a W block of zero minutes still names a werkbon, and
        filtering it out of `regels` would make that werkbon's row disappear from
        "Aansluiting per werkbon" whenever no hours were booked on it either.
        Hiding a row must not remove a werkbon from the reconciliation.
        """
        return [regel for regel in self.regels if regel.blok.duur_minuten > 0]

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
    def prive_uren(self) -> Decimal:
        """Time at an address linked as P, in hours.

        Reported on its own, next to the comparison rather than inside it: it is
        not work, so it may not raise the booked-hours figure, and it is not a
        shortfall either, so subtracting it from anything would misstate the day
        (docs/decisions.md, 07-09-2026 avond).
        """
        return _naar_uren(
            sum(
                regel.blok.duur_minuten
                for regel in self.regels
                if regel.blok.soort == Soort.PRIVE
            )
        )

    @property
    def verschil(self) -> Decimal:
        """Booked minus on-location. Positive: more booked than driven to."""
        return self.gefactureerde_uren - self.uren_op_locatie

    def _minuten_per_werkbon(self) -> dict[str, int]:
        """Reconstructed minutes per werkbon on this day, from the W blocks."""
        per_werkbon: dict[str, int] = {}
        for regel in self.regels:
            if regel.blok.soort == Soort.WERKBON and regel.blok.werkbon:
                per_werkbon[regel.blok.werkbon] = (
                    per_werkbon.get(regel.blok.werkbon, 0) + regel.blok.duur_minuten
                )
        return per_werkbon

    @property
    def klant_minuten(self) -> int:
        return sum(
            regel.blok.duur_minuten
            for regel in self.regels
            if regel.blok.soort == Soort.KLANT
        )

    @property
    def aansluiting(self) -> list[AansluitingRegel]:
        """Per-werkbon reconciliation of this day: on site against declared.

        The day comparison above this table blends every werkbon into one pair of
        numbers, which cannot show that four hours were spent on werkbon A while
        the hours were booked on werkbon B — the discrepancy this app exists to
        find (docs/decisions.md, 07-09-2026).

        Every werkbon of the day gets a row, from either source: booked hours,
        reconstructed W blocks, or both. Rows are never dropped for reconciling,
        and above all never for having nothing on one side — a werkbon with hours
        but no W block at all is the loudest signal this table can give, and
        leaving it out would turn it into silence.

        Not to be confused with the volledigheidscontrole (docs/decisions.md,
        02-09-2026): that one asks, over a werkbon's whole life, whether a
        finished werkbon ever got hours. This asks, for one day, whether two
        sources that are both already present agree.
        """
        op_locatie = self._minuten_per_werkbon()
        gedeclareerd = self.gedeclareerd_per_werkbon

        werkbonnen = sorted(set(op_locatie) | {w for w in gedeclareerd if w})
        regels = [
            AansluitingRegel(
                label=werkbon,
                op_locatie=_naar_uren(op_locatie.get(werkbon, 0)),
                gedeclareerd=gedeclareerd.get(werkbon, Decimal("0.00")),
                klantnaam=self.klantnaam_per_werkbon.get(werkbon),
            )
            for werkbon in werkbonnen
        ]

        indirect = gedeclareerd.get("", Decimal("0.00"))
        if indirect:
            regels.append(
                AansluitingRegel(
                    label=INDIRECT_LABEL, op_locatie=None, gedeclareerd=indirect
                )
            )

        # Always shown, also at nil: this row is the answer to "was there client
        # time no werkbon accounts for", and an absent row reads as "no", which
        # is exactly the confusion the table is meant to remove.
        regels.append(
            AansluitingRegel(
                label=KLANT_LABEL,
                op_locatie=_naar_uren(self.klant_minuten),
                gedeclareerd=None,
            )
        )
        return regels

    @property
    def aansluiting_totaal(self) -> AansluitingRegel:
        """The day's bottom line: all time on site against everything declared.

        On site counts W and K together — K is client time too, it just carries
        no werkbon number. L (locatie) and C (crediteur) stay out: the question
        is about hours attached to a client (docs/decisions.md, 07-09-2026).

        The declared side is the day figure itself rather than the rows added up,
        so this total is the same number as the comparison directly above the
        table. Two totals differing by a rounding cent would cost more trust than
        the cent is worth.
        """
        minuten = sum(self._minuten_per_werkbon().values()) + self.klant_minuten
        return AansluitingRegel(
            label="Totaal",
            op_locatie=_naar_uren(minuten),
            gedeclareerd=self.gefactureerde_uren,
        )

    @property
    def heeft_aansluiting(self) -> bool:
        """Whether this day has anything to reconcile at all."""
        return any(
            regel.op_locatie or regel.gedeclareerd for regel in self.aansluiting
        )


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
    def prive_uren(self) -> Decimal:
        return sum((dag.prive_uren for dag in self.dagen), start=Decimal("0.00"))

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

    Every block is kept here, zero-minute ones included; which of them reach the
    day table is `DagOverzicht.zichtbare_regels`.
    """
    maandag = dt.date.fromisocalendar(jaar, week, 1)
    zondag = maandag + dt.timedelta(days=6)

    uren_per_dag = _geboekte_uren(monteur, maandag, zondag)
    uren_per_werkbon = _geboekte_uren_per_werkbon(monteur, maandag, zondag)
    klantnamen = _klantnaam_per_werkbon(monteur, maandag, zondag)

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
                gedeclareerd_per_werkbon=uren_per_werkbon.get(blok.datum, {}),
                klantnaam_per_werkbon=klantnamen.get(blok.datum, {}),
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


def _geboekte_uren_per_werkbon(
    monteur: Monteur, van: dt.date, tot: dt.date
) -> dict[dt.date, dict[str, Decimal]]:
    """Hours booked per date *and* werkbon — the declared side of the reconciliation.

    The same rows `_geboekte_uren` totals, only grouped one level finer. Rows
    without a werkbon number keep their empty key rather than being filtered out:
    they are real booked hours (Kantoor, Verlof, Reisuren, Magazijn onderhoud),
    and dropping them would leave the table's own total short of the day figure
    it sits under, with nothing on screen to explain the gap.
    """
    rijen = (
        Uren.objects.filter(
            medewerker=monteur.medewerker_nummer, datum__range=(van, tot)
        )
        .values("datum", "werkbon")
        .annotate(totaal=Sum("aantal"))
    )
    per_dag: dict[dt.date, dict[str, Decimal]] = {}
    for rij in rijen:
        # `aantal` is nullable, so a werkbon whose rows are all empty sums to
        # None; quantised for the same reason as in _geboekte_uren.
        per_dag.setdefault(rij["datum"], {})[rij["werkbon"]] = (
            rij["totaal"] or Decimal(0)
        ).quantize(Decimal("0.01"))
    return per_dag


def _klantnaam_per_werkbon(
    monteur: Monteur, van: dt.date, tot: dt.date
) -> dict[dt.date, dict[str, str]]:
    """The client name per date *and* werkbon, for the reconciliation table.

    Read from the same Uren rows the declared hours come from, so a name can
    only ever appear next to a werkbon that was actually booked on that date —
    the table's "absent is not zero" rule applied to text (docs/decisions.md,
    08-09-2026).

    Rows without a name are left out rather than stored as "": an empty string
    would occupy the slot and hide a name on a sibling row of the same werkbon.
    Should two rows of one (date, werkbon) disagree about the name, the first
    wins without complaint — this column is there to save Wim a lookup while he
    judges a difference, not to be a source of truth about who the client is.
    """
    rijen = (
        Uren.objects.filter(
            medewerker=monteur.medewerker_nummer, datum__range=(van, tot)
        )
        .exclude(project_opdrachtgever_naam="")
        .values("datum", "werkbon", "project_opdrachtgever_naam")
    )
    per_dag: dict[dt.date, dict[str, str]] = {}
    for rij in rijen:
        per_dag.setdefault(rij["datum"], {}).setdefault(
            rij["werkbon"], rij["project_opdrachtgever_naam"]
        )
    return per_dag


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
