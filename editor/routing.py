from django.urls import path
from .consumers import SalaConsumer

websocket_urlpatterns = [
    path("ws/sala/", SalaConsumer.as_asgi()),
    path("ws/juego/", SalaConsumer.as_asgi()),  # Same consumer for game room
]
