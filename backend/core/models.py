from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    full_name = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.TextField(blank=True, null=True) # Base64
    about = models.CharField(max_length=255, default="Hey there! I am using WhatsApp Clone.")

    def __str__(self):
        return self.username
