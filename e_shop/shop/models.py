from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal


# Create your models here.

# categorize products in the e-shop
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Sustainability extension: default emission factor (kg CO2e per unit) used as fallback for products
    default_emission_factor_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Fallback kg CO₂e per unit if product value not provided"
    )
    
    class Meta: 
        verbose_name = 'Categories'  


    def __str__(self): 
        return self.name


# Products in the e-sho
class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2) # like 10.99
    stock = models.PositiveIntegerField(default=0)  
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True)
    # Impact extension fields
    carbon_footprint_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Specific kg CO₂e per unit; leave blank to use category default"
    )
    ethics_score = models.PositiveIntegerField(default=50, help_text="0-100 composite ethics score")
    impact_confidence = models.PositiveIntegerField(default=80, help_text="Confidence in impact data (0-100)")


    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Get URL for product detail page"""
        from django.urls import reverse
        return reverse('shop:product_detail', kwargs={'slug': self.slug})
    
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews.count() > 0:
            return sum([review.rating for review in reviews]) / reviews.count()
        
        # Fallback to old ratings system if no reviews
        ratings = self.ratings.all()
        if ratings.count() > 0:
            return sum([rating.rating for rating in ratings]) / ratings.count()
        return 0
    
    def get_review_count(self):
        """Get total number of reviews"""
        return self.reviews.count()
    
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0
    
    def can_add_to_cart(self, quantity=1):
        """Check if quantity can be added to cart"""
        return self.available and self.stock >= quantity
    
    # Sustainability helper: effective carbon (product value or category fallback)
    def effective_carbon_kg(self):
        if self.carbon_footprint_kg is not None:
            return self.carbon_footprint_kg
        if self.category and self.category.default_emission_factor_kg:
            return self.category.default_emission_factor_kg
        return Decimal("0.00")



# Ratings for products
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"
    


# Shopping Cart for users
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Cart of {self.user.username}"
    
    def get_total_price(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def get_total_item(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_total_items_count(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())



# Cart Items for products in the cart
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        # prevent duplicate products in same cart.
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} X {self.product.name}"

    def get_cost(self):
        return self.product.price * self.quantity
   

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    note = models.TextField(blank=True)
    paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Enhanced tracking fields
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    courier_service = models.CharField(max_length=100, blank=True, help_text="e.g., DHL, FedEx, UPS")


    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"Order {self.id}"
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
        
    def get_status_display_class(self):
        """Return CSS class for status display"""
        status_classes = {
            'Pending': 'warning',
            'Processing': 'info',
            'Shipped': 'primary',
            'Out for Delivery': 'info',
            'Delivered': 'success',
            'Cancelled': 'danger',
            'Returned': 'secondary',
        }
        return status_classes.get(self.status, 'secondary')


# Order Items for products in the order
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} X {self.product.name}"

    def get_cost(self):
        return self.price * self.quantity


# ---------------- Sustainability / Impact Additions ---------------- #

class UserImpact(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='impact_summary')
    total_carbon_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_saved_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Baseline - actual cumulative")
    current_month_carbon_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    month_budget_kg = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="User-set monthly carbon budget")
    low_impact_streak = models.PositiveIntegerField(default=0, help_text="Consecutive below-baseline (saved>0) orders")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Impact for {self.user}" 


class OrderImpact(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='impact')
    carbon_kg = models.DecimalField(max_digits=10, decimal_places=2)
    baseline_kg = models.DecimalField(max_digits=10, decimal_places=2)
    saved_kg = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OrderImpact(order={self.order_id}, carbon={self.carbon_kg})"


class Badge(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    condition_type = models.CharField(max_length=50, help_text="Metric key, e.g. TOTAL_SAVED, STREAK, FIRST_ORDER")
    threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Enhanced badge features
    BADGE_CATEGORIES = [
        ('CARBON', 'Carbon Reduction'),
        ('GENERAL', 'General Achievement'),
        ('STREAK', 'Streak Achievement'),
        ('MILESTONE', 'Milestone Achievement'),
    ]
    category = models.CharField(max_length=20, choices=BADGE_CATEGORIES, default='GENERAL')
    icon = models.CharField(max_length=50, default='🌱')  # Emoji or CSS class
    popup_message = models.TextField(blank=True)  # Custom popup message

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='holders')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user} -> {self.badge.code}"


# ================ Carbon Intelligence Features ================ #

class EnvironmentalImpact(models.Model):
    """Conversion factors for environmental impact visualization"""
    metric_name = models.CharField(max_length=100, unique=True)
    co2_per_unit = models.DecimalField(max_digits=10, decimal_places=4)  # kg CO2 per unit
    unit_label = models.CharField(max_length=50)  # e.g., "trees", "miles", "lightbulbs"
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🌳')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.metric_name} ({self.unit_label})"


# ---------------- Phase 3: Advanced Features ---------------- #

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class StockAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stock_alerts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts')
    threshold = models.PositiveIntegerField(default=5, help_text="Alert when stock falls below this number")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"Alert for {self.user.username} - {self.product.name} (threshold: {self.threshold})"


class UserNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('stock_alert', 'Stock Alert'),
        ('order_update', 'Order Update'),
        ('new_product', 'New Product'),
        ('price_drop', 'Price Drop'),
        ('sustainability', 'Sustainability Achievement'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    related_order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_verified_purchase = models.BooleanField(default=False)
    helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"
