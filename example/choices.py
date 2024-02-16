from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin"
    MANANGER = "manager"
    WORKER = "worker"

class ProjectStatus(models.TextChoices):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"
