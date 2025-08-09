from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Order
from shop.services.impact import record_order_impact


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created:
        try:
            record_order_impact(instance)
        except Exception:
            # In production add logging
            pass
