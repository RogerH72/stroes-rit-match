"""Which monteur's rides drive another monteur's day.

A junior monteur who rides along with a senior has no rides of his own in
RouteVision — either he has no driver code at all, or he simply did not drive
that day. His day is then reconstructed from the *senior's* rides, while the
work still has to be matched against the *junior's* own booked hours: it is his
Uren rows, on the rides he shared.

Which senior applies is a global setting with three modes (docs/decisions.md,
03-09-2026):

* VAST    — one permanent senior per junior, stored on Monteur.vaste_meerijder.
* PERIODE — a koppeltabel with a validity period, so a junior can ride with
            different seniors at different times.
* SYNTESS — reserved, deliberately without any logic: Syntess does not fill its
            "Monteur meegereden" column reliably yet. Instelling refuses to save
            this mode at all, so it can never reach the code below.
"""

from __future__ import annotations

import datetime as dt

from django.db.models import Q

from matching.models import Instelling, MeegeredenKoppeling, MeegeredenModus, Monteur


def resolve_bronmonteur(monteur: Monteur, datum: dt.date) -> Monteur:
    """The monteur whose Rit rows describe `monteur`'s movements on `datum`.

    Returns `monteur` himself whenever no meegereden-koppeling applies, which is
    the normal case for anyone who drives his own van.
    """
    modus = Instelling.load().meegereden_modus

    if modus == MeegeredenModus.VAST:
        return monteur.vaste_meerijder or monteur

    if modus == MeegeredenModus.PERIODE:
        koppeling = _koppeling_op(monteur, datum)
        return koppeling.senior if koppeling else monteur

    # No other mode can be stored (Instelling rejects SYNTESS on save), so a
    # value arriving here means the data was tampered with outside the app.
    # Falling back on the monteur himself is the safe reading: it produces his
    # own rides rather than silently attributing someone else's.
    return monteur


def _koppeling_op(monteur: Monteur, datum: dt.date) -> MeegeredenKoppeling | None:
    """The koppeling covering `datum`, most recently started first.

    Two koppelingen for the same junior can no longer overlap — `clean()`
    rejects that when the row is saved (docs/decisions.md, 07-09-2026) — so the
    ordering here is a formality rather than a real tie-breaker. It is kept
    because rows written before that check existed, or straight into the
    database, would otherwise make this return an arbitrary one of the two.
    """
    still_open = Q(datum_tot__isnull=True) | Q(datum_tot__gte=datum)
    return (
        MeegeredenKoppeling.objects.filter(junior=monteur, datum_van__lte=datum)
        .filter(still_open)
        .select_related("senior")
        .order_by("-datum_van")
        .first()
    )


def bron_bestuurder_codes(monteur: Monteur) -> set[str]:
    """Every driver code whose rides could ever belong to `monteur`.

    His own code, plus the codes of anyone he might ride along with under either
    mode. Used to find the dates worth reconstructing before it is known which
    senior applies on which date — the exact bronmonteur per date is resolved
    afterwards by `resolve_bronmonteur`.
    """
    codes = set()
    if monteur.bestuurder_code:
        codes.add(monteur.bestuurder_code)
    if monteur.vaste_meerijder and monteur.vaste_meerijder.bestuurder_code:
        codes.add(monteur.vaste_meerijder.bestuurder_code)
    codes.update(
        MeegeredenKoppeling.objects.filter(junior=monteur)
        .exclude(senior__bestuurder_code="")
        .values_list("senior__bestuurder_code", flat=True)
    )
    return codes
