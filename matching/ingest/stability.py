"""File stability check for the polling-based file detection.

A file on the share only counts as complete once its size has stayed unchanged
for STABILITY_MINUTES. Since detection is polling-based (SMB shares make
filesystem events unreliable — see docs/architecture.md), that margin is
expressed as a number of consecutive unchanged measurements, derived from the
two independently configurable settings.

Everything here is plain Python: no Django models, no scheduler, no clock. That
keeps the rule unit-testable without waiting on a real timer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Measurement:
    """One observation of a file's size, plus the streak it belongs to.

    `unchanged_polls` counts the consecutive polls that saw this same size,
    including this one — so a freshly appearing (or freshly changed) file starts
    at 1.
    """

    size: int
    unchanged_polls: int = 1
    measured_at: datetime | None = None


def required_consecutive_polls(stability_minutes: int, poll_interval_minutes: int) -> int:
    """How many unchanged measurements in a row make a file "complete".

    With the defaults (30 minutes stability, a 5 minute poll interval) this is 6,
    as described in docs/architecture.md. The result is rounded up when the two
    do not divide evenly, and is never less than 1 — which also covers a
    stability margin configured shorter than the poll interval, where a single
    measurement is all the interval can offer.
    """
    if poll_interval_minutes <= 0:
        raise ValueError("poll_interval_minutes must be positive")
    if stability_minutes <= 0:
        return 1
    return max(1, math.ceil(stability_minutes / poll_interval_minutes))


def next_measurement(
    previous: Measurement | None, size: int, measured_at: datetime | None = None
) -> Measurement:
    """Fold a fresh size reading into the running streak.

    The streak continues while the size is unchanged and restarts at 1 as soon as
    the file grows or shrinks — i.e. while it is still being written.
    """
    if previous is not None and previous.size == size:
        return Measurement(size, previous.unchanged_polls + 1, measured_at)
    return Measurement(size, 1, measured_at)


def is_stable(
    previous: Measurement | None,
    current: Measurement,
    required_consecutive: int,
) -> bool:
    """Has the file's size stayed unchanged long enough to be read?

    `previous` is the measurement stored at the previous poll (None the first time
    a file is seen), `current` the measurement just taken — normally the result of
    `next_measurement(previous, size_on_disk)`. Passing a `current` that was not
    folded from `previous` still gives the right answer, because a size difference
    between the two restarts the streak regardless.
    """
    required = max(1, required_consecutive)
    if previous is not None and previous.size != current.size:
        # The file changed since the previous poll, so the run starts over at 1.
        return required <= 1
    return current.unchanged_polls >= required
