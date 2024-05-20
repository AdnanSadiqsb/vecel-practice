from django.test import TestCase

# Create your tests here.
from django.db.models.signals import post_save
from django.dispatch import receiver
from rota.models import CustomerCompany, Contract

@receiver(post_save, sender=CustomerCompany)
def create_default_contract(sender, instance, created, **kwargs):
    if created:
        Contract.objects.create(
            name="Contract - default",
            customer_company=instance,        
            company = instance.company,
            charge_rate = 12,
            over_rate = 14
        )