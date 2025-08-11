"""
Notification service for handling user notifications
"""
from django.contrib.auth.models import User
from ..models import UserNotification, StockAlert, Product


def create_notification(user, title, message, notification_type, related_product=None, related_order=None):
    """Create a new notification for a user"""
    return UserNotification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_product=related_product,
        related_order=related_order
    )


def create_stock_alert_notification(product):
    """Create stock alert notifications for users who have set alerts for this product"""
    alerts = StockAlert.objects.filter(
        product=product,
        is_active=True,
        threshold__gte=product.stock
    ).select_related('user')
    
    notifications_created = 0
    for alert in alerts:
        title = f"Stock Alert: {product.name}"
        message = f"The product '{product.name}' is now at {product.stock} units (below your threshold of {alert.threshold}). Get it before it's out of stock!"
        
        # Check if we haven't already sent this notification recently
        recent_notification = UserNotification.objects.filter(
            user=alert.user,
            related_product=product,
            notification_type='stock_alert'
        ).order_by('-created_at').first()
        
        # Only send if no recent notification or stock has changed significantly
        should_send = True
        if recent_notification:
            # Don't spam - only send if it's been a while or stock dropped significantly
            import datetime
            from django.utils import timezone
            if recent_notification.created_at > timezone.now() - datetime.timedelta(hours=24):
                should_send = False
        
        if should_send:
            create_notification(
                user=alert.user,
                title=title,
                message=message,
                notification_type='stock_alert',
                related_product=product
            )
            notifications_created += 1
    
    return notifications_created


def create_order_update_notification(order, status_change=None):
    """Create order status update notification"""
    status_messages = {
        'Processing': 'Your order is being processed.',
        'Shipped': f'Your order has been shipped! Tracking number: {order.tracking_number or "Will be provided soon"}',
        'Out for Delivery': 'Your order is out for delivery and will arrive soon!',
        'Delivered': 'Your order has been delivered. Thank you for shopping with us!',
        'Cancelled': 'Your order has been cancelled. If you have any questions, please contact support.',
    }
    
    message = status_messages.get(order.status, f'Your order status has been updated to: {order.status}')
    
    create_notification(
        user=order.user,
        title=f"Order #{order.id} Update",
        message=message,
        notification_type='order_update',
        related_order=order
    )


def create_new_product_notification(product, category_followers=None):
    """Create notifications for new products (for users following categories)"""
    # This could be enhanced to notify users who have shown interest in similar products
    # For now, it's a placeholder for future implementation
    pass


def create_price_drop_notification(product, old_price, new_price):
    """Create notifications for price drops on wishlisted items"""
    from ..models import Wishlist
    
    # Get users who have this product in their wishlist
    wishlist_users = Wishlist.objects.filter(product=product).select_related('user')
    
    notifications_created = 0
    for wishlist_item in wishlist_users:
        title = f"Price Drop: {product.name}"
        message = f"Great news! The price of '{product.name}' has dropped from ${old_price} to ${new_price}. Get it now!"
        
        create_notification(
            user=wishlist_item.user,
            title=title,
            message=message,
            notification_type='price_drop',
            related_product=product
        )
        notifications_created += 1
    
    return notifications_created


def create_sustainability_notification(user, achievement_type, details):
    """Create sustainability achievement notifications"""
    achievement_messages = {
        'first_green_purchase': 'Congratulations on your first eco-friendly purchase!',
        'carbon_savings_milestone': f'Amazing! You\'ve saved {details.get("saved_kg", 0)}kg of CO₂ with your sustainable choices.',
        'monthly_budget_achieved': 'Great job staying within your monthly carbon budget!',
        'streak_milestone': f'Fantastic! You\'re on a {details.get("streak", 0)}-order eco-friendly streak!',
    }
    
    title = "Sustainability Achievement!"
    message = achievement_messages.get(achievement_type, 'You\'ve made a positive environmental impact!')
    
    create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='sustainability'
    )


def get_unread_count(user):
    """Get count of unread notifications for a user"""
    return UserNotification.objects.filter(user=user, is_read=False).count()


def mark_notifications_read(user, notification_ids=None):
    """Mark notifications as read"""
    queryset = UserNotification.objects.filter(user=user, is_read=False)
    
    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)
    
    return queryset.update(is_read=True)
