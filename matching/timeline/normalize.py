"""Turning source addresses into the keys the matching compares on.

These are the PoC's `street()` / `pc_of()` / `plaatsnaam()` helpers
(D:/STROES/PoC-demo/rmw_sbtt.py), unchanged in behaviour. They live in their
own module because the models import them too — a BekendeLocatie stores its
`waarde` already normalised, so a hand-typed "Randweg 6a" and a RouteVision
"randweg" end up as the same key.

Deliberately no dependency on the models, so importing this from models.py
cannot become a circular import.
"""

from __future__ import annotations

import re

# "Randweg 6a" -> "randweg": everything from the first house number onwards is
# dropped, because RouteVision and Syntess disagree on house numbers far more
# often than on street names (docs/business-rules.md: postcode-exact is not
# enough, a street fallback is needed).
_HOUSE_NUMBER = re.compile(r"\s*\d+.*$")

# A Dutch postcode anywhere at the start of the value: RouteVision writes its
# places as "4104 AC Culemborg", Syntess writes its postcodes as "4104 AC".
_POSTCODE = re.compile(r"(\d{4}\s?[A-Z]{2})")


def street(value: object) -> str:
    """The bare street name of an address, lowercased and without house number."""
    return _HOUSE_NUMBER.sub("", str(value or "")).strip().lower()


def postcode(value: object) -> str:
    """The postcode in a value, without its space ("4104 AC Culemborg" -> "4104AC").

    Empty string when the value holds no postcode, which callers treat as "no
    postcode to match on" rather than as a key.
    """
    match = _POSTCODE.match(str(value or "").strip().upper())
    return match.group(1).replace(" ", "") if match else ""


def plaatsnaam(value: object) -> str:
    """The town of a RouteVision place, without the postcode in front of it."""
    return re.sub(r"^\d{4}\s?[A-Z]{2}\s*", "", str(value or "").strip()).strip()


def minutes_to_hhmm(minutes: float) -> str:
    """A duration in minutes as h:mm, the way the PoC printed its day summary."""
    total = int(round(minutes))
    sign = "-" if total < 0 else ""
    total = abs(total)
    return f"{sign}{total // 60}:{total % 60:02d}"
