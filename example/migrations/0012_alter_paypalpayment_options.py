# Generated by Django 5.1.1 on 2024-10-19 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0011_paypalpayment_checkoutlink'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='paypalpayment',
            options={'ordering': ['-created_at']},
        ),
    ]
