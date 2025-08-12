from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Authorization(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # REMOVED: password field - storing plaintext passwords is a security vulnerability
    # Instead, we'll trust the Authorization.user relationship and validate token2 + expiry
    token1 = models.UUIDField(default=uuid.uuid4, unique=True)
    token2 = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True)
    # FIXED: Use callable for default to avoid being evaluated at import time
    # This ensures each new Authorization gets a fresh expiry time
    expires = models.DateTimeField(default=lambda: timezone.now() + timezone.timedelta(seconds=30), blank=True)
    
    def __str__(self):
        return f"Auth for {self.user.username} expires {self.expires}"
    
    class Meta:
        # Add index on expires for efficient cleanup queries
        indexes = [
            models.Index(fields=['expires']),
        ]
