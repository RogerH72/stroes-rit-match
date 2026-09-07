"""Tests for the "Data resetten" admin action.

Two modes with one rule in common: nothing outside the six import/matching
tables may ever be touched, and nothing is deleted until a second, explicit
confirmation. The koppeltabellen are what SBTT maintains by hand, so a reset
losing them would cost real work — that is what most of these tests are for.
"""

from __future__ import annotations

import datetime as dt

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from matching import reset
from matching.forms import DataResetForm
from matching.models import (
    BekendeLocatie,
    ImportedFile,
    Instelling,
    MatchmotorStatus,
    MeegeredenKoppeling,
    Monteur,
    Relatie,
    Rit,
    SourceKind,
    Tijdblok,
    ToleranceRegel,
    Uren,
    WerkbonControle,
)
from matching.tests import factories

JULI = dt.date(2026, 7, 15)
AUGUSTUS = dt.date(2026, 8, 12)

RESET_URL = "admin:matching_data_resetten"

# The tables a reset may never touch, whichever mode ran.
KOPPELTABELLEN = (
    Monteur,
    BekendeLocatie,
    Instelling,
    MeegeredenKoppeling,
    ToleranceRegel,
    MatchmotorStatus,
)


def _tijdblok(monteur: Monteur, datum: dt.date) -> Tijdblok:
    return Tijdblok.objects.create(
        monteur=monteur,
        datum=datum,
        volgorde=1,
        soort="W",
        start_tijd=dt.datetime.combine(datum, dt.time(8, 0), dt.timezone.utc),
        eind_tijd=dt.datetime.combine(datum, dt.time(9, 0), dt.timezone.utc),
        duur_minuten=60,
    )


class ResetDataMixin:
    """Two days of data in every table, one in July and one in August.

    Split over two months so a period reset has something it must leave alone —
    a reset that quietly deleted everything would otherwise pass the period
    tests too.
    """

    @classmethod
    def vul_database(cls):
        cls.monteur = factories.monteur("Berg D", "002", "Dennis van de Berg")
        cls.andere_monteur = factories.monteur("Vor M.", "030", "Mike de Vor")

        for datum in (JULI, AUGUSTUS):
            factories.urenregel("002", datum, f"W{datum.month}000")
            factories.rit("Dennis van de Berg", datum, "08:00", "09:00")
            factories.werkbon_controle(f"W{datum.month}000", "002", datum, "Afgerond")
            _tijdblok(cls.monteur, datum)

        Relatie.objects.create(
            source_file=factories.import_bestand(SourceKind.RELATIE),
            row_number=2,
            code="0001",
            relatienaam="Syntess Software",
        )

        factories.bekende_locatie("postcode", "4104AC", "L")
        ToleranceRegel.objects.create(activiteit="Storing", drempel_minuten=15)
        MeegeredenKoppeling.objects.create(
            junior=cls.andere_monteur, senior=cls.monteur, datum_van=JULI
        )
        Instelling.load()
        MatchmotorStatus.load()

        # Each factory call hangs its row off its own ImportedFile, so the exact
        # number is the factories' business, not this test's.
        cls.aantal_bestanden = ImportedFile.objects.count()

    def bewaarde_aantallen(self) -> dict[str, int]:
        return {model.__name__: model.objects.count() for model in KOPPELTABELLEN}


class ResetLogicaTests(ResetDataMixin, TestCase):
    """The counting and deleting itself, without the admin around it."""

    @classmethod
    def setUpTestData(cls):
        cls.vul_database()

    def test_volledige_selectie_dekt_precies_zes_tabellen(self):
        self.assertEqual(
            set(reset.volledige_selectie()),
            {Tijdblok, Uren, Rit, Relatie, WerkbonControle, ImportedFile},
        )

    def test_periode_selectie_laat_relatie_en_importedfile_erbuiten(self):
        selectie = reset.periode_selectie(JULI, AUGUSTUS)
        self.assertEqual(set(selectie), {Tijdblok, Uren, Rit, WerkbonControle})

    def test_tellen_verwijdert_niets(self):
        telling = reset.tel(reset.volledige_selectie())

        self.assertEqual(telling.per_model[Uren], 2)
        self.assertEqual(Uren.objects.count(), 2)
        self.assertEqual(Tijdblok.objects.count(), 2)
        self.assertEqual(ImportedFile.objects.count(), self.aantal_bestanden)

    def test_volledig_maakt_alle_zes_tabellen_leeg(self):
        bewaard = self.bewaarde_aantallen()
        reset.verwijder(reset.volledige_selectie())

        for model in (Uren, Rit, Relatie, WerkbonControle, Tijdblok, ImportedFile):
            with self.subTest(model=model.__name__):
                self.assertEqual(model.objects.count(), 0)
        self.assertEqual(self.bewaarde_aantallen(), bewaard)

    def test_periode_raakt_alleen_de_dagen_in_het_bereik(self):
        reset.verwijder(reset.periode_selectie(AUGUSTUS, AUGUSTUS))

        self.assertEqual([u.datum for u in Uren.objects.all()], [JULI])
        self.assertEqual([r.vertrekdatum for r in Rit.objects.all()], [JULI])
        self.assertEqual([w.datum for w in WerkbonControle.objects.all()], [JULI])
        self.assertEqual([t.datum for t in Tijdblok.objects.all()], [JULI])

    def test_periode_laat_relaties_en_bestandsadministratie_staan(self):
        # A period reset must not quietly forget that a source file was
        # processed: re-reading one stays `check_imports --reprocess`.
        relaties, bestanden = Relatie.objects.count(), ImportedFile.objects.count()
        reset.verwijder(reset.periode_selectie(JULI, AUGUSTUS))

        self.assertEqual(Relatie.objects.count(), relaties)
        self.assertEqual(ImportedFile.objects.count(), bestanden)

    def test_periode_is_inclusief_aan_beide_kanten(self):
        self.assertEqual(reset.tel(reset.periode_selectie(JULI, AUGUSTUS)).totaal, 8)
        self.assertEqual(reset.tel(reset.periode_selectie(JULI, JULI)).totaal, 4)

    def test_periode_laat_de_koppeltabellen_staan(self):
        bewaard = self.bewaarde_aantallen()
        reset.verwijder(reset.periode_selectie(JULI, AUGUSTUS))
        self.assertEqual(self.bewaarde_aantallen(), bewaard)

    def test_een_rit_zonder_vertrekdatum_valt_in_geen_enkele_periode(self):
        rit = Rit.objects.first()
        rit.vertrekdatum = None
        rit.save(update_fields=["vertrekdatum"])

        reset.verwijder(reset.periode_selectie(dt.date(2000, 1, 1), dt.date(2100, 1, 1)))

        self.assertEqual(Rit.objects.count(), 1)

    def test_telling_rapporteert_wat_er_werkelijk_weg_ging(self):
        telling = reset.verwijder(reset.periode_selectie(AUGUSTUS, AUGUSTUS))

        self.assertEqual(telling.per_model[Uren], 1)
        self.assertEqual(telling.per_model[Tijdblok], 1)
        self.assertEqual(telling.totaal, 4)

    def test_samenvatting_noemt_alleen_gevulde_tabellen(self):
        telling = reset.tel(reset.periode_selectie(JULI, JULI))
        self.assertIn("1 urenregels", telling.samenvatting())

        leeg = reset.tel(reset.periode_selectie(dt.date(1999, 1, 1), dt.date(1999, 1, 2)))
        self.assertEqual(leeg.samenvatting(), "niets")


class DataResetFormTests(TestCase):
    def test_periode_vereist_beide_datums(self):
        form = DataResetForm({"modus": DataResetForm.MODUS_PERIODE})

        self.assertFalse(form.is_valid())
        self.assertIn("van", form.errors)
        self.assertIn("tot", form.errors)

    def test_omgekeerd_bereik_wordt_geweigerd(self):
        form = DataResetForm(
            {"modus": DataResetForm.MODUS_PERIODE, "van": AUGUSTUS, "tot": JULI}
        )

        self.assertFalse(form.is_valid())
        self.assertIn("tot", form.errors)

    def test_volledig_negeert_achtergebleven_datums(self):
        # Switching modes in the browser leaves the date inputs filled; they must
        # not narrow a full wipe into a period.
        form = DataResetForm(
            {"modus": DataResetForm.MODUS_VOLLEDIG, "van": JULI, "tot": JULI}
        )

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["van"])
        self.assertEqual(len(form.selectie()), 6)


class DataResetAdminTests(ResetDataMixin, TestCase):
    """The screen: who may open it, and that nothing goes without confirming."""

    @classmethod
    def setUpTestData(cls):
        cls.vul_database()
        cls.superuser = User.objects.create_superuser("roger", "r@x.nl", "geheim")
        cls.beheerder = User.objects.create_user(
            "wim", "w@sbtt.nl", "geheim", is_staff=True, is_superuser=False
        )
        # Every permission the app defines, deliberately: the point of the gate
        # is that permissions are not what opens this screen.
        cls.beheerder.user_permissions.set(Permission.objects.all())
        cls.url = reverse(RESET_URL)

    def test_een_gewone_beheerder_komt_er_niet_in(self):
        # Deliberately gated on is_superuser rather than a model permission, so a
        # staff account holding every permission in the app is still refused.
        self.client.force_login(self.beheerder)

        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(
            self.client.post(
                self.url,
                {"modus": DataResetForm.MODUS_VOLLEDIG, "bevestigd": "ja"},
            ).status_code,
            403,
        )
        self.assertEqual(Uren.objects.count(), 2)

    def test_uitgelogd_leidt_naar_de_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_het_formulier_opent_voor_een_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/matching/data_resetten.html")

    def test_eerste_post_toont_alleen_een_preview(self):
        self.client.force_login(self.superuser)
        response = self.client.post(self.url, {"modus": DataResetForm.MODUS_VOLLEDIG})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "admin/matching/data_resetten_bevestigen.html"
        )
        self.assertEqual(response.context["telling"].per_model[Uren], 2)
        # The whole point of the preview: everything is still there.
        self.assertEqual(Uren.objects.count(), 2)
        self.assertEqual(Tijdblok.objects.count(), 2)
        self.assertEqual(ImportedFile.objects.count(), self.aantal_bestanden)

    def test_preview_van_een_periode_telt_alleen_dat_bereik(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.url,
            {
                "modus": DataResetForm.MODUS_PERIODE,
                "van": AUGUSTUS.isoformat(),
                "tot": AUGUSTUS.isoformat(),
            },
        )

        self.assertEqual(response.context["telling"].totaal, 4)
        self.assertEqual(Uren.objects.count(), 2)

    def test_bevestigde_post_maakt_volledig_leeg(self):
        self.client.force_login(self.superuser)
        bewaard = self.bewaarde_aantallen()
        response = self.client.post(
            self.url,
            {"modus": DataResetForm.MODUS_VOLLEDIG, "bevestigd": "ja"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Uren.objects.count(), 0)
        self.assertEqual(ImportedFile.objects.count(), 0)
        self.assertEqual(self.bewaarde_aantallen(), bewaard)

    def test_bevestigde_periode_post_verwijdert_alleen_dat_bereik(self):
        self.client.force_login(self.superuser)
        self.client.post(
            self.url,
            {
                "modus": DataResetForm.MODUS_PERIODE,
                "van": AUGUSTUS.isoformat(),
                "tot": AUGUSTUS.isoformat(),
                "bevestigd": "ja",
            },
            follow=True,
        )

        self.assertEqual([u.datum for u in Uren.objects.all()], [JULI])
        self.assertEqual(ImportedFile.objects.count(), self.aantal_bestanden)

    def test_een_ongeldig_bereik_verwijdert_niets(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.url,
            {
                "modus": DataResetForm.MODUS_PERIODE,
                "van": AUGUSTUS.isoformat(),
                "tot": JULI.isoformat(),
                "bevestigd": "ja",
            },
        )

        self.assertTemplateUsed(response, "admin/matching/data_resetten.html")
        self.assertEqual(Uren.objects.count(), 2)

    def test_de_reset_herberekent_niets(self):
        # Reimporting and rematching stay separate, deliberate steps, so the
        # status row must look untouched afterwards.
        self.client.force_login(self.superuser)
        voor = MatchmotorStatus.load().laatste_run_afgerond_op

        self.client.post(
            self.url,
            {"modus": DataResetForm.MODUS_VOLLEDIG, "bevestigd": "ja"},
            follow=True,
        )

        self.assertEqual(MatchmotorStatus.load().laatste_run_afgerond_op, voor)

    def test_de_link_staat_alleen_op_het_scherm_voor_superusers(self):
        changelist = reverse("admin:matching_matchmotorstatus_changelist")

        self.client.force_login(self.superuser)
        self.assertContains(self.client.get(changelist), "Data resetten")

        self.client.force_login(self.beheerder)
        self.assertNotContains(self.client.get(changelist), "Data resetten")
