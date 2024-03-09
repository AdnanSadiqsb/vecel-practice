from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime
from .choices import UserRole, ProjectStatus
from django.dispatch import receiver


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=UserRole.choices, default=UserRole.ADMIN
    )
    avatar = models.FileField(upload_to="static/users_avatars", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    phoneNumber = models.CharField(max_length=20, null=True, blank=True)
    first_name = None
    last_name = None
    username = models.CharField(max_length=100)
    is_sentMail = models.CharField(max_length=10, default=False)

    class Meta:
        ordering = ['-date_joined']
# Signal to delete avatar file when a User instance is deleted
@receiver(models.signals.post_delete, sender=User)
def auto_delete_avatar(sender, instance, **kwargs):
    """
    Deletes avatar file from filesystem when corresponding `User` object is deleted.
    """
    if instance.avatar:
        if instance.avatar.storage.exists(instance.avatar.name):
            instance.avatar.storage.delete(instance.avatar.name)


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="static/projects_images", blank=True, null=True)
    
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    managers = models.ManyToManyField(User, related_name='managers')
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.PENDING)
    is_active = models.BooleanField(default=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created']
        
        

class Tasks(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_tasks')
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    workers = models.ManyToManyField(User, related_name='task_workers')
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.PENDING)
    is_active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=20, default='#3788D8')
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural ='Tasks'
        ordering = ['-created']
