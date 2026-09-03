"""The screens outside the Django admin.

The beheerschermen (koppeltabellen, tolerantietabel, matchmotor-status) are
Django-admin screens by contract (GUIDELINES.md, "Technology stack"). The
uitzonderingenscherm is not: SBTT staff will use it often, so it is part of the
web application itself, with its own simple style (docs/decisions.md,
2026-09-03).

Authentication reuses the admin's session login — there is no separate front-end
login in this app, and staff are already signed in there when they come from the
matchmotor-status page.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter
from dataclasses import dataclass, field

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

from matching.forms import KoppelLocatieForm
from matching.models import LocatieType, Soort, Tijdblok
from matching.timeline.runner import run_matching_and_record_status

#: Where an anonymous visitor is sent; the admin owns the only login page.
LOGIN_URL = "/admin/login/"


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
        if blok.postcode:
            sleutel = (LocatieType.POSTCODE, blok.postcode)
        elif blok.straat:
            sleutel = (LocatieType.STRAAT, blok.straat)
        else:
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


@login_required(login_url=LOGIN_URL)
def uitzonderingen(request):
    """The list of unexplained addresses, most frequent first."""
    return render(
        request,
        "matching/uitzonderingen.html",
        {"groepen": _onverklaarde_groepen()},
    )


# The permission gate covers the GET as well as the POST: a user who may not
# create a BekendeLocatie has no use for a form he cannot submit. It is Django's
# own model permission, the same one the admin checks when adding that row by
# hand — this screen deliberately has no rights system of its own
# (docs/decisions.md, 2026-09-03).
@login_required(login_url=LOGIN_URL)
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
        form = KoppelLocatieForm(initial=_beginwaarden(groep))

    return render(request, "matching/koppelen.html", {"groep": groep, "form": form})


def _beginwaarden(groep: Uitzondering) -> dict[str, str]:
    """Pre-fill: the precision the group itself represents, and its own value."""
    return {"type": groep.precisie, "waarde": groep.sleutel}


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
