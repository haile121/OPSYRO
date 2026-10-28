import uuid

from django.db import migrations, models


def populate_public_tokens(apps, schema_editor):
    CreatorSession = apps.get_model("creator_sessions", "CreatorSession")
    database = schema_editor.connection.alias
    for session in CreatorSession.objects.using(database).filter(public_token__isnull=True).iterator():
        session.public_token = uuid.uuid4()
        session.save(update_fields=["public_token"], using=database)


class Migration(migrations.Migration):
    dependencies = [("creator_sessions", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="creatorsession",
            name="public_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(populate_public_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="creatorsession",
            name="public_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
