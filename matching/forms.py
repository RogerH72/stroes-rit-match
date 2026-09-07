"""Forms for the screens outside the Django admin, plus the admin's own reset form.

Phase 5 brought exactly one of the former: the confirmation form of the
uitzonderingenscherm, which turns an unexplained address into a BekendeLocatie.
DataResetForm is the exception to the module's name — it belongs to an admin
view, but it is a plain Form over the reset options rather than anything the
admin generates, so it reads better here than wedged into matching/admin.py.
"""

from __future__ import annotations

from django import forms

from matching import reset
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


class DataResetForm(forms.Form):
    """Which reset to run: everything, or one date range.

    The dates only apply to the period mode, so they cannot be required outright;
    `clean` makes them required for that mode and drops them for the other, which
    keeps the view from having to know that rule too.
    """

    MODUS_VOLLEDIG = "volledig"
    MODUS_PERIODE = "periode"

    modus = forms.ChoiceField(
        label="Wat wil je verwijderen?",
        choices=(
            (
                MODUS_VOLLEDIG,
                "Volledig leegmaken — alle ingelezen bestanden, importregels en "
                "berekende tijdblokken",
            ),
            (
                MODUS_PERIODE,
                "Periode verwijderen — alleen urenregels, ritten, werkbonnen en "
                "tijdblokken binnen een van-tot bereik",
            ),
        ),
        widget=forms.RadioSelect,
        initial=MODUS_VOLLEDIG,
    )
    van = forms.DateField(
        label="Van",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    tot = forms.DateField(
        label="Tot en met",
        required=False,
        help_text="Deze dag telt zelf ook mee.",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        opgeschoond = super().clean()
        modus = opgeschoond.get("modus")
        van, tot = opgeschoond.get("van"), opgeschoond.get("tot")

        if modus == self.MODUS_PERIODE:
            if not van:
                self.add_error("van", "Vul een begindatum in.")
            if not tot:
                self.add_error("tot", "Vul een einddatum in.")
            if van and tot and van > tot:
                # Silently swapping them would delete a period the user never
                # asked about, which is not a thing to be helpful about.
                self.add_error("tot", "De einddatum ligt vóór de begindatum.")
        else:
            # A date left over from switching modes must not travel any further:
            # a full wipe is a full wipe.
            opgeschoond["van"] = None
            opgeschoond["tot"] = None

        return opgeschoond

    def selectie(self):
        """The querysets this form describes, ready to count or delete."""
        if self.cleaned_data["modus"] == self.MODUS_VOLLEDIG:
            return reset.volledige_selectie()
        return reset.periode_selectie(
            self.cleaned_data["van"], self.cleaned_data["tot"]
        )
