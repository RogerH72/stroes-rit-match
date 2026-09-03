"""Running the matching over a selection of monteurs and dates.

The engine reconstructs one monteur-day; this decides which days to reconstruct
and what to do with days that already have a result.

Recomputing is always explicit. A stored Tijdblok is what phase 5 and 6 build
on, so a day that already has one is left alone unless `--force` is given, in
which case that day is deleted and inserted again — the same idempotent
delete-and-reinsert `check_imports --reprocess` uses for a re-imported file.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.db import transaction

from matching.models import Monteur, Rit, Tijdblok
from matching.timeline.engine import (
    DagTijdlijn,
    Koppeltabellen,
    build_day,
    home_streets_for,
)
from matching.timeline.meegereden import bron_bestuurder_codes, resolve_bronmonteur


@dataclass
class MatchResult:
    """What one run did, for the command output."""

    dry_run: bool = False
    dagen: list[DagTijdlijn] = field(default_factory=list)
    overgeslagen: list[tuple[Monteur, dt.date]] = field(default_factory=list)
    zonder_ritten: list[Monteur] = field(default_factory=list)

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
    """
    result = MatchResult(dry_run=dry_run)
    koppeltabellen = Koppeltabellen.load()
    # Home streets are a property of the driver, not of the day, so they are
    # detected once per bronmonteur instead of per day.
    home_streets_cache: dict[int, set[str]] = {}

    for monteur in _selected_monteurs(medewerker_nummer):
        dagen = _dates_for(monteur, van, tot)
        if not dagen:
            result.zonder_ritten.append(monteur)
            continue

        for datum in dagen:
            bronmonteur = resolve_bronmonteur(monteur, datum)
            if bronmonteur.pk not in home_streets_cache:
                home_streets_cache[bronmonteur.pk] = home_streets_for(bronmonteur)

            tijdlijn = build_day(
                monteur,
                datum,
                koppeltabellen=koppeltabellen,
                home_streets=home_streets_cache[bronmonteur.pk],
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
            result.dagen.append(tijdlijn)

    return result


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
