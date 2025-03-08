# ResQNetServer/routing.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import core.routing  # Replace "your_app" with your actual app's name

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ResQNetServer.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        core.routing.websocket_urlpatterns  # Ensure this exists in your app's routing.py
    ),
})
