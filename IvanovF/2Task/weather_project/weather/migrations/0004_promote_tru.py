from django.db import migrations


def promote_tru(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='tru').update(is_staff=True)


def demote_tru(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username='tru').update(is_staff=False)


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0003_weathersnapshot'),
    ]

    operations = [
        migrations.RunPython(promote_tru, demote_tru),
    ]
