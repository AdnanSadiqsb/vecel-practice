from django.contrib.auth.models import AbstractUser
from django.db import models

from .choices import UserRole


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=UserRole.choices, default=UserRole.ADMIN
    )
