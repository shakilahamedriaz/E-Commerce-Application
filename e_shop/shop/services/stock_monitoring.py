"""
Stock monitoring and inventory management service
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from ..models import Product, StockAlert
from .notifications import create_stock_alert_notification, create_notification


def check_low_stock_alerts(product):
    """Check and send low stock alerts for a product"""
    if product.stock <= 0:
        return  # Don't send alerts for out of stock items
    
    # Get active alerts for this product where current stock is at or below threshold
    alerts = StockAlert.objects.filter(
        product=product,
        is_active=True,
        threshold__gte=product.stock
    ).select_related('user')
    
    for alert in alerts:
        # Create notification
        title = f"Stock Alert: {product.name}"
        message = f"📦 '{product.name}' is running low! Only {product.stock} left in stock (your alert threshold: {alert.threshold}). Order now before it's gone!"
        
        create_notification(
            user=alert.user,
            title=title,
            message=message,
            notification_type='stock_alert',
            related_product=product
        )


def check_back_in_stock(product, old_stock):
    """Check if product is back in stock and notify interested users"""
    if old_stock <= 0 and product.stock > 0:
        # Product is back in stock!
        # Notify users who have this in their wishlist
        from ..models import Wishlist
        
        wishlist_users = Wishlist.objects.filter(product=product).select_related('user')
        
        for wishlist_item in wishlist_users:
            title = f"Back in Stock: {product.name}"
            message = f"Good news! '{product.name}' is back in stock with {product.stock} units available. Get yours now!"
            
            create_notification(
                user=wishlist_item.user,
                title=title,
                message=message,
                notification_type='stock_alert',
                related_product=product
            )


def get_low_stock_products(threshold=10):
    """Get products that are running low on stock"""
    return Product.objects.filter(
        stock__lte=threshold,
        stock__gt=0,
        available=True
    ).order_by('stock')


def get_out_of_stock_products():
    """Get products that are completely out of stock"""
    return Product.objects.filter(
        stock=0,
        available=True
    ).order_by('updated')


def update_product_availability():
    """Update product availability based on stock levels"""
    # Auto-disable products that are out of stock
    out_of_stock = Product.objects.filter(stock=0, available=True)
    updated_count = out_of_stock.update(available=False)
    
    # Auto-enable products that are back in stock
    back_in_stock = Product.objects.filter(stock__gt=0, available=False)
    enabled_count = back_in_stock.update(available=True)
    
    return {
        'disabled': updated_count,
        'enabled': enabled_count
    }


def get_stock_report():
    """Generate a comprehensive stock report"""
    from django.db.models import Count, Sum, F
    
    total_products = Product.objects.count()
    in_stock = Product.objects.filter(stock__gt=0).count()
    out_of_stock = Product.objects.filter(stock=0).count()
    low_stock = Product.objects.filter(stock__lte=10, stock__gt=0).count()
    
    # Calculate total inventory value
    total_value = Product.objects.aggregate(
        total=Sum(F('price') * F('stock'))
    )['total'] or 0
    
    return {
        'total_products': total_products,
        'in_stock': in_stock,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'total_inventory_value': total_value,
        'stock_percentage': (in_stock / total_products * 100) if total_products > 0 else 0
    }


# Signal handlers for automatic stock monitoring
@receiver(pre_save, sender=Product)
def product_stock_pre_save(sender, instance, **kwargs):
    """Store old stock value before saving"""
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            instance._old_stock = old_instance.stock
        except Product.DoesNotExist:
            instance._old_stock = 0
    else:
        instance._old_stock = 0


@receiver(post_save, sender=Product)
def product_stock_post_save(sender, instance, created, **kwargs):
    """Monitor stock changes and send notifications"""
    if not created and hasattr(instance, '_old_stock'):
        old_stock = instance._old_stock
        new_stock = instance.stock
        
        # Check if stock decreased and is now below alert thresholds
        if new_stock < old_stock:
            check_low_stock_alerts(instance)
        
        # Check if product is back in stock
        if old_stock <= 0 and new_stock > 0:
            check_back_in_stock(instance, old_stock)


def create_restock_suggestion(product, suggested_quantity=None):
    """Create a restock suggestion for a product"""
    if not suggested_quantity:
        # Simple algorithm: suggest restocking to average of last 3 months sales
        # This is a placeholder - in real implementation, you'd use more sophisticated forecasting
        suggested_quantity = max(50, product.stock * 2)
    
    return {
        'product': product,
        'current_stock': product.stock,
        'suggested_quantity': suggested_quantity,
        'priority': 'high' if product.stock == 0 else 'medium' if product.stock <= 5 else 'low'
    }


def bulk_update_stock(stock_updates):
    """Bulk update stock for multiple products
    
    Args:
        stock_updates: List of dicts with 'product_id' and 'new_stock' keys
    """
    updated_products = []
    
    for update in stock_updates:
        try:
            product = Product.objects.get(id=update['product_id'])
            old_stock = product.stock
            product.stock = update['new_stock']
            product.save()
            
            updated_products.append({
                'product': product,
                'old_stock': old_stock,
                'new_stock': product.stock
            })
        except Product.DoesNotExist:
            continue
    
    return updated_products
