from django.urls import re_path
from .consumers import AdminConsumer, ProgressConsumer, CityConsumer, VolunteerRequestConsumer, PhoneConsumer

websocket_urlpatterns = [
    re_path(r'ws/admin/$', AdminConsumer.as_asgi()),
    re_path(r'ws/progress/$', ProgressConsumer.as_asgi()),
    re_path(r'ws/city_updates/$', CityConsumer.as_asgi()), 
    re_path(r'ws/volunteer_requests/(?P<admin_id>\d+)/$', VolunteerRequestConsumer.as_asgi()),
    re_path(r'ws/phone_updates/(?P<phone_number>[\d\+]+)/$', PhoneConsumer.as_asgi()),
]

