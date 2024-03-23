# Generated by Django 3.2.12 on 2024-03-23 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0016_user_plain_password'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastMail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sentAt', models.DateTimeField()),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin'), ('manager', 'Mananger'), ('contractor', 'Contractor'), ('client', 'Client')], default='admin', max_length=200),
        ),
    ]