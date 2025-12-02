import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime

# NOTA: Esto solo funciona con un solo worker (Azure Student Plan)
# Si se escala horizontalmente, se necesita Redis.
usuarios_conectados = set()

class SalaConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.sala = "principal"
        self.username = self.scope["user"].username

        if not self.username:
            self.username = "Invitado"

        # Añadir usuario al set global
        usuarios_conectados.add(self.username)

        await self.channel_layer.group_add(
            self.sala,
            self.channel_name
        )

        await self.accept()
        await self.actualizar_todos()

    async def disconnect(self, close_code):
        # Eliminar usuario del set global
        if self.username in usuarios_conectados:
            usuarios_conectados.discard(self.username)

        await self.channel_layer.group_discard(
            self.sala,
            self.channel_name
        )

        await self.actualizar_todos()

    async def receive(self, text_data):
        data = json.loads(text_data)
        tipo = data.get('type')
        
        if tipo == 'chat_message':
            await self.channel_layer.group_send(
                self.sala,
                {
                    'type': 'chat_message',
                    'user': self.username,
                    'message': data.get('message')
                }
            )
        elif tipo == 'bingo_claim':
            # Validate the bingo claim
            from .models import Partida, Carton
            from .services import GameEngineService
            from django.contrib.auth.models import User
            
            user = await self.get_user()
            if not user:
                return
                
            # Get user's card and game state
            partida = await self.get_active_partida()
            if not partida:
                return
                
            carton = await self.get_user_carton(user, partida)
            if not carton:
                return
            
            # Validate
            engine = GameEngineService()
            balotas = partida.get_balotas()
            matriz = carton.get_matriz()
            
            is_winner = engine.validate_bingo(matriz, balotas)
            
            if is_winner:
                # Mark as winner
                partida.ganador = user
                partida.estado = 'FINISHED'
                await self.save_partida(partida)
                
                # Announce winner to all
                await self.channel_layer.group_send(
                    self.sala,
                    {
                        'type': 'game_over',
                        'winner': self.username
                    }
                )
            else:
                # False alarm
                await self.channel_layer.group_send(
                    self.sala,
                    {
                        'type': 'chat_message',
                        'user': 'SISTEMA',
                        'message': f'❌ {self.username} cantó BINGO pero no tiene un patrón ganador.'
                    }
                )

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

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user': event['user'],
            'message': event['message']
        }))
        
    async def new_ball(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_ball',
            'number': event['number']
        }))
        
    async def game_over(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'winner': event['winner']
        }))
    
    # Helper methods for async database access
    @database_sync_to_async
    def get_user(self):
        from django.contrib.auth.models import User
        try:
            return User.objects.get(username=self.username)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_active_partida(self):
        from .models import Partida, Sala
        sala = Sala.objects.first()
        if not sala:
            return None
        return Partida.objects.filter(sala=sala, estado__in=['WAITING', 'PLAYING']).last()
    
    @database_sync_to_async
    def get_user_carton(self, user, partida):
        from .models import Carton
        try:
            return Carton.objects.get(usuario=user, partida=partida)
        except Carton.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_partida(self, partida):
        partida.save()
