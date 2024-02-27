from django.contrib import admin

# Register your models here.
from .models import User, Tasks, Project


admin.site.register(User)
admin.site.register(Tasks)
admin.site.register(Project)