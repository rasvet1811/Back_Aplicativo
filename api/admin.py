from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Rol, User, Empleado, Caso, Alerta, Documento, 
    Seguimiento, Reporte, CasoReporte, TokenVerification, ExpiringToken
)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['id_rol', 'tipo']
    search_fields = ['tipo']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'nombre', 'correo', 'rol', 'estado', 'date_joined']
    list_filter = ['rol', 'estado', 'is_staff', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('nombre', 'rol', 'correo', 'estado')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('nombre', 'rol', 'correo', 'estado')}),
    )
    search_fields = ['username', 'nombre', 'correo']


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'cargo', 'area', 'estado', 'fecha_ingreso']
    list_filter = ['estado', 'area', 'division', 'fecha_ingreso']
    search_fields = ['nombre', 'apellido', 'correo', 'cargo']
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'fecha_nacimiento', 'foto')
        }),
        ('Información Laboral', {
            'fields': ('cargo', 'division', 'area', 'supervisor', 'fecha_ingreso', 'estado')
        }),
        ('Contacto', {
            'fields': ('correo', 'telefono')
        }),
    )


@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ['id_caso', 'empleado', 'tipo_fuero', 'estado', 'fecha_inicio', 'responsable', 'fecha_cierre']
    list_filter = ['estado', 'tipo_fuero', 'fecha_inicio', 'fecha_cierre']
    search_fields = ['empleado__nombre', 'empleado__apellido', 'diagnostico', 'observaciones']
    readonly_fields = ['fecha_inicio']
    fieldsets = (
        ('Información General', {
            'fields': ('empleado', 'tipo_fuero', 'diagnostico', 'estado', 'responsable')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_cierre')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'caso', 'tipo', 'estado', 'fecha_generada', 'fecha_vencimiento']
    list_filter = ['tipo', 'estado', 'fecha_generada', 'fecha_vencimiento']
    search_fields = ['titulo', 'descripcion', 'caso__empleado__nombre']
    readonly_fields = ['fecha_generada']


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'caso', 'tipo', 'usuario_creador', 'fecha_carga', 'extension']
    list_filter = ['tipo', 'fecha_carga', 'extension']
    search_fields = ['nombre', 'descripcion', 'caso__empleado__nombre']
    readonly_fields = ['fecha_carga', 'fecha_modificacion']


@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ['id_seguimiento', 'caso', 'usuario_responsable', 'accion_realizada', 'fecha']
    list_filter = ['fecha', 'usuario_responsable']
    search_fields = ['accion_realizada', 'observaciones', 'caso__empleado__nombre']
    readonly_fields = ['fecha']


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'formato', 'estado']
    list_filter = ['tipo', 'formato', 'estado']
    search_fields = ['codigo', 'nombre']


@admin.register(CasoReporte)
class CasoReporteAdmin(admin.ModelAdmin):
    list_display = ['caso', 'reporte']
    list_filter = ['caso', 'reporte']


@admin.register(TokenVerification)
class TokenVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'operacion', 'usado', 'fecha_creacion', 'fecha_expiracion']
    list_filter = ['operacion', 'usado', 'fecha_creacion']
    search_fields = ['user__username', 'token']
    readonly_fields = ['fecha_creacion', 'fecha_expiracion']


@admin.register(ExpiringToken)
class ExpiringTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'fecha_creacion', 'ultima_actividad', 'is_expired']
    list_filter = ['fecha_creacion', 'ultima_actividad']
    search_fields = ['user__username', 'key']
    readonly_fields = ['key', 'fecha_creacion', 'ultima_actividad']
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'
