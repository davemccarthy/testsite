# Generated manually to fix security issues

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('twofaclogin', '0002_alter_authorization_expires'),
    ]

    operations = [
        # Remove the password field (security vulnerability)
        migrations.RemoveField(
            model_name='authorization',
            name='password',
        ),
        # Update token1 to UUIDField with unique constraint
        migrations.AlterField(
            model_name='authorization',
            name='token1',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
        # Update token2 to UUIDField with unique constraint and allow null
        migrations.AlterField(
            model_name='authorization',
            name='token2',
            field=models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True),
        ),
        # Add index on expires field for efficient cleanup queries
        migrations.AddIndex(
            model_name='authorization',
            index=models.Index(fields=['expires'], name='twofaclogin_expires_idx'),
        ),
    ]
