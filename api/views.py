from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import ExpiringToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.db.models import Q
import secrets
import logging
from datetime import timedelta

# Configurar logger
logger = logging.getLogger(__name__)

from .models import (
    Rol, User, Empleado, Caso, Alerta, Documento, Carpeta,
    Seguimiento, Reporte, TokenVerification
)
from .serializers import (
    RolSerializer, UserSerializer, UserPublicSerializer, LoginSerializer,
    EmpleadoSerializer, CasoSerializer, AlertaSerializer, DocumentoSerializer,
    CarpetaSerializer, SeguimientoSerializer, ReporteSerializer, CambioRolSerializer, TokenVerificationSerializer
)


# ==================== PERMISOS PERSONALIZADOS ====================

class IsAdminOrTHA(BasePermission):
    """
    Permiso personalizado que permite el acceso solo a usuarios con rol
    'Administrador' o 'THA' (case-insensitive)
    """
    def has_permission(self, request, view):
        # Verificar que el usuario esté autenticado
        if not request.user or not request.user.is_authenticated:
            print(f"[IsAdminOrTHA] Usuario no autenticado: {request.user}")
            return False
        
        # IMPORTANTE: Recargar el usuario con el rol desde la BD para evitar problemas de cache
        try:
            # Usar select_related para cargar el rol en una sola consulta
            user = User.objects.select_related('rol').get(pk=request.user.pk)
            print(f"[IsAdminOrTHA] Usuario cargado: {user.username}, ID: {user.pk}")
        except User.DoesNotExist:
            print(f"[IsAdminOrTHA] Usuario no encontrado en BD: {request.user.pk}")
            return False
        except Exception as e:
            print(f"[IsAdminOrTHA] Error al cargar usuario: {e}")
            return False
        
        # Verificar que el usuario tenga un rol asignado
        if not user.rol:
            print(f"[IsAdminOrTHA] Usuario {user.username} sin rol asignado")
            return False
        
        # Verificar que el rol sea 'Administrador' o 'THA' (case-insensitive)
        rol_tipo = user.rol.tipo
        if not rol_tipo:
            print(f"[IsAdminOrTHA] Rol sin tipo para usuario {user.username}")
            return False
        
        # Convertir a minúsculas para comparación case-insensitive
        rol_tipo_lower = rol_tipo.lower()
        resultado = rol_tipo_lower in ['administrador', 'tha']
        
        print(f"[IsAdminOrTHA] Usuario: {user.username}, Rol tipo: '{rol_tipo}' -> '{rol_tipo_lower}', Permiso: {resultado}")
        
        return resultado


# ==================== FUNCIONES PÚBLICAS ====================

@api_view(['GET', 'POST'])
@permission_classes([])  # Público
def api_info(request):
    """Información general de la API"""
    return Response({
        'nombre': 'BackMaaji API',
        'version': '1.0.0',
        'descripcion': 'Sistema de Gestión de Documentos para Talento Humano',
        'endpoints': {
            'autenticacion': {
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'verificar_token': '/api/auth/verificar-token/',
                'renovar_token': '/api/auth/renovar-token/',
            },
            'recursos': {
                'usuarios': '/api/usuarios/',
                'empleados': '/api/empleados/',
                'casos': '/api/casos/',
                'documentos': '/api/documentos/',
                'carpetas': '/api/carpetas/',
                'alertas': '/api/alertas/',
                'seguimientos': '/api/seguimientos/',
                'reportes': '/api/reportes/',
            }
        }
    })


@api_view(['POST'])
@permission_classes([])  # Público
def login(request):
    """Iniciar sesión y obtener token"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Eliminar tokens expirados del usuario
        ExpiringToken.objects.filter(user=user).delete()
        
        # Crear nuevo token
        token, created = ExpiringToken.objects.get_or_create(user=user)
        
        # Serializar usuario (sin información sensible)
        user_serializer = UserPublicSerializer(user)
        
        return Response({
            'token': token.key,
            'user': user_serializer.data,
            'mensaje': 'Inicio de sesión exitoso'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Credenciales inválidas',
        'detalles': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Cerrar sesión y eliminar token"""
    try:
        token = ExpiringToken.objects.get(user=request.user)
        token.delete()
        return Response({
            'mensaje': 'Sesión cerrada exitosamente'
        }, status=status.HTTP_200_OK)
    except ExpiringToken.DoesNotExist:
        return Response({
            'mensaje': 'No hay sesión activa'
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([])  # Público
def verificar_token(request):
    """Verificar si un token es válido"""
    token_key = None
    
    # Obtener token del header o del body
    if request.method == 'GET':
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
    else:  # POST
        token_key = request.data.get('token') or request.headers.get('Authorization', '').replace('Token ', '')
    
    if not token_key:
        return Response({
            'valido': False,
            'mensaje': 'Token no proporcionado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = ExpiringToken.objects.get(key=token_key)
        
        if token.is_expired():
            token.delete()
            return Response({
                'valido': False,
                'mensaje': 'Token expirado'
            }, status=status.HTTP_200_OK)
        
        # Actualizar última actividad
        token.save()
        
        # Calcular tiempo restante
        minutos_expiracion = getattr(settings, 'TOKEN_EXPIRATION_MINUTES', 30)
        tiempo_inactivo = (timezone.now() - token.ultima_actividad).total_seconds()
        minutos_restantes = max(0, (minutos_expiracion * 60 - tiempo_inactivo) / 60)
        
        user_serializer = UserPublicSerializer(token.user)
        
        return Response({
            'valido': True,
            'user': user_serializer.data,
            'minutos_restantes': round(minutos_restantes, 2),
            'mensaje': 'Token válido'
        }, status=status.HTTP_200_OK)
        
    except ExpiringToken.DoesNotExist:
        return Response({
            'valido': False,
            'mensaje': 'Token inválido'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renovar_token(request):
    """Renovar el token actual"""
    try:
        token = ExpiringToken.objects.get(user=request.user)
        
        # Eliminar token actual
        token.delete()
        
        # Crear nuevo token
        new_token, created = ExpiringToken.objects.get_or_create(user=request.user)
        
        user_serializer = UserPublicSerializer(request.user)
        
        return Response({
            'token': new_token.key,
            'user': user_serializer.data,
            'mensaje': 'Token renovado exitosamente'
        }, status=status.HTTP_200_OK)
        
    except ExpiringToken.DoesNotExist:
        # Si no hay token, crear uno nuevo
        new_token, created = ExpiringToken.objects.get_or_create(user=request.user)
        user_serializer = UserPublicSerializer(request.user)
        
        return Response({
            'token': new_token.key,
            'user': user_serializer.data,
            'mensaje': 'Token creado exitosamente'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def solicitar_verificacion_rol(request):
    """Solicitar verificación de identidad para cambio de rol"""
    user_id = request.data.get('user_id')
    nuevo_rol_id = request.data.get('nuevo_rol_id')
    
    if not user_id or not nuevo_rol_id:
        return Response({
            'error': 'Se requiere user_id y nuevo_rol_id'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id)
        nuevo_rol = Rol.objects.get(id_rol=nuevo_rol_id)
    except (User.DoesNotExist, Rol.DoesNotExist):
        return Response({
            'error': 'Usuario o rol no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Generar token de verificación
    token_verificacion = secrets.token_urlsafe(32)
    fecha_expiracion = timezone.now() + timedelta(minutes=15)
    
    TokenVerification.objects.create(
        user=request.user,
        token=token_verificacion,
        operacion='cambio_rol',
        datos={
            'user_id': user_id,
            'nuevo_rol_id': nuevo_rol_id,
            'usuario_objetivo': user.username,
            'rol_objetivo': nuevo_rol.tipo
        },
        fecha_expiracion=fecha_expiracion
    )
    
    return Response({
        'token_verificacion': token_verificacion,
        'mensaje': 'Token de verificación generado. Debe confirmar la operación con este token.',
        'fecha_expiracion': fecha_expiracion.isoformat()
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """Solicitar restablecimiento de contraseña"""
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'El campo email es requerido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verificar si existe un usuario con ese email
        user = User.objects.filter(correo=email).first()
        
        if user:
            # Generar token de verificación para reset de contraseña
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=1)  # Expira en 1 hora
            
            TokenVerification.objects.create(
                user=user,
                token=token,
                operacion='reset_password',
                datos={'email': email},
                fecha_expiracion=expires_at
            )
            
            # Enviar email de restablecimiento
            reset_url = f"http://localhost:3000/reset-password?token={token}"
            try:
                send_mail(
                    'Restablecimiento de contraseña - BackMaaji',
                    f'Haz clic en el siguiente enlace para restablecer tu contraseña:\n\n{reset_url}\n\n'
                    f'Este enlace expirará en 1 hora.\n\n'
                    f'Si no solicitaste este restablecimiento, ignora este mensaje.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                logger.info(f"Email de reset enviado a {email}")
            except Exception as e:
                logger.error(f"Error enviando email de reset a {email}: {e}")
                # En desarrollo, mostrar el token en la respuesta
                if settings.DEBUG:
                    return Response({
                        'message': 'Email enviado (desarrollo)',
                        'token': token,
                        'reset_url': reset_url
                    }, status=status.HTTP_200_OK)
        
        # Por seguridad, siempre devolver el mismo mensaje
        return Response({
            'message': 'Si el email existe en nuestro sistema, se envió un enlace de restablecimiento'
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error en password reset request: {e}")
        return Response(
            {'error': 'Error al procesar la solicitud'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== VIEWSETS ====================

class RolViewSet(viewsets.ModelViewSet):
    """ViewSet para roles"""
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        # Solo admin puede crear, modificar o eliminar roles
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para usuarios"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return UserPublicSerializer
        return UserSerializer
    
    def get_permissions(self):
        # Solo usuarios con rol 'Administrador' o 'THA' pueden crear, modificar o eliminar usuarios
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminOrTHA()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrTHA])
    def cambiar_rol(self, request, pk=None):
        """Cambiar rol de un usuario con verificación"""
        serializer = CambioRolSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token_verificacion = serializer.validated_data['token_verificacion']
        nuevo_rol_id = serializer.validated_data['nuevo_rol_id']
        
        try:
            verificacion = TokenVerification.objects.get(
                token=token_verificacion,
                operacion='cambio_rol',
                usado=False
            )
            
            if not verificacion.is_valid():
                return Response({
                    'error': 'Token de verificación expirado o inválido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = self.get_object()
            nuevo_rol = Rol.objects.get(id_rol=nuevo_rol_id)
            user.rol = nuevo_rol
            user.save()
            
            # Marcar token como usado
            verificacion.usado = True
            verificacion.save()
            
            user_serializer = UserPublicSerializer(user)
            return Response({
                'mensaje': 'Rol cambiado exitosamente',
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except TokenVerification.DoesNotExist:
            return Response({
                'error': 'Token de verificación no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Rol.DoesNotExist:
            return Response({
                'error': 'Rol no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)


class EmpleadoViewSet(viewsets.ModelViewSet):
    """ViewSet para empleados"""
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Empleado.objects.all()
        
        # Filtros opcionales
        # Aceptar tanto 'search' como 'nombre' para compatibilidad
        search = self.request.query_params.get('search', None)
        nombre = self.request.query_params.get('nombre', None) or search
        estado = self.request.query_params.get('estado', None)
        area = self.request.query_params.get('area', None)
        ciudad = self.request.query_params.get('ciudad', None)
        tipo_documento = self.request.query_params.get('tipo_documento', None)
        numero_documento = self.request.query_params.get('numero_documento', None)
        
        if nombre:
            queryset = queryset.filter(
                Q(nombre__icontains=nombre) | 
                Q(apellido__icontains=nombre) |
                Q(numero_documento__icontains=nombre)
            )
        if estado:
            queryset = queryset.filter(estado=estado)
        if area:
            queryset = queryset.filter(area=area)
        if ciudad:
            queryset = queryset.filter(ciudad__icontains=ciudad)
        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)
        if numero_documento:
            queryset = queryset.filter(numero_documento__icontains=numero_documento)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def casos(self, request, pk=None):
        """Obtener casos de un empleado"""
        empleado = self.get_object()
        casos = empleado.casos.all()
        serializer = CasoSerializer(casos, many=True, context={'request': request})
        return Response(serializer.data)


class CasoViewSet(viewsets.ModelViewSet):
    """ViewSet para casos"""
    queryset = Caso.objects.all()
    serializer_class = CasoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Caso.objects.all()
        
        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        empleado_id = self.request.query_params.get('empleado', None)
        tipo_fuero = self.request.query_params.get('tipo_fuero', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if empleado_id:
            queryset = queryset.filter(empleado_id=empleado_id)
        if tipo_fuero:
            queryset = queryset.filter(tipo_fuero=tipo_fuero)
        
        return queryset
    
    def perform_create(self, serializer):
        # Asignar responsable automáticamente si no se proporciona
        if 'responsable' not in serializer.validated_data or serializer.validated_data.get('responsable') is None:
            serializer.save(responsable=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """Cerrar un caso"""
        caso = self.get_object()
        caso.cerrar()
        serializer = self.get_serializer(caso)
        return Response({
            'mensaje': 'Caso cerrado exitosamente',
            'caso': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        """Obtener documentos de un caso"""
        caso = self.get_object()
        documentos = caso.documentos.all()
        serializer = DocumentoSerializer(documentos, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def alertas(self, request, pk=None):
        """Obtener alertas de un caso"""
        caso = self.get_object()
        alertas = caso.alertas.all()
        serializer = AlertaSerializer(alertas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def seguimientos(self, request, pk=None):
        """Obtener seguimientos de un caso"""
        caso = self.get_object()
        seguimientos = caso.seguimientos.all()
        serializer = SeguimientoSerializer(seguimientos, many=True)
        return Response(serializer.data)


class AlertaViewSet(viewsets.ModelViewSet):
    """ViewSet para alertas"""
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Alerta.objects.all()
        
        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        caso_id = self.request.query_params.get('caso', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if caso_id:
            queryset = queryset.filter(caso_id=caso_id)
        
        return queryset


class CarpetaViewSet(viewsets.ModelViewSet):
    """ViewSet para carpetas"""
    queryset = Carpeta.objects.all()
    serializer_class = CarpetaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Carpeta.objects.all()
        
        # Filtro por empleado usando query parameter ?empleado=ID
        empleado_id = self.request.query_params.get('empleado', None)
        
        if empleado_id:
            queryset = queryset.filter(empleado_id=empleado_id)
        
        return queryset


class DocumentoViewSet(viewsets.ModelViewSet):
    """ViewSet para documentos"""
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Documento.objects.all()
        
        # Filtros opcionales
        caso_id = self.request.query_params.get('caso', None)
        tipo = self.request.query_params.get('tipo', None)
        
        if caso_id:
            queryset = queryset.filter(caso_id=caso_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset
    
    def perform_create(self, serializer):
        # Asignar usuario creador (ahora es ForeignKey, no string)
        serializer.save(usuario_creador=self.request.user)


class SeguimientoViewSet(viewsets.ModelViewSet):
    """ViewSet para seguimientos"""
    queryset = Seguimiento.objects.all()
    serializer_class = SeguimientoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Seguimiento.objects.all()
        
        # Filtros opcionales
        caso_id = self.request.query_params.get('caso', None)
        
        if caso_id:
            queryset = queryset.filter(caso_id=caso_id)
        
        return queryset
    
    def perform_create(self, serializer):
        # Asignar usuario responsable
        serializer.save(usuario_responsable=self.request.user.username)


class ReporteViewSet(viewsets.ModelViewSet):
    """ViewSet para reportes"""
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticated]
