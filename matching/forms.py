"""Forms for the screens outside the Django admin.

Phase 5 has exactly one: the confirmation form of the uitzonderingenscherm,
which turns an unexplained address into a BekendeLocatie.
"""

from __future__ import annotations

from django import forms

from matching.models import BekendeLocatie


class KoppelLocatieForm(forms.ModelForm):
    """Link one unexplained address to a known location.

    A thin wrapper around BekendeLocatie on purpose: normalising `waarde` and
    the uniqueness of (type, waarde) already live on the model, so the form only
    has to present the fields. Re-implementing that validation here would give
    this screen its own idea of what a valid location is, next to the admin's.

    `is_depot` is deliberately absent — not defaulted to False, but not offered
    at all. A depot outranks every other rule in the matching (see
    `_classify_stop`), so it stays admin-managed configuration; it must not be
    possible to create one in passing while clearing an exception
    (docs/decisions.md, 2026-09-03).

    `soort` needs no restriction here: the model field already offers only K, L
    and C (HANDMATIGE_SOORTEN) — W/?/O/R always follow from the matching itself.
    """

    class Meta:
        model = BekendeLocatie
        fields = ("type", "waarde", "soort", "label")
        widgets = {
            "label": forms.TextInput(
                attrs={"placeholder": "Bijv. Groothandel Van Egmond"}
            ),
        }
        help_texts = {
            "label": "Waaraan herken je dit adres terug in het weekoverzicht?",
        }
