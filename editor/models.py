from django.db import models

class Sala(models.Model):
    nombre = models.CharField(max_length=100)
    hora_inicio = models.TimeField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
