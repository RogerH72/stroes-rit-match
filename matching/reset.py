"""Deliberately clearing imported and computed data.

The raw import tables and the timeline are read-only in the admin, deletion
included (docs/decisions.md, 03-09-2026 plus the 07-09-2026 addendum). That is
right for day-to-day use, but it left no way at all to make a clean slate —
needed when testing, and when a period was imported wrongly and has to go before
it is read in again. This module is that way: two narrow, named resets instead of
row-by-row selecting, which the generic admin action could not do anyway (over a
thousand rows exceeds DATA_UPLOAD_MAX_NUMBER_FIELDS, see docs/changelog.md,
07-09-2026).

Counting and deleting run off the same querysets on purpose, so the preview a
user confirms is built by the same code that then does the deleting — a preview
assembled separately would be free to drift from it.

Nothing here reimports or recomputes. That stays a separate, deliberate step, the
same way "Matching nu draaien" is (docs/decisions.md, 07-09-2026).
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from django.db import models, transaction

from matching.models import (
    ImportedFile,
    Relatie,
    Rit,
    Tijdblok,
    Uren,
    WerkbonControle,
)

logger = logging.getLogger(__name__)

# Delete order: from the computed end back towards the source. Uren, Rit,
# Relatie and WerkbonControle hang off ImportedFile with on_delete=CASCADE, so
# emptying them before it keeps every table's reported count its own rather than
# a cascade someone else triggered.
VOLLEDIG_MODELLEN: tuple[type[models.Model], ...] = (
    Tijdblok,
    Uren,
    Rit,
    Relatie,
    WerkbonControle,
    ImportedFile,
)

# {model: the field that says which day a row belongs to}, in the same delete
# order. Two of the six tables are deliberately absent:
#
# - Relatie is customer/supplier master data with no date at all.
# - ImportedFile is bookkeeping per *file*, not per period. Clearing it for a
#   period would quietly forget that a source file had been processed, and
#   re-reading a file has to stay the explicit `check_imports --reprocess` step
#   (docs/decisions.md, 01-09-2026 on the trigger mechanism).
PERIODE_VELDEN: dict[type[models.Model], str] = {
    Tijdblok: "datum",
    Uren: "datum",
    # A ride belongs to the day it left on — the same field the matching itself
    # groups and filters on (matching/timeline/runner.py). It is nullable, and a
    # range filter drops those rows, which is what we want: a ride without a
    # departure date is in no period.
    Rit: "vertrekdatum",
    WerkbonControle: "datum",
}


@dataclass(frozen=True)
class ResetTelling:
    """How many rows a reset covers, per table.

    Used for both halves of the flow: what a preview promises to delete, and what
    a finished reset actually deleted.
    """

    per_model: dict[type[models.Model], int]

    @property
    def totaal(self) -> int:
        return sum(self.per_model.values())

    def regels(self) -> list[tuple[str, int]]:
        """(table name, count) pairs for the screen, in delete order."""
        return [
            (model._meta.verbose_name_plural, aantal)
            for model, aantal in self.per_model.items()
        ]

    def samenvatting(self) -> str:
        """One line naming only the tables that actually had rows."""
        gevuld = [f"{aantal} {naam}" for naam, aantal in self.regels() if aantal]
        return ", ".join(gevuld) if gevuld else "niets"


def volledige_selectie() -> dict[type[models.Model], models.QuerySet]:
    """Everything in the six import/matching tables."""
    return {model: model.objects.all() for model in VOLLEDIG_MODELLEN}


def periode_selectie(
    van: dt.date, tot: dt.date
) -> dict[type[models.Model], models.QuerySet]:
    """The four dated tables, limited to `van` up to and including `tot`."""
    return {
        model: model.objects.filter(**{f"{veld}__gte": van, f"{veld}__lte": tot})
        for model, veld in PERIODE_VELDEN.items()
    }


def tel(selectie: dict[type[models.Model], models.QuerySet]) -> ResetTelling:
    """Count what a selection covers, without touching anything."""
    return ResetTelling({model: qs.count() for model, qs in selectie.items()})


def verwijder(selectie: dict[type[models.Model], models.QuerySet]) -> ResetTelling:
    """Delete a selection in one transaction, and report what went.

    All or nothing: a reset that fails halfway would leave the database in a
    state no source file describes — Tijdblokken pointing at a period whose
    Urenregels are gone, say — and the way out of that is not obvious to whoever
    is looking at the screen.

    The counts come from what `delete()` reports rather than from a count taken
    beforehand, so the number shown afterwards is what the database really lost.
    """
    verwijderd: dict[type[models.Model], int] = {model: 0 for model in selectie}
    per_label = {model._meta.label: model for model in selectie}

    with transaction.atomic():
        for model, qs in selectie.items():
            _, details = qs.delete()
            for label, aantal in details.items():
                # Anything cascaded into another table we are resetting counts
                # towards that table, not this one.
                doel = per_label.get(label)
                if doel is not None:
                    verwijderd[doel] += aantal
                elif aantal:
                    # Should not happen: these six tables cascade only into each
                    # other. Worth a log line rather than a silent surprise.
                    logger.warning(
                        "Reset of %s also removed %s row(s) from %s.",
                        model._meta.label,
                        aantal,
                        label,
                    )

    telling = ResetTelling(verwijderd)
    logger.info("Data reset removed: %s.", telling.samenvatting())
    return telling
