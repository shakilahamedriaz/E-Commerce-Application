from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import render
import csv
import logging

from .models import (
    Category, Product, Rating, Cart, CartItem, Order, OrderItem, 
    UserImpact, OrderImpact, Badge, UserBadge, Wishlist, StockAlert, 
    UserNotification, ProductReview, EnvironmentalImpact
)

# Set up logging
logger = logging.getLogger('shop.admin')

# Helper function for safe float conversion
def safe_float(value, default=0.0):
    """Safely convert a value to float, handling None and Decimal types"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ===================== CUSTOM ADMIN SITE ===================== #

class EcoCommerceAdminSite(AdminSite):
    site_header = "🌱 EcoCommerce Sustainability Dashboard"
    site_title = "EcoCommerce Admin"
    index_title = "E-commerce & Environmental Impact Management"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
            path('export-orders/', self.admin_view(self.export_orders), name='ecoadmin_export_orders'),
            path('sustainability-report/', self.admin_view(self.sustainability_report), name='sustainability_report'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        """Enhanced admin dashboard with comprehensive analytics"""
        # Time periods
        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        # Order Analytics
        recent_orders = Order.objects.filter(created__gte=last_30_days)
        order_stats = {
            'total_orders_30d': recent_orders.count(),
            'paid_orders_30d': recent_orders.filter(paid=True).count(),
            'pending_orders': Order.objects.filter(status='Pending').count(),
            'processing_orders': Order.objects.filter(status='Processing').count(),
            'total_revenue_30d': recent_orders.filter(paid=True).aggregate(
                total=Sum('items__price')
            )['total'] or 0,
            'avg_order_value': recent_orders.filter(paid=True).aggregate(
                avg=Avg('items__price')
            )['avg'] or 0,
        }
        
        # Product Analytics
        product_stats = {
            'total_products': Product.objects.filter(available=True).count(),
            'low_stock_products': Product.objects.filter(stock__lt=10, available=True).count(),
            'out_of_stock': Product.objects.filter(stock=0).count(),
            'green_products': Product.objects.filter(carbon_footprint_kg__lt=5).count(),
        }
        
        # Sustainability Metrics
        total_carbon_saved = UserImpact.objects.aggregate(
            total=Sum('total_saved_kg')
        )['total'] or 0
        
        impact_stats = {
            'total_carbon_saved': total_carbon_saved,
            'eco_conscious_users': UserImpact.objects.filter(total_saved_kg__gt=0).count(),
            'badges_earned': UserBadge.objects.count(),
            'avg_carbon_per_order': OrderImpact.objects.aggregate(
                avg=Avg('carbon_kg')
            )['avg'] or 0,
            'trees_equivalent': int(total_carbon_saved / 22) if total_carbon_saved > 0 else 0,
        }
        
        # User Analytics
        user_stats = {
            'total_users': User.objects.count(),
            'active_users_7d': Order.objects.filter(
                created__gte=last_7_days
            ).values('user').distinct().count(),
            'new_users_30d': User.objects.filter(
                date_joined__gte=last_30_days
            ).count(),
        }
        
        # Top Performing Products
        top_products = Product.objects.annotate(
            order_count=Count('orderitem'),
            revenue=Sum('orderitem__price')
        ).filter(order_count__gt=0).order_by('-order_count')[:5]
        
        # Recent Activity
        recent_activity = []
        
        # Recent orders
        recent_orders_list = Order.objects.select_related('user').order_by('-created')[:5]
        for order in recent_orders_list:
            recent_activity.append({
                'type': 'order',
                'icon': '🛍️',
                'message': f"Order #{order.id} placed by {order.user.username}",
                'time': order.created,
                'value': f"${order.get_total_cost():.2f}" if hasattr(order, 'get_total_cost') else 'N/A'
            })
        
        # Recent user registrations
        recent_users = User.objects.order_by('-date_joined')[:3]
        for user in recent_users:
            recent_activity.append({
                'type': 'user',
                'icon': '👤',
                'message': f"New user registered: {user.username}",
                'time': user.date_joined,
                'value': ''
            })
        
        # Sort by time
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        recent_activity = recent_activity[:8]
        
        # Low Stock Alerts
        low_stock_products = Product.objects.filter(
            stock__lt=10, stock__gt=0, available=True
        ).order_by('stock')[:5]
        
        extra_context = extra_context or {}
        extra_context.update({
            'order_stats': order_stats,
            'product_stats': product_stats,
            'impact_stats': impact_stats,
            'user_stats': user_stats,
            'top_products': top_products,
            'recent_activity': recent_activity,
            'low_stock_products': low_stock_products,
            'dashboard_date': today,
        })
        
        return super().index(request, extra_context)
    
    def analytics_view(self, request):
        """Detailed analytics view"""
        # Add detailed analytics here
        context = {
            'title': 'Analytics Dashboard',
        }
        return render(request, 'admin/analytics.html', context)
    
    def export_orders(self, request):
        """Export orders to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'User', 'Date', 'Status', 'Total', 'Carbon Impact'])
        
        orders = Order.objects.select_related('user').order_by('-created')
        for order in orders:
            carbon_impact = 'N/A'
            if hasattr(order, 'impact'):
                carbon_impact = f"{order.impact.carbon_kg}kg"
            
            writer.writerow([
                order.id,
                order.user.username,
                order.created.strftime('%Y-%m-%d'),
                order.status,
                f"${order.get_total_cost():.2f}" if hasattr(order, 'get_total_cost') else 'N/A',
                carbon_impact
            ])
        
        logger.info(f"Orders exported by {request.user.username}")
        return response
    
    def sustainability_report(self, request):
        """Generate sustainability report"""
        # Implementation for sustainability report
        return JsonResponse({'message': 'Sustainability report generated'})

# Create custom admin site
admin_site = EcoCommerceAdminSite(name='ecoadmin')

# ===================== ENHANCED MODEL ADMINS ===================== #

# ===================== ENHANCED MODEL ADMINS ===================== #

# Admin for User model
@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'default_emission_factor_kg', 'product_count', 'avg_carbon_footprint')
    list_editable = ('default_emission_factor_kg',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('product_count', 'avg_carbon_footprint')
    
    def product_count(self, obj):
        count = obj.products.filter(available=True).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    product_count.short_description = '🛍️ Products'
    
    def avg_carbon_footprint(self, obj):
        avg = obj.products.aggregate(avg=Avg('carbon_footprint_kg'))['avg']
        if avg:
            avg_float = safe_float(avg)
            color = 'green' if avg_float < 10 else 'orange' if avg_float < 20 else 'red'
            formatted_avg = f"{avg_float:.1f}"
            return format_html('<span style="color: {}; font-weight: bold;">{}kg CO₂e</span>', color, formatted_avg)
        return 'No data'
    avg_carbon_footprint.short_description = '🌱 Avg Carbon'

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created')
    can_delete = False
    max_num = 5

# Enhanced Product Admin with Sustainability Focus
@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'category', 'price', 'stock_status', 
        'carbon_badge', 'ethics_badge', 'available'
    )
    list_filter = ('available', 'category', 'created', 'ethics_score')
    search_fields = ('name', 'description', 'category__name')
    list_editable = ('price', 'available')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created', 'updated')
    inlines = [RatingInline]
    actions = ['make_available', 'make_unavailable', 'update_carbon_footprint']
    
    fieldsets = (
        ('📋 Basic Information', {
            'fields': ('name', 'slug', 'category', 'description', 'image'),
            'classes': ('wide',)
        }),
        ('💰 Pricing & Inventory', {
            'fields': ('price', 'stock', 'available'),
            'classes': ('wide',)
        }),
        ('🌱 Sustainability Metrics', {
            'fields': ('carbon_footprint_kg', 'ethics_score', 'impact_confidence'),
            'classes': ('collapse',),
            'description': 'Environmental and ethical impact measurements'
        })
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; border: 2px solid #ddd;"/>',
                obj.image.url
            )
        return format_html('<div style="width: 60px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999;">📷</div>')
    image_preview.short_description = 'Image'
    
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ Out of Stock</span>')
        elif obj.stock < 10:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Low Stock ({})</span>', obj.stock)
        else:
            return format_html('<span style="color: green; font-weight: bold;">✅ In Stock ({})</span>', obj.stock)
    stock_status.short_description = '📦 Stock'
    
    def carbon_badge(self, obj):
        carbon = safe_float(obj.effective_carbon_kg())
        formatted_carbon = f"{carbon:.1f}"
        if carbon < 5:
            return format_html('<span style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">🌱 {}kg</span>', formatted_carbon)
        elif carbon < 15:
            return format_html('<span style="background: #ff9800; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">🟡 {}kg</span>', formatted_carbon)
        else:
            return format_html('<span style="background: #f44336; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">🔴 {}kg</span>', formatted_carbon)
    carbon_badge.short_description = '🌱 Carbon'
    
    def ethics_badge(self, obj):
        score = obj.ethics_score
        if score >= 80:
            return format_html('<span style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">⭐ {}/100</span>', score)
        elif score >= 60:
            return format_html('<span style="background: #ff9800; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">📊 {}/100</span>', score)
        else:
            return format_html('<span style="background: #f44336; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">📉 {}/100</span>', score)
    ethics_badge.short_description = '🤝 Ethics'
    
    # Admin Actions
    def make_available(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(request, f'{updated} products marked as available.')
        logger.info(f"{request.user.username} made {updated} products available")
    make_available.short_description = "Mark selected products as available"
    
    def make_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(request, f'{updated} products marked as unavailable.')
        logger.info(f"{request.user.username} made {updated} products unavailable")
    make_unavailable.short_description = "Mark selected products as unavailable"



class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('quantity',)

# Enhanced Cart Admin
@admin.register(Cart, site=admin_site)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'items_count', 'total_value', 'created_at', 'updated_at', 'cart_status')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total_value', 'items_count')
    inlines = [CartItemInline]
    
    def items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    items_count.short_description = '🛒 Items'
    
    def total_value(self, obj):
        total = sum(item.product.price * item.quantity for item in obj.items.all())
        return f"${total:.2f}"
    total_value.short_description = '💰 Total'
    
    def cart_status(self, obj):
        count = obj.items.count()
        if count == 0:
            return format_html('<span style="color: gray;">🔄 Empty</span>')
        elif count > 5:
            return format_html('<span style="color: green;">🛍️ Full</span>')
        else:
            return format_html('<span style="color: orange;">📦 Active</span>')
    cart_status.short_description = 'Status'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price', 'line_total')
    
    def line_total(self, obj):
        return f"${obj.price * obj.quantity:.2f}"
    line_total.short_description = 'Line Total'

# Enhanced Order Admin with Comprehensive Management
@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user_link', 'status_badge', 'payment_badge', 
        'total_amount', 'carbon_impact', 'created', 'quick_actions'
    )
    list_filter = ('status', 'paid', 'created', 'courier_service')
    search_fields = ('user__username', 'user__email', 'id', 'tracking_number')
    readonly_fields = ('created', 'updated', 'total_amount')
    inlines = [OrderItemInline]
    actions = ['mark_processing', 'mark_shipped', 'mark_delivered', 'send_confirmation_email']
    date_hierarchy = 'created'
    
    fieldsets = (
        ('📋 Order Information', {
            'fields': ('user', 'status', 'paid', 'transaction_id'),
            'classes': ('wide',)
        }),
        ('📦 Shipping Details', {
            'fields': ('first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'courier_service', 'tracking_number'),
            'classes': ('wide',)
        }),
        ('📊 Order Summary', {
            'fields': ('total_amount', 'created', 'updated'),
            'classes': ('collapse',)
        })
    )
    
    def order_number(self, obj):
        return f"#{obj.id:06d}"
    order_number.short_description = 'Order #'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}" style="text-decoration: none;">👤 {}</a>', url, obj.user.username)
    user_link.short_description = 'Customer'
    
    def status_badge(self, obj):
        status_styles = {
            'Pending': ('🕐', '#ff9800', 'white'),
            'Processing': ('⚙️', '#2196f3', 'white'), 
            'Shipped': ('🚚', '#4caf50', 'white'),
            'Delivered': ('✅', '#388e3c', 'white'),
            'Cancelled': ('❌', '#f44336', 'white')
        }
        icon, bg_color, text_color = status_styles.get(obj.status, ('❓', '#gray', 'white'))
        return format_html(
            '<span style="background: {}; color: {}; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{} {}</span>',
            bg_color, text_color, icon, obj.status
        )
    status_badge.short_description = 'Status'
    
    def payment_badge(self, obj):
        if obj.paid:
            return format_html('<span style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✅ Paid</span>')
        else:
            return format_html('<span style="background: #f44336; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">❌ Unpaid</span>')
    payment_badge.short_description = 'Payment'
    
    def total_amount(self, obj):
        total = obj.get_total_cost() if hasattr(obj, 'get_total_cost') else 0
        formatted_total = f"{safe_float(total):.2f}"
        return f"${formatted_total}"
    total_amount.short_description = '💰 Total'
    
    def carbon_impact(self, obj):
        if hasattr(obj, 'impact'):
            carbon = safe_float(obj.impact.carbon_kg)
            formatted_carbon = f"{carbon:.1f}"
            if carbon < 10:
                return format_html('<span style="color: green;">🌱 {}kg</span>', formatted_carbon)
            elif carbon < 20:
                return format_html('<span style="color: orange;">🟡 {}kg</span>', formatted_carbon)
            else:
                return format_html('<span style="color: red;">🔴 {}kg</span>', formatted_carbon)
        return format_html('<span style="color: gray;">No data</span>')
    carbon_impact.short_description = '🌱 Carbon'
    
    def quick_actions(self, obj):
        return format_html(
            '<a class="button" href="mailto:{}?subject=Order Update #{}" style="margin-right: 5px;">📧</a>'
            '<a class="button" href="/admin/order/{}/invoice/" style="margin-right: 5px;">📄</a>',
            obj.email, obj.id, obj.id
        )
    quick_actions.short_description = 'Actions'
    
    # Admin Actions
    def mark_processing(self, request, queryset):
        updated = queryset.update(status='Processing')
        self.message_user(request, f'{updated} orders marked as processing.')
        logger.info(f"{request.user.username} marked {updated} orders as processing")
    mark_processing.short_description = "⚙️ Mark as Processing"
    
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status='Shipped')
        self.message_user(request, f'{updated} orders marked as shipped.')
        logger.info(f"{request.user.username} marked {updated} orders as shipped")
    mark_shipped.short_description = "🚚 Mark as Shipped"
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='Delivered')
        self.message_user(request, f'{updated} orders marked as delivered.')
        logger.info(f"{request.user.username} marked {updated} orders as delivered")
    mark_delivered.short_description = "✅ Mark as Delivered"

# Enhanced Rating Admin
@admin.register(Rating, site=admin_site)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_link', 'rating_stars', 'comment_preview', 'created')
    list_filter = ['rating', 'created']
    search_fields = ('user__username', 'product__name', 'comment')
    readonly_fields = ('created',)
    
    def product_link(self, obj):
        url = reverse('admin:shop_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = 'Product'
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span title="{}/5">{}</span>', obj.rating, stars)
    rating_stars.short_description = 'Rating'
    
    def comment_preview(self, obj):
        if obj.comment:
            preview = obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
            return format_html('<span title="{}">{}</span>', obj.comment, preview)
        return 'No comment'
    comment_preview.short_description = 'Comment'


# ===================== SUSTAINABILITY-FOCUSED ADMINS ===================== #

@admin.register(UserImpact, site=admin_site)
class UserImpactAdmin(admin.ModelAdmin):
    list_display = (
        'user_profile', 'sustainability_level', 'carbon_summary', 'budget_status', 'last_activity'
    )
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('updated_at',)
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        ('👤 User Information', {
            'fields': ('user',),
        }),
        ('🌱 Carbon Impact', {
            'fields': ('total_carbon_kg', 'total_saved_kg', 'current_month_carbon_kg', 'month_budget_kg'),
            'classes': ('wide',)
        }),
        ('📊 Analytics', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    def user_profile(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 40px; height: 40px; background: #4caf50; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 10px;">'
            '{}</div>'
            '<div><strong>{}</strong><br><small>{}</small></div>'
            '</div>',
            obj.user.username[0].upper(),
            obj.user.username,
            obj.user.email
        )
    user_profile.short_description = 'User'
    
    def sustainability_level(self, obj):
        saved = safe_float(obj.total_saved_kg)
        formatted_saved = f"{saved:.1f}"
        if saved > 100:
            return format_html('<span style="background: #4caf50; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">🏆 CHAMPION<br>{}kg saved</span>', formatted_saved)
        elif saved > 50:
            return format_html('<span style="background: #2196f3; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">🌟 LEADER<br>{}kg saved</span>', formatted_saved)
        elif saved > 20:
            return format_html('<span style="background: #ff9800; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">🌿 ACTIVE<br>{}kg saved</span>', formatted_saved)
        elif saved > 0:
            return format_html('<span style="background: #4caf50; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">🌱 BEGINNER<br>{}kg saved</span>', formatted_saved)
        else:
            return format_html('<span style="background: #9e9e9e; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">🆕 NEW<br>Start journey</span>')
    sustainability_level.short_description = 'Level'
    
    def carbon_summary(self, obj):
        formatted_carbon = f"{safe_float(obj.total_carbon_kg):.1f}"
        return format_html(
            '<div style="text-align: center;">'
            '<div style="color: #f44336; font-weight: bold;">{}kg</div>'
            '<small>Total Carbon</small>'
            '</div>',
            formatted_carbon
        )
    carbon_summary.short_description = '🔥 Carbon'
    
    def budget_status(self, obj):
        if obj.month_budget_kg > 0:
            usage = (safe_float(obj.current_month_carbon_kg) / safe_float(obj.month_budget_kg)) * 100
            formatted_usage = f"{usage:.0f}"
            if usage < 70:
                return format_html('<span style="color: green; font-weight: bold;">✅ ON TRACK<br>{}% used</span>', formatted_usage)
            elif usage < 100:
                return format_html('<span style="color: orange; font-weight: bold;">⚠️ WARNING<br>{}% used</span>', formatted_usage)
            else:
                return format_html('<span style="color: red; font-weight: bold;">❌ OVER BUDGET<br>{}% used</span>', formatted_usage)
        return format_html('<span style="color: gray;">No budget set</span>')
    budget_status.short_description = '📊 Budget'
    
    def last_activity(self, obj):
        return format_html('<small>{}</small>', obj.updated_at.strftime('%Y-%m-%d'))
    last_activity.short_description = 'Last Update'

@admin.register(OrderImpact, site=admin_site)
class OrderImpactAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'carbon_impact', 'savings_achieved', 'efficiency_rating', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__id', 'order__user__username')
    readonly_fields = ('created_at', 'efficiency_rating')
    
    def order_link(self, obj):
        url = reverse('admin:shop_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    
    def carbon_impact(self, obj):
        carbon = safe_float(obj.carbon_kg)
        formatted_carbon = f"{carbon:.1f}"
        if carbon < 10:
            return format_html('<span style="color: green; font-weight: bold;">🌱 {}kg CO₂e</span>', formatted_carbon)
        elif carbon < 20:
            return format_html('<span style="color: orange; font-weight: bold;">🟡 {}kg CO₂e</span>', formatted_carbon)
        else:
            return format_html('<span style="color: red; font-weight: bold;">🔴 {}kg CO₂e</span>', formatted_carbon)
    carbon_impact.short_description = 'Carbon Impact'
    
    def savings_achieved(self, obj):
        saved = safe_float(obj.saved_kg)
        if saved > 0:
            formatted_saved = f"{saved:.1f}"
            return format_html('<span style="color: green; font-weight: bold;">✅ +{}kg saved</span>', formatted_saved)
        else:
            return format_html('<span style="color: gray;">No savings</span>')
    savings_achieved.short_description = 'Savings'
    
    def efficiency_rating(self, obj):
        baseline = safe_float(obj.baseline_kg)
        actual = safe_float(obj.carbon_kg)
        if baseline > 0:
            efficiency = ((baseline - actual) / baseline) * 100
            formatted_efficiency = f"{efficiency:.0f}"
            if efficiency > 20:
                return format_html('<span style="color: green;">⭐⭐⭐ Excellent ({}%)</span>', formatted_efficiency)
            elif efficiency > 10:
                return format_html('<span style="color: orange;">⭐⭐ Good ({}%)</span>', formatted_efficiency)
            elif efficiency > 0:
                return format_html('<span style="color: blue;">⭐ Fair ({}%)</span>', formatted_efficiency)
        return 'No baseline'
    efficiency_rating.short_description = 'Efficiency'

@admin.register(Badge, site=admin_site)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('badge_display', 'code', 'category_badge', 'condition_summary', 'users_earned')
    list_filter = ('category', 'condition_type')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('users_earned',)
    
    fieldsets = (
        ('🏆 Badge Information', {
            'fields': ('name', 'code', 'description', 'icon'),
            'classes': ('wide',)
        }),
        ('📋 Category & Conditions', {
            'fields': ('category', 'condition_type', 'threshold'),
            'classes': ('wide',)
        }),
        ('💬 User Experience', {
            'fields': ('popup_message',),
            'classes': ('collapse',)
        }),
        ('📊 Statistics', {
            'fields': ('users_earned',),
            'classes': ('collapse',)
        })
    )
    
    def badge_display(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="font-size: 24px; margin-right: 10px;">{}</div>'
            '<div><strong>{}</strong></div>'
            '</div>',
            obj.icon or '🏆',
            obj.name
        )
    badge_display.short_description = 'Badge'
    
    def category_badge(self, obj):
        colors = {
            'carbon_reduction': '#4caf50',
            'milestone': '#2196f3',
            'engagement': '#ff9800',
            'special': '#9c27b0'
        }
        color = colors.get(obj.category, '#9e9e9e')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.category.replace('_', ' ').title()
        )
    category_badge.short_description = 'Category'
    
    def condition_summary(self, obj):
        return format_html(
            '<small>{}<br><strong>{}</strong></small>',
            obj.condition_type.replace('_', ' ').title(),
            f"Threshold: {obj.threshold}" if obj.threshold else "No threshold"
        )
    condition_summary.short_description = 'Conditions'
    
    def users_earned(self, obj):
        count = obj.holders.count()
        return format_html('<span style="font-weight: bold;">{} users</span>', count)
    users_earned.short_description = '👥 Earned By'

@admin.register(UserBadge, site=admin_site)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'badge_display', 'earned_date', 'time_since_earned')
    list_filter = ('badge', 'earned_at')
    search_fields = ('user__username', 'badge__name')
    readonly_fields = ('earned_at', 'time_since_earned')
    
    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                         reverse('admin:auth_user_change', args=[obj.user.id]),
                         obj.user.username)
    user_link.short_description = 'User'
    
    def badge_display(self, obj):
        return format_html(
            '<span style="font-size: 16px; margin-right: 5px;">{}</span>{}',
            obj.badge.icon or '🏆',
            obj.badge.name
        )
    badge_display.short_description = 'Badge'
    
    def earned_date(self, obj):
        return obj.earned_at.strftime('%Y-%m-%d')
    earned_date.short_description = 'Date Earned'
    
    def time_since_earned(self, obj):
        delta = timezone.now() - obj.earned_at
        if delta.days > 30:
            return f"{delta.days // 30} months ago"
        elif delta.days > 0:
            return f"{delta.days} days ago"
        else:
            return "Today"
    time_since_earned.short_description = 'Time Ago'

@admin.register(EnvironmentalImpact, site=admin_site)
class EnvironmentalImpactAdmin(admin.ModelAdmin):
    list_display = ('metric_display', 'co2_per_unit', 'unit_label', 'usage_example')
    list_editable = ('co2_per_unit',)
    search_fields = ('metric_name', 'description')
    list_filter = ('unit_label',)
    
    fieldsets = (
        ('🌍 Metric Information', {
            'fields': ('metric_name', 'icon', 'description'),
            'classes': ('wide',)
        }),
        ('📊 Calculation Data', {
            'fields': ('co2_per_unit', 'unit_label'),
            'classes': ('wide',)
        })
    )
    
    def metric_display(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="font-size: 20px; margin-right: 10px;">{}</div>'
            '<div><strong>{}</strong></div>'
            '</div>',
            obj.icon or '🌍',
            obj.metric_name
        )
    metric_display.short_description = 'Metric'
    
    def usage_example(self, obj):
        # Example calculation
        example_co2 = 10  # 10kg CO2
        co2_per_unit = safe_float(obj.co2_per_unit, 1)
        
        if co2_per_unit == 0:
            return format_html('<small>No data available</small>')
        
        equivalent = example_co2 / co2_per_unit
        formatted_equivalent = f"{equivalent:.1f}"
        return format_html(
            '<small>10kg CO₂ = {} {}</small>',
            formatted_equivalent, obj.unit_label
        )
    usage_example.short_description = 'Example (10kg CO₂)'


# ================== PHASE 3: ADVANCED FEATURES ADMIN ================== #

@admin.register(Wishlist, site=admin_site)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'product_price', 'stock_status', 'added_at', 'quick_actions')
    list_filter = ('added_at', 'product__category')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('added_at',)
    
    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                         reverse('admin:auth_user_change', args=[obj.user.id]),
                         obj.user.username)
    user_link.short_description = 'User'
    
    def product_link(self, obj):
        return format_html('<a href="{}">{}</a>',
                         reverse('admin:shop_product_change', args=[obj.product.id]),
                         obj.product.name)
    product_link.short_description = 'Product'
    
    def product_price(self, obj):
        return f"${obj.product.price:.2f}"
    product_price.short_description = 'Price'
    
    def stock_status(self, obj):
        if obj.product.stock > 0:
            return format_html('<span style="color: green;">✅ In Stock ({})</span>', obj.product.stock)
        else:
            return format_html('<span style="color: red;">❌ Out of Stock</span>')
    stock_status.short_description = 'Stock'
    
    def quick_actions(self, obj):
        return format_html(
            '<a class="button" href="mailto:{}?subject=Wishlist Item Available&body=Your wishlist item {} is available!">📧 Notify</a>',
            obj.user.email, obj.product.name
        )
    quick_actions.short_description = 'Actions'

@admin.register(StockAlert, site=admin_site)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'threshold', 'current_stock', 'alert_status', 'created_at')
    list_filter = ('is_active', 'created_at', 'product__category')
    search_fields = ('user__username', 'product__name')
    actions = ['activate_alerts', 'deactivate_alerts', 'send_stock_notifications']
    
    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                         reverse('admin:auth_user_change', args=[obj.user.id]),
                         obj.user.username)
    user_link.short_description = 'User'
    
    def product_link(self, obj):
        return format_html('<a href="{}">{}</a>',
                         reverse('admin:shop_product_change', args=[obj.product.id]),
                         obj.product.name)
    product_link.short_description = 'Product'
    
    def current_stock(self, obj):
        stock = obj.product.stock
        if stock <= obj.threshold:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', stock)
        else:
            return format_html('<span style="color: green;">{}</span>', stock)
    current_stock.short_description = 'Current Stock'
    
    def alert_status(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: gray;">🔕 Inactive</span>')
        elif obj.product.stock <= obj.threshold:
            return format_html('<span style="color: red;">🚨 ALERT</span>')
        else:
            return format_html('<span style="color: green;">✅ Monitoring</span>')
    alert_status.short_description = 'Status'
    
    def activate_alerts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} alerts activated.')
    activate_alerts.short_description = "Activate selected alerts"
    
    def deactivate_alerts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} alerts deactivated.')
    deactivate_alerts.short_description = "Deactivate selected alerts"

@admin.register(UserNotification, site=admin_site)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'notification_badge', 'title_preview', 'status_badge', 'created_at', 'quick_actions')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    actions = ['mark_as_read', 'mark_as_unread', 'delete_old_notifications']
    readonly_fields = ('created_at',)
    
    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                         reverse('admin:auth_user_change', args=[obj.user.id]),
                         obj.user.username)
    user_link.short_description = 'User'
    
    def notification_badge(self, obj):
        type_styles = {
            'order': ('📦', '#2196f3'),
            'stock': ('📋', '#ff9800'),
            'sustainability': ('🌱', '#4caf50'),
            'general': ('💬', '#9e9e9e'),
            'promotion': ('🎯', '#e91e63')
        }
        icon, color = type_styles.get(obj.notification_type, ('📝', '#9e9e9e'))
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{} {}</span>',
            color, icon, obj.notification_type.title()
        )
    notification_badge.short_description = 'Type'
    
    def title_preview(self, obj):
        preview = obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
        return format_html('<span title="{}">{}</span>', obj.title, preview)
    title_preview.short_description = 'Title'
    
    def status_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✅ Read</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">📬 Unread</span>')
    status_badge.short_description = 'Status'
    
    def quick_actions(self, obj):
        if obj.is_read:
            return format_html('<small style="color: gray;">Read</small>')
        else:
            return format_html('<a class="button" href="?mark_read={}">Mark Read</a>', obj.id)
    quick_actions.short_description = 'Actions'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected as unread"

@admin.register(ProductReview, site=admin_site)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'rating_stars', 'title_preview', 'verified_badge', 'helpful_count', 'moderation_status', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('user__username', 'product__name', 'title', 'content')
    readonly_fields = ('created_at', 'updated_at', 'helpful_count')
    actions = ['approve_reviews', 'hide_reviews', 'feature_reviews']
    
    fieldsets = (
        ('👤 Review Information', {
            'fields': ('user', 'product', 'rating', 'title'),
        }),
        ('📝 Review Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('✅ Verification & Moderation', {
            'fields': ('is_verified_purchase', 'helpful_votes'),
            'classes': ('collapse',)
        }),
        ('📊 Statistics', {
            'fields': ('helpful_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                         reverse('admin:auth_user_change', args=[obj.user.id]),
                         obj.user.username)
    user_link.short_description = 'Reviewer'
    
    def product_link(self, obj):
        return format_html('<a href="{}">{}</a>',
                         reverse('admin:shop_product_change', args=[obj.product.id]),
                         obj.product.name)
    product_link.short_description = 'Product'
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span title="{}/5">{}</span>', obj.rating, stars)
    rating_stars.short_description = 'Rating'
    
    def title_preview(self, obj):
        preview = obj.title[:30] + '...' if len(obj.title) > 30 else obj.title
        return format_html('<span title="{}">{}</span>', obj.title, preview)
    title_preview.short_description = 'Title'
    
    def verified_badge(self, obj):
        if obj.is_verified_purchase:
            return format_html('<span style="background: #4caf50; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;">✅ VERIFIED</span>')
        else:
            return format_html('<span style="background: #9e9e9e; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;">❓ UNVERIFIED</span>')
    verified_badge.short_description = 'Verified'
    
    def helpful_count(self, obj):
        return f"👍 {obj.helpful_votes}"
    helpful_count.short_description = 'Helpful'
    
    def moderation_status(self, obj):
        # This would require a moderation field in the model
        return format_html('<span style="color: green;">✅ Approved</span>')
    moderation_status.short_description = 'Status'

# ===================== ADMIN SITE CUSTOMIZATION ===================== #

# Register User model with the custom admin site
admin_site.register(User, UserAdmin)

# Set as default admin site
admin.site = admin_site
admin.sites.site = admin_site
