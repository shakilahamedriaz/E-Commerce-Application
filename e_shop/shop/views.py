from unicodedata import category
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
from .services.alternatives import greener_alternative, swap_ladder
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, RatingForm, CheckoutForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min, Max, Avg
from django.contrib.auth.decorators import login_required
from .utils import generate_sslcommerz_payment, send_order_confirmation_email
from decimal import Decimal
from .services.budget import budget_status, update_budget
from .services.simulator import project_scenario
from .forms import CarbonBudgetForm
from django.views.decorators.csrf import csrf_exempt
from .services.impact import record_order_impact



# Create your views from here ..... 


# login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('shop:register')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'shop/login.html')


# Register view
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful")
            return redirect('shop:login')
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

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'user_rating': user_rating,
        'rating_form': rating_form,
        'alternative': alternative,
        'ladder': ladder,
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
    product = get_object_or_404(Product, id=product_id)
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product, quantity=1)

    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('shop:product_detail', slug=product.slug)


# Cart remove view
@login_required
def cart_remove(request, product_id):
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
            return redirect('shop:home')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty!')
        return redirect('shop:cart_detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
            cart.items.all().delete()
            request.session['order_id'] = order.id
            messages.success(request, 'Your order has been placed successfully!')
            return redirect('shop:payment_process')
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
@login_required
def payment_success(request, order_id):
    order=get_object_or_404(Order, id=order_id, user=request.user)
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
    send_order_confirmation_email(order)
    messages.success(request, 'Payment successful! Your order has been placed.')
    return redirect('shop:profile')



# Payment fail view
@csrf_exempt
@login_required
def payment_fail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'Cancelled'
    order.save()
    return redirect('shop:checkout')



# Payment cancel view
@csrf_exempt
@login_required
def payment_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'Cancelled'
    order.save()
    return redirect('shop:cart_detail')


# Profile view
@login_required
def profile(request):
    tab = request.GET.get('tab')
    orders = Order.objects.filter(user=request.user).order_by('-created')
    completed_orders = orders.filter(status='Delivered').count()
    total_spent = sum(order.get_total_cost for order in orders if order.paid)
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
    form = CarbonBudgetForm(initial={'month_budget_kg': ui.month_budget_kg if ui else 0})
    return render(request, 'shop/impact_dashboard.html', {
        'impact': ui,
        'budget_status': status,
        'recent_impacts': recent_impacts,
        'budget_form': form,
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
