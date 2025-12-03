from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import your custom 404 view
from main import views as main_views  # adjust 'main' if your app is named differently

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('candidates/', include('main.urls')),
    path('accounts/', include('allauth.urls')),
]

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 404 handler
handler404 = main_views.custom_404
