from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
    path('refund/', views.refund_policy, name='refund'),
]
