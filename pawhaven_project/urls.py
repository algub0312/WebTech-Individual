"""
URL configuration for pawhaven_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Override built-in login to use your custom template
    # (keep this BEFORE the generic auth include)
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='shelter/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),

    # Django auth (logout, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # App URLs
    path('', include('shelter.urls')),
]

# Serve media/static in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
