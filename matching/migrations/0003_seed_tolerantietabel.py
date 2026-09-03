"""Seed the tolerantietabel with its fallback row.

The PoC hardcoded DREMPEL = 15 minutes; the table replaces that constant, so it
has to start with the same value or the first run after the upgrade would behave
differently. "algemeen" is the row every lookup falls back on when no
activity-specific rule applies — and today there are none, because the
per-activity values still have to be confirmed with the customer
(docs/functioneel-ontwerp.md §9, point 2).
"""

from django.db import migrations

ALGEMEEN = "algemeen"
DREMPEL_MINUTEN = 15


def seed(apps, schema_editor):
    ToleranceRegel = apps.get_model("matching", "ToleranceRegel")
    ToleranceRegel.objects.get_or_create(
        activiteit=ALGEMEEN, defaults={"drempel_minuten": DREMPEL_MINUTEN}
    )


def unseed(apps, schema_editor):
    # Only removes the untouched default: a value the customer changed is theirs,
    # and rolling a migration back is no reason to throw it away.
    ToleranceRegel = apps.get_model("matching", "ToleranceRegel")
    ToleranceRegel.objects.filter(
        activiteit=ALGEMEEN, drempel_minuten=DREMPEL_MINUTEN
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0002_toleranceregel_bekendelocatie_instelling_monteur_and_more"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
