# Generated manually to fix database constraint issue

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('twofaclogin', '0003_remove_password_update_tokens'),
    ]

    operations = [
        # Allow NULL values for token1 since we clear it after use
        migrations.AlterField(
            model_name='authorization',
            name='token1',
            field=models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True),
        ),
    ]
