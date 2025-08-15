from unicodedata import category
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem, Wishlist, StockAlert, UserNotification, ProductReview, UserImpact, Badge, UserBadge, EnvironmentalImpact
from .services.alternatives import greener_alternative, swap_ladder
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, RatingForm, CheckoutForm, ProductReviewForm, StockAlertForm, AdvancedSearchForm, PasswordResetRequestForm, SetNewPasswordForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min, Max, Avg, Count
from django.contrib.auth.decorators import login_required
from .utils import generate_sslcommerz_payment, send_order_confirmation_email, send_password_reset_email
from decimal import Decimal
from .services.budget import budget_status, update_budget
from .services.simulator import project_scenario
from .forms import CarbonBudgetForm
from django.views.decorators.csrf import csrf_exempt
from .services.impact import record_order_impact
from .services.carbon_intelligence import (
    analyze_product_carbon_impact, 
    generate_impact_story, 
    check_carbon_achievements,
    simulate_future_impact,
    get_environmental_equivalents
)
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.models import User



# Create your views from here ..... 


# login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('shop:home')  # ✅ Fixed: redirect to home instead of register
        else:
            messages.error(request, 'Invalid username or password')

    context = {}
    return render(request, 'shop/login.html', context)


# Register view
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Specify the backend explicitly to avoid authentication backend conflict
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful")
            return redirect('shop:home')  # Redirect to home instead of login after successful registration
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})


# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('shop:login')



# Home view
def home(request):
    # Product model uses 'created' field (not 'created_at')
    featured_products = Product.objects.filter(available=True).order_by('-created')[:8]
    categories = Category.objects.all()

    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'categories': categories
    })


# Product list view
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    price_range = products.aggregate(min_price=Min('price'), max_price=Max('price'))
    min_price = price_range['min_price']
    max_price = price_range['max_price']

    # Filters
    if request.GET.get('min_price'):
        try:
            products = products.filter(price__gte=Decimal(request.GET.get('min_price')))
        except Exception:
            pass
    if request.GET.get('max_price'):
        try:
            products = products.filter(price__lte=Decimal(request.GET.get('max_price')))
        except Exception:
            pass
    if request.GET.get('rating'):
        try:
            min_rating = int(request.GET.get('rating'))
            products = products.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)
        except Exception:
            pass

    query = request.GET.get('search', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    return render(request, 'shop/product_list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': query,
    })


# Product detail view
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available = True)
    related_products = Product.objects.filter(category = product.category).exclude(id=product.id)
    user_rating = None

    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product=product, user=request.user)
        except Rating.DoesNotExist:
            pass
    rating_form = RatingForm(instance=user_rating)

    # Impact additions
    alternative = greener_alternative(product)
    ladder = swap_ladder(product)
    
    # Carbon intelligence analysis
    carbon_analysis = analyze_product_carbon_impact(product)
    
    # Get user's environmental impact story if authenticated
    impact_story = None
    if request.user.is_authenticated:
        impact_story = generate_impact_story(request.user)

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'user_rating': user_rating,
        'rating_form': rating_form,
        'alternative': alternative,
        'ladder': ladder,
        'carbon_analysis': carbon_analysis,
        'impact_story': impact_story,
    })



# Cart detail view
@login_required
def cart_detail(request):
   try:
       cart = Cart.objects.get(user=request.user)
   except Cart.DoesNotExist:
       cart = Cart.objects.create(user=request.user)
   # Build items footprint + alternative suggestions
   items_with_alt = []
   total_footprint = 0
   for item in cart.items.select_related('product', 'product__category'):
       p = item.product
       line_footprint = p.effective_carbon_kg() * item.quantity if hasattr(p, 'effective_carbon_kg') else 0
       total_footprint += line_footprint
       alt = greener_alternative(p)
       potential_save = 0
       if alt:
           potential_save = max((p.effective_carbon_kg() - alt.effective_carbon_kg()) * item.quantity, 0)
       items_with_alt.append({
           'item': item,
           'alt': alt,
           'line_footprint': line_footprint,
           'potential_save': potential_save,
       })

   return render(request, 'shop/cart_detail.html', {
       'cart': cart,
       'items_with_alt': items_with_alt,
       'total_footprint': total_footprint,
   })




# Cart add view
@login_required
def cart_add(request, product_id):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('shop:home')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is in stock
    if not product.is_in_stock():
        messages.error(request, f"Sorry, {product.name} is currently out of stock.")
        return redirect('shop:product_detail', slug=product.slug)
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)

    quantity = int(request.POST.get('quantity', 1))
    
    # Validate quantity
    if quantity <= 0:
        messages.error(request, "Invalid quantity.")
        return redirect('shop:product_detail', slug=product.slug)
    
    # Check if adding this quantity would exceed stock
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        new_total = cart_item.quantity + quantity
        if new_total > product.stock:
            messages.error(request, f"Cannot add {quantity} items. Only {product.stock - cart_item.quantity} available.")
            return redirect('shop:product_detail', slug=product.slug)
        cart_item.quantity = new_total
        cart_item.save()
    except CartItem.DoesNotExist:
        if quantity > product.stock:
            messages.error(request, f"Cannot add {quantity} items. Only {product.stock} available.")
            return redirect('shop:product_detail', slug=product.slug)
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)

    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('shop:product_detail', slug=product.slug)


# Cart remove view
@login_required
def cart_remove(request, product_id):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('shop:cart_detail')
    
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    cart_item.delete()
    messages.success(request, f"{product.name} has been removed from your cart.")
    return redirect('shop:cart_detail')



# Cart update view
@login_required
def cart_update(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        cart_item.delete()
        messages.success(request, f"{product.name} has been removed from your cart!")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"{product.name} has been updated in your cart.")
    return redirect('shop:cart_detail')



# Checkout view
@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty!')
            return redirect('shop:cart_detail')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty!')
        return redirect('shop:cart_detail')

    # Validate cart items before checkout
    invalid_items = []
    for item in cart.items.all():
        if not item.product.is_in_stock():
            invalid_items.append(f"{item.product.name} is out of stock")
        elif item.quantity > item.product.stock:
            invalid_items.append(f"{item.product.name}: only {item.product.stock} available (you have {item.quantity})")
    
    if invalid_items:
        for error in invalid_items:
            messages.error(request, error)
        return redirect('shop:cart_detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                # Double-check stock before creating order
                for item in cart.items.all():
                    if not item.product.is_in_stock() or item.quantity > item.product.stock:
                        messages.error(request, f"Stock unavailable for {item.product.name}. Please update your cart.")
                        return redirect('shop:cart_detail')
                
                order = form.save(commit=False)
                order.user = request.user
                order.save()

                # Create order items and update stock
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order, 
                        product=item.product, 
                        price=item.product.price, 
                        quantity=item.quantity
                    )
                    # Update product stock
                    item.product.stock -= item.quantity
                    item.product.save()
                
                # Clear cart
                cart.items.all().delete()
                request.session['order_id'] = order.id
                messages.success(request, 'Your order has been placed successfully!')
                return redirect('shop:payment_process')
            except Exception as e:
                messages.error(request, 'An error occurred while processing your order. Please try again.')
                return redirect('shop:checkout')
    else:
        initial_data = {}
        if request.user.first_name:
            initial_data['first_name'] = request.user.first_name
        if request.user.last_name:
            initial_data['last_name'] = request.user.last_name
        if request.user.email:
            initial_data['email'] = request.user.email
        form = CheckoutForm(initial=initial_data)

    return render(request, 'shop/checkout.html', {
           'cart': cart,
           'form': form
       })


# Payment process view
@csrf_exempt    # use this decorator to exempt the view from CSRF verification for payment processing
@login_required
def payment_process(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'No order found.')
        return redirect('shop:home')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment_data = generate_sslcommerz_payment(order, request)

    if payment_data['status'] == 'SUCCESS':
        # Payment was successful
        return redirect(payment_data['GatewayPageURL'])
    else:
        # Payment failed
        messages.error(request, 'Payment failed. Please try again.')
        return redirect('shop:checkout')


# Payment success view
@csrf_exempt
def payment_success(request, order_id):
    # Debug session and authentication
    print(f"🔍 Payment success called for order #{order_id}")
    print(f"🔍 User authenticated: {request.user.is_authenticated}")
    print(f"🔍 User: {request.user}")
    print(f"🔍 Session key: {request.session.session_key}")
    
    # Check if user is authenticated, if not try to get order without user filter
    if not request.user.is_authenticated:
        print("⚠️ User not authenticated in payment_success, trying to find order without user filter")
        order = get_object_or_404(Order, id=order_id)
        # If order exists but user not authenticated, it might be a session issue
        # Let's continue processing but redirect differently
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    
    order.paid = True
    # Align with defined choices ('Processing')
    order.status = 'Processing'
    order.transaction_id = order.id
    order.save()

    order_items = order.items.all()
    for item in order_items:
        product = item.product
        product.stock -= item.quantity

        if product.stock < 0:
            product.stock = 0
        product.save()

    # Record sustainability impact after successful payment
    try:
        record_order_impact(order)
    except Exception:
        pass
    
    # Send order confirmation email
    print(f"🔔 Attempting to send order confirmation email for order #{order.id}")
    email_sent = send_order_confirmation_email(order)
    if email_sent:
        print(f"✅ Order confirmation email sent successfully to {order.email}")
    else:
        print(f"❌ Failed to send order confirmation email to {order.email}")
    
    messages.success(request, 'Payment successful! Your order has been placed.')
    
    # Redirect to order success page instead of profile/login
    return redirect('shop:order_success', order_id=order.id)



# Order success page view
def order_success(request, order_id):
    """Order success page that works for both authenticated and anonymous users"""
    print(f"🔍 Order success page called for order #{order_id}")
    print(f"🔍 User authenticated: {request.user.is_authenticated}")
    
    # Try to get order, don't require authentication
    try:
        if request.user.is_authenticated:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Check for carbon achievements
            check_carbon_achievements(request.user, order)
            
        else:
            order = get_object_or_404(Order, id=order_id)
            
        return render(request, 'shop/order_success.html', {
            'order_id': order_id,
            'order': order
        })
    except:
        messages.error(request, 'Order not found.')
        return redirect('shop:home')



# Payment fail view
@csrf_exempt
def payment_fail(request, order_id):
    print(f"🔍 Payment fail called for order #{order_id}")
    print(f"🔍 User authenticated: {request.user.is_authenticated}")
    
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)
        
    order.status = 'Cancelled'
    order.save()
    messages.error(request, 'Payment failed. Please try again.')
    
    if request.user.is_authenticated:
        return redirect('shop:checkout')
    else:
        return redirect('shop:login')



# Payment cancel view
@csrf_exempt
def payment_cancel(request, order_id):
    print(f"🔍 Payment cancel called for order #{order_id}")
    print(f"🔍 User authenticated: {request.user.is_authenticated}")
    
    if request.user.is_authenticated:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    else:
        order = get_object_or_404(Order, id=order_id)
        
    order.status = 'Cancelled'
    order.save()
    messages.info(request, 'Payment was cancelled.')
    
    if request.user.is_authenticated:
        return redirect('shop:cart_detail')
    else:
        return redirect('shop:login')


# Profile view
@login_required
def profile(request):
    tab = request.GET.get('tab')
    orders = Order.objects.filter(user=request.user).order_by('-created')
    completed_orders = orders.filter(status='Delivered').count()
    total_spent = sum(order.get_total_cost() for order in orders if order.paid)  # Fixed: added ()
    order_history_active = (tab == 'orders')
    return render(request, 'shop/profile.html', {
        'user' : request.user,
        'orders' : orders,
        'order_history_active' : order_history_active,
        'completed_orders' : completed_orders,
        'total_spent' : total_spent,
    })


# Impact dashboard view
@login_required
def impact_dashboard(request):
    ui = getattr(request.user, 'impact_summary', None)
    status = budget_status(request.user)
    recent_impacts = []
    if ui:
        # Get recent orders with impact data
        recent_orders = request.user.orders.filter(impact__isnull=False).select_related('impact').order_by('-created')[:5]
        recent_impacts = [
            {
                'id': order.id,
                'carbon': order.impact.carbon_kg,
                'saved': order.impact.saved_kg,
                'created': order.impact.created_at,
            }
            for order in recent_orders
        ]
    
    # Generate personalized impact story
    impact_story = generate_impact_story(request.user)
    
    # Get user's badges
    user_badges = UserBadge.objects.filter(user=request.user).select_related('badge').order_by('-earned_at')
    
    form = CarbonBudgetForm(initial={'month_budget_kg': ui.month_budget_kg if ui else 0})
    return render(request, 'shop/impact_dashboard.html', {
        'impact': ui,
        'budget_status': status,
        'recent_impacts': recent_impacts,
        'budget_form': form,
        'impact_story': impact_story,
        'user_badges': user_badges,
    })


# Update budget view
@login_required
def set_budget(request):
    if request.method == 'POST':
        form = CarbonBudgetForm(request.POST)
        if form.is_valid():
            update_budget(request.user, form.cleaned_data['month_budget_kg'])
            messages.success(request, 'Budget updated.')
            return redirect('shop:impact_dashboard')
    return redirect('shop:impact_dashboard')


# Simple what-if simulator (POST)
@login_required
def what_if_simulator(request):
    if request.method == 'POST':
        try:
            swap_fraction = Decimal(request.POST.get('swap_fraction', '0'))  # 0-1
            saving_ratio = Decimal(request.POST.get('saving_ratio', '0.3'))   # average per swap
            months = int(request.POST.get('months', '3'))
        except Exception:
            messages.error(request, 'Invalid input for simulation.')
            return redirect('shop:impact_dashboard')
        from decimal import Decimal as D
        result = project_scenario(request.user, swap_fraction, saving_ratio, months)
        request.session['simulator_result'] = {k: str(v) for k,v in result.items()}
        return redirect('shop:impact_dashboard')
    return redirect('shop:impact_dashboard')


# Environmental Impact Simulator
@login_required
def environmental_simulator(request):
    if request.method == 'POST':
        try:
            monthly_reduction = Decimal(request.POST.get('monthly_reduction', '5.0'))
            timeframe_months = int(request.POST.get('timeframe', '12'))
            
            # Simulate future impact
            simulation = simulate_future_impact(monthly_reduction, timeframe_months)
            
            return JsonResponse({
                'success': True,
                'simulation': simulation
            })
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid input parameters'
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})



# Rate product view
@login_required
def rate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    ordered_items = OrderItem.objects.filter(
        order__user=request.user,
        order__paid=True,
        product=product
    )

    if not ordered_items.exists():
        messages.warning(request, 'You can only rate products you have purchased')
        return redirect('shop:product_detail', slug=product.slug)

    try:
        rating = Rating.objects.get(product=product, user=request.user)
    except Rating.DoesNotExist:
        rating = None

    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = product
            rating.user = request.user
            rating.save()
            return redirect('shop:product_detail')
    else:
        form = RatingForm(instance=rating)
    

    return render(request, 'shop/rate_product.html', {
        'form': form,
        'product': product,
        'rating': rating
    })


# ==================== Phase 3: Advanced Features ==================== #

# Wishlist Views
@login_required
def wishlist(request):
    """Display user's wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    return render(request, 'shop/wishlist.html', {
        'wishlist_items': wishlist_items
    })


@login_required
def wishlist_add(request, product_id):
    """Add product to wishlist"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            messages.success(request, f"{product.name} has been added to your wishlist.")
        else:
            messages.info(request, f"{product.name} is already in your wishlist.")
    
    return redirect('shop:product_detail', slug=product.slug)


@login_required
def wishlist_remove(request, product_id):
    """Remove product from wishlist"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, product=product)
            wishlist_item.delete()
            messages.success(request, f"{product.name} has been removed from your wishlist.")
        except Wishlist.DoesNotExist:
            messages.error(request, "Product not found in your wishlist.")
    
    return redirect('shop:wishlist')


# Order Tracking Views
@login_required
def order_detail(request, order_id):
    """Detailed order tracking page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Order status timeline
    status_timeline = []
    if order.created:
        status_timeline.append({
            'status': 'Order Placed',
            'date': order.created,
            'completed': True
        })
    
    if order.paid:
        status_timeline.append({
            'status': 'Payment Confirmed',
            'date': order.updated,  # Approximate
            'completed': True
        })
    
    if order.status in ['Processing', 'Shipped', 'Out for Delivery', 'Delivered']:
        status_timeline.append({
            'status': 'Processing',
            'date': order.updated,
            'completed': True
        })
    
    if order.shipped_at:
        status_timeline.append({
            'status': 'Shipped',
            'date': order.shipped_at,
            'completed': True
        })
    
    if order.status == 'Out for Delivery':
        status_timeline.append({
            'status': 'Out for Delivery',
            'date': order.updated,
            'completed': True
        })
    
    if order.delivered_at:
        status_timeline.append({
            'status': 'Delivered',
            'date': order.delivered_at,
            'completed': True
        })
    
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'status_timeline': status_timeline
    })


# Product Reviews
@login_required
def product_review(request, product_id):
    """Add or edit product review"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__paid=True,
        product=product
    ).exists()
    
    if not has_purchased:
        messages.warning(request, 'You can only review products you have purchased.')
        return redirect('shop:product_detail', slug=product.slug)
    
    # Get existing review if any
    try:
        review = ProductReview.objects.get(product=product, user=request.user)
    except ProductReview.DoesNotExist:
        review = None
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.is_verified_purchase = has_purchased
            review.save()
            messages.success(request, 'Your review has been saved successfully!')
            return redirect('shop:product_detail', slug=product.slug)
    else:
        form = ProductReviewForm(instance=review)
    
    return render(request, 'shop/product_review.html', {
        'form': form,
        'product': product,
        'review': review
    })


@login_required
def review_helpful(request, review_id):
    """Mark review as helpful"""
    if request.method == 'POST':
        review = get_object_or_404(ProductReview, id=review_id)
        review.helpful_votes += 1
        review.save()
        return JsonResponse({'status': 'success', 'helpful_votes': review.helpful_votes})
    
    return JsonResponse({'status': 'error'})


# Stock Alerts
@login_required
def stock_alert_create(request, product_id):
    """Create stock alert for product"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        form = StockAlertForm(request.POST)
        
        if form.is_valid():
            alert, created = StockAlert.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'threshold': form.cleaned_data['threshold']}
            )
            
            if created:
                messages.success(request, f"Stock alert created for {product.name}")
            else:
                alert.threshold = form.cleaned_data['threshold']
                alert.is_active = True
                alert.save()
                messages.success(request, f"Stock alert updated for {product.name}")
        
        return redirect('shop:product_detail', slug=product.slug)
    
    return redirect('shop:home')


@login_required
def stock_alerts_list(request):
    """List all user's stock alerts"""
    alerts = StockAlert.objects.filter(user=request.user, is_active=True).select_related('product')
    
    return render(request, 'shop/stock_alerts.html', {
        'alerts': alerts
    })


@login_required
def stock_alert_remove(request, alert_id):
    """Remove stock alert"""
    if request.method == 'POST':
        alert = get_object_or_404(StockAlert, id=alert_id, user=request.user)
        alert.is_active = False
        alert.save()
        messages.success(request, f"Stock alert removed for {alert.product.name}")
    
    return redirect('shop:stock_alerts_list')


# Notifications
@login_required
def notifications(request):
    """User notifications page"""
    notifications = UserNotification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    
    # Mark all as read when viewing
    notifications.filter(is_read=False).update(is_read=True)
    
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'shop/notifications.html', {
        'notifications': page_obj,
        'unread_count': unread_count
    })


@login_required
def notifications_count(request):
    """Get unread notifications count (AJAX)"""
    count = UserNotification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


# Enhanced Product Search
def product_search(request):
    """Advanced product search with filters"""
    form = AdvancedSearchForm(request.GET)
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        min_rating = form.cleaned_data.get('min_rating')
        in_stock_only = form.cleaned_data.get('in_stock_only')
        sort_by = form.cleaned_data.get('sort_by')
        
        # Apply filters
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)
        
        if min_rating:
            products = products.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=int(min_rating))
        
        if in_stock_only:
            products = products.filter(stock__gt=0)
        
        # Apply sorting
        if sort_by:
            if sort_by == '-avg_rating':
                products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
            else:
                products = products.order_by(sort_by)
    
    # Annotate with ratings for display
    products = products.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'shop/product_search.html', {
        'form': form,
        'products': page_obj,
        'categories': categories,
        'total_results': products.count()
    })


# Enhanced Product Detail with Reviews
def enhanced_product_detail(request, slug):
    """Enhanced product detail page with reviews and recommendations"""
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # Get product reviews
    reviews = ProductReview.objects.filter(product=product).select_related('user').order_by('-created_at')
    review_stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        rating_distribution[i] = reviews.filter(rating=i).count()
    
    # User's existing review
    user_review = None
    user_has_purchased = False
    if request.user.is_authenticated:
        try:
            user_review = ProductReview.objects.get(product=product, user=request.user)
        except ProductReview.DoesNotExist:
            pass
        
        user_has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__paid=True,
            product=product
        ).exists()
    
    # Related products based on category and ratings
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating')[:4]
    
    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Stock alert form
    stock_alert_form = StockAlertForm()
    
    # Impact additions
    alternative = greener_alternative(product)
    ladder = swap_ladder(product)
    
    return render(request, 'shop/enhanced_product_detail.html', {
        'product': product,
        'reviews': reviews[:5],  # Show first 5 reviews
        'review_stats': review_stats,
        'rating_distribution': rating_distribution,
        'user_review': user_review,
        'user_has_purchased': user_has_purchased,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
        'stock_alert_form': stock_alert_form,
        'alternative': alternative,
        'ladder': ladder,
    })


# =================== Password Reset Views =================== #

def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                # Handle multiple users with same email - get the first one
                user = User.objects.filter(email=email).first()
                if user:
                    email_sent = send_password_reset_email(user, request)
                    if email_sent:
                        messages.success(request, 
                            f'Password reset instructions have been sent to {email}. '
                            'Please check your email and follow the instructions.')
                        return redirect('shop:login')
                    else:
                        messages.error(request, 'Failed to send password reset email. Please try again.')
                else:
                    # This shouldn't happen due to form validation, but just in case
                    messages.error(request, 'No account found with this email address.')
            except Exception as e:
                messages.error(request, 'An error occurred while processing your request. Please try again.')
                print(f"Password reset error: {e}")
        else:
            messages.error(request, 'Please enter a valid email address.')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'shop/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation with token validation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetNewPasswordForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data['password1']
                user.set_password(password)
                user.save()
                messages.success(request, 
                    'Your password has been successfully reset. You can now log in with your new password.')
                return redirect('shop:login')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = SetNewPasswordForm()
        
        return render(request, 'shop/password_reset_confirm.html', {
            'form': form,
            'uidb64': uidb64,
            'token': token
        })
    else:
        messages.error(request, 
            'The password reset link is invalid or has expired. Please request a new password reset.')
        return redirect('shop:password_reset_request')
