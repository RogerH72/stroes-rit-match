from pathlib import Path, PurePosixPath

from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from matching import reset
from matching.forms import DataResetForm
from matching.ingest.detection import scan_share
from matching.ingest.filenames import classify_filename
from matching.models import (
    BekendeLocatie,
    ImportedFile,
    Instelling,
    MatchmotorStatus,
    MeegeredenKoppeling,
    Monteur,
    Relatie,
    Rit,
    Tijdblok,
    ToleranceRegel,
    Uren,
    WerkbonControle,
)
from matching.timeline.runner import run_matching_and_record_status

# Admin UI text is Dutch (project convention: UI in Dutch, code in English).
admin.site.site_header = "RMW — Ritten Match Werkbon"
admin.site.site_title = "RMW"
admin.site.index_title = "Beheer"
# The "view site" link in the admin header. Its default is "/", which lands on
# the weekoverzicht too but only after a redirect; naming the screen directly
# keeps the URL in the status bar honest about where the link goes. reverse_lazy
# because this module is imported before the URLconf is loaded.
admin.site.site_url = reverse_lazy("weekoverzicht")

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

    def has_delete_permission(self, request, obj=None):
        # Deleting mattered as much as editing and was the one hole left open:
        # these rows are a copy of the share, so a row deleted here comes back
        # on the next reprocess while the matching in between silently misses
        # it. Saying "no" here also takes "delete selected" out of the actions
        # dropdown altogether (Django filters actions on this permission), which
        # is what the screen needs — trying it on a full Urenregels table posted
        # one hidden field per row and hit DATA_UPLOAD_MAX_NUMBER_FIELDS, so the
        # offer ended in a bare 400 rather than a refusal.
        return False


@admin.register(ImportedFile)
class ImportedFileAdmin(ReadOnlyImportAdmin):
    """The import bookkeeping: which file was seen, and what was done with it.

    Read-only for a different reason than the tables below. Those are a copy of
    the share, so editing one only makes the database disagree with it. This one
    is the app's own record of what it has already read in, and both scan_share()
    and the matching take it at its word: a row added or edited by hand — a
    status set to "verwerkt" for a file that was never actually read — would make
    the app claim an import that never happened, and nothing downstream would
    notice the difference.

    Putting a real mistake right stays a deliberate, separate action:
    `check_imports --reprocess` for one file (command-line only by design, see
    docs/architecture.md), or "Data resetten" for the whole table.
    """

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
        "thuisadres",
        "vaste_meerijder",
        "actief",
    )
    # Whether a home address is filled in decides whether his day edges come out
    # as T or as unexplained stops, so it is worth being able to list the
    # monteurs who still have none (docs/decisions.md, 07-09-2026).
    list_filter = ("actief", "thuisadres_type")
    search_fields = (
        "naam",
        "medewerker_nummer",
        "bestuurder_code",
        "kenteken",
        "thuisadres",
    )
    ordering = ("naam",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Name the empty choice of `vaste_meerijder` instead of "---------".

        The empty option always worked — clearing the field and saving removes
        the koppeling — but Django's default label is a row of dashes, which
        does not read as "no koppeling" to someone looking for a way to undo one
        (docs/decisions.md, 08-09-2026). Only the label changes; the choice
        itself, and everything it does, is unchanged.
        """
        if db_field.name == "vaste_meerijder":
            kwargs["empty_label"] = "— geen vaste meerijder —"
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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

    def has_delete_permission(self, request, obj=None):
        # Same reason as the read-only import admins: run_matching owns these
        # rows, so deleting one here only makes the timeline wrong until the
        # next run puts it back.
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


@admin.register(MatchmotorStatus)
class MatchmotorStatusAdmin(admin.ModelAdmin):
    """The status screen, and the one button SBTT needs.

    The matching is never scheduled — it only recomputes when someone asks
    (docs/database.md). Editing a koppeltabel therefore has no visible effect
    until a run happens, and until now the only way to trigger one was
    `python manage.py run_matching --force` on the server. SBTT staff have no
    shell, so this screen is that command.

    Singleton like Instelling, but fully read-only like Tijdblok: adding,
    changing and deleting are all off, and the changelist doubles as the status
    view.
    """

    list_display = (
        "__str__",
        "laatste_run_gestart_op",
        "laatste_run_afgerond_op",
        "succes",
        "dagen_verwerkt",
    )
    change_list_template = "admin/matching/matchmotorstatus/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Read-only for the same reason as TijdblokAdmin: this row is a report
        # of what run_matching did, not an input. Hand-editing it would only
        # make the screen lie until the next run overwrote it; the way to change
        # the outcome is to correct a koppeltabel and run the matching again.
        return False

    def changelist_view(self, request, extra_context=None):
        # Make sure the single row exists, so the list is never empty and the
        # button always has a page to live on.
        MatchmotorStatus.load()
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        # Ahead of the default admin URLs, so the literal path is not swallowed
        # by the <object_id> pattern.
        return [
            # First in the list because it is first in the working order too:
            # read the files in, then recompute.
            path(
                "bestanden-nu-inlezen/",
                self.admin_site.admin_view(self.bestanden_inlezen_view),
                name="matching_bestanden_inlezen",
            ),
            # The fallback next to it: same destination (the servermap), other
            # way in (the browser) for when the share itself is not reachable.
            path(
                "bestanden-uploaden/",
                self.admin_site.admin_view(self.bestanden_uploaden_view),
                name="matching_bestanden_uploaden",
            ),
            path(
                "matching-nu-draaien/",
                self.admin_site.admin_view(self.run_matching_view),
                name="matching_matchmotorstatus_run",
            ),
            # Lives under this admin because this is the screen the two belong
            # together on: reset the data, then deliberately read it in and
            # recompute. It is not a MatchmotorStatus operation as such.
            path(
                "data-resetten/",
                self.admin_site.admin_view(self.data_resetten_view),
                name="matching_data_resetten",
            ),
            *super().get_urls(),
        ]

    @method_decorator(require_POST)
    def bestanden_inlezen_view(self, request):
        """Import whatever is ready on the share right now, then report back.

        POST-only, for the same reason as "Matching nu draaien": this writes
        rows, so a link preview or a refreshed tab must not be able to set it
        off.

        `force=True` so the button does not sit out the stability margin — that
        margin exists for the unattended scheduler, not for someone standing at
        the screen asking for it now. `reprocess` stays off: re-importing a file
        already marked verwerkt is a command-line-only action
        (docs/architecture.md), so the button cannot cause a double import by
        accident. And it deliberately does not run the matching afterwards:
        importing and recomputing stay two separate, deliberate steps, exactly
        as after "Data resetten".
        """
        # Same reasoning as run_matching_view: `self.has_change_permission()` is
        # False for everyone so the row cannot be edited, but pressing this
        # button *is* a change, so it is gated on the underlying permission.
        if not request.user.has_perm("matching.change_matchmotorstatus"):
            raise PermissionDenied

        redirect_to = reverse("admin:matching_matchmotorstatus_changelist")
        result = scan_share(force=True)
        self._meld_scanresultaat(request, result)

        if not result.imported:
            if not result.seen:
                self.message_user(
                    request,
                    "Geen herkende bronbestanden gevonden op de servermap.",
                    level=messages.WARNING,
                )
            elif not result.failed:
                # Recognised files, nothing imported and nothing broken: they
                # were all already verwerkt. Said plainly, because "niets
                # gebeurd" on a share full of files otherwise reads as a
                # malfunction. A failure speaks for itself through the error
                # messages _meld_scanresultaat already put on the screen.
                self.message_user(
                    request,
                    "Niets nieuws om in te lezen.",
                    level=messages.WARNING,
                )

        return HttpResponseRedirect(redirect_to)

    @method_decorator(require_POST)
    def bestanden_uploaden_view(self, request):
        """Put source files on the servermap through the browser, then read them in.

        The fallback for the period before Stric has the network share working,
        and for an occasional outage after that. It does not replace the
        share-based path but feeds it: an uploaded file is written under its own
        name into the very same inbox directory `scan_share()` scans, so from
        the moment it lands there it is an ordinary source file with an ordinary
        ImportedFile row. Nothing is cleaned up afterwards, for the same reason
        nothing on the share ever is — the database alone records what has been
        done (docs/architecture.md).

        POST-only and gated on `matching.change_matchmotorstatus`, for the same
        reasons as "Bestanden nu inlezen": this writes files and rows.

        Uploading and importing are deliberately *one* action here, unlike on
        the share. The stability margin exists to catch a file an export job is
        still writing; a file that arrived complete over HTTP has nothing left
        to wait for. Running the matching afterwards stays the separate,
        deliberate step it is everywhere else.
        """
        if not request.user.has_perm("matching.change_matchmotorstatus"):
            raise PermissionDenied

        redirect_to = reverse("admin:matching_matchmotorstatus_changelist")

        uploads = request.FILES.getlist("bestanden")
        if not uploads:
            self.message_user(
                request,
                "Geen bestanden gekozen om te uploaden.",
                level=messages.WARNING,
            )
            return HttpResponseRedirect(redirect_to)

        inbox = Path(settings.SERVERMAP_PATH)
        try:
            # The share is normally there already; this only covers a local or
            # containerised inbox that has never been written to yet.
            inbox.mkdir(parents=True, exist_ok=True)
        except OSError as fout:
            self.message_user(
                request,
                f"De servermap {inbox} is niet beschikbaar om naar te "
                f"schrijven: {fout}",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(redirect_to)

        geaccepteerd: list[str] = []
        for upload in uploads:
            naam, weigering = self._bewaar_upload(upload, inbox)
            if weigering is None:
                geaccepteerd.append(naam)
            else:
                # Per file, not per batch: one unusable file among four must not
                # cost the other three, exactly as in scan_share().
                self.message_user(
                    request,
                    f"Geweigerd: {naam} — {weigering}",
                    level=messages.ERROR,
                )

        if not geaccepteerd:
            # Nothing reached the servermap, so there is nothing new to scan
            # for; scanning anyway would only add "niets nieuws" underneath the
            # refusals, which reads as a second, unrelated complaint.
            return HttpResponseRedirect(redirect_to)

        self.message_user(
            request,
            f"Naar de servermap geüpload: {len(geaccepteerd)} bestand(en) — "
            f"{', '.join(geaccepteerd)}.",
            level=messages.SUCCESS,
        )
        self._meld_scanresultaat(request, scan_share(force=True))
        return HttpResponseRedirect(redirect_to)

    @staticmethod
    def _bewaar_upload(upload, inbox: Path) -> tuple[str, str | None]:
        """Write one uploaded file into the inbox; return its name and any refusal.

        Both refusals are deliberate and per file. An unrecognised name would
        land on the share as a file `scan_share()` silently ignores, leaving the
        uploader thinking he had delivered it; and an existing name is never
        overwritten, because the file already there may be the one that was
        imported — replacing it would make its ImportedFile row describe
        something other than what is on disk.
        """
        # Django's MultiPartParser already strips directories from the posted
        # filename, but this name becomes a path that gets written to, so it
        # gets the second lock too: only ever the last component, on either
        # platform's separator.
        naam = PurePosixPath(upload.name.replace("\\", "/")).name

        if classify_filename(naam) is None:
            return naam or upload.name, (
                "niet herkend als bronbestand. Verwacht wordt een bestandsnaam "
                "met Uren, Werkbonnen of Relaties erin (.xlsx), of Ritten "
                "(.csv)."
            )

        doel = inbox / naam
        try:
            # "xb" rather than checking exists() and then writing: the check and
            # the write are one step this way, so a file that turns up in
            # between cannot be silently overwritten after all.
            with doel.open("xb") as bestand:
                for blok in upload.chunks():
                    bestand.write(blok)
        except FileExistsError:
            return naam, "bestaat al op de servermap, niet opnieuw geüpload."
        except OSError as fout:
            # A half-written file would be picked up as a real source file on
            # the next scan, so it must not be left lying there.
            doel.unlink(missing_ok=True)
            return naam, f"kon niet worden weggeschreven ({fout})."

        return naam, None

    def _meld_scanresultaat(self, request, result) -> None:
        """Report one scan_share() pass: what went in, and what tripped over it.

        Shared by both buttons that import — "Bestanden nu inlezen" and
        "Bestanden uploaden" — so an import reads the same whichever way the
        file got onto the servermap. What is *missing* from the share is not
        reported here: an empty share means something different to each of the
        two, so each says that in its own words.
        """
        if result.imported:
            aantal_rijen = sum(result.imported.values())
            self.message_user(
                request,
                f"Ingelezen: {len(result.imported)} bestand(en), "
                f"{aantal_rijen} rij(en) — {', '.join(result.imported)}. "
                "De matching is niet automatisch herberekend; doe dat als "
                "aparte stap.",
                level=messages.SUCCESS,
            )

        for bestand, fout in result.failed.items():
            # One message per file: a run that imports three files and trips
            # over the fourth has to say both halves.
            self.message_user(
                request,
                f"Mislukt: {bestand} — {fout}",
                level=messages.ERROR,
            )

    @method_decorator(require_POST)
    def run_matching_view(self, request):
        """Recompute everything, then report back on the changelist.

        POST-only: this rewrites every Tijdblok, which is not something a link
        preview or a refreshed browser tab should be able to set off.

        Deliberately synchronous. There is no task queue in this app and one
        client's week of data takes well under a second, so the honest thing is
        to make the user wait and then tell him what happened, rather than add
        infrastructure to hide a wait that barely exists.

        `force=True` and no filters: the button is the common case ("I changed
        something, recompute everything"). The command keeps
        `--monteur`/`--van`/`--tot` for a targeted re-run.
        """
        # Not `self.has_change_permission()`: that is False for everyone, so the
        # form cannot be used to edit the row. Pressing the button is still a
        # change — it rewrites the timeline and this row — so it is gated on the
        # underlying Django permission the admin method would otherwise consult.
        if not request.user.has_perm("matching.change_matchmotorstatus"):
            raise PermissionDenied

        redirect_to = reverse("admin:matching_matchmotorstatus_changelist")
        try:
            result = run_matching_and_record_status(force=True)
        except Exception as exc:
            # The status row already recorded the failure; this is only to put
            # it in front of the person who pressed the button.
            self.message_user(
                request,
                f"De matching is mislukt: {exc}",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(redirect_to)

        self.message_user(
            request,
            f"Matching afgerond: {len(result.dagen)} dag(en) herberekend, "
            f"{result.aantal_blokken} tijdblok(ken).",
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(redirect_to)

    def data_resetten_view(self, request):
        """Empty the import/matching tables on purpose — everything, or a period.

        Three states on one endpoint: the form (GET), the preview of what would
        go (POST), and the reset itself (POST with the confirmation field set).
        Two POSTs rather than one, because the preview is the whole point — a
        user should see "1190 urenregels" before agreeing to it, not afterwards.

        Superuser-only, checked here rather than through a model permission:
        this is a technical repair tool, not an SBTT staff function, and it does
        not belong to any one model whose permission could carry it
        (docs/decisions.md, 07-09-2026).

        Deliberately does not reimport or recompute afterwards, for the same
        reason the file detection never reprocesses by itself: what the screen
        shows must never change without someone asking for it.
        """
        if not request.user.is_superuser:
            raise PermissionDenied

        context = {
            **self.admin_site.each_context(request),
            "title": "Data resetten",
            # What is there now, so the choice is made against real numbers
            # rather than from memory.
            "huidig": reset.tel(reset.volledige_selectie()),
            "opts": self.opts,
        }

        if request.method != "POST":
            return render(
                request,
                "admin/matching/data_resetten.html",
                {**context, "form": DataResetForm()},
            )

        form = DataResetForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "admin/matching/data_resetten.html",
                {**context, "form": form},
            )

        selectie = form.selectie()

        # The confirmation field only exists on the preview page, so a first
        # POST can never delete: it can only ever produce the preview that asks.
        if request.POST.get("bevestigd") != "ja":
            return render(
                request,
                "admin/matching/data_resetten_bevestigen.html",
                {**context, "form": form, "telling": reset.tel(selectie)},
            )

        telling = reset.verwijder(selectie)
        self.message_user(
            request,
            f"Data resetten uitgevoerd — verwijderd: {telling.samenvatting()}. "
            "Er is niets opnieuw ingelezen of herberekend; doe dat als aparte "
            "stap.",
            level=messages.SUCCESS if telling.totaal else messages.WARNING,
        )
        return HttpResponseRedirect(
            reverse("admin:matching_matchmotorstatus_changelist")
        )
