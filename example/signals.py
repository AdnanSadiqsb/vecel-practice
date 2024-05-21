from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from example.models import  Project,Tasks

colors = [
    '#2c3e50',
    '#58cd32',
    '#7c8dad'
]
@receiver(pre_save, sender=Project)
def set_color(sender, instance, **kwargs):
    if not instance.pk:
        # Set the color for new projects based on the last project's color
        last_project = Project.objects.order_by('-id').first()
        if last_project:
            last_color = last_project.color
            if last_color in colors:
                next_index = (colors.index(last_color) + 1) % len(colors)
                instance.color = colors[next_index]
            else:
                instance.color = colors[0]
        else:
            instance.color = colors[0]
    else:
        print("update")
        # Update task colors if the project's color has changed
        original_project = Project.objects.get(pk=instance.pk)
        print("original_project", original_project.color)
        print("instace", instance.color)
        if original_project.color != instance.color:
            Tasks.objects.filter(project=instance).update(color=instance.color)