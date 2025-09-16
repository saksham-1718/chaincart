from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # extra fields for ChainCart
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=True)

    def __str__(self):
        return self.username
