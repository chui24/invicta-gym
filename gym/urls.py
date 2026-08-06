from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/validar_semaforo/', views.validar_acceso_semaforo, name='validar_semaforo'),
    path('api/validar_rostro/', views.validar_rostro, name='validar_rostro'),
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('cliente/crear/', views.cliente_crear, name='cliente_crear'),
    path('cliente/renovar/<int:cliente_id>/', views.renovar_suscripcion, name='cliente_renovar'),
    path('cliente/editar/<int:pk>/', views.cliente_editar, name='cliente_editar'),
    path('cliente/eliminar/<int:pk>/', views.cliente_eliminar, name='cliente_eliminar'),
    path('asistencias/', views.asistencia_list, name='asistencia_list'),
]
