from django.urls import path
from . import views

urlpatterns = [
    # Interfaz web HTML
    path('', views.index_view, name='index'),

    # Autenticación
    path('api/auth/login/', views.login_view, name='login'),
    path('api/auth/logout/', views.logout_view, name='logout'),
    path('api/auth/me/', views.me_view, name='me'),

    # Recursos del sistema
    path('api/usuarios/', views.usuarios_view, name='usuarios'),
    path('api/libros/', views.libros_view, name='libros'),
    path('api/prestamos/', views.prestamos_view, name='prestamos'),
    path('api/prestamos/<int:pk>/devolver/', views.devolver_prestamo_view, name='devolver_prestamo'),

    # Inspector de BD PostgreSQL (solo admin)
    path('api/sistema/tablas/', views.inspector_tablas_view, name='inspector_tablas'),
]
