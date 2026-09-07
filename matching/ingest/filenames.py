"""Recognising which source file is which, by filename.

OPEN ITEM (docs/functioneel-ontwerp.md §9, item 1): the filename convention of the
real automatic Syntess/RouteVision export is not confirmed yet with Stric / RVS
Solutions / RouteVision. The sample files in voorbeeld-data/ carry manually chosen
PoC names:

    20260826 Download uit Syntess Uren  26 8 2026.xlsx
    20260826 Download uit Syntess Relaties  26 8 2026.xlsx
    20260826 Download uit Syntess Werkbonnen  26 8 2026.xlsx
    20260826 Ritten_Alle_voertuigen aug 26 (CSV uit Syntess).csv

Matching is therefore deliberately loose — one keyword plus the expected extension,
case-insensitive, anywhere in the name — so a dated prefix, a different suffix or a
changed separator does not break detection. When the real convention is confirmed,
the only thing that needs changing is FILE_PATTERNS below (or the RMW_FILE_PATTERNS
setting, which overrides it without touching this module).

Loose is not the same as sloppy: the keyword has to sit on a word boundary, or
"Facturen 2026.xlsx" would be picked up as an Uren export because it happens to
end in "uren". And a name that is loose enough to match a dated Syntess export is
also loose enough to match Excel's own lock file for that export, so the "~$"
prefix is rejected outright (see LOCK_FILE_PREFIX).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from django.conf import settings

from matching.models import SourceKind

logger = logging.getLogger(__name__)


def keyword(*variants: str) -> str:
    """A regex for a keyword that has to stand on its own in the filename.

    Digits and letters may not touch either side, so "Uren", "SYNTESS_UREN_2026"
    and "... Syntess Uren 26 8 2026" all match while "Facturen" does not.
    Separators the exports actually use — spaces, underscores, hyphens, dots —
    are all fine.
    """
    return rf"(?<![a-z0-9])(?:{'|'.join(variants)})(?![a-z0-9])"


# {source kind: (regex matched case-insensitively against the filename, allowed
# extensions)}. Order matters only for the warning about an ambiguous name.
FILE_PATTERNS: dict[str, tuple[str, tuple[str, ...]]] = {
    SourceKind.UREN: (keyword("uren"), (".xlsx",)),
    SourceKind.WERKBON_CONTROLE: (keyword("werkbonnen", "werkbon"), (".xlsx",)),
    SourceKind.RELATIE: (keyword("relaties", "relatie"), (".xlsx",)),
    SourceKind.RIT: (keyword("ritten", "rit"), (".csv",)),
}


# Microsoft Office writes a hidden lock file next to every open document, named
# after it with a "~$" prefix ("~$Uren 26 8 2026.xlsx"). It is a real .xlsx-named
# file of a few hundred bytes, so every pattern below happily matches it — which
# is how simply opening a source file in Excel produced a phantom second
# ImportedFile row for it. Nothing on the share that starts with this prefix is
# ever one of our exports.
LOCK_FILE_PREFIX = "~$"


def _patterns() -> dict[str, tuple[str, tuple[str, ...]]]:
    """The active pattern table, overridable per deployment via settings."""
    return getattr(settings, "RMW_FILE_PATTERNS", None) or FILE_PATTERNS


def classify_filename(filename: str) -> str | None:
    """Return the SourceKind for a filename, or None if it is not one of ours.

    Anything on the share that does not match — other exports, temporary files a
    writer leaves behind — is simply ignored rather than treated as an error.
    """
    name = Path(filename).name
    if name.startswith(LOCK_FILE_PREFIX):
        return None

    suffix = Path(name).suffix.lower()

    matches = [
        kind
        for kind, (pattern, extensions) in _patterns().items()
        if suffix in extensions and re.search(pattern, name, re.IGNORECASE)
    ]
    if not matches:
        return None
    if len(matches) > 1:
        # Not fatal, but worth knowing about: it means the patterns need
        # tightening once the real naming convention is confirmed.
        logger.warning(
            "Filename %r matches multiple source kinds (%s); using %s.",
            name,
            ", ".join(matches),
            matches[0],
        )
    return matches[0]
