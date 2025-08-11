"""
Management command to send daily stock alert notifications
Usage: python manage.py send_stock_alerts
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from shop.models import Product, StockAlert
from shop.services.notifications import create_stock_alert_notification


class Command(BaseCommand):
    help = 'Send stock alert notifications to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold',
            type=int,
            default=10,
            help='Stock threshold for alerts (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending notifications'
        )

    def handle(self, *args, **options):
        threshold = options['threshold']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Checking for products with stock <= {threshold}...")
        
        # Get low stock products
        low_stock_products = Product.objects.filter(
            stock__lte=threshold,
            stock__gt=0,
            available=True
        ).order_by('stock')
        
        total_notifications = 0
        
        for product in low_stock_products:
            # Check if there are active alerts for this product
            active_alerts = StockAlert.objects.filter(
                product=product,
                is_active=True,
                threshold__gte=product.stock
            ).count()
            
            if active_alerts > 0:
                if dry_run:
                    self.stdout.write(
                        f"Would send alerts for '{product.name}' (stock: {product.stock}, alerts: {active_alerts})"
                    )
                    total_notifications += active_alerts
                else:
                    notifications_sent = create_stock_alert_notification(product)
                    total_notifications += notifications_sent
                    self.stdout.write(
                        f"Sent {notifications_sent} alerts for '{product.name}' (stock: {product.stock})"
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would send {total_notifications} notifications")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully sent {total_notifications} stock alert notifications")
            )
