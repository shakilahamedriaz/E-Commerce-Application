from django.contrib import admin
from .models import (Category, Product, Rating, Cart, CartItem, Order, OrderItem, 
                     UserImpact, OrderImpact, Badge, UserBadge, Wishlist, StockAlert, 
                     UserNotification, ProductReview, EnvironmentalImpact)
from django.contrib.auth.models import User

# Register your models here.

# Admin for User model
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}



class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created')
    can_delete = False

# Admin for Product model
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'stock', 'available', 'created', 'updated', 'carbon_footprint_kg', 'ethics_score')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'stock', 'available', 'carbon_footprint_kg', 'ethics_score']
    inlines = [RatingInline]



class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

# Admin for Cart model
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Admin for Order model
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'email', 'paid', 'created', 'status', 'tracking_number')
    list_filter = ['paid', 'created', 'status', 'courier_service']
    search_fields = ['first_name', 'last_name', 'email', 'tracking_number']
    inlines = [OrderItemInline]
    readonly_fields = ('created', 'updated')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Admin for OrderItem model
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'comment', 'created')
    list_filter = ['rating', 'created']


@admin.register(UserImpact)
class UserImpactAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_carbon_kg', 'total_saved_kg', 'current_month_carbon_kg', 'month_budget_kg', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(OrderImpact)
class OrderImpactAdmin(admin.ModelAdmin):
    list_display = ('order', 'carbon_kg', 'baseline_kg', 'saved_kg', 'created_at')
    search_fields = ('order__id', 'order__user__username')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'condition_type', 'threshold', 'category', 'icon')
    search_fields = ('code', 'name')
    list_filter = ('category', 'condition_type')
    fields = ('code', 'name', 'description', 'condition_type', 'threshold', 'category', 'icon', 'popup_message')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    search_fields = ('user__username', 'badge__code')


@admin.register(EnvironmentalImpact)
class EnvironmentalImpactAdmin(admin.ModelAdmin):
    list_display = ('metric_name', 'co2_per_unit', 'unit_label', 'icon')
    search_fields = ('metric_name', 'description')
    list_filter = ('unit_label',)
    fields = ('metric_name', 'co2_per_unit', 'unit_label', 'description', 'icon')


# ================== Phase 3: Advanced Features Admin ================== #

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'threshold', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'product__name')


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'title', 'rating', 'is_verified_purchase', 'helpful_votes', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('user__username', 'product__name', 'title', 'content')
    readonly_fields = ('created_at', 'updated_at')
