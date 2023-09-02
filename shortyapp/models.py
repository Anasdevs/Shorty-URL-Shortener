from django.db import models
from django.utils import timezone

class ShortURL(models.Model):
    short_code = models.CharField(max_length=10, unique=True)
    original_url = models.URLField()
    created_at = models.DateTimeField(default=timezone.now)
    expiration_date = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)

class ClickAnalytics(models.Model):
    short_url = models.ForeignKey(ShortURL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField()