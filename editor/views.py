from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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