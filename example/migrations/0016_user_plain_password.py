# Generated by Django 3.2.12 on 2024-03-19 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0015_auto_20240319_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='plain_password',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
