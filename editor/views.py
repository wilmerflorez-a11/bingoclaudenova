from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib import messages


# =============
# REGISTRO
# =============
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Iniciar sesión automáticamente después del registro
                login(request, user)
                messages.success(request, f'¡Cuenta creada exitosamente para {user.username}!')
                # Redirigir a la sala de espera (ajusta el nombre de la URL según tu proyecto)
                return redirect('sala_espera')  # O 'dashboard', 'lobby', etc.
            except Exception as e:
                # Capturar cualquier error de integridad
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
                return render(request, 'editor/registro.html', {'form': form})
        else:
            # Si el formulario no es válido, mostrar errores
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserCreationForm()
    
    return render(request, 'editor/registro.html', {'form': form})


# ALTERNATIVA: Si usas un formulario personalizado
from django.contrib.auth.models import User

def registro_custom(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email', '')
        
        # Validaciones
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'editor/registro.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return render(request, 'editor/registro.html')
        
        try:
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            # Iniciar sesión
            login(request, user)
            messages.success(request, f'¡Bienvenido {username}!')
            return redirect('sala_espera')  # Ajusta según tu URL
        except Exception as e:
            messages.error(request, f'Error al crear cuenta: {str(e)}')
            return render(request, 'editor/registro.html')
    
    return render(request, 'editor/registro.html')


# =============
# LOGIN
# =============
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('sala_espera')
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
    ahora = timezone.localtime()

    # HORA PROGRAMADA DEL JUEGO (CAMBIA AQUÍ)
    hora_juego = ahora.replace(hour=9, minute=0, second=0, microsecond=0)

    if ahora > hora_juego:
        hora_juego += timezone.timedelta(days=1)

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
        "jugadores": jugadores
    })
