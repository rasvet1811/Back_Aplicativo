from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import (
    Rol, User, Empleado, Caso, Alerta, Documento, Carpeta,
    Seguimiento, Reporte, TokenVerification
)
import os


class RolSerializer(serializers.ModelSerializer):
    """Serializer para roles"""
    id = serializers.SerializerMethodField()
    
    class Meta:
        model = Rol
        fields = ['id', 'tipo']
        read_only_fields = ['id']
    
    def get_id(self, obj):
        return obj.id_rol


class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuarios"""
    password = serializers.CharField(write_only=True, required=False)
    rol_tipo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'nombre', 'rol', 'rol_tipo', 
            'correo', 'estado', 'password',
            'ciudad', 'puesto', 'experiencia', 'fecha_ingreso', 
            'area', 'division'
        ]
        read_only_fields = ['id']
    
    def get_rol_tipo(self, obj):
        return obj.rol.tipo if obj.rol else None
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer público para usuarios (sin información sensible)"""
    rol_tipo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'nombre', 'rol', 'rol_tipo', 'correo', 'estado',
            'ciudad', 'puesto', 'experiencia', 'fecha_ingreso', 'area', 'division'
        ]
    
    def get_rol_tipo(self, obj):
        return obj.rol.tipo if obj.rol else None


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            if not user.is_active or not user.estado:
                raise serializers.ValidationError('Usuario inactivo')
            data['user'] = user
        else:
            raise serializers.ValidationError('Debe proporcionar username y password')
        
        return data


class EmpleadoSerializer(serializers.ModelSerializer):
    """Serializer para empleados"""
    id = serializers.SerializerMethodField()
    foto_url = serializers.SerializerMethodField()
    total_casos = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Empleado
        fields = [
            'id', 'nombre', 'apellido', 'nombre_completo', 'cargo', 
            'division', 'area', 'supervisor', 'fecha_nacimiento', 
            'fecha_ingreso', 'correo', 'telefono', 'estado', 'foto', 
            'foto_url', 'total_casos', 'ciudad', 'numero_documento', 
            'tipo_documento'
        ]
        read_only_fields = ['id']
    
    def get_id(self, obj):
        return obj.id_empleado
    
    def get_foto_url(self, obj):
        if obj.foto:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None
    
    def get_total_casos(self, obj):
        return obj.casos.count()
    
    def get_nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"


class CasoSerializer(serializers.ModelSerializer):
    """Serializer para casos"""
    id = serializers.SerializerMethodField()
    empleado_nombre = serializers.SerializerMethodField()
    responsable_nombre = serializers.SerializerMethodField()
    total_documentos = serializers.SerializerMethodField()
    total_alertas = serializers.SerializerMethodField()
    total_seguimientos = serializers.SerializerMethodField()
    
    class Meta:
        model = Caso
        fields = [
            'id', 'empleado', 'empleado_nombre', 'tipo_fuero', 
            'diagnostico', 'fecha_inicio', 'estado', 'responsable', 
            'responsable_nombre', 'fecha_cierre', 'observaciones',
            'total_documentos', 'total_alertas', 'total_seguimientos'
        ]
        read_only_fields = ['id', 'fecha_inicio']
    
    def get_id(self, obj):
        return obj.id_caso
    
    def get_empleado_nombre(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"
    
    def get_responsable_nombre(self, obj):
        return obj.responsable.nombre if obj.responsable else None
    
    def get_total_documentos(self, obj):
        return obj.documentos.count()
    
    def get_total_alertas(self, obj):
        return obj.alertas.count()
    
    def get_total_seguimientos(self, obj):
        return obj.seguimientos.count()
    
    def validate_empleado(self, value):
        """Validar que el empleado existe y está activo"""
        if not value:
            raise serializers.ValidationError("El empleado es requerido")
        if hasattr(value, 'estado') and value.estado != 'Activo':
            raise serializers.ValidationError("El empleado debe estar activo")
        return value
    
    def validate_estado(self, value):
        """Validar que el estado sea uno de los valores permitidos"""
        estados_permitidos = ['pendiente', 'abierto', 'cerrado']
        if value and value.lower() not in estados_permitidos:
            raise serializers.ValidationError(
                f"El estado debe ser uno de: {', '.join(estados_permitidos)}"
            )
        return value.lower() if value else value
    
    def create(self, validated_data):
        """Crear un caso"""
        # Asegurar que el estado tenga el valor por defecto si no se proporciona
        if 'estado' not in validated_data:
            validated_data['estado'] = 'abierto'
        # Normalizar el estado a minúsculas
        if 'estado' in validated_data and validated_data['estado']:
            validated_data['estado'] = validated_data['estado'].lower()
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Si se cambia el estado a cerrado, actualizar fecha_cierre
        if 'estado' in validated_data:
            estado = validated_data['estado'].lower() if validated_data['estado'] else validated_data['estado']
            validated_data['estado'] = estado
            if estado == 'cerrado' and not instance.fecha_cierre:
                from django.utils import timezone
                validated_data['fecha_cierre'] = timezone.now().date()
        return super().update(instance, validated_data)


class AlertaSerializer(serializers.ModelSerializer):
    """Serializer para alertas"""
    id = serializers.SerializerMethodField()
    caso_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Alerta
        fields = [
            'id', 'caso', 'caso_info', 'titulo', 'tipo', 
            'fecha_generada', 'fecha_envio', 'fecha_vencimiento',
            'estado', 'descripcion'
        ]
        read_only_fields = ['id', 'fecha_generada']
    
    def get_id(self, obj):
        return obj.id_alerta
    
    def get_caso_info(self, obj):
        return f"Caso #{obj.caso.id_caso} - {obj.caso.empleado}"
    
    def validate_estado(self, value):
        """Validar que el estado sea uno de los valores permitidos"""
        estados_permitidos = ['pendiente', 'enviada', 'vencida']
        if value and value.lower() not in estados_permitidos:
            raise serializers.ValidationError(
                f"El estado debe ser uno de: {', '.join(estados_permitidos)}"
            )
        return value.lower() if value else value
    
    def create(self, validated_data):
        """Crear una alerta"""
        # Asegurar que el estado tenga el valor por defecto si no se proporciona
        if 'estado' not in validated_data or not validated_data.get('estado'):
            validated_data['estado'] = 'pendiente'
        # Normalizar el estado a minúsculas
        if 'estado' in validated_data and validated_data['estado']:
            validated_data['estado'] = validated_data['estado'].lower()
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar una alerta"""
        # Normalizar el estado a minúsculas si se proporciona
        if 'estado' in validated_data and validated_data['estado']:
            validated_data['estado'] = validated_data['estado'].lower()
        return super().update(instance, validated_data)


class CarpetaSerializer(serializers.ModelSerializer):
    """Serializer para carpetas"""
    id = serializers.SerializerMethodField()
    empleado_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Carpeta
        fields = ['id', 'empleado', 'empleado_nombre', 'nombre', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion', 'empleado_nombre']
    
    def get_id(self, obj):
        return obj.id_carpeta
    
    def get_empleado_nombre(self, obj):
        """Retorna el nombre completo del empleado (nombre + apellido)"""
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"
    
    def validate_empleado(self, value):
        """Validar que el empleado existe"""
        if not value:
            raise serializers.ValidationError("El empleado es requerido")
        return value
    
    def validate_nombre(self, value):
        """Validar que el nombre no esté vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre de la carpeta no puede estar vacío")
        return value.strip()


class DocumentoSerializer(serializers.ModelSerializer):
    """Serializer para documentos"""
    id = serializers.SerializerMethodField()
    archivo_url = serializers.SerializerMethodField()
    archivo_nombre = serializers.SerializerMethodField()
    caso_info = serializers.SerializerMethodField()
    usuario_creador_nombre = serializers.SerializerMethodField()
    caso = serializers.PrimaryKeyRelatedField(queryset=Caso.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Documento
        fields = [
            'id', 'caso', 'caso_info', 'nombre', 'tipo', 
            'fecha_carga', 'fecha_modificacion', 'usuario_creador',
            'usuario_creador_nombre', 'descripcion', 'ruta', 
            'archivo_url', 'archivo_nombre', 'extension', 'empleado', 'carpeta'
        ]
        read_only_fields = ['id', 'fecha_carga', 'fecha_modificacion', 'extension']
    
    def get_id(self, obj):
        return obj.id_documento
    
    def get_archivo_url(self, obj):
        if obj.ruta:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.ruta.url)
            return obj.ruta.url
        return None
    
    def get_archivo_nombre(self, obj):
        if obj.ruta:
            return os.path.basename(obj.ruta.name)
        return None
    
    def get_caso_info(self, obj):
        if obj.caso:
            return f"Caso #{obj.caso.id_caso} - {obj.caso.empleado}"
        return None
    
    def get_usuario_creador_nombre(self, obj):
        return obj.usuario_creador.nombre if obj.usuario_creador else None


class SeguimientoSerializer(serializers.ModelSerializer):
    """Serializer para seguimientos"""
    id = serializers.SerializerMethodField()
    caso_info = serializers.SerializerMethodField()
    usuario_responsable_nombre = serializers.SerializerMethodField()
    reportes_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Seguimiento
        fields = [
            'id', 'caso', 'caso_info', 'fecha', 'usuario_responsable',
            'usuario_responsable_nombre', 'accion_realizada', 
            'observaciones', 'reportes', 'reportes_info'
        ]
        read_only_fields = ['id', 'fecha']
    
    def get_id(self, obj):
        return obj.id_seguimiento
    
    def get_caso_info(self, obj):
        return f"Caso #{obj.caso.id_caso} - {obj.caso.empleado}"
    
    def get_usuario_responsable_nombre(self, obj):
        return obj.usuario_responsable.nombre if obj.usuario_responsable else None
    
    def get_reportes_info(self, obj):
        return [{'id': r.id_reporte, 'nombre': r.nombre, 'codigo': r.codigo} for r in obj.reportes.all()]


class ReporteSerializer(serializers.ModelSerializer):
    """Serializer para reportes"""
    id = serializers.SerializerMethodField()
    total_seguimientos = serializers.SerializerMethodField()
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'formato', 
            'estado', 'total_seguimientos'
        ]
        read_only_fields = ['id']
    
    def get_id(self, obj):
        return obj.id_reporte
    
    def get_total_seguimientos(self, obj):
        return obj.seguimientos.count()


class CambioRolSerializer(serializers.Serializer):
    """Serializer para cambio de rol con verificación"""
    user_id = serializers.IntegerField()
    nuevo_rol_id = serializers.IntegerField()
    token_verificacion = serializers.CharField(write_only=True)


class TokenVerificationSerializer(serializers.ModelSerializer):
    """Serializer para tokens de verificación"""
    class Meta:
        model = TokenVerification
        fields = ['id', 'operacion', 'fecha_creacion', 'fecha_expiracion', 'usado']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_expiracion', 'usado']
