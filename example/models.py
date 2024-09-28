from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime
from .choices import UserRole, ProjectStatus, TaskPeriority
from django.dispatch import receiver
from django.utils import timezone
import randomcolor
from django.contrib.postgres.fields import ArrayField

import uuid
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=200, choices=UserRole.choices, default=UserRole.ADMIN
    )
    avatar = models.FileField(upload_to="static/users_avatars", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    plain_password = models.CharField(max_length = 100, null=True, blank=True)
    phoneNumber = models.CharField(max_length=200, null=True, blank=True)
    first_name = None
    last_name = None
    username = models.CharField(max_length=100)
    is_sentMail = models.BooleanField(default=False)

    supplier = models.ForeignKey('self', on_delete=models.CASCADE, related_name='worker_supplier', null=True, blank=True)

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    image = models.FileField(upload_to="static/projects_images", blank=True, null=True)
    color = models.CharField(max_length=20, default='#2c3e50')
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    managers = models.ManyToManyField(User, related_name='managers', null =True, blank=True)
    client = models.ForeignKey(User,related_name='client', on_delete=models.SET_NULL, null=True, blank =True )
    contractor = models.ForeignKey(User,related_name='contractor',on_delete=models.SET_NULL, null=True, blank =True )
    status = models.CharField(max_length=200, choices=ProjectStatus.choices, default=ProjectStatus.PENDING)
    is_active = models.BooleanField(default=True)
    address = models.CharField(max_length=100, null=True, blank=True)

    wifiAvaliabe = models.BooleanField(default= False)
    parkingAvaliable = models.BooleanField(default=False)
    property_features = models.JSONField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)

    uploaded_files = ArrayField(
       models.CharField(max_length=1000), default=[]
   )


    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created']
        
        

class Tasks(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_tasks')
    color = models.CharField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    workers = models.ManyToManyField(User, related_name='task_workers', null =True, blank = True)
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=200, choices=ProjectStatus.choices, default=ProjectStatus.PENDING)
    is_active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    costCode = models.CharField(null=True, blank=True, max_length=1000)
    quantity = models.CharField(null=True, blank=True,max_length=400)
    unit = models.CharField(null=True, blank=True, max_length=200)

    fileName = models.CharField(null=True, blank=True, max_length=200)

    note = models.CharField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=TaskPeriority  , default=TaskPeriority.MEDIUM)
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural ='Tasks'
        ordering = ['-created']
    def save(self, *args, **kwargs):
        # Set the color of the task to match the color of the associated project
        self.color = self.project.color
        super().save(*args, **kwargs)
        
class LastMail(models.Model):
    sentAt = models.DateTimeField()
  


class Foo(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    bar = models.CharField(max_length=30)
