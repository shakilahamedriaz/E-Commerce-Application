from unicodedata import category
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from urllib3 import request
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm, RatingForm, CheckoutForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Min, Max, Avg
from django.contrib.auth.decorators import login_required



# Create your views from here ..... 

# Home view
def home(request):
    return render(request, 'shop/home.html')

#authentication views
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'shop/login.html')
    return render(request, 'shop/login.html')



def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful")
            return redirect('home')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


def home(request):
    featured_products = Product.objects.filter(available=True).order_by('-created_at')[:8]
    categories = Category.objects.all()

    return render(request, 'shop/home.html', {
        'featured_products': featured_products,
        'categories': categories
    })


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available = True)
    
    if category_slug :
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    min_price = products.aggregate(Min('price'))['price_min']
    max_price = products.aggregate(Max('price'))['price_max']
    
    if request.GET.get(min_price) and request.GET.get(max_price):
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        products = products.filter(price__gte=min_price, price__lte=max_price)

    if request.GET.get('min_price'):
        products = products.filter(price__gte=request.GET.get('min_price'))
    if request.GET.get('max_price'):
        products = products.filter(price__lte=request.GET.get('max_price'))
    if request.GET.get('rating'):
        min_rating = request.GET.get('rating')
        products = products.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=min_rating)

    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    return render(request, 'shop/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': query
    })


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

    return render(request, 'shop/product/detail.html', {
        'product': product,
        'related_products': related_products,
        'user_rating': user_rating,
        'rating_form': rating_form
    })


@login_required
def cart_detail(request):
   try:
       cart = Cart.objects.get(user=request.user)
   except Cart.DoesNotExist:
       cart = Cart.objects.create(user=request.user)

   return render(request, 'shop/cart/detail.html', {
       'cart': cart
   })




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
    return redirect('')


@login_required
def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    cart_item.delete()
    messages.success(request, f"{product.name} has been removed from your cart.")
    return redirect('')


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
        cart.save()
        messages.success(request, f"{product.name} has been updated in your cart.")
    return redirect('')


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty!')
            return redirect('')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty!')
        return redirect('')
    
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
            return redirect('order_success')
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
