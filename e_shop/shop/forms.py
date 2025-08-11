from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Rating, Order, ProductReview, StockAlert



# Registration Form
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        }


# Login Form
class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )


# Rating Form
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Leave a comment...'}),
        }



# Order Form
class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'note']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'address': forms.TextInput(attrs={'placeholder': 'Address'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal Code'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'note': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Order Notes...'}),
        }


# Budget Form
class CarbonBudgetForm(forms.Form):
    month_budget_kg = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
        help_text="Set your monthly carbon budget in kg CO₂e"
    )


# ------------------- Phase 3 Forms ------------------- #

# Product Review Form
class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['title', 'content', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Review title',
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'rows': 5, 
                'placeholder': 'Share your experience with this product...',
                'class': 'form-control'
            }),
            'rating': forms.Select(
                choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
        }


# Stock Alert Form
class StockAlertForm(forms.ModelForm):
    class Meta:
        model = StockAlert
        fields = ['threshold']
        widgets = {
            'threshold': forms.NumberInput(attrs={
                'placeholder': 'Alert when stock falls below',
                'class': 'form-control',
                'min': 1,
                'value': 5
            }),
        }


# Advanced Search Form
class AdvancedSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search products...',
            'class': 'form-control'
        })
    )
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min price',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max price',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    min_rating = forms.ChoiceField(
        choices=[('', 'Any Rating')] + [(i, f"{i}+ Stars") for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    in_stock_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('', 'Default'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('price', 'Price Low-High'),
            ('-price', 'Price High-Low'),
            ('-created', 'Newest First'),
            ('created', 'Oldest First'),
            ('-avg_rating', 'Highest Rated'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )