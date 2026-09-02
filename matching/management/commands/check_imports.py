"""Check the server share for new source files and import the ones that are ready.

Called by the scheduler inside the container every POLL_INTERVAL_MINUTES (see
scripts/scheduler.sh), and runnable by hand at any time — which is the manual
trigger for development and testing:

    python manage.py check_imports
    python manage.py check_imports --path voorbeeld-data --force
    python manage.py check_imports --dry-run
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from matching.ingest.detection import scan_share


class Command(BaseCommand):
    help = "Detect and import the Syntess/RouteVision source files on the server share."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Folder to check instead of SERVERMAP_PATH (development/testing).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Import recognised files immediately, without waiting for the "
            "stability margin.",
        )
        parser.add_argument(
            "--reprocess",
            action="store_true",
            help="Also re-import files already marked verwerkt. Manual only; the "
            "scheduled run never reprocesses by itself.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would happen without writing anything.",
        )

    def handle(self, *args, **options):
        result = scan_share(
            path=options["path"],
            force=options["force"],
            reprocess=options["reprocess"],
            dry_run=options["dry_run"],
        )

        share = options["path"] or settings.SERVERMAP_PATH
        self.stdout.write(
            f"Share: {share} "
            f"(stability: {result.required_consecutive} unchanged measurement(s))"
        )

        for filename, row_count in result.imported.items():
            self.stdout.write(
                self.style.SUCCESS(f"  imported  {filename} ({row_count} rows)")
            )
        for filename in result.waiting:
            self.stdout.write(f"  waiting   {filename}")
        for filename in result.skipped_processed:
            self.stdout.write(f"  verwerkt  {filename} (skipped)")
        for filename, error in result.failed.items():
            self.stderr.write(self.style.ERROR(f"  failed    {filename}: {error}"))
        if result.ignored:
            self.stdout.write(f"  ignored   {len(result.ignored)} unrecognised file(s)")
        if not result.seen:
            self.stdout.write("  no recognised source files found")
