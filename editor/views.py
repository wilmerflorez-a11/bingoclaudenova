
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError

# =============
# REGISTRO
# =============
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.username}!')
                return redirect('sala_espera')
            except IntegrityError:
                messages.error(request, 'Este nombre de usuario ya existe.')
            except Exception as e:
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()
    
    # IMPORTANTE: Cambia el nombre del template si es diferente
    return render(request, 'editor/register.html', {'form': form})


# =============
# LOGIN
# =============
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('sala_espera')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'editor/login.html', {'form': form})


# =============
# SALA DE ESPERA
# =============
@login_required
def sala_espera(request):
    return render(request, 'editor/sala_espera.html', {
        'username': request.user.username
    })


# =============
# ESTADO DEL JUEGO
# =============
@login_required
def estado_juego(request):
    from .services import StaticGameScheduleService
    
    ahora = timezone.localtime()
    
    # Use the service to get the game time (OCP)
    # In the future, we can inject a DatabaseGameScheduleService here
    schedule_service = StaticGameScheduleService()
    hora_juego, sala_nombre = schedule_service.get_next_game_time(ahora)

    # SESIONES ACTIVAS
    sesiones = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = []

    for s in sesiones:
        data = s.get_decoded()
        uid = data.get('_auth_user_id')
        if uid:
            user_ids.append(uid)

    jugadores = list(User.objects.filter(id__in=user_ids).values_list("username", flat=True))

    return JsonResponse({
        "hora_servidor": ahora.strftime("%H:%M:%S"),
        "hora_juego": hora_juego.strftime("%H:%M:%S"),
        "faltan": int((hora_juego - ahora).total_seconds()),
        "jugadores": jugadores,
        "sala_nombre": sala_nombre
    })

@login_required
def juego(request):
    from .models import Partida, Carton, Sala
    from .services import BingoCardService
    import json
    
    # Get or create active game
    # For MVP, we assume one active game in the main room
    sala = Sala.objects.first() # Assuming at least one room exists
    if not sala:
        # Create default room if none
        sala = Sala.objects.create(nombre="Sala Principal", hora_inicio="09:00")
        
    partida = Partida.objects.filter(sala=sala, estado__in=['WAITING', 'PLAYING']).last()
    
    if not partida:
        partida = Partida.objects.create(sala=sala, estado='WAITING')
        
    # Get or create user's card for this game
    carton = Carton.objects.filter(partida=partida, usuario=request.user).first()
    
    if not carton:
        card_service = BingoCardService()
        matriz = card_service.generate_card()
        carton = Carton.objects.create(
            partida=partida,
            usuario=request.user,
            matriz=json.dumps(matriz) # Store as JSON string
        )
        
    return render(request, 'editor/juego.html', {
        'partida_id': partida.id,
        'carton_matriz': carton.matriz # Already JSON string
    })

@login_required
def admin_panel(request):
    from .models import Partida, Sala
    
    # Only allow staff/admin
    if not request.user.is_staff:
        return redirect('juego')
        
    sala = Sala.objects.first()
    if not sala:
        sala = Sala.objects.create(nombre="Sala Principal", hora_inicio="09:00")
        
    partida = Partida.objects.filter(sala=sala, estado__in=['WAITING', 'PLAYING']).last()
    
    if not partida:
        partida = Partida.objects.create(sala=sala, estado='WAITING')
        
    return render(request, 'editor/admin_panel.html', {
        'partida_id': partida.id
    })

@login_required
def sortear_balota(request):
    from .models import Partida
    from .services import GameEngineService
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    import json
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    data = json.loads(request.body)
    partida_id = data.get('partida_id')
    
    partida = Partida.objects.get(id=partida_id)
    drawn = partida.get_balotas()
    
    engine = GameEngineService()
    new_ball = engine.draw_ball(drawn)
    
    if new_ball == -1:
        return JsonResponse({'error': 'Todas las balotas han sido sorteadas'})
        
    drawn.append(new_ball)
    partida.set_balotas(drawn)
    partida.estado = 'PLAYING'
    partida.save()
    
    # Send to all connected clients via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'principal',
        {
            'type': 'new_ball',
            'number': new_ball
        }
    )
    
    return JsonResponse({'number': new_ball})

@csrf_exempt
@login_required
def reiniciar_juego(request):
    from .models import Partida, Sala
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    import json
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    # Get the latest active game
    partida = Partida.objects.filter(estado__in=['WAITING', 'PLAYING', 'FINISHED']).last()
    
    if not partida:
        return JsonResponse({'error': 'No hay partida activa'}, status=404)
    
    # Reset the game
    partida.balotas_sorteadas = "[]"  # Empty JSON array, not empty string
    partida.ganador = None
    partida.estado = 'WAITING'
    partida.save()
    
    # Broadcast reset event to all connected players
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "principal",  # Must match the group name in consumers.py
        {
            "type": "game_reset",
        }
    )
    
    return JsonResponse({'success': True})

def _get_proxima_hora_juego(ahora):
    # This function definition was incomplete and syntactically incorrect in the provided snippet.
    # It seems it was intended to be a helper function, but its body was missing or malformed.
    # For now, I'm providing a placeholder. Please complete its implementation.
    return ahora # Placeholder, replace with actual logic