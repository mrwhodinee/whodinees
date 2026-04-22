from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from store import views as store_views
from .webhook_handler import unified_stripe_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    # Unified webhook endpoint (handles both store and portrait payments)
    path("api/stripe/webhook/", unified_stripe_webhook, name="unified-stripe-webhook"),
    path("api/", include("store.urls")),
    path("api/", include("portraits.urls")),
    # SPA catch-all. Keep last; admin and api are matched first.
    re_path(r"^(?!static/|media/|api/|admin/).*$", store_views.spa_index, name="spa"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
