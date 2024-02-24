# Generated by Django 3.2.12 on 2024-02-24 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0010_alter_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='address',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='tasks',
            name='color',
            field=models.CharField(default='#3788D8', max_length=20),
        ),
    ]