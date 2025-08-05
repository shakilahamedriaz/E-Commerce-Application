from django.contrib import admin
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
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
    list_display = ('name', 'slug', 'price', 'stock', 'available', 'created', 'updated')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'stock', 'available']
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
    list_display = ('id', 'user', 'first_name', 'last_name', 'email', 'paid', 'created', 'status')
    list_filter = ['paid', 'created', 'status']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Admin for OrderItem model
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'comment', 'created')
    list_filter = ['rating', 'created']
