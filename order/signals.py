from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Notification, Order


@receiver(pre_save, sender=Order)
def create_notification_on_status_change(sender, instance, **kwargs):
    # Skip new orders
    if not instance.pk:
        return

    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    # If status changed, create a notification
    if old_order.order_status != instance.order_status:
        Notification.objects.create(
            user=instance.user,
            message=f"Your order #{instance.id}  was {instance.order_status}.",
        )
