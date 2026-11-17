from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):
    ROLES = (
        ('admin', 'Administrador'),
        ('lector', 'Lector'),
    )
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    rol = models.CharField(max_length=20, choices=ROLES, default='lector')
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios'

    def set_password(self, raw_password):
        # Encripta la contraseña con el algoritmo seguro PBKDF2 de Django
        self.password = make_password(raw_password)

    def verificar_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.nombre} ({self.rol})"


class Libro(models.Model):
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=200)
    isbn = models.CharField(max_length=30, unique=True)
    copias_totales = models.PositiveIntegerField(default=1)
    copias_disponibles = models.PositiveIntegerField(default=1)
    portada_url = models.URLField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'libros'

    def __str__(self):
        return self.titulo


class Prestamo(models.Model):
    ESTADOS = (
        ('activo', 'Activo'),
        ('devuelto', 'Devuelto'),
    )
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='prestamos')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='prestamos')
    fecha_prestamo = models.DateTimeField(default=timezone.now)
    fecha_limite = models.DateTimeField()
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')

    class Meta:
        db_table = 'prestamos'

    def __str__(self):
        return f"{self.libro.titulo} -> {self.usuario.nombre}"
