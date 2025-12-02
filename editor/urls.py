from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='home'),

    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('register/', views.registro, name='registro_ingles'),
    path('login/', views.login_view, name='login'),

    # Sala de espera
    path('sala-espera/', views.sala_espera, name='sala_espera'),
    path("estado-juego/", views.estado_juego, name="estado_juego"),
    path("juego/", views.juego, name="juego"),
    
    # Panel de control
    path("panel/", views.admin_panel, name="admin_panel"),
    path("panel/sortear-balota/", views.sortear_balota, name="sortear_balota"),
    path("panel/reiniciar-juego/", views.reiniciar_juego, name="reiniciar_juego"),
]

# ✅ SOLO EN DESARROLLO
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
