"""The models of the matching app, in two layers.

Phase 2 (data ingestion) — one table per source file, stored 1-to-1 as
delivered: no matching, no timeline reconstruction, no derived values.

Phase 3 (matching engine) — the koppeltabellen SBTT maintains itself (Monteur,
BekendeLocatie, Instelling, MeegeredenKoppeling, ToleranceRegel) plus Tijdblok,
the reconstructed day the engine writes. See the section marker further down.

Phase 4 (beheerschermen) — MatchmotorStatus, which records when the matching
last ran and how it went, so the admin can show that and offer a re-run.

Field lists follow docs/database.md.

Naming convention (docs/decisions.md, 01-09-2026): Dutch domain terms from the
format SBTT designed themselves (Werkbon, Monteur, Rit, Medewerker, the Fase
values) stay Dutch in model and field names; generic technical structure
(source_file, row_number, status timestamps) is English.
"""

import datetime as dt

from django.core.exceptions import ValidationError
from django.db import models

from matching.timeline import normalize


class SourceKind(models.TextChoices):
    """The four files the app reads from the server share.

    The values are stable identifiers used in the database; the labels are shown
    in the Dutch admin UI.
    """

    UREN = "uren", "Uren"
    RIT = "rit", "Ritten (RouteVision)"
    RELATIE = "relatie", "Relaties"
    WERKBON_CONTROLE = "werkbon_controle", "Werkbonnen (volledigheidscontrole)"


class ImportStatus(models.TextChoices):
    """Where a file sits in the detection cycle.

    Deliberately the three Dutch statuses from docs/database.md. A file that
    fails to parse stays STABIEL with `last_error` filled, so the next scheduled
    run retries it — there is no separate failure state to clear by hand.
    """

    WACHTEND = "wachtend", "Wachtend op stabiliteit"
    STABIEL = "stabiel", "Stabiel"
    VERWERKT = "verwerkt", "Verwerkt"


class ImportedFile(models.Model):
    """Bookkeeping for one file on the server share.

    This is the *only* place "already processed" is tracked. Files on the share
    are never moved or deleted and there is no separate "processed" folder (see
    docs/architecture.md).

    Every source file is tracked independently: one row per file, so a missing
    or not-yet-stable Werkbonnen.xlsx never holds up Uren.xlsx or the RouteVision
    CSV (docs/functioneel-ontwerp.md §3a).

    docs/database.md calls this table ImportBestand. The English name is used
    here because it is generic technical bookkeeping rather than a domain term
    from the SBTT format; the admin shows it as "Importbestand".
    """

    filename = models.CharField("bestandsnaam", max_length=255, unique=True)
    source_kind = models.CharField(
        "bron", max_length=32, choices=SourceKind.choices, db_index=True
    )

    # Stability tracking. `unchanged_polls` counts how many consecutive polls saw
    # `size_bytes`, including the most recent one; see matching/ingest/stability.py.
    size_bytes = models.BigIntegerField("bestandsgrootte (bytes)")
    unchanged_polls = models.PositiveIntegerField("ongewijzigde metingen", default=1)
    last_measured_at = models.DateTimeField("laatste meting")

    status = models.CharField(
        "status",
        max_length=16,
        choices=ImportStatus.choices,
        default=ImportStatus.WACHTEND,
        db_index=True,
    )
    processed_at = models.DateTimeField("verwerkt op", null=True, blank=True)
    row_count = models.PositiveIntegerField("aantal regels", null=True, blank=True)
    last_error = models.TextField("laatste foutmelding", blank=True)

    first_seen_at = models.DateTimeField("voor het eerst gezien", auto_now_add=True)

    class Meta:
        verbose_name = "importbestand"
        verbose_name_plural = "importbestanden"
        ordering = ("-last_measured_at", "filename")

    def __str__(self) -> str:
        return f"{self.filename} ({self.get_status_display()})"


class SourceRow(models.Model):
    """Shared columns for every raw imported row.

    `source_file` ties each row to the file it came from, which makes a re-import
    of that file a delete-and-insert of exactly its own rows. `row_number` is the
    1-based position in the source file, so a value can be traced back to the
    line it came from when something looks wrong.
    """

    row_number = models.PositiveIntegerField("regelnummer")

    class Meta:
        abstract = True


class Uren(SourceRow):
    """One booked-hours line from Uren.xlsx — the main matching source."""

    source_file = models.ForeignKey(
        ImportedFile, on_delete=models.CASCADE, related_name="uren_rows"
    )

    medewerker = models.CharField("medewerker", max_length=32, db_index=True)
    naam = models.CharField("naam", max_length=128, blank=True)
    werkbon = models.CharField("werkbon", max_length=32, db_index=True)
    datum = models.DateField("datum", db_index=True)
    aantal = models.DecimalField("aantal", max_digits=7, decimal_places=2, null=True)
    taak_code = models.CharField("taak code", max_length=32, blank=True)
    taak_omschrijving = models.CharField("taak omschrijving", max_length=255, blank=True)
    project_opdrachtgever_naam = models.CharField(
        "project opdrachtgever naam", max_length=255, blank=True
    )
    postcode = models.CharField("postcode", max_length=16, blank=True)
    plaats = models.CharField("plaats", max_length=128, blank=True)
    adres = models.CharField("adres", max_length=255, blank=True)
    # Never filled in the sample exports, but part of the source layout.
    begintijd = models.TimeField("begintijd", null=True, blank=True)
    eindtijd = models.TimeField("eindtijd", null=True, blank=True)

    class Meta:
        verbose_name = "urenregel"
        verbose_name_plural = "urenregels"
        ordering = ("datum", "medewerker", "row_number")
        indexes = [models.Index(fields=["medewerker", "datum"])]

    def __str__(self) -> str:
        return f"{self.datum} {self.medewerker} {self.werkbon}"


class Rit(SourceRow):
    """One trip from the RouteVision CSV — the main matching source.

    Kilometre and CO2 columns arrive with Dutch decimal commas and are stored as
    decimals; `duur` is stored as a real duration rather than a clock time.
    """

    source_file = models.ForeignKey(
        ImportedFile, on_delete=models.CASCADE, related_name="rit_rows"
    )

    kenteken = models.CharField("kenteken", max_length=32, db_index=True)
    bestuurder = models.CharField("bestuurder", max_length=128, blank=True, db_index=True)
    reis_van_de_dag = models.PositiveIntegerField("reis van de dag", null=True, blank=True)
    reistype = models.CharField("reistype", max_length=8, blank=True)

    vertrekdatum = models.DateField("vertrekdatum", null=True, blank=True, db_index=True)
    vertrektijd = models.TimeField("vertrektijd", null=True, blank=True)
    vertrekadres = models.CharField("vertrekadres", max_length=255, blank=True)
    vertrekplaats = models.CharField("vertrekplaats", max_length=128, blank=True)

    aankomstdatum = models.DateField("aankomstdatum", null=True, blank=True)
    aankomsttijd = models.TimeField("aankomsttijd", null=True, blank=True)
    aankomstadres = models.CharField("aankomstadres", max_length=255, blank=True)
    aankomstplaats = models.CharField("aankomstplaats", max_length=128, blank=True)

    duur = models.DurationField("duur", null=True, blank=True)

    km_prive = models.DecimalField(
        "privé (km)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    co2_prive = models.DecimalField(
        "privé CO2 (kg)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    km_zakelijk = models.DecimalField(
        "zakelijke (km)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    co2_zakelijk = models.DecimalField(
        "zakelijk CO2 (kg)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    km_woonwerk = models.DecimalField(
        "woon-werk (km)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    co2_woonwerk = models.DecimalField(
        "woon-werk CO2 (kg)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    km_totaal = models.DecimalField(
        "totaal (km)", max_digits=10, decimal_places=2, null=True, blank=True
    )
    co2_totaal = models.DecimalField(
        "totaal CO2 (kg)", max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Speed columns are imported because they are part of the source file
    # (docs/database.md). Using them for a speed check is separate, undecided
    # extra work with an AVG/HR angle — see docs/decisions.md.
    max_snelheid = models.PositiveIntegerField("maximum (km/u)", null=True, blank=True)
    max_snelheid_datum = models.DateField("max. snelheid datum", null=True, blank=True)
    max_snelheid_tijd = models.TimeField("max. snelheid tijd", null=True, blank=True)
    max_snelheid_adres = models.CharField("max. snelheid adres", max_length=255, blank=True)
    max_snelheid_plaats = models.CharField("max. snelheid stad", max_length=128, blank=True)

    eindstand_km = models.DecimalField(
        "eindstand (km)", max_digits=12, decimal_places=2, null=True, blank=True
    )
    opmerking = models.CharField("opmerking", max_length=255, blank=True)

    class Meta:
        verbose_name = "rit"
        verbose_name_plural = "ritten"
        ordering = ("vertrekdatum", "kenteken", "row_number")
        indexes = [models.Index(fields=["bestuurder", "vertrekdatum"])]

    def __str__(self) -> str:
        return f"{self.vertrekdatum} {self.kenteken} #{self.reis_van_de_dag}"


class Relatie(SourceRow):
    """Customer/supplier master data from Relaties.xlsx."""

    source_file = models.ForeignKey(
        ImportedFile, on_delete=models.CASCADE, related_name="relatie_rows"
    )

    code = models.CharField("code", max_length=32, db_index=True)
    relatienaam = models.CharField("relatienaam", max_length=255, blank=True)
    postcode = models.CharField("postcode", max_length=16, blank=True)
    huisnr = models.CharField("huisnr", max_length=32, blank=True)
    email = models.CharField("e-mail", max_length=255, blank=True)
    telefoon = models.CharField("telefoon", max_length=64, blank=True)

    class Meta:
        verbose_name = "relatie"
        verbose_name_plural = "relaties"
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} {self.relatienaam}".strip()


class FaseStatus(models.TextChoices):
    """Fase-status of a Werkbon, resolved from its Fase transition rows.

    Only these two matter for the completeness check (docs/business-rules.md):
    a Werkbon that is finished but has no booked hours is a real signal, one that
    has not started yet is expected.
    """

    AFGEROND = "afgerond", "Afgerond"
    NIET_GESTART = "nog niet gestart", "Nog niet gestart"


class WerkbonControle(SourceRow):
    """One Werkbon/medewerker/date from Werkbonnen.xlsx.

    Mainly for the completeness check (a finished werkbon without booked hours),
    with one exception described below.

    Every column the export offers is now stored (docs/decisions.md,
    2026-09-03). Source files on the share are never deleted, so nothing would
    have been lost by leaving them out — but capturing them in the migration this
    table needed anyway avoids a second migration and a second read-through later
    if a use ever appears. Storing is not using:

    * `postcode` is the exception, and the only field the matching reads: it is a
      fallback matching key, because it comes from the office planning rather
      than from what a monteur hand-typed into his own Uren booking. Documented
      where it is used, in matching/timeline/engine.py.
    * `titel` is shown as description text only when that fallback fires — for
      readability, never as a matching key of its own.
    * `reistijd` and `werktijd` are kept verbatim as text: their unit and format
      are not confirmed, and since nothing reads them, forcing a numeric type
      would only risk failing an import over a value nobody acts on. They stay
      out of the matching entirely — werktijd follows from the ride data
      (docs/business-rules.md).
    * `monteur_meegereden` is reserved for the SYNTESS mode of
      `Instelling.meegereden_modus`, which is deliberately disabled; nothing
      reads it yet.

    Werkbonnen.xlsx holds one row per Fase transition, and a Werkbon can appear on
    several dates. Rows are stored per (Werkbon, Medewerker, Datum) — the grain the
    completeness check needs to line up against Uren — while `fase_status` is
    resolved per Werkbon across all of its rows (see matching/ingest/parsers/werkbonnen.py).
    """

    source_file = models.ForeignKey(
        ImportedFile, on_delete=models.CASCADE, related_name="werkbon_controle_rows"
    )

    werkbon = models.CharField("werkbon", max_length=32, db_index=True)
    medewerker = models.CharField("medewerker", max_length=32, db_index=True)
    datum = models.DateField("datum", db_index=True)
    fase_status = models.CharField(
        "fase-status", max_length=32, choices=FaseStatus.choices
    )

    # Stored raw, exactly like Uren.postcode; normalised at match time by
    # matching/timeline/normalize.py rather than at parse time, so the stored
    # value stays a faithful copy of the source.
    postcode = models.CharField("postcode", max_length=10, blank=True)
    titel = models.CharField("titel", max_length=255, blank=True)
    tijd = models.TimeField("tijd", null=True, blank=True)
    reistijd = models.CharField("reistijd", max_length=32, blank=True)
    werktijd = models.CharField("werktijd", max_length=32, blank=True)
    monteur_meegereden = models.CharField(
        "monteur meegereden", max_length=16, blank=True
    )

    class Meta:
        verbose_name = "werkbon (controle)"
        verbose_name_plural = "werkbonnen (controle)"
        ordering = ("datum", "medewerker", "werkbon")
        constraints = [
            models.UniqueConstraint(
                fields=["source_file", "werkbon", "medewerker", "datum"],
                name="unique_werkbon_controle_per_file",
            )
        ]

    def __str__(self) -> str:
        return f"{self.werkbon} {self.datum} ({self.get_fase_status_display()})"


# ---------------------------------------------------------------------------
# Roadmap phase 3 — the koppeltabellen the matching engine needs, and the
# timeline it produces (docs/database.md, "Voorzien voor fase 3/4").
#
# Everything above this line is a 1-to-1 copy of a source file. Everything below
# is either data SBTT maintains itself (Monteur, BekendeLocatie, Instelling,
# MeegeredenKoppeling, ToleranceRegel) or the computed result (Tijdblok).
# ---------------------------------------------------------------------------


class Soort(models.TextChoices):
    """The SOORT-codes of a time block.

    K/L/C/W/?/O/R come from the weekly overview SBTT designed themselves in Excel
    (docs/functioneel-ontwerp.md §3b) — those are not ours to rename. P was added
    on 07-09-2026 (docs/decisions.md): without it an obviously private stop had no
    way of being cleared and stayed in the uitzonderingen list as O forever.

    Only K, L, C and P are ever chosen by hand (on a BekendeLocatie); W, ?, O and
    R always follow from the matching itself.

    Declaration order is display order everywhere the codes are totalled or
    listed (SOORT_VOLGORDE), so P sits with the other hand-assigned codes rather
    than at the end.
    """

    KLANT = "K", "Klant"
    LOCATIE = "L", "Locatie"
    CREDITEUR = "C", "Crediteur"
    PRIVE = "P", "Privé"
    WERKBON = "W", "Werkbon"
    ONBEKEND = "?", "Onbekend"
    ONVERKLAARD = "O", "Onverklaard"
    REISTIJD = "R", "Reistijd"


#: The subset a user may assign to an address by hand; see Soort above.
HANDMATIGE_SOORTEN = (Soort.KLANT, Soort.LOCATIE, Soort.CREDITEUR, Soort.PRIVE)


class Monteur(models.Model):
    """A monteur, and the bridge between the two identification systems.

    Syntess identifies people by personnel number (`Uren.medewerker`,
    `WerkbonControle.medewerker`), RouteVision by driver code (`Rit.bestuurder`).
    Without this row the two sources cannot be laid side by side at all, which
    makes it the first link the matching needs (docs/database.md).

    `bestuurder_code` is optional: a monteur who always rides along with someone
    else never drives under a code of his own. His day is then reconstructed from
    another monteur's rides — see `vaste_meerijder` and MeegeredenKoppeling.
    """

    naam = models.CharField("naam", max_length=128)
    medewerker_nummer = models.CharField(
        "personeelsnummer (Syntess)", max_length=32, unique=True, db_index=True
    )
    bestuurder_code = models.CharField(
        "bestuurderscode (RouteVision)",
        max_length=128,
        blank=True,
        help_text=(
            "Leeg laten voor een monteur die nooit onder een eigen code rijdt "
            "omdat hij altijd meerijdt."
        ),
    )
    kenteken = models.CharField("kenteken", max_length=32, blank=True)
    vaste_meerijder = models.ForeignKey(
        "self",
        verbose_name="rijdt vast mee met",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vaste_meerijders",
        help_text=(
            "De senior monteur wiens ritten de tijdlijn van deze monteur bepalen. "
            "Alleen gebruikt wanneer de meegereden-modus op 'Vast' staat."
        ),
    )
    actief = models.BooleanField("actief", default=True)

    class Meta:
        verbose_name = "monteur"
        verbose_name_plural = "monteurs"
        ordering = ("naam",)
        constraints = [
            # unique=True would trip over every second monteur without a driver
            # code, so uniqueness only applies once a code is filled in.
            models.UniqueConstraint(
                fields=["bestuurder_code"],
                condition=~models.Q(bestuurder_code=""),
                name="unique_bestuurder_code_when_set",
            )
        ]

    def __str__(self) -> str:
        return f"{self.naam} ({self.medewerker_nummer})"


class LocatieType(models.TextChoices):
    """What a BekendeLocatie is recognised by."""

    POSTCODE = "postcode", "Postcode"
    STRAAT = "straat", "Straatnaam"


class BekendeLocatie(models.Model):
    """Koppeltabel: a postcode or street that is known to be K, L or C.

    Replaces the demo file (`locaties_demo.csv`) the PoC read. `waarde` is stored
    normalised — a postcode without its space, a street name lowercased and
    without house number — so a hand-typed value is compared exactly the way the
    matching compares a RouteVision address (matching/timeline/normalize.py).

    `is_depot` marks the company's own depot/magazijn. A depot visit is
    recognised before anything else, so a stop there is never read as work for
    the customer who happens to share that address (docs/business-rules.md:
    "een depotbezoek vóór het werk wordt herkend").
    """

    type = models.CharField(
        "herkenning", max_length=16, choices=LocatieType.choices, db_index=True
    )
    waarde = models.CharField(
        "waarde",
        max_length=255,
        help_text="Postcode (4104 AC) of straatnaam (Randweg) — huisnummer weglaten.",
    )
    soort = models.CharField(
        "SOORT",
        max_length=1,
        choices=[(soort.value, soort.label) for soort in HANDMATIGE_SOORTEN],
    )
    label = models.CharField("omschrijving", max_length=255)
    is_depot = models.BooleanField(
        "is depot",
        default=False,
        help_text="Eigen magazijn/zaak: wordt vóór alle andere regels herkend.",
    )

    class Meta:
        verbose_name = "bekende locatie"
        verbose_name_plural = "bekende locaties"
        ordering = ("type", "waarde")
        unique_together = (("type", "waarde"),)

    def __str__(self) -> str:
        return f"{self.waarde} ({self.get_soort_display()}) - {self.label}"

    def clean(self):
        self.waarde = self.normalised_waarde()
        if not self.waarde:
            raise ValidationError({"waarde": "Vul een postcode of straatnaam in."})

    def save(self, *args, **kwargs):
        # Normalised on every write, not only through the admin form: a value
        # that skipped normalisation would silently never match anything.
        self.waarde = self.normalised_waarde()
        super().save(*args, **kwargs)

    def normalised_waarde(self) -> str:
        if self.type == LocatieType.POSTCODE:
            return normalize.postcode(self.waarde)
        return normalize.street(self.waarde)


class MeegeredenModus(models.TextChoices):
    """How a monteur who rides along gets his ride data assigned.

    Three modes, one global setting (docs/decisions.md, 03-09-2026). SYNTESS is a
    reserved choice with no logic behind it: Syntess does not fill its "Monteur
    meegereden" column reliably yet, so `WerkbonControle` deliberately does not
    even store that column. Enabling it is a separate, later decision.
    """

    VAST = "VAST", "Vast — permanent aan één senior gekoppeld"
    PERIODE = "PERIODE", "Periode — koppeltabel met geldigheidsperiode"
    SYNTESS = "SYNTESS", "Uit Syntess (nog niet beschikbaar)"


#: Primary key of the one Instelling row. A module constant because a nested
#: Meta class cannot read a class attribute of the model it belongs to.
INSTELLING_SINGLETON_PK = 1


class Instelling(models.Model):
    """App-wide configuration — exactly one row.

    Settings that hold for the whole app rather than per record. Read it with
    `Instelling.load()`, which creates the single row on first use so no caller
    has to handle an empty table.
    """

    #: The one and only row.
    SINGLETON_PK = INSTELLING_SINGLETON_PK

    meegereden_modus = models.CharField(
        "meegereden-modus",
        max_length=16,
        choices=MeegeredenModus.choices,
        default=MeegeredenModus.VAST,
    )

    class Meta:
        verbose_name = "instelling"
        verbose_name_plural = "instellingen"
        constraints = [
            # save() pins the primary key, and this makes that a guarantee rather
            # than a convention: a second row can never be inserted, not even by
            # a fixture or a hand-written query.
            models.CheckConstraint(
                condition=models.Q(id=INSTELLING_SINGLETON_PK),
                name="instelling_is_singleton",
            )
        ]

    def __str__(self) -> str:
        return "Instellingen"

    @classmethod
    def load(cls) -> "Instelling":
        """The singleton row, created with its defaults if it does not exist yet."""
        instelling, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return instelling

    def clean(self):
        self._check_meegereden_modus()

    def save(self, *args, **kwargs):
        # Pinning the primary key is what makes this a singleton: a second row
        # can only ever overwrite the first one.
        self.pk = self.SINGLETON_PK
        # save() bypasses clean(), so the disabled mode is rejected here as well:
        # otherwise a script or a fixture could store a mode that has no logic
        # behind it, and the matching would silently fall back to something else.
        self._check_meegereden_modus()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "De instellingen kunnen niet verwijderd worden; pas ze aan in plaats "
            "daarvan."
        )

    def _check_meegereden_modus(self):
        if self.meegereden_modus == MeegeredenModus.SYNTESS:
            raise ValidationError(
                {
                    "meegereden_modus": (
                        "De stand 'Uit Syntess' staat uit: Syntess vult de kolom "
                        "'Monteur meegereden' nog niet betrouwbaar. Kies 'Vast' of "
                        "'Periode'."
                    )
                }
            )


class MeegeredenKoppeling(models.Model):
    """Koppeltabel: which senior a junior rode along with, and between which dates.

    Only consulted when `Instelling.meegereden_modus` is PERIODE. An empty
    `datum_tot` means open-ended: the koppeling still applies.
    """

    junior = models.ForeignKey(
        Monteur,
        verbose_name="monteur die meerijdt",
        on_delete=models.CASCADE,
        related_name="meegereden_als_junior",
    )
    senior = models.ForeignKey(
        Monteur,
        verbose_name="rijdt mee met",
        on_delete=models.CASCADE,
        related_name="meegereden_als_senior",
    )
    datum_van = models.DateField("geldig van")
    datum_tot = models.DateField(
        "geldig tot en met",
        null=True,
        blank=True,
        help_text="Leeg laten wanneer de koppeling nog loopt.",
    )

    class Meta:
        verbose_name = "meegereden-koppeling"
        verbose_name_plural = "meegereden-koppelingen"
        ordering = ("junior", "-datum_van")
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(junior=models.F("senior")),
                name="meegereden_junior_is_not_senior",
            )
        ]

    def __str__(self) -> str:
        tot = self.datum_tot.isoformat() if self.datum_tot else "heden"
        return f"{self.junior} rijdt mee met {self.senior} ({self.datum_van} - {tot})"

    def clean(self):
        if self.junior_id and self.junior_id == self.senior_id:
            raise ValidationError(
                {"senior": "Een monteur kan niet met zichzelf meerijden."}
            )
        if self.datum_van and self.datum_tot and self.datum_tot < self.datum_van:
            raise ValidationError({"datum_tot": "De einddatum ligt vóór de begindatum."})
        self._check_no_overlap()

    def _check_no_overlap(self):
        """No two koppelingen for the same junior may cover the same day.

        A junior rides along with one senior at a time, and the matching resolves
        exactly one bronmonteur per day — two overlapping rows would make that
        choice arbitrary (matching/timeline/meegereden.py picks the most recently
        started one, which is a tie-breaker, not an intention).

        Two details, both taken from `geldt_op()` below so validation and
        resolution agree on what a period means:

        * An empty `datum_tot` is open-ended, so it is compared as if it ran
          infinitely far into the future — not as "no end, therefore no overlap".
        * Both ends are inclusive, so periods sharing a single boundary day
          overlap: a junior cannot be reassigned to another senior on a day he
          already rode with the first one.
        """
        if not self.junior_id or not self.datum_van:
            return

        eigen_tot = self.datum_tot or dt.date.max
        andere = MeegeredenKoppeling.objects.filter(junior_id=self.junior_id).exclude(
            pk=self.pk
        )
        for ander in andere:
            ander_tot = ander.datum_tot or dt.date.max
            if self.datum_van <= ander_tot and ander.datum_van <= eigen_tot:
                raise ValidationError(
                    {
                        "datum_van": (
                            "Overlapt met een bestaande koppeling van "
                            f"{ander.junior} met {ander.senior} "
                            f"({ander.datum_van} – {ander.datum_tot or 'heden'})."
                        )
                    }
                )

    def geldt_op(self, datum) -> bool:
        """Whether this koppeling covers `datum`."""
        if datum < self.datum_van:
            return False
        return self.datum_tot is None or datum <= self.datum_tot


class ToleranceRegel(models.Model):
    """Tolerantietabel: from how many minutes an unexplained stop counts as one.

    Replaces the PoC's hardcoded DREMPEL of 15 minutes. `activiteit` is a free
    key with one seeded row, "algemeen", which every lookup falls back on. The
    per-activity values still have to be confirmed with the customer
    (docs/functioneel-ontwerp.md §9, point 2), so the table starts with only that
    default.
    """

    #: The row every lookup falls back on.
    ALGEMEEN = "algemeen"

    activiteit = models.CharField("activiteit", max_length=128, unique=True)
    drempel_minuten = models.PositiveIntegerField("drempel (minuten)", default=15)

    class Meta:
        verbose_name = "tolerantieregel"
        verbose_name_plural = "tolerantietabel"
        ordering = ("activiteit",)

    def __str__(self) -> str:
        return f"{self.activiteit}: {self.drempel_minuten} min"


class Tijdblok(models.Model):
    """One block of a reconstructed day — the result of the matching.

    Stored rather than recomputed per page view, so phase 5 (uitzonderingen) and
    phase 6 (weekoverzicht) build on stable data. Recomputing is explicit, via
    `python manage.py run_matching --force`, which is what you run after changing
    a koppeltabel (docs/database.md).

    `werkbon` is free text on purpose: there is no Werkbon entity anywhere in
    this app — phase 2 stores werkbon numbers as plain values too.

    `postcode` and `straat` hold the normalised matching keys of the stop, next
    to the composed `adres` text that is only there to be displayed. They are
    stored rather than derived later because the uitzonderingenscherm (phase 5)
    groups and counts by them: re-parsing them out of `adres` works today, but
    would break silently the moment that display string changes shape
    (docs/decisions.md, 2026-09-03).

    No WB-vs-SYS signal field: that part of the PoC is deliberately not built
    (docs/decisions.md, 02-09-2026).
    """

    monteur = models.ForeignKey(
        Monteur, on_delete=models.CASCADE, related_name="tijdblokken"
    )
    datum = models.DateField("datum", db_index=True)
    volgorde = models.PositiveIntegerField("volgorde")

    soort = models.CharField("SOORT", max_length=1, choices=Soort.choices)
    start_tijd = models.DateTimeField("starttijd")
    eind_tijd = models.DateTimeField("eindtijd")
    duur_minuten = models.PositiveIntegerField("duur (minuten)")

    omschrijving = models.CharField("omschrijving", max_length=255, blank=True)
    adres = models.CharField("adres", max_length=512, blank=True)
    # Indexed because the uitzonderingenscherm groups and counts on these two.
    postcode = models.CharField("postcode", max_length=6, blank=True, db_index=True)
    straat = models.CharField("straat", max_length=255, blank=True, db_index=True)
    werkbon = models.CharField("werkbon", max_length=32, blank=True, db_index=True)

    berekend_op = models.DateTimeField("berekend op", auto_now=True)

    class Meta:
        verbose_name = "tijdblok"
        verbose_name_plural = "tijdblokken"
        ordering = ("datum", "monteur", "volgorde")
        unique_together = (("monteur", "datum", "volgorde"),)
        indexes = [models.Index(fields=["monteur", "datum"])]

    def __str__(self) -> str:
        return f"{self.datum} {self.monteur.naam} #{self.volgorde} {self.soort}"

    @property
    def koppelsleutel(self) -> tuple[str, str] | None:
        """How this block is addressed when it is linked to a BekendeLocatie.

        Postcode first, street as fallback: the postcode is the more precise key
        and RouteVision supplies one for nearly every stop, so grouping on the
        street would merge two different addresses in the same street.

        Lives on the model because two screens depend on producing the *same*
        key — the uitzonderingenscherm groups its list by it (phase 5) and the
        weekoverzicht links an O block straight to that group (phase 6). If the
        two ever disagreed, the link would open a form about another address.

        None for a block with neither key: there is nothing to link it to. In
        practice only blocks from before these two fields existed
        (`run_matching --force` fills them in).
        """
        if self.postcode:
            return (LocatieType.POSTCODE, self.postcode)
        if self.straat:
            return (LocatieType.STRAAT, self.straat)
        return None


# ---------------------------------------------------------------------------
# Roadmap phase 4 — the beheerschermen.
# ---------------------------------------------------------------------------


#: Primary key of the one MatchmotorStatus row. See INSTELLING_SINGLETON_PK.
MATCHMOTOR_STATUS_SINGLETON_PK = 1


class MatchmotorStatus(models.Model):
    """When the matching last ran, and how it went — exactly one row.

    The matching is never scheduled: it only runs when someone asks for it
    (docs/database.md). That makes "when did this last run, and did it work"
    a real question, and the admin has nowhere else to read the answer from.

    Both trigger paths — the `run_matching` command and the admin's "matching nu
    draaien" button — go through
    `matching.timeline.runner.run_matching_and_record_status`, so this row is
    accurate regardless of who started a run.
    """

    #: The one and only row.
    SINGLETON_PK = MATCHMOTOR_STATUS_SINGLETON_PK

    # Written before the run rather than after, so a run that crashes or is
    # killed still leaves a trace that it was attempted.
    laatste_run_gestart_op = models.DateTimeField(
        "laatste run gestart op", null=True, blank=True
    )
    laatste_run_afgerond_op = models.DateTimeField(
        "laatste run afgerond op", null=True, blank=True
    )
    # Three states, not two: null is "nog nooit gedraaid", which is not the same
    # signal as False ("de laatste run is mislukt").
    succes = models.BooleanField("gelukt", null=True, blank=True)
    dagen_verwerkt = models.PositiveIntegerField("dagen verwerkt", default=0)
    foutmelding = models.TextField("foutmelding", blank=True)

    class Meta:
        verbose_name = "matchmotor-status"
        verbose_name_plural = "matchmotor-status"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id=MATCHMOTOR_STATUS_SINGLETON_PK),
                name="matchmotor_status_is_singleton",
            )
        ]

    def __str__(self) -> str:
        return "Matchmotor-status"

    @classmethod
    def load(cls) -> "MatchmotorStatus":
        """The singleton row, created with its defaults if it does not exist yet."""
        status, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return status

    def save(self, *args, **kwargs):
        # Pinning the primary key is what makes this a singleton: a second row
        # can only ever overwrite the first one.
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "De matchmotor-status kan niet verwijderd worden; hij wordt bij elke "
            "run overschreven."
        )
