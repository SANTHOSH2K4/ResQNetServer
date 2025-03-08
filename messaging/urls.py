from django.urls import path
from .views import add_message, test_server, receive_sms

urlpatterns = [
    path('add_message/', add_message, name='add_message'),
    path('api/sms/receive/', receive_sms, name='receive_sms'),
    path('', test_server, name='test_server'),
]
