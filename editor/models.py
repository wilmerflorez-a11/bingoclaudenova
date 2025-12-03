from django.db import models
from django.contrib.auth.models import User
import json

class Sala(models.Model):
    nombre = models.CharField(max_length=100)
    hora_inicio = models.TimeField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Partida(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='partidas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[
        ('WAITING', 'Esperando'),
        ('PLAYING', 'Jugando'),
        ('FINISHED', 'Finalizado')
    ], default='WAITING')
    balotas_sorteadas = models.TextField(default="[]") # JSON list of integers
    ganador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidas_ganadas')

    def set_balotas(self, lista):
        self.balotas_sorteadas = json.dumps(lista)

    def get_balotas(self):
        if not self.balotas_sorteadas or self.balotas_sorteadas.strip() == "":
            return []
        try:
            return json.loads(self.balotas_sorteadas)
        except (json.JSONDecodeError, ValueError):
            return []

    def __str__(self):
        return f"Partida {self.id} - {self.estado}"

class Carton(models.Model):
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='cartones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cartones')
    matriz = models.TextField() # JSON 5x5 matrix
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def set_matriz(self, matriz):
        self.matriz = json.dumps(matriz)

    def get_matriz(self):
        return json.loads(self.matriz)

    def __str__(self):
        return f"Cartón {self.id} - {self.usuario.username}"
