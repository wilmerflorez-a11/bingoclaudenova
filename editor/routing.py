from django.urls import path
from .consumers import SalaConsumer

websocket_urlpatterns = [
    path("ws/sala/", SalaConsumer.as_asgi()),
]
