from django.urls import re_path
from .consumers import AdminConsumer, ProgressConsumer

websocket_urlpatterns = [
    re_path(r'ws/admin/$', AdminConsumer.as_asgi()),
    re_path(r'ws/progress/$', ProgressConsumer.as_asgi()),
]
