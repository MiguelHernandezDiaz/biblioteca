import re
from rest_framework import serializers
from .models import Usuario, Libro, Prestamo


def _normalizar_isbn(isbn):
    return re.sub(r'[^0-9Xx]', '', str(isbn or '')).upper()


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'email', 'password', 'rol', 'activo', 'creado_en']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        raw_password = validated_data.pop('password', None)
        if not raw_password:
            raise serializers.ValidationError({'password': 'La contraseña es obligatoria.'})
        usuario = Usuario(**validated_data)
        usuario.set_password(raw_password)
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        raw_password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if raw_password and raw_password.strip():
            instance.set_password(raw_password)
        instance.save()
        return instance


class LibroSerializer(serializers.ModelSerializer):
    portada_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Libro
        fields = [
            'id', 'titulo', 'autor', 'isbn',
            'copias_totales', 'copias_disponibles',
            'portada_url', 'activo', 'creado_en'
        ]

    def validate_isbn(self, value):
        limpio = _normalizar_isbn(value)
        if not limpio:
            raise serializers.ValidationError('El ISBN no puede estar vacío.')
        return limpio

    def create(self, validated_data):
        if 'copias_disponibles' not in validated_data:
            validated_data['copias_disponibles'] = validated_data.get('copias_totales', 1)
        if not validated_data.get('portada_url'):
            validated_data['portada_url'] = f"https://covers.openlibrary.org/b/isbn/{validated_data['isbn']}-L.jpg"
        return super().create(validated_data)

    def update(self, instance, validated_data):
        isbn_nuevo = validated_data.get('isbn', instance.isbn)
        if 'portada_url' in validated_data and not validated_data['portada_url']:
            validated_data['portada_url'] = f"https://covers.openlibrary.org/b/isbn/{isbn_nuevo}-L.jpg"
        elif 'isbn' in validated_data and not validated_data.get('portada_url') and (
            not instance.portada_url or 'covers.openlibrary.org' in instance.portada_url
        ):
            validated_data['portada_url'] = f"https://covers.openlibrary.org/b/isbn/{isbn_nuevo}-L.jpg"

        libro = super().update(instance, validated_data)
        if libro.copias_disponibles > libro.copias_totales:
            libro.copias_disponibles = libro.copias_totales
            libro.save(update_fields=['copias_disponibles'])
        return libro


class PrestamoSerializer(serializers.ModelSerializer):
    libro_titulo = serializers.ReadOnlyField(source='libro.titulo')
    usuario_nombre = serializers.ReadOnlyField(source='usuario.nombre')

    class Meta:
        model = Prestamo
        fields = [
            'id', 'libro', 'libro_titulo',
            'usuario', 'usuario_nombre',
            'fecha_prestamo', 'fecha_limite', 'fecha_devolucion', 'estado'
        ]
