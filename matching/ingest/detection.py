"""Detecting and processing the source files on the server share.

One pass over the share, executed by the `check_imports` management command on a
fixed interval (see scripts/scheduler.sh). Polling, not filesystem events: the
share is an SMB network mount, where event-based watching is unreliable
(docs/architecture.md).

Every recognised file is tracked independently in its own ImportedFile row, so a
missing or still-growing Werkbonnen.xlsx never holds up Uren.xlsx or the
RouteVision CSV (docs/functioneel-ontwerp.md §3a).

Files on the share are only ever read: nothing is moved, renamed or deleted, and
there is no "processed" folder — the database alone records what has been done.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from matching.ingest.filenames import classify_filename
from matching.ingest.importer import import_file
from matching.ingest.stability import (
    Measurement,
    is_stable,
    next_measurement,
    required_consecutive_polls,
)
from matching.models import ImportedFile, ImportStatus

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """What one pass over the share did, for logging and command output."""

    required_consecutive: int
    seen: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    waiting: list[str] = field(default_factory=list)
    imported: dict[str, int] = field(default_factory=dict)
    failed: dict[str, str] = field(default_factory=dict)
    skipped_processed: list[str] = field(default_factory=list)


def required_polls() -> int:
    """The configured stability margin expressed in consecutive measurements."""
    return required_consecutive_polls(
        settings.STABILITY_MINUTES, settings.POLL_INTERVAL_MINUTES
    )


def scan_share(
    *,
    path: Path | None = None,
    force: bool = False,
    reprocess: bool = False,
    dry_run: bool = False,
) -> ScanResult:
    """Measure every recognised file on the share and import the ones that are ready.

    force
        Import a stable-or-not file immediately, for development and for a manual
        run that should not wait out the stability margin.
    reprocess
        Also re-import files already marked verwerkt. Manual only — the scheduled
        run never reprocesses anything by itself (docs/architecture.md).
    dry_run
        Measure and report, but write nothing.
    """
    share = Path(path) if path is not None else Path(settings.SERVERMAP_PATH)
    result = ScanResult(required_consecutive=required_polls())

    if not share.is_dir():
        logger.warning("Server share %s is not available; nothing to check.", share)
        return result

    logger.info(
        "Checking %s (stability: %s unchanged measurement(s), %s min / %s min poll).",
        share,
        result.required_consecutive,
        settings.STABILITY_MINUTES,
        settings.POLL_INTERVAL_MINUTES,
    )

    for entry in sorted(share.iterdir()):
        if not entry.is_file():
            continue

        source_kind = classify_filename(entry.name)
        if source_kind is None:
            result.ignored.append(entry.name)
            continue

        result.seen.append(entry.name)
        _handle_file(entry, source_kind, result, force, reprocess, dry_run)

    return result


def _handle_file(
    entry: Path,
    source_kind: str,
    result: ScanResult,
    force: bool,
    reprocess: bool,
    dry_run: bool,
) -> None:
    """Measure one file, update its bookkeeping row, and import it when ready."""
    try:
        size = entry.stat().st_size
    except OSError as error:
        # A file being rewritten on a network share can vanish between listing
        # and stat; the next poll picks it up again.
        logger.warning("Could not read %s: %s", entry.name, error)
        result.failed[entry.name] = str(error)
        return

    now = timezone.now()
    record = ImportedFile.objects.filter(filename=entry.name).first()
    previous = (
        Measurement(record.size_bytes, record.unchanged_polls, record.last_measured_at)
        if record is not None
        else None
    )
    current = next_measurement(previous, size, now)
    stable = force or is_stable(previous, current, result.required_consecutive)

    if record is None:
        record = ImportedFile(filename=entry.name, source_kind=source_kind)

    already_processed = record.status == ImportStatus.VERWERKT

    # A processed file whose size changed is reported but never re-read on its
    # own: reprocessing is a manual action only (docs/architecture.md).
    if already_processed and previous is not None and previous.size != size:
        logger.warning(
            "%s changed after being processed (%s -> %s bytes); "
            "not reprocessed automatically.",
            entry.name,
            previous.size,
            size,
        )

    record.source_kind = source_kind
    record.size_bytes = current.size
    record.unchanged_polls = current.unchanged_polls
    record.last_measured_at = now
    if not already_processed:
        record.status = ImportStatus.STABIEL if stable else ImportStatus.WACHTEND

    if already_processed and not reprocess:
        result.skipped_processed.append(entry.name)
        if not dry_run:
            record.save()
        return

    if not stable:
        result.waiting.append(entry.name)
        logger.info(
            "%s not stable yet (%s/%s unchanged measurement(s) at %s bytes).",
            entry.name,
            current.unchanged_polls,
            result.required_consecutive,
            size,
        )
        if not dry_run:
            record.save()
        return

    if dry_run:
        result.imported[entry.name] = 0
        logger.info("%s would be imported (dry run).", entry.name)
        return

    record.save()
    try:
        row_count = import_file(record, entry)
    except Exception as error:  # noqa: BLE001 - one bad file must not stop the rest
        # Status stays "stabiel" with the error recorded, so the next scheduled
        # run retries this file while the other sources carry on.
        logger.exception("Importing %s failed.", entry.name)
        record.last_error = str(error)
        record.save(update_fields=["last_error"])
        result.failed[entry.name] = str(error)
        return

    record.status = ImportStatus.VERWERKT
    record.processed_at = timezone.now()
    record.row_count = row_count
    record.last_error = ""
    record.save(update_fields=["status", "processed_at", "row_count", "last_error"])
    result.imported[entry.name] = row_count
