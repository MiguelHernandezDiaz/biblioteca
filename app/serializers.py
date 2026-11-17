from rest_framework import serializers
from .models import Usuario, Libro, Prestamo


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'email', 'password', 'rol', 'activo', 'creado_en']
        extra_kwargs = {
            # La contraseña solo se acepta al crear/enviar, nunca se devuelve en respuestas GET
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        raw_password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(raw_password)
        usuario.save()
        return usuario


class LibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = [
            'id', 'titulo', 'autor', 'isbn',
            'copias_totales', 'copias_disponibles',
            'portada_url', 'activo', 'creado_en'
        ]

    def create(self, validated_data):
        # Si al registrar un libro no se indican copias disponibles,
        # por defecto todas las copias totales inician disponibles.
        if 'copias_disponibles' not in validated_data:
            validated_data['copias_disponibles'] = validated_data.get('copias_totales', 1)
        return super().create(validated_data)


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
