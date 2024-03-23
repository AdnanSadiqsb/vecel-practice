from django.contrib import admin

# Register your models here.
from .models import User, Tasks, Project, LastMail


admin.site.register(User)
admin.site.register(Tasks)
admin.site.register(Project)
admin.site.register(LastMail)