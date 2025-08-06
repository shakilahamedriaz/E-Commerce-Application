from email.mime import message
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth.decorators import login_required



# Create your views from here ..... 
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
            return render(request, 'login.html')
    return render(request, 'login.html')



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
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')