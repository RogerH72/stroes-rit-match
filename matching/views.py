"""The screens outside the Django admin.

The beheerschermen (koppeltabellen, tolerantietabel, matchmotor-status) are
Django-admin screens by contract (GUIDELINES.md, "Technology stack"). The
uitzonderingenscherm (phase 5) and the weekoverzicht (phase 6) are not: SBTT
staff will use them often, so they are part of the web application itself, with
their own simple style (docs/decisions.md, 2026-09-03).

Authentication reuses the admin's session login — there is no separate front-end
login in this app, and staff are already signed in there when they come from the
matchmotor-status page. Where that login page lives is settings.LOGIN_URL, so a
bare @login_required is enough here; the ?next= it appends is what brings the
user back to the screen he asked for instead of into the admin.

The week assembly itself lives in matching/weekoverzicht.py; the views here only
resolve which monteur and which week were asked for, and hand the result to a
template or to the Excel writer.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass, field

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from matching import weekoverzicht as week
from matching.forms import KoppelLocatieForm
from matching.models import LocatieType, Monteur, Relatie, Soort, Tijdblok
from matching.timeline import normalize
from matching.timeline.runner import run_matching_and_record_status
from matching.weekoverzicht_excel import bestandsnaam, bouw_werkboek


def health(request):
    """Liveness endpoint, used by the container healthcheck."""
    return JsonResponse({"status": "ok"})


# --- the uitzonderingenscherm -----------------------------------------------


@dataclass
class Uitzondering:
    """All unexplained stops at one address, as one row of the list.

    One row per address rather than per stop, because one koppeling resolves
    every stop at that address at once — now and after every later re-run. That
    is the "de lijst wordt vanzelf korter" effect the customer explainer
    describes (docs/decisions.md, 2026-09-03).
    """

    #: Which of the two keys this group was formed on (a LocatieType value).
    precisie: str
    #: The value of that key — what the URL of the confirm form addresses.
    sleutel: str
    postcode: str = ""
    straat: str = ""
    aantal: int = 0
    monteurs: list[str] = field(default_factory=list)
    datums: list[dt.date] = field(default_factory=list)

    @property
    def adres(self) -> str:
        """Postcode and street together when both are known, else whichever is."""
        return " · ".join(deel for deel in (self.postcode, self.straat) if deel)


def _onverklaarde_groepen() -> list[Uitzondering]:
    """Every onverklaarde stop, grouped by address, most frequent first.

    Grouping is postcode-first and falls back to the street: the postcode is the
    more precise key and RouteVision supplies one for nearly every stop, so
    grouping on the street would needlessly merge two different addresses in the
    same street into one row. The street is the fallback for the stops where
    RouteVision left the place empty.

    An O row is by definition not linked to a BekendeLocatie yet — that is what
    ONVERKLAARD means in `_classify_stop` — so there is no "already linked"
    filter to apply: every O row belongs in this list.

    Rows with neither key are skipped, because there is nothing to link them to.
    In practice those only exist in a database that has not been reprocessed
    since the two fields were added (`run_matching --force`).

    The key itself comes from `Tijdblok.koppelsleutel`, which the weekoverzicht
    (phase 6) uses too, so a link from there always lands on the group shown
    here.
    """
    groepen: dict[tuple[str, str], Uitzondering] = {}
    # A Counter per group rather than one street on the group: rows sharing a
    # postcode can carry slightly different street spellings, and the confirm
    # form offers the most common one when the user switches to street precision.
    straten: dict[tuple[str, str], Counter] = {}

    blokken = (
        Tijdblok.objects.filter(soort=Soort.ONVERKLAARD)
        .select_related("monteur")
        .order_by("datum", "monteur__naam", "volgorde")
    )
    for blok in blokken:
        sleutel = blok.koppelsleutel
        if sleutel is None:
            continue

        groep = groepen.get(sleutel)
        if groep is None:
            groep = groepen[sleutel] = Uitzondering(
                precisie=sleutel[0], sleutel=sleutel[1], postcode=blok.postcode
            )
            straten[sleutel] = Counter()

        groep.aantal += 1
        if blok.straat:
            straten[sleutel][blok.straat] += 1
        if blok.monteur.naam not in groep.monteurs:
            groep.monteurs.append(blok.monteur.naam)
        if blok.datum not in groep.datums:
            groep.datums.append(blok.datum)

    for sleutel, groep in groepen.items():
        meest_voorkomend = straten[sleutel].most_common(1)
        groep.straat = meest_voorkomend[0][0] if meest_voorkomend else ""

    # Most-recurring first: that is the address worth explaining once, because
    # linking it removes the most rows from this list.
    return sorted(groepen.values(), key=lambda groep: (-groep.aantal, groep.adres))


def _groep_of_404(precisie: str, waarde: str) -> Uitzondering:
    """The group the confirm form is about, or 404 when it no longer exists.

    Looked up through the same grouping the list uses, so the form can never
    describe a group differently from the row it was opened from. A group that
    has disappeared (someone else linked the address in the meantime) is a real
    404: there is nothing left to confirm.
    """
    for groep in _onverklaarde_groepen():
        if groep.precisie == precisie and groep.sleutel == waarde:
            return groep
    raise Http404("Deze onverklaarde stop staat niet meer in de lijst.")


@login_required
def uitzonderingen(request):
    """The list of unexplained addresses, most frequent first."""
    return render(
        request,
        "matching/uitzonderingen.html",
        {"groepen": _onverklaarde_groepen(), "scherm": "uitzonderingen"},
    )


# The permission gate covers the GET as well as the POST: a user who may not
# create a BekendeLocatie has no use for a form he cannot submit. It is Django's
# own model permission, the same one the admin checks when adding that row by
# hand — this screen deliberately has no rights system of its own
# (docs/decisions.md, 2026-09-03).
@login_required
@permission_required("matching.add_bekendelocatie", raise_exception=True)
def uitzonderingen_koppelen(request, precisie: str, waarde: str):
    """Turn one unexplained address into a BekendeLocatie, then recompute."""
    if precisie not in LocatieType.values:
        raise Http404("Onbekende herkenning.")
    groep = _groep_of_404(precisie, waarde)

    if request.method == "POST":
        form = KoppelLocatieForm(request.POST)
        if form.is_valid():
            return _koppel_en_herbereken(request, form)
    else:
        form = KoppelLocatieForm(initial=_beginwaarden(groep, request))

    suggesties = _relatie_suggesties(groep.postcode) if groep.postcode else []
    return render(
        request,
        "matching/koppelen.html",
        {
            "groep": groep,
            "form": form,
            # Only worth showing when there is a choice to make: a single
            # candidate has already filled the form in, and listing it would ask
            # the user to pick what is on screen anyway.
            "suggesties": suggesties if len(suggesties) > 1 else [],
            "gekozen_suggestie": request.GET.get("suggestie", ""),
        },
    )


@dataclass
class RelatieSuggestie:
    """One Relatie row that matches a group's postcode, as a suggestion."""

    code: str
    relatienaam: str
    #: A Soort value, already translated — never Relatie's own K/L letter.
    soort: str
    label: str


#: Relatie's letters translated into SOORT-codes. The two alphabets look alike
#: and are not: Relatie "L" is a Leverancier, which this domain books as a
#: Crediteur (SOORT "C"). SOORT's own "L" means Locatie, so copying the letter
#: across would quietly file every supplier as something else
#: (docs/decisions.md, 08-09-2026).
_KLANT_OF_LEVERANCIER_NAAR_SOORT = {
    "K": Soort.KLANT,
    "L": Soort.CREDITEUR,
}


def _relatie_suggesties(postcode: str) -> list[RelatieSuggestie]:
    """The Relatie rows on this postcode, with their letter already translated.

    Rows whose klant_of_leverancier is empty or unrecognised are skipped: a
    suggestion without a SOORT is not a suggestion, and guessing one from the
    name would be the automatic classification this was deliberately not made
    (docs/decisions.md, 08-09-2026).

    Compared through `normalize.postcode` on both sides because Relatie.postcode
    is raw Excel text — unlike BekendeLocatie.waarde, it is not normalised on
    save, so "4104 AC" and "4104AC" are the same address in two spellings. That
    also means the filtering happens in Python rather than in the query; the
    relatietabel is a few thousand rows of master data, not a row per stop, so
    that is cheap enough to leave until it measurably is not.
    """
    doel = normalize.postcode(postcode)
    if not doel:
        return []

    suggesties: list[RelatieSuggestie] = []
    gezien = set()
    for relatie in Relatie.objects.exclude(postcode="").exclude(
        klant_of_leverancier=""
    ):
        if normalize.postcode(relatie.postcode) != doel:
            continue
        soort = _KLANT_OF_LEVERANCIER_NAAR_SOORT.get(relatie.klant_of_leverancier)
        if soort is None:
            continue
        # One suggestion per (name, soort): the same relation can occupy several
        # rows of the file (one per contact person), and offering the same name
        # three times would look like three different candidates.
        sleutel = (relatie.relatienaam, soort)
        if sleutel in gezien:
            continue
        gezien.add(sleutel)
        suggesties.append(
            RelatieSuggestie(
                code=relatie.code,
                relatienaam=relatie.relatienaam,
                soort=soort,
                label=relatie.relatienaam,
            )
        )
    return suggesties


def _beginwaarden(groep: Uitzondering, request) -> dict[str, str]:
    """Pre-fill: the group's own precision and value, plus a Relatie suggestion.

    The suggestion only ever fills in soort and label — type and waarde keep
    coming from the group itself, since those say which address is being linked
    and no relation gets to change that.

    Nothing is saved here: the user still confirms by pressing "Koppelen", the
    same as for a hand-typed koppeling (suggest-then-confirm, docs/decisions.md
    08-09-2026). With several candidates nothing is pre-filled until the user
    picks one from the list, because filling in one of several would look like an
    answer rather than a guess.

    Gated on `groep.postcode` rather than on the group's precision: a group keyed
    on street still carries the postcode of its stops when RouteVision supplied
    one, and that postcode is just as matchable.
    """
    beginwaarden = {"type": groep.precisie, "waarde": groep.sleutel}

    suggesties = _relatie_suggesties(groep.postcode) if groep.postcode else []
    if len(suggesties) == 1:
        gekozen = suggesties[0]
    elif len(suggesties) > 1:
        gekozen = next(
            (s for s in suggesties if s.code == request.GET.get("suggestie")),
            None,
        )
    else:
        gekozen = None

    if gekozen is not None:
        beginwaarden["soort"] = gekozen.soort
        beginwaarden["label"] = gekozen.label

    return beginwaarden


def _koppel_en_herbereken(request, form: KoppelLocatieForm):
    """Save the location and re-run the matching, then report on the list.

    The re-run is synchronous, exactly like the admin's "matching nu draaien"
    button: this app has no task queue, and one client's data takes well under a
    second, so waiting and then saying what happened is more honest than adding
    infrastructure to hide a wait that barely exists.
    """
    locatie = form.save()
    try:
        result = run_matching_and_record_status(force=True)
    except Exception as exc:
        # The status row already recorded the failure. The location itself was
        # saved, so the next run still picks it up; only the list on screen is
        # not up to date yet.
        messages.error(
            request,
            f"'{locatie.label}' is gekoppeld, maar de matching is mislukt: {exc}",
        )
    else:
        messages.success(
            request,
            f"'{locatie.label}' gekoppeld aan {locatie.waarde}. "
            f"Matching afgerond: {len(result.dagen)} dag(en) herberekend, "
            f"{result.aantal_blokken} tijdblok(ken).",
        )
    return redirect("uitzonderingen")


# --- het weekoverzicht ------------------------------------------------------


@dataclass
class Weekkeuze:
    """Which monteur and which week the page is showing, plus the alternatives."""

    monteur: Monteur
    jaar: int
    week: int
    #: What the dropdown offers.
    monteurs: list[Monteur] = field(default_factory=list)


@login_required
def weekoverzicht(request):
    """One monteur's week: the reconstructed days, per SOORT and in total."""
    keuze = _weekkeuze(request)
    if keuze is None:
        # No monteurs at all: an empty dropdown with an empty table underneath
        # would leave the user guessing, so say what is missing instead.
        return render(
            request,
            "matching/weekoverzicht.html",
            {"overzicht": None, "scherm": "weekoverzicht"},
        )

    overzicht = week.bouw_weekoverzicht(keuze.monteur, keuze.jaar, keuze.week)
    return render(
        request,
        "matching/weekoverzicht.html",
        {
            "overzicht": overzicht,
            "monteurs": keuze.monteurs,
            "scherm": "weekoverzicht",
        },
    )


@login_required
def weekoverzicht_excel(request):
    """The same week as an .xlsx, with the same SOORT colours as the page."""
    keuze = _weekkeuze(request)
    if keuze is None:
        raise Http404("Er zijn nog geen monteurs ingericht.")

    overzicht = week.bouw_weekoverzicht(keuze.monteur, keuze.jaar, keuze.week)
    antwoord = HttpResponse(
        bouw_werkboek(overzicht),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    antwoord["Content-Disposition"] = (
        f'attachment; filename="{bestandsnaam(overzicht)}"'
    )
    return antwoord


def _weekkeuze(request) -> Weekkeuze | None:
    """Read `?monteur=<id>&week=<jaar>-W<nr>`; None when there is no monteur yet.

    A parameter that is absent falls back to a sensible default, because a bare
    /weekoverzicht/ is what the root URL and the navigation link both open, and
    that must never be an empty screen: the first active monteur alphabetically,
    and his most recent processed week (not the current week — see
    `week.laatste_week_met_data`). A parameter that is *present but wrong* is a
    404 rather than a silent fallback: showing week 30 under a URL that says
    week 99 is the kind of thing someone screenshots and then acts on.
    """
    # order_by is explicit rather than left to Monteur.Meta, because "the first
    # one alphabetically" is the defined default of this screen and should not
    # change along with the model's default ordering.
    monteurs = list(Monteur.objects.filter(actief=True).order_by("naam"))

    gevraagd = request.GET.get("monteur")
    if gevraagd:
        monteur = Monteur.objects.filter(pk=_als_getal(gevraagd)).first()
        if monteur is None:
            raise Http404("Onbekende monteur.")
        if monteur not in monteurs:
            # An inactive monteur is still viewable — his past weeks did happen
            # — so he is added to the dropdown for as long as he is selected.
            monteurs = sorted(monteurs + [monteur], key=lambda m: m.naam)
    elif monteurs:
        monteur = monteurs[0]
    else:
        return None

    gevraagde_week = request.GET.get("week")
    if gevraagde_week:
        gekozen = week.parse_week(gevraagde_week)
        if gekozen is None:
            raise Http404("Onbekende week.")
    else:
        gekozen = week.laatste_week_met_data(monteur)

    return Weekkeuze(
        monteur=monteur, jaar=gekozen[0], week=gekozen[1], monteurs=monteurs
    )


def _als_getal(waarde: str) -> int | None:
    """The primary key from the URL, or None when it is not a number at all."""
    return int(waarde) if waarde.isdigit() else None
