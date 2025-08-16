from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9o7cqidb6ln4#p9roquk(d-wng92^^+gw-th%rdqulvf-&p6_#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'shop',  # created custom app for the e-shop 
    'ai_chatbot_agent',  # AI chatbot app for customer support


    #required for social media authentication
    'allauth',
    'allauth.account',
    #optional
    'allauth.socialaccount',
    #include the providers you want to enable:
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Add the account middleware:
    "allauth.account.middleware.AccountMiddleware",
]


AUTHENTICATION_BACKENDS = [
    
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
    
]


ROOT_URLCONF = 'e_shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],  # template directory that is has created in the project root
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors for shop's total cart item count
                'shop.context_processors.cart_items_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'e_shop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'  # Directory to collect static files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Directory to store uploaded media files


#allauth settings
SITE_ID = 2
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Session settings to maintain login state during payment
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'



# sslcommerz settings - for payment Getway
SSLCOMMERZ_STORE_ID = 'eshop689628c65c7b8'
SSLCOMMERZ_STORE_PASSWORD = 'eshop689628c65c7b8@ssl'

SSLCOMMERZ_PAYMENT_URL = 'https://sandbox.sslcommerz.com/gwprocess/v3/api.php'
SSLCOMMERZ_VALIDATION_URL = 'https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php'



# Email setup 
# Switched to SMTP backend for real email sending
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'riaz35-995@diu.edu.bd'
# Gmail App Password (16 characters without spaces)
EMAIL_HOST_PASSWORD = 'nxvfyfvlnemqnwfc'  
DEFAULT_FROM_EMAIL = 'E-Shop <riaz35-995@diu.edu.bd>'



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===================== ENHANCED ADMIN CONFIGURATION ===================== #

# Admin Interface Configuration
X_FRAME_OPTIONS = 'SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

# Admin Security Settings
ADMIN_ENABLED = True
ADMIN_URL = 'admin/'  # Change this in production for security

# Session Security
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF Security
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = True

# Admin Interface Theme Settings
ADMIN_INTERFACE = {
    'ENVIRONMENT': 'EcoCommerce Admin Dashboard',
    'ENVIRONMENT_COLOR': '#2e7d32',  # Green theme
    'ENVIRONMENT_CRITICAL': False,
    'RELATED_MODAL_ACTIVE': True,
    'RELATED_MODAL_BACKGROUND_OPACITY': 0.3,
    'RELATED_MODAL_CLOSE_BUTTON': True,
    'RECENT_ACTIONS_VISIBLE': True,
    'THEME': 'green-theme',
}

# Logging Configuration for Admin Activities
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'admin_activities.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.contrib.admin': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'shop.admin': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'ai_chatbot_agent': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# AI Chatbot Configuration
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'ecommerce-chatbot')

# Chatbot Settings
CHATBOT_CONFIG = {
    'MODEL_NAME': 'Qwen/Qwen2-7B-Instruct',
    'TEMPERATURE': 0.7,
    'MAX_TOKENS': 500,
    'TOP_P': 0.9,
    'REPETITION_PENALTY': 1.1,
    'VECTOR_DIMENSION': 384,
    'MAX_SEARCH_RESULTS': 5,
}



