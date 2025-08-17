"""
Signal handlers for orders app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_fsm.signals import post_transition

from .models import Order, OrderStatusHistory


@receiver(post_transition, sender=Order)
def track_order_status_change(sender, instance, name, source, target, **kwargs):
    """
    Track order status changes in history.
    """
    OrderStatusHistory.objects.create(
        order=instance,
        from_status=source,
        to_status=target,
        # You could track the user who made the change here
        # changed_by=kwargs.get('user'),
        reason=f'Status changed via {name} transition'
    )