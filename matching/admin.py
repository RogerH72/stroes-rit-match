from django.contrib import admin

from matching.models import (
    BekendeLocatie,
    ImportedFile,
    Instelling,
    MeegeredenKoppeling,
    Monteur,
    Relatie,
    Rit,
    Tijdblok,
    ToleranceRegel,
    Uren,
    WerkbonControle,
)

# Admin UI text is Dutch (project convention: UI in Dutch, code in English).
admin.site.site_header = "RMW — Ritten Match Werkbon"
admin.site.site_title = "RMW"
admin.site.index_title = "Beheer"

# The raw import tables are registered read-only: they are a 1-to-1 copy of the
# source files, so editing a row here would only make the database disagree with
# the share. The koppeltabellen and the tolerantietabel further down *are*
# editable — that is the data SBTT maintains itself.


class ReadOnlyImportAdmin(admin.ModelAdmin):
    """Look at what was imported, but do not change it here."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ImportedFile)
class ImportedFileAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "source_kind",
        "status",
        "size_bytes",
        "unchanged_polls",
        "last_measured_at",
        "processed_at",
        "row_count",
    )
    list_filter = ("status", "source_kind")
    search_fields = ("filename",)
    readonly_fields = ("first_seen_at",)


@admin.register(Uren)
class UrenAdmin(ReadOnlyImportAdmin):
    list_display = (
        "datum",
        "medewerker",
        "naam",
        "werkbon",
        "aantal",
        "plaats",
        "adres",
    )
    list_filter = ("datum", "medewerker")
    search_fields = ("werkbon", "naam", "project_opdrachtgever_naam", "adres")
    date_hierarchy = "datum"


@admin.register(Rit)
class RitAdmin(ReadOnlyImportAdmin):
    list_display = (
        "vertrekdatum",
        "kenteken",
        "bestuurder",
        "reis_van_de_dag",
        "vertrektijd",
        "vertrekplaats",
        "aankomsttijd",
        "aankomstplaats",
        "duur",
        "km_totaal",
    )
    list_filter = ("vertrekdatum", "kenteken", "bestuurder")
    search_fields = ("kenteken", "bestuurder", "vertrekadres", "aankomstadres")
    date_hierarchy = "vertrekdatum"


@admin.register(Relatie)
class RelatieAdmin(ReadOnlyImportAdmin):
    list_display = ("code", "relatienaam", "postcode", "huisnr", "telefoon")
    search_fields = ("code", "relatienaam", "postcode")


@admin.register(WerkbonControle)
class WerkbonControleAdmin(ReadOnlyImportAdmin):
    # `postcode` is in the list because it is the one column of this table the
    # matching actually reads (see matching/timeline/engine.py). The remaining
    # stored columns — titel, tijd, reistijd, werktijd, monteur_meegereden — are
    # unused and stay off the list; like every read-only import admin here, the
    # detail view restricts no fields, so they are all visible when a row is
    # opened.
    list_display = ("werkbon", "medewerker", "datum", "postcode", "fase_status")
    list_filter = ("fase_status", "datum", "medewerker")
    search_fields = ("werkbon", "postcode", "titel")
    date_hierarchy = "datum"


# --- The koppeltabellen (roadmap phase 3/4) ---------------------------------
#
# These are editable on purpose: unlike the import tables above, this is data
# SBTT maintains itself. Plain admin screens for now — the polished
# one-click uitzonderingen flow is phase 5.


@admin.register(Monteur)
class MonteurAdmin(admin.ModelAdmin):
    list_display = (
        "naam",
        "medewerker_nummer",
        "bestuurder_code",
        "kenteken",
        "vaste_meerijder",
        "actief",
    )
    list_filter = ("actief",)
    search_fields = ("naam", "medewerker_nummer", "bestuurder_code", "kenteken")
    ordering = ("naam",)


@admin.register(BekendeLocatie)
class BekendeLocatieAdmin(admin.ModelAdmin):
    list_display = ("waarde", "type", "soort", "label", "is_depot")
    list_filter = ("type", "soort", "is_depot")
    search_fields = ("waarde", "label")


@admin.register(Instelling)
class InstellingAdmin(admin.ModelAdmin):
    """One row, so adding and deleting are turned off — there is only editing."""

    list_display = ("__str__", "meegereden_modus")

    def has_add_permission(self, request):
        return Instelling.objects.exists() is False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Make sure the single row exists, so the list is never empty and the
        # user lands on something he can open.
        Instelling.load()
        return super().changelist_view(request, extra_context)


@admin.register(MeegeredenKoppeling)
class MeegeredenKoppelingAdmin(admin.ModelAdmin):
    list_display = ("junior", "senior", "datum_van", "datum_tot")
    list_filter = ("junior", "senior")
    search_fields = ("junior__naam", "senior__naam")
    autocomplete_fields = ("junior", "senior")


@admin.register(ToleranceRegel)
class ToleranceRegelAdmin(admin.ModelAdmin):
    list_display = ("activiteit", "drempel_minuten")
    search_fields = ("activiteit",)


@admin.register(Tijdblok)
class TijdblokAdmin(admin.ModelAdmin):
    """The computed timeline: read-only, because run_matching owns these rows.

    Editing a block by hand would be overwritten by the next run; the way to
    change the outcome is to correct a koppeltabel and run the matching again.
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    list_display = (
        "datum",
        "monteur",
        "volgorde",
        "soort",
        "start_tijd",
        "eind_tijd",
        "duur_minuten",
        "werkbon",
        "omschrijving",
    )
    list_filter = ("soort", "datum", "monteur")
    search_fields = ("werkbon", "omschrijving", "adres")
    date_hierarchy = "datum"
