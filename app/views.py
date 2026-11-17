from datetime import timedelta
from django.shortcuts import render
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Usuario, Libro, Prestamo
from .serializers import UsuarioSerializer, LibroSerializer, PrestamoSerializer


def _usuario_actual(request):
    """Obtiene el usuario autenticado desde la sesión de Django."""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    return Usuario.objects.filter(id=usuario_id, activo=True).first()


# 1. Vista raíz: entrega el frontend HTML directamente
def index_view(request):
    return render(request, 'app/index.html')


# 2. Autenticación (Login, Sesión actual y Logout)
@api_view(['POST'])
def login_view(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response(
            {'ok': False, 'error': 'Debes ingresar correo y contraseña.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuario = Usuario.objects.filter(email=email, activo=True).first()
    if not usuario or not usuario.verificar_password(password):
        return Response(
            {'ok': False, 'error': 'Correo o contraseña incorrectos.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Guardamos el ID en la sesión del servidor (cookie segura HttpOnly)
    request.session['usuario_id'] = usuario.id
    return Response({'ok': True, 'user': UsuarioSerializer(usuario).data})


@api_view(['POST'])
def logout_view(request):
    request.session.flush()
    return Response({'ok': True})


@api_view(['GET'])
def me_view(request):
    usuario = _usuario_actual(request)
    if not usuario:
        return Response({'authenticated': False}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'authenticated': True, 'user': UsuarioSerializer(usuario).data})


# 3. Gestión de Usuarios (Solo Administrador)
@api_view(['GET', 'POST'])
def usuarios_view(request):
    actual = _usuario_actual(request)
    if not actual or actual.rol != 'admin':
        return Response({'error': 'Acceso exclusivo para administradores.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        usuarios = Usuario.objects.all().order_by('id')
        return Response(UsuarioSerializer(usuarios, many=True).data)

    data = request.data.copy()
    data['email'] = data.get('email', '').strip().lower()
    serializer = UsuarioSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 4. Catálogo y Registro de Libros
@api_view(['GET', 'POST'])
def libros_view(request):
    actual = _usuario_actual(request)
    if not actual:
        return Response({'error': 'Debes iniciar sesión.'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        # Por defecto solo devolvemos libros con al menos 1 copia disponible
        incluir_todos = request.query_params.get('todos') == '1' and actual.rol == 'admin'
        qs = Libro.objects.filter(activo=True)
        if not incluir_todos:
            qs = qs.filter(copias_disponibles__gt=0)
        return Response(LibroSerializer(qs.order_by('id'), many=True).data)

    if actual.rol != 'admin':
        return Response({'error': 'Solo los administradores pueden agregar libros.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = LibroSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 5. Préstamos con Transacción Atómica (Evita condiciones de carrera)
@api_view(['GET', 'POST'])
def prestamos_view(request):
    actual = _usuario_actual(request)
    if not actual:
        return Response({'error': 'Debes iniciar sesión.'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        qs = Prestamo.objects.select_related('libro', 'usuario').filter(estado='activo')
        if actual.rol != 'admin':
            qs = qs.filter(usuario=actual)
        return Response(PrestamoSerializer(qs.order_by('-fecha_prestamo'), many=True).data)

    libro_id = request.data.get('libro_id')
    dias = int(request.data.get('dias', 7))
    usuario_destino_id = request.data.get('usuario_id') if actual.rol == 'admin' else actual.id
    if not usuario_destino_id:
        usuario_destino_id = actual.id

    try:
        with transaction.atomic():
            # Bloqueo de fila en PostgreSQL hasta terminar la transacción
            libro = Libro.objects.select_for_update().get(id=libro_id, activo=True)
            if libro.copias_disponibles <= 0:
                return Response(
                    {'error': 'No quedan copias disponibles de este libro.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            usuario_destino = Usuario.objects.get(id=usuario_destino_id, activo=True)

            libro.copias_disponibles -= 1
            libro.save()

            prestamo = Prestamo.objects.create(
                libro=libro,
                usuario=usuario_destino,
                fecha_limite=timezone.now() + timedelta(days=max(1, min(dias, 90))),
                estado='activo'
            )
            return Response(PrestamoSerializer(prestamo).data, status=status.HTTP_201_CREATED)

    except Libro.DoesNotExist:
        return Response({'error': 'Libro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


# 6. Devolución de Libro
@api_view(['POST'])
def devolver_prestamo_view(request, pk):
    actual = _usuario_actual(request)
    if not actual:
        return Response({'error': 'Debes iniciar sesión.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        with transaction.atomic():
            prestamo = Prestamo.objects.select_for_update().get(id=pk, estado='activo')
            if actual.rol != 'admin' and prestamo.usuario_id != actual.id:
                return Response({'error': 'No autorizado para devolver este préstamo.'}, status=status.HTTP_403_FORBIDDEN)

            prestamo.estado = 'devuelto'
            prestamo.fecha_devolucion = timezone.now()
            prestamo.save()

            libro = Libro.objects.select_for_update().get(id=prestamo.libro_id)
            libro.copias_disponibles = min(libro.copias_totales, libro.copias_disponibles + 1)
            libro.save()

            return Response({'ok': True, 'mensaje': 'Libro devuelto correctamente.'})
    except Prestamo.DoesNotExist:
        return Response({'error': 'Préstamo activo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


# 7. Inspector de PostgreSQL (Exclusivo para Administradores)
@api_view(['GET'])
def inspector_tablas_view(request):
    actual = _usuario_actual(request)
    if not actual or actual.rol != 'admin':
        return Response({'error': 'Acceso exclusivo para administradores.'}, status=status.HTTP_403_FORBIDDEN)

    usuarios = list(Usuario.objects.order_by('id').values('id', 'nombre', 'email', 'rol', 'activo'))
    libros = list(Libro.objects.order_by('id').values('id', 'titulo', 'autor', 'isbn', 'copias_totales', 'copias_disponibles', 'activo'))
    prestamos = list(Prestamo.objects.order_by('id').values('id', 'libro_id', 'usuario_id', 'fecha_prestamo', 'fecha_limite', 'fecha_devolucion', 'estado'))

    return Response({
        'tablas': {
            'usuarios': {'total': len(usuarios), 'filas': usuarios},
            'libros': {'total': len(libros), 'filas': libros},
            'prestamos': {'total': len(prestamos), 'filas': prestamos},
        }
    })
