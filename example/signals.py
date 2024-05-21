from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from example.models import  Project,Tasks


@receiver(pre_save, sender=Project)
def set_color(sender, instance, **kwargs):

        print("update")
        # Update task colors if the project's color has changed
        original_project = Project.objects.get(pk=instance.pk)
        print("original_project", original_project.color)
        print("instace", instance.color)
        if original_project.color != instance.color:
            Tasks.objects.filter(project=instance).update(color=instance.color)