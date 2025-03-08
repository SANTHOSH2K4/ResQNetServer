from django.urls import re_path
from messaging.consumers import MessageConsumer

websocket_urlpatterns = [
    re_path(r'^msg/ws/messages/$', MessageConsumer.as_asgi()),
]
