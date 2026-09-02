from django.contrib import admin

from matching.models import ImportedFile, Relatie, Rit, Uren, WerkbonControle

# Admin UI text is Dutch (project convention: UI in Dutch, code in English).
admin.site.site_header = "RMW — Ritten Match Werkbon"
admin.site.site_title = "RMW"
admin.site.index_title = "Beheer"

# The raw import tables are registered read-only: they are a 1-to-1 copy of the
# source files, so editing a row here would only make the database disagree with
# the share. The koppeltabellen and the tolerantietabel — the screens that are
# actually meant to be edited — are roadmap phase 4.


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
    list_display = ("werkbon", "medewerker", "datum", "fase_status")
    list_filter = ("fase_status", "datum", "medewerker")
    search_fields = ("werkbon",)
    date_hierarchy = "datum"
