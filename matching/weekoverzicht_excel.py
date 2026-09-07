"""The weekoverzicht as an .xlsx workbook (roadmap phase 6).

Deliberately the same content and the same SOORT colours as the web page: the
export exists so Wim can mail a week to someone or keep it next to his own
sheets, not so he gets a second, different overview. `matching/weekoverzicht.py`
assembles the week; this module only lays it out.

Written with openpyxl, which is already a dependency for reading the Syntess
exports (requirements.txt) — no extra package for the writing side.
"""

from __future__ import annotations

import datetime as dt
import io
import re
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from matching.models import Soort
from matching.weekoverzicht import SOORT_KLEUREN, DagOverzicht, WeekOverzicht

#: The six columns of a day table — the prototype's columns minus WB and ⚑
#: (docs/functioneel-ontwerp.md §3b: the WB-vs-SYS signal is not built).
KOLOMMEN = ["Aankomst", "Vertrek", "Tijd", "SOORT", "Omschrijving", "Adres"]
KOLOMBREEDTES = [11, 11, 9, 8, 46, 52]

#: Column indexes used by name, so a layout change stays a one-line edit.
KOL_TIJD = 3
KOL_SOORT = 4
KOL_OMSCHRIJVING = 5

NAVY = "133B78"
GRIJS = "F2F2F2"
LICHTGRIJS = "FAFBFC"
WAARSCHUWING = "D97706"
RAND = "E3E3E3"

#: Two decimals, and a leading sign on the difference so "te veel" and "te
#: weinig geboekt" are distinguishable at a glance.
UREN_FORMAAT = "0.00"
VERSCHIL_FORMAAT = "+0.00;-0.00;0.00"

_ONVEILIG = re.compile(r"[^A-Za-z0-9]+")


def bestandsnaam(overzicht: WeekOverzicht) -> str:
    """A filename a user can drop in a folder and still recognise later."""
    monteur = _ONVEILIG.sub("-", overzicht.monteur.naam).strip("-") or "monteur"
    return f"RMW-weekoverzicht-{overzicht.waarde}-{monteur}.xlsx"


def bouw_werkboek(overzicht: WeekOverzicht) -> bytes:
    """The whole week as one worksheet, in the order the web page shows it."""
    workbook = Workbook()
    blad = workbook.active
    blad.title = f"Week {overzicht.week:02d}"

    for kolom, breedte in enumerate(KOLOMBREEDTES, start=1):
        blad.column_dimensions[get_column_letter(kolom)].width = breedte

    regel = _kop(blad, overzicht, start=1)
    regel = _weektotaal(blad, overzicht, start=regel)
    for dag in overzicht.dagen:
        regel = _dag(blad, dag, start=regel)

    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


# --- the parts of the sheet -------------------------------------------------


def _kop(blad: Worksheet, overzicht: WeekOverzicht, *, start: int) -> int:
    """Title, period, and — when the week is incomplete — the warning."""
    regel = start
    _cel(blad, regel, 1, "RMW-weekoverzicht", bold=True, size=15)
    regel += 1
    _cel(
        blad,
        regel,
        1,
        f"{overzicht.monteur.naam} ({overzicht.monteur.medewerker_nummer}) · "
        f"week {overzicht.week:02d} · "
        f"{_datum(overzicht.maandag)} t/m {_datum(overzicht.zondag)}"
        + (f" · bus {overzicht.monteur.kenteken}" if overzicht.monteur.kenteken else ""),
    )
    regel += 1
    _cel(
        blad,
        regel,
        1,
        "Tijden komen uit RouteVision; de werktijd volgt uit de ritten, niet uit "
        "de door de monteur ingevulde werkbontijd.",
        italic=True,
        kleur="5C5C5C",
    )
    regel += 2

    if overzicht.ontbrekende_dagen:
        # The same warning the page carries: a week total that quietly leaves
        # days out is worse than no total at all.
        _cel(
            blad,
            regel,
            1,
            "Let op — onvolledige week. Geen ritgegevens voor: "
            + "; ".join(_ontbrekend(dag) for dag in overzicht.ontbrekende_dagen)
            + ". De totalen hieronder gaan alleen over de dagen die er wél zijn.",
            bold=True,
            kleur="FFFFFF",
            vulling=WAARSCHUWING,
        )
        regel += 2

    _cel(blad, regel, 1, "Legenda", bold=True)
    regel += 1
    for kolom, soort in enumerate(Soort, start=1):
        _cel(
            blad,
            regel,
            kolom,
            f"{soort.value}  {soort.label}",
            kleur="FFFFFF",
            bold=True,
            vulling=SOORT_KLEUREN[soort.value].lstrip("#"),
            centreren=True,
        )
    return regel + 2


def _weektotaal(blad: Worksheet, overzicht: WeekOverzicht, *, start: int) -> int:
    """The week's SOORT totals and the gefactureerd/op-locatie comparison."""
    regel = _sectiekop(blad, "Weektotaal", start=start)
    regel = _totaalblok(
        blad,
        regel,
        totalen=overzicht.totalen,
        totaal=overzicht.totaal,
        totaal_label="Totaal week",
        gefactureerd=overzicht.gefactureerde_uren,
        op_locatie=overzicht.uren_op_locatie,
        verschil=overzicht.verschil,
    )
    return regel + 1


def _dag(blad: Worksheet, dag: DagOverzicht, *, start: int) -> int:
    """One day: header, block rows, and the day's own totals."""
    regel = _sectiekop(
        blad, f"{_dagnaam(dag.datum)} {_datum(dag.datum)} · totaal {dag.totaal}", start=start
    )

    for kolom, naam in enumerate(KOLOMMEN, start=1):
        _cel(blad, regel, kolom, naam, bold=True, vulling=GRIJS, rand=True)
    regel += 1

    for rij in dag.regels:
        achtergrond = LICHTGRIJS if rij.is_reistijd else None
        _cel(blad, regel, 1, rij.start.strftime("%H:%M"), centreren=True, vulling=achtergrond, rand=True)
        _cel(blad, regel, 2, rij.eind.strftime("%H:%M"), centreren=True, vulling=achtergrond, rand=True)
        _cel(blad, regel, 3, rij.duur, centreren=True, bold=True, vulling=achtergrond, rand=True)
        # The SOORT cell carries the colour, exactly like the pill on the page.
        _cel(
            blad,
            regel,
            4,
            rij.blok.soort,
            centreren=True,
            bold=True,
            kleur="FFFFFF",
            vulling=rij.kleur.lstrip("#"),
            rand=True,
        )
        _cel(blad, regel, 5, rij.blok.omschrijving, vulling=achtergrond, rand=True)
        _cel(blad, regel, 6, rij.blok.adres, vulling=achtergrond, kleur="5C5C5C", rand=True)
        regel += 1

    regel = _totaalblok(
        blad,
        regel,
        totalen=dag.totalen,
        totaal=dag.totaal,
        totaal_label="Totaal dag",
        gefactureerd=dag.gefactureerde_uren,
        op_locatie=dag.uren_op_locatie,
        verschil=dag.verschil,
    )
    return regel + 1


def _totaalblok(
    blad: Worksheet,
    regel: int,
    *,
    totalen,
    totaal: str,
    totaal_label: str,
    gefactureerd: Decimal,
    op_locatie: Decimal,
    verschil: Decimal,
) -> int:
    """Per-SOORT totals, the overall total, and the hours comparison.

    Written in the same columns as the block rows above it (time, code,
    description) rather than as a sentence, so the numbers stay sortable and
    readable as numbers — an Excel export that only holds prose would be no
    better than a screenshot.
    """
    for soort_totaal in totalen:
        _cel(blad, regel, KOL_TIJD, soort_totaal.tijd, centreren=True)
        _cel(
            blad,
            regel,
            KOL_SOORT,
            soort_totaal.code,
            centreren=True,
            bold=True,
            kleur="FFFFFF",
            vulling=soort_totaal.kleur.lstrip("#"),
        )
        _cel(blad, regel, KOL_OMSCHRIJVING, soort_totaal.label, kleur="5C5C5C")
        regel += 1

    _cel(blad, regel, KOL_TIJD, totaal, centreren=True, bold=True)
    _cel(blad, regel, KOL_OMSCHRIJVING, totaal_label, bold=True)
    regel += 1

    for label, waarde, formaat in (
        ("Totaal (excl. reistijd) (Uren.xlsx)", gefactureerd, UREN_FORMAAT),
        ("Uren op locatie (SOORT W)", op_locatie, UREN_FORMAAT),
        ("Verschil", verschil, VERSCHIL_FORMAAT),
    ):
        # Real numbers, not "8,50 u" text: this is the figure a planner wants to
        # sort, filter and total further in his own sheet.
        cel = _cel(blad, regel, KOL_TIJD, float(waarde), centreren=True)
        cel.number_format = formaat
        _cel(blad, regel, KOL_OMSCHRIJVING, label, bold=label == "Verschil")
        regel += 1
    return regel


def _sectiekop(blad: Worksheet, tekst: str, *, start: int) -> int:
    """A full-width navy bar, the way the page separates its days."""
    blad.merge_cells(
        start_row=start, start_column=1, end_row=start, end_column=len(KOLOMMEN)
    )
    _cel(blad, start, 1, tekst, bold=True, kleur="FFFFFF", vulling=NAVY)
    return start + 1


# --- small helpers ----------------------------------------------------------


def _cel(
    blad: Worksheet,
    regel: int,
    kolom: int,
    waarde,
    *,
    bold: bool = False,
    italic: bool = False,
    size: int | None = None,
    kleur: str | None = None,
    vulling: str | None = None,
    centreren: bool = False,
    rand: bool = False,
):
    """Write one cell and style it; returns the cell for further tweaking."""
    cel = blad.cell(row=regel, column=kolom, value=waarde)
    if bold or italic or kleur or size:
        cel.font = Font(bold=bold, italic=italic, color=kleur, size=size or 11)
    if vulling:
        cel.fill = PatternFill("solid", fgColor=vulling)
    if centreren:
        cel.alignment = Alignment(horizontal="center")
    if rand:
        zijde = Side(style="thin", color=RAND)
        cel.border = Border(bottom=zijde)
    return cel


def _datum(datum: dt.date) -> str:
    return datum.strftime("%d-%m-%Y")


#: Weekday names: Django's own date filter is not available outside a template,
#: and one fixed Dutch list beats depending on the server's locale.
DAGNAMEN = [
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
]


def _dagnaam(datum: dt.date) -> str:
    return DAGNAMEN[datum.weekday()]


def _ontbrekend(dag) -> str:
    tekst = f"{_dagnaam(dag.datum).lower()} {_datum(dag.datum)}"
    if dag.gefactureerde_uren:
        tekst += f" (wel {dag.gefactureerde_uren:.2f} uur geboekt)"
    return tekst
