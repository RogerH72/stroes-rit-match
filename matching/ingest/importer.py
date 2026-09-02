"""Importing one recognised source file into its raw table.

Phase 2 stores the sources 1-to-1 and nothing more — no matching, no timeline
reconstruction (roadmap phase 3).

Re-importing a file is a delete-and-insert of exactly the rows that came from
that file: every raw row carries a foreign key to its ImportedFile, so the tables
stay consistent whether a file is imported once or read again after a change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from matching.ingest.parsers import relaties, ritten, uren, werkbonnen
from matching.models import ImportedFile, Relatie, Rit, SourceKind, Uren, WerkbonControle

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Handler:
    """How one source kind is turned into rows."""

    model: type
    build_rows: object


HANDLERS: dict[str, Handler] = {
    SourceKind.UREN: Handler(Uren, uren.build_rows),
    SourceKind.RIT: Handler(Rit, ritten.build_rows),
    SourceKind.RELATIE: Handler(Relatie, relaties.build_rows),
    SourceKind.WERKBON_CONTROLE: Handler(WerkbonControle, werkbonnen.build_rows),
}


def import_file(imported_file: ImportedFile, path: Path) -> int:
    """Parse `path` into the raw table for its source kind and return the row count.

    The whole import is one transaction, so a file that fails halfway leaves no
    partial data behind and can simply be retried on the next run.
    """
    handler = HANDLERS[imported_file.source_kind]

    rows = handler.build_rows(path, imported_file)
    with transaction.atomic():
        deleted, _ = handler.model.objects.filter(source_file=imported_file).delete()
        if deleted:
            logger.info(
                "Replacing %s existing row(s) for %s.", deleted, imported_file.filename
            )
        handler.model.objects.bulk_create(rows, batch_size=500)

    logger.info(
        "Imported %s row(s) from %s into %s.",
        len(rows),
        imported_file.filename,
        handler.model._meta.verbose_name_plural,
    )
    return len(rows)
