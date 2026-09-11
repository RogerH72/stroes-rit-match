"""Reconstruct the day timelines and store them as Tijdblok rows.

Unlike check_imports this is not on a schedule: a stored timeline is what the
uitzonderingen- and weekoverzicht-screens build on, so it never changes by
itself. Run it after a fresh import, or after changing a koppeltabel. With
--force the selection is also cleared of days that no longer produce a result:

    python manage.py run_matching
    python manage.py run_matching --monteur 005 --van 2026-08-03 --tot 2026-08-07
    python manage.py run_matching --dry-run
    python manage.py run_matching --force
"""

from __future__ import annotations

import datetime as dt

from django.core.management.base import BaseCommand, CommandError

from matching.models import Soort
from matching.timeline.normalize import minutes_to_hhmm
from matching.timeline.runner import run_matching_and_record_status


def _date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise CommandError(f"Ongeldige datum: {value!r} (verwacht JJJJ-MM-DD)") from None


class Command(BaseCommand):
    help = "Rebuild the per-monteur day timelines from the imported ritten and uren."

    def add_arguments(self, parser):
        parser.add_argument(
            "--monteur",
            default=None,
            help="Personeelsnummer (Uren.Medewerker). Standaard: alle actieve monteurs.",
        )
        parser.add_argument(
            "--van",
            type=_date,
            default=None,
            help="Eerste datum (JJJJ-MM-DD). Standaard: elke datum met ritdata.",
        )
        parser.add_argument(
            "--tot",
            type=_date,
            default=None,
            help="Laatste datum (JJJJ-MM-DD), inclusief.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overschrijf dagen die al berekend zijn (verwijderen en opnieuw "
            "opbouwen) en verwijder binnen de selectie de dagen die geen "
            "resultaat meer opleveren. Nodig na een wijziging in een koppeltabel.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Toon wat er berekend zou worden, zonder iets weg te schrijven.",
        )

    def handle(self, *args, **options):
        van, tot = options["van"], options["tot"]
        if van and tot and tot < van:
            raise CommandError("--tot ligt vóór --van.")

        result = run_matching_and_record_status(
            medewerker_nummer=options["monteur"],
            van=van,
            tot=tot,
            force=options["force"],
            dry_run=options["dry_run"],
        )

        if options["dry_run"]:
            self.stdout.write("Dry run — er is niets weggeschreven.")

        for dag in result.dagen:
            self.stdout.write(f"  {dag.datum}  {dag.monteur.naam}{self._bron(dag)}")
            self.stdout.write(f"      {self._totalen(dag)}")

        for monteur, datum in result.overgeslagen:
            self.stdout.write(
                f"  {datum}  {monteur.naam}: al berekend (gebruik --force)"
            )
        for monteur in result.zonder_ritten:
            self.stdout.write(f"  {monteur.naam}: geen ritdata in deze selectie")
        for monteur, datum in result.opgeruimd:
            self.stdout.write(f"  {datum}  {monteur.naam}: vervallen, verwijderd")

        summary = (
            f"{len(result.dagen)} dag(en) berekend, "
            f"{result.aantal_blokken} tijdblok(ken)"
        )
        if result.overgeslagen:
            summary += f", {len(result.overgeslagen)} overgeslagen"
        if result.opgeruimd:
            summary += f", {len(result.opgeruimd)} vervallen dag(en) verwijderd"
        self.stdout.write(self.style.SUCCESS(summary))

    def _bron(self, dag) -> str:
        """Name the source monteur when the day came from someone else's rides."""
        if not dag.meegereden:
            return ""
        return f" (meegereden met {dag.bronmonteur.naam})"

    def _totalen(self, dag) -> str:
        """The per-SOORT day summary, in the spirit of the PoC's printed line."""
        totalen = dag.totalen()
        parts = [
            f"{soort.value} {minutes_to_hhmm(totalen[soort.value])}"
            for soort in Soort
            if totalen[soort.value]
        ]
        parts.append(f"totaal {minutes_to_hhmm(sum(totalen.values()))}")
        return "  ".join(parts)
