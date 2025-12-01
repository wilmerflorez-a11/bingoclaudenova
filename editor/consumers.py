import json
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime

usuarios_conectados = set()

class SalaConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.sala = "principal"
        self.username = self.scope["user"].username

        if self.username == "AnonymousUser":
            self.username = "Invitado"

        usuarios_conectados.add(self.username)

        await self.channel_layer.group_add(
            self.sala,
            self.channel_name
        )

        await self.accept()

        await self.actualizar_todos()

    async def disconnect(self, close_code):

        usuarios_conectados.discard(self.username)

        await self.channel_layer.group_discard(
            self.sala,
            self.channel_name
        )

        await self.actualizar_todos()

    async def actualizar_todos(self):
        hora_servidor = datetime.now().strftime("%H:%M:%S")

        await self.channel_layer.group_send(
            self.sala,
            {
                "type": "broadcast",
                "usuarios": list(usuarios_conectados),
                "hora": hora_servidor
            }
        )

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event))
