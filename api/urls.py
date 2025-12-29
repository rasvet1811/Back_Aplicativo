from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'roles', views.RolViewSet, basename='rol')
router.register(r'usuarios', views.UserViewSet, basename='usuario')
router.register(r'empleados', views.EmpleadoViewSet, basename='empleado')
router.register(r'casos', views.CasoViewSet, basename='caso')
router.register(r'alertas', views.AlertaViewSet, basename='alerta')
router.register(r'documentos', views.DocumentoViewSet, basename='documento')
router.register(r'carpetas', views.CarpetaViewSet, basename='carpeta')
router.register(r'seguimientos', views.SeguimientoViewSet, basename='seguimiento')
router.register(r'reportes', views.ReporteViewSet, basename='reporte')

urlpatterns = [
    # Información de la API (público)
    path('info/', views.api_info, name='api_info'),
    
    # Autenticación
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/verificar-token/', views.verificar_token, name='verificar_token'),
    path('auth/renovar-token/', views.renovar_token, name='renovar_token'),
    
    # Verificación de identidad
    path('auth/solicitar-verificacion-rol/', views.solicitar_verificacion_rol, name='solicitar_verificacion_rol'),
    
    # Restablecimiento de contraseña
    path('auth/password-reset/', views.password_reset_request, name='password_reset_request'),
    
    # Rutas del router
    path('', include(router.urls)),
]
