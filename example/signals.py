from django.db.models.signals import post_save
from django.dispatch import receiver
from example.models import  Project,Tasks

colors = [
    '#2c3e50',
    '#58cd32',
    '#7c8dad'
]
@receiver(post_save, sender=Project)
def set_color(sender, instance, created, **kwargs):
    if created:
        last_project = Project.objects.exclude(id=instance.id).order_by('-id').first()
        if last_project:
            last_color = last_project.color
            if last_color in colors:
                next_index = (colors.index(last_color) + 1) % len(colors)
                instance.color = colors[next_index]
            else:
                instance.color = colors[0]
        else:
            instance.color = colors[0]
        instance.save()

    else:
        # Check if the project's color has changed
        project = instance
        original_project = Project.objects.get(id=project.id)
        if original_project.color != project.color:
            # Update the color of all tasks associated with this project
            Tasks.objects.filter(project=project).update(color=project.color)