from django.urls import path, include

urlpatterns = [
    # Todas las rutas desde la raíz '' se envían a app/urls.py
    path('', include('app.urls')),
]
