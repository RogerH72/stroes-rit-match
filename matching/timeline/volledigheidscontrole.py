"""Werkbonnen without booked hours — the completeness check.

Deliberately not a model: it is a set difference over data that is already
stored, so there is nothing to persist and nothing that could go stale
(docs/database.md, "Geen aparte tabel, wel een berekening").

Two things were already decided and are simply used here rather than
re-derived:

* The check judges a werkbon *as a whole*, not per date — a werkbon can run
  across several days (Uitgevoerd on one, Gereed on the next), and "was this
  werkbon ever finished without hours ever being booked on it" is the question
  that matters (docs/functioneel-ontwerp.md §3b, 02-09-2026).
* Whether a werkbon is finished was resolved during the phase 2 import, per
  werkbon across all of its Fase rows, and stored as `fase_status`. A werkbon
  that never got past "nog niet gestart" is expected to have no hours and is
  not a signal.

A missing Werkbonnen.xlsx does not block anything: the check simply reports that
it did not run, while the matching itself carries on (docs/business-rules.md,
02-09-2026).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from matching.models import FaseStatus, Uren, WerkbonControle


@dataclass
class ControleResultaat:
    """Outcome of one completeness check."""

    uitgevoerd: bool
    werkbonnen: list[str]

    #: Reason the check did not run, empty when it did.
    reden: str = ""

    def __bool__(self) -> bool:
        """True when the check ran and found something to report."""
        return self.uitgevoerd and bool(self.werkbonnen)


def werkbonnen_zonder_uren(
    van: dt.date | None = None, tot: dt.date | None = None
) -> ControleResultaat:
    """Finished werkbonnen that have no booked hours at all.

    `van`/`tot` narrow down which werkbonnen are looked at (by the dates they
    appear on in Werkbonnen.xlsx); the hours are then checked without any date
    restriction, because hours may well be booked on a different date than the
    Fase transition.
    """
    controle = WerkbonControle.objects.all()
    if not controle.exists():
        return ControleResultaat(
            uitgevoerd=False,
            werkbonnen=[],
            reden="Werkbonnen.xlsx is niet ingelezen; controle niet uitgevoerd.",
        )

    if van is not None:
        controle = controle.filter(datum__gte=van)
    if tot is not None:
        controle = controle.filter(datum__lte=tot)

    afgerond = set(
        controle.filter(fase_status=FaseStatus.AFGEROND).values_list(
            "werkbon", flat=True
        )
    )
    met_uren = set(
        Uren.objects.filter(werkbon__in=afgerond).values_list("werkbon", flat=True)
    )
    return ControleResultaat(uitgevoerd=True, werkbonnen=sorted(afgerond - met_uren))
