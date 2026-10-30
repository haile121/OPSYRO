from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="TwitchConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("twitch_user_id", models.CharField(max_length=32, unique=True)),
                ("login", models.CharField(max_length=64)),
                ("display_name", models.CharField(max_length=128)),
                ("profile_image_url", models.URLField(blank=True, max_length=500)),
                ("encrypted_access_token", models.TextField()),
                ("encrypted_refresh_token", models.TextField()),
                ("scopes", models.JSONField(blank=True, default=list)),
                ("token_expires_at", models.DateTimeField()),
                ("connected_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="twitch_connection", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
