from django.contrib.auth.models import AbstractUser
from django.db import models

from .choices import UserRole
from django.dispatch import receiver


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=UserRole.choices, default=UserRole.ADMIN
    )
    avatar = models.FileField(upload_to="static/users_avatars", blank=True)

# Signal to delete avatar file when a User instance is deleted
@receiver(models.signals.post_delete, sender=User)
def auto_delete_avatar(sender, instance, **kwargs):
    """
    Deletes avatar file from filesystem when corresponding `User` object is deleted.
    """
    if instance.avatar:
        if instance.avatar.storage.exists(instance.avatar.name):
            instance.avatar.storage.delete(instance.avatar.name)
