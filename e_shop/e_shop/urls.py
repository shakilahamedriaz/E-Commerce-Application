from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from shop.admin import admin_site  # Import custom admin site


urlpatterns = [
    path('admin/', admin_site.urls),  # Use custom admin site
    path('accounts/', include('allauth.urls')),  # Add allauth URLs
    path('', include('shop.urls')),
]



urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)