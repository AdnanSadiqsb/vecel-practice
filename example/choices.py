from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin"
    MANANGER = "manager"
    CONTRACTOR = "contractor"
    CLIENT = "client"
    WORKER = "worker"
    SUPPLIER = 'supplier'


class ProjectStatus(models.TextChoices):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"


class TaskPeriority(models.TextChoices):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
