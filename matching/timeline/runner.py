"""Running the matching over a selection of monteurs and dates.

The engine reconstructs one monteur-day; this decides which days to reconstruct
and what to do with days that already have a result.

Recomputing is always explicit. A stored Tijdblok is what phase 5 and 6 build
on, so a day that already has one is left alone unless `--force` is given, in
which case that day is deleted and inserted again — the same idempotent
delete-and-reinsert `check_imports --reprocess` uses for a re-imported file.

A forced run also clears days that no longer produce a result at all, which
delete-and-reinsert per rebuilt day cannot do: a junior whose meegereden-
koppeling was removed, or a day whose rides disappeared in a corrected import,
is simply never visited again and would keep its now-void blocks forever while
the run reports success. See `_verwijder_vervallen()` for how that stays inside
the selection the run was asked for.

Callers should use `run_matching_and_record_status()` rather than
`run_matching()` directly, so the MatchmotorStatus row the admin shows keeps up
with reality.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from matching.models import MatchmotorStatus, Monteur, Rit, Tijdblok
from matching.timeline.engine import (
    DagTijdlijn,
    Koppeltabellen,
    build_day,
)
from matching.timeline.meegereden import bron_bestuurder_codes, resolve_bronmonteur


@dataclass
class MatchResult:
    """What one run did, for the command output."""

    dry_run: bool = False
    dagen: list[DagTijdlijn] = field(default_factory=list)
    overgeslagen: list[tuple[Monteur, dt.date]] = field(default_factory=list)
    zonder_ritten: list[Monteur] = field(default_factory=list)
    #: Days that had a stored result but no longer produce one, cleared by a
    #: forced run (or, on a dry run, only reported).
    opgeruimd: list[tuple[Monteur, dt.date]] = field(default_factory=list)

    @property
    def aantal_blokken(self) -> int:
        return sum(len(dag.blokken) for dag in self.dagen)


def run_matching(
    *,
    medewerker_nummer: str | None = None,
    van: dt.date | None = None,
    tot: dt.date | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> MatchResult:
    """Reconstruct every selected monteur-day.

    Without `medewerker_nummer` every active monteur is processed; without
    `van`/`tot` every date that has ride data for him — including dates he only
    has through a meegereden-koppeling, since those are days he worked too.

    With `force` the run owns the whole selection rather than only the days it
    happens to rebuild: what it does not rebuild, it clears.
    """
    result = MatchResult(dry_run=dry_run)
    koppeltabellen = Koppeltabellen.load()

    for monteur in _selected_monteurs(medewerker_nummer):
        dagen = _dates_for(monteur, van, tot)
        if not dagen:
            result.zonder_ritten.append(monteur)

        herbouwd: set[dt.date] = set()
        for datum in dagen:
            bronmonteur = resolve_bronmonteur(monteur, datum)
            tijdlijn = build_day(
                monteur,
                datum,
                koppeltabellen=koppeltabellen,
                bronmonteur=bronmonteur,
            )
            if tijdlijn is None:
                continue

            bestaand = Tijdblok.objects.filter(monteur=monteur, datum=datum)
            if bestaand.exists() and not force:
                result.overgeslagen.append((monteur, datum))
                continue

            if not dry_run:
                _store(tijdlijn)
            herbouwd.add(datum)
            result.dagen.append(tijdlijn)

        if force:
            for datum in _verwijder_vervallen(
                monteur, van, tot, herbouwd, dry_run=dry_run
            ):
                result.opgeruimd.append((monteur, datum))

    return result


def run_matching_and_record_status(**kwargs) -> MatchResult:
    """run_matching(), recording the outcome on the MatchmotorStatus singleton.

    Both trigger paths — the `run_matching` command and the admin's "matching nu
    draaien" button — go through here rather than calling `run_matching()`
    directly. The matching is never scheduled, so "when did this last run and did
    it work" has no other source of truth; having one wrapper own that
    bookkeeping keeps the two paths from drifting apart.

    A failed run is recorded and then re-raised: the caller still sees the
    exception (the command still fails loudly, the admin still shows the error),
    it is only no longer invisible afterwards.

    A dry run is not recorded at all. It writes no Tijdblok rows, so calling it
    "de laatste run" would make the status claim work that never happened.
    """
    if kwargs.get("dry_run"):
        return run_matching(**kwargs)

    status = MatchmotorStatus.load()
    # Stamped before the work starts, so a run that dies halfway still leaves
    # evidence that it was attempted.
    status.laatste_run_gestart_op = timezone.now()
    status.save()

    try:
        result = run_matching(**kwargs)
    except Exception as exc:
        status.laatste_run_afgerond_op = timezone.now()
        status.succes = False
        status.foutmelding = str(exc)
        status.save()
        raise

    status.laatste_run_afgerond_op = timezone.now()
    status.succes = True
    status.dagen_verwerkt = len(result.dagen)
    status.foutmelding = ""
    status.save()
    return result


def _verwijder_vervallen(
    monteur: Monteur,
    van: dt.date | None,
    tot: dt.date | None,
    herbouwd: set[dt.date],
    *,
    dry_run: bool,
) -> list[dt.date]:
    """Clear this monteur's stored days that the run did not rebuild.

    `_store()` can only refresh a day that was rebuilt, and a day is only
    rebuilt when there is still ride data behind it. So the days that go *away*
    — the junior who was uncoupled from his senior, the day whose rides a
    corrected import removed — are exactly the ones nothing else touches. They
    are deleted here instead.

    The selection is the boundary, deliberately expressed with the same monteur
    and the same `van`/`tot` the run was given: a run for one monteur never
    reaches another, and a run over a date range never reaches a day outside it.
    An unbounded run does clear everything stale, which is what asking to
    recompute everything means.
    """
    blokken = Tijdblok.objects.filter(monteur=monteur)
    if van is not None:
        blokken = blokken.filter(datum__gte=van)
    if tot is not None:
        blokken = blokken.filter(datum__lte=tot)

    vervallen = sorted(set(blokken.values_list("datum", flat=True)) - herbouwd)
    if vervallen and not dry_run:
        blokken.filter(datum__in=vervallen).delete()
    return vervallen


@transaction.atomic
def _store(tijdlijn: DagTijdlijn) -> None:
    """Replace one monteur-day with its freshly computed blocks."""
    Tijdblok.objects.filter(
        monteur=tijdlijn.monteur, datum=tijdlijn.datum
    ).delete()
    Tijdblok.objects.bulk_create(tijdlijn.blokken)


def _selected_monteurs(medewerker_nummer: str | None) -> list[Monteur]:
    monteurs = Monteur.objects.select_related("vaste_meerijder")
    if medewerker_nummer:
        return list(monteurs.filter(medewerker_nummer=medewerker_nummer))
    return list(monteurs.filter(actief=True))


def _dates_for(
    monteur: Monteur, van: dt.date | None, tot: dt.date | None
) -> list[dt.date]:
    """Every date worth reconstructing for this monteur.

    Taken from the ride data of every driver code that could supply his day: his
    own, and those of the seniors he rides along with. Which of them actually
    applies on a given date is decided per day by `resolve_bronmonteur`.
    """
    codes = bron_bestuurder_codes(monteur)
    if not codes:
        return []

    ritten = Rit.objects.filter(bestuurder__in=codes, vertrekdatum__isnull=False)
    if van is not None:
        ritten = ritten.filter(vertrekdatum__gte=van)
    if tot is not None:
        ritten = ritten.filter(vertrekdatum__lte=tot)
    return sorted(set(ritten.values_list("vertrekdatum", flat=True)))
