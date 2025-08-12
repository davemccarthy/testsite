from django.urls import re_path
from . import clients

websocket_urlpatterns = [
    re_path(r'ws/testsite/$', clients.AuthClient.as_asgi()),
]