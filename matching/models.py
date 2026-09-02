"""Raw import models for roadmap phase 2 (data ingestion).

One table per source file, stored 1-to-1 as delivered — no matching, no timeline
reconstruction, no derived values. Field lists follow docs/database.md.

Naming convention (docs/decisions.md, 01-09-2026): Dutch domain terms from the
format SBTT designed themselves (Werkbon, Monteur, Rit, Medewerker, the Fase
values) stay Dutch in model and field names; generic technical structure
(source_file, row_number, status timestamps) is English.
"""

from django.db import models


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
    """One Werkbon/medewerker/date from Werkbonnen.xlsx, for the completeness check only.

    Never an input for the matching itself (docs/business-rules.md). Reistijd,
    Werktijd, Titel and "Monteur meegereden" are deliberately not stored: they are
    unreliable and unused anywhere in the design.

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
