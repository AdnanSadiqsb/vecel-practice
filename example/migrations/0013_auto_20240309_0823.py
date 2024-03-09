# Generated by Django 3.2.12 on 2024-03-09 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0012_alter_user_is_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'ordering': ['-created'], 'verbose_name': 'Project', 'verbose_name_plural': 'Projects'},
        ),
        migrations.AlterModelOptions(
            name='tasks',
            options={'ordering': ['-created'], 'verbose_name': 'Task', 'verbose_name_plural': 'Tasks'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['-date_joined']},
        ),
        migrations.AddField(
            model_name='user',
            name='is_sentMail',
            field=models.CharField(default=False, max_length=10),
        ),
    ]
