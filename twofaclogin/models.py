from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Authorization(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=64, default='')
    token1 = models.CharField(max_length=512)
    token2 = models.CharField(max_length=512)
    expires = models.DateTimeField(default=timezone.now() + timezone.timedelta(seconds=30), blank=True)
