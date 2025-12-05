from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework.authtoken.models import Token as DRFToken
from django.conf import settings
from datetime import timedelta


class Rol(models.Model):
    """Roles del sistema - Mapea a tabla Rol"""
    id_rol = models.AutoField(primary_key=True, db_column='Id_Rol')
    tipo = models.CharField(max_length=100, db_column='Tipo')
    
    class Meta:
        db_table = 'Rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['tipo']
    
    def __str__(self):
        return self.tipo


class User(AbstractUser):
    """Usuario del sistema - Mapea a tabla Usuario"""
    id = models.AutoField(primary_key=True, db_column='Id_Usuario')
    nombre = models.CharField(max_length=150, db_column='Nombre')
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, db_column='Rol', related_name='usuarios')
    contrasena = models.CharField(max_length=255, db_column='Contrasena', blank=True)  # Django usa password, pero mapeamos este campo
    correo = models.EmailField(unique=True, max_length=150, db_column='Correo')
    estado = models.CharField(max_length=50, db_column='Estado', default='Activo')
    
    # Nuevos campos agregados
    ciudad = models.CharField(max_length=100, blank=True, null=True, db_column='Ciudad')
    puesto = models.CharField(max_length=150, blank=True, null=True, db_column='Puesto')
    experiencia = models.TextField(blank=True, null=True, db_column='Experiencia')
    fecha_ingreso = models.DateField(blank=True, null=True, db_column='Fecha_Ingreso')
    area = models.CharField(max_length=100, blank=True, null=True, db_column='Area')
    division = models.CharField(max_length=100, blank=True, null=True, db_column='Division')
    
    class Meta:
        db_table = 'Usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.rol.tipo if self.rol else 'Sin rol'})"
    
    def save(self, *args, **kwargs):
        # Sincronizar password con contrasena
        if hasattr(self, 'password') and self.password:
            # Django hashea la contraseña en el campo password
            # Guardamos también en contrasena para compatibilidad
            self.contrasena = self.password
        super().save(*args, **kwargs)
    
    @property
    def is_admin(self):
        return self.rol and self.rol.tipo.lower() == 'administrador'


class ExpiringToken(DRFToken):
    """Token con expiración personalizado - Tabla adicional para autenticación"""
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Token con Expiración'
        verbose_name_plural = 'Tokens con Expiración'
    
    def is_expired(self):
        """Verifica si el token ha expirado basado en última actividad"""
        minutos_expiracion = getattr(settings, 'TOKEN_EXPIRATION_MINUTES', 30)
        # Usar última actividad en lugar de fecha de creación para mejor UX
        tiempo_inactivo = (timezone.now() - self.ultima_actividad).total_seconds()
        return tiempo_inactivo > (minutos_expiracion * 60)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.fecha_creacion = timezone.now()
        self.ultima_actividad = timezone.now()
        return super().save(*args, **kwargs)


class Empleado(models.Model):
    """Empleados de la empresa - Mapea a tabla Empleado"""
    # Opciones para Tipo_Documento según el constraint CHECK
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('RC', 'Registro Civil'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
        ('NIT', 'NIT'),
    ]
    
    id_empleado = models.AutoField(primary_key=True, db_column='Id_Empleado')
    nombre = models.CharField(max_length=100, db_column='Nombre')
    apellido = models.CharField(max_length=100, db_column='Apellido')
    cargo = models.CharField(max_length=100, blank=True, null=True, db_column='Cargo')
    division = models.CharField(max_length=100, blank=True, null=True, db_column='Division')
    area = models.CharField(max_length=100, blank=True, null=True, db_column='Area')
    supervisor = models.CharField(max_length=150, blank=True, null=True, db_column='Supervisor')
    fecha_nacimiento = models.DateField(blank=True, null=True, db_column='Fecha_Nacimiento')
    fecha_ingreso = models.DateField(blank=True, null=True, db_column='Fecha_Ingreso')
    correo = models.EmailField(blank=True, null=True, max_length=150, db_column='Correo')
    telefono = models.CharField(max_length=50, blank=True, null=True, db_column='Telefono')
    estado = models.CharField(max_length=50, blank=True, null=True, db_column='Estado', default='Activo')
    foto = models.ImageField(upload_to='empleados/fotos/', blank=True, null=True)  # Campo adicional no en BD
    
    # Nuevos campos agregados
    ciudad = models.CharField(max_length=100, blank=True, null=True, db_column='Ciudad')
    numero_documento = models.CharField(max_length=50, blank=True, null=True, db_column='Numero_Documento')
    tipo_documento = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        db_column='Tipo_Documento',
        choices=TIPO_DOCUMENTO_CHOICES
    )
    
    class Meta:
        db_table = 'Empleado'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['apellido', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Caso(models.Model):
    """Casos de documentación - Mapea a tabla Caso"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('abierto', 'Abierto'),
        ('cerrado', 'Cerrado'),
    ]
    
    id_caso = models.AutoField(primary_key=True, db_column='Id_Caso')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='Id_Empleado', related_name='casos')
    tipo_fuero = models.CharField(max_length=100, blank=True, null=True, db_column='Tipo_Fuero')
    diagnostico = models.TextField(blank=True, null=True, db_column='Diagnostico')
    fecha_inicio = models.DateField(auto_now_add=True, db_column='Fecha_Inicio')
    estado = models.CharField(
        max_length=50, 
        db_column='Estado', 
        default='abierto',
        choices=ESTADO_CHOICES
    )
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, db_column='Responsable', related_name='casos_responsable')
    fecha_cierre = models.DateField(blank=True, null=True, db_column='Fecha_Cierre')
    observaciones = models.TextField(blank=True, null=True, db_column='Observaciones')
    
    class Meta:
        db_table = 'Caso'
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Caso #{self.id_caso} - {self.empleado} ({self.estado})"
    
    def cerrar(self):
        """Cierra el caso"""
        self.estado = 'cerrado'
        self.fecha_cierre = timezone.now().date()
        self.save()


class Alerta(models.Model):
    """Alertas asociadas a casos - Mapea a tabla Alerta"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('vencida', 'Vencida'),
    ]
    
    id_alerta = models.AutoField(primary_key=True, db_column='Id_Alerta')
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, db_column='Id_Caso', related_name='alertas')
    titulo = models.CharField(max_length=150, blank=True, null=True, db_column='Titulo')
    tipo = models.CharField(max_length=100, blank=True, null=True, db_column='Tipo')
    fecha_generada = models.DateField(auto_now_add=True, db_column='Fecha_Generada')
    fecha_envio = models.DateField(blank=True, null=True, db_column='Fecha_Envio')
    fecha_vencimiento = models.DateField(blank=True, null=True, db_column='Fecha_Vencimiento')
    estado = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        db_column='Estado', 
        default='pendiente',
        choices=ESTADO_CHOICES
    )
    descripcion = models.TextField(blank=True, null=True, db_column='Descripcion')
    
    class Meta:
        db_table = 'Alerta'
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-fecha_generada']
    
    def __str__(self):
        return f"{self.titulo} - {self.caso}"


class Carpeta(models.Model):
    """Carpetas para organizar documentos - Mapea a tabla Carpeta"""
    id_carpeta = models.AutoField(primary_key=True, db_column='Id_Carpeta')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='Id_Empleado', related_name='carpetas')
    nombre = models.CharField(max_length=150, db_column='Nombre')
    fecha_creacion = models.DateField(auto_now_add=True, db_column='Fecha_Creacion')
    
    class Meta:
        db_table = 'Carpeta'
        verbose_name = 'Carpeta'
        verbose_name_plural = 'Carpetas'
        ordering = ['-fecha_creacion', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.empleado}"


class Documento(models.Model):
    """Documentos asociados a casos - Mapea a tabla Documento"""
    id_documento = models.AutoField(primary_key=True, db_column='Id_Documento')
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, blank=True, null=True, db_column='Id_Caso', related_name='documentos')
    nombre = models.CharField(max_length=150, blank=True, null=True, db_column='Nombre')
    tipo = models.CharField(max_length=100, blank=True, null=True, db_column='Tipo')
    fecha_carga = models.DateField(auto_now_add=True, db_column='Fecha_Carga')
    fecha_modificacion = models.DateField(auto_now=True, db_column='Fecha_Modificacion')
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, db_column='Usuario_Creador', related_name='documentos_creados')
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, blank=True, null=True, db_column='Id_Empleado', related_name='documentos')
    carpeta = models.ForeignKey('Carpeta', on_delete=models.SET_NULL, blank=True, null=True, db_column='Id_Carpeta', related_name='documentos')
    descripcion = models.TextField(blank=True, null=True, db_column='Descripcion')
    ruta = models.TextField(blank=True, null=True, db_column='Ruta')  # Ruta del archivo
    extension = models.CharField(max_length=20, blank=True, null=True, db_column='Extension')
    archivo = models.FileField(upload_to='documentos/', blank=True, null=True)  # Campo adicional para FileField
    
    class Meta:
        db_table = 'Documento'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-fecha_carga']
    
    def __str__(self):
        return f"{self.nombre} - {self.caso}"
    
    def save(self, *args, **kwargs):
        # Si hay archivo, actualizar ruta y extensión
        if self.archivo:
            self.ruta = self.archivo.name
            if '.' in self.archivo.name:
                self.extension = self.archivo.name.split('.')[-1].lower()
        super().save(*args, **kwargs)


class Seguimiento(models.Model):
    """Seguimientos de casos - Mapea a tabla Seguimiento"""
    id_seguimiento = models.AutoField(primary_key=True, db_column='Id_Seguimiento')
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, db_column='Id_Caso', related_name='seguimientos')
    fecha = models.DateField(auto_now_add=True, db_column='Fecha')
    usuario_responsable = models.CharField(max_length=150, blank=True, null=True, db_column='Usuario_Responsable')
    accion_realizada = models.TextField(blank=True, null=True, db_column='Accion_Realizada')
    observaciones = models.TextField(blank=True, null=True, db_column='Observaciones')
    
    class Meta:
        db_table = 'Seguimiento'
        verbose_name = 'Seguimiento'
        verbose_name_plural = 'Seguimientos'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Seguimiento #{self.id_seguimiento} - {self.caso} - {self.fecha}"


class Reporte(models.Model):
    """Reportes del sistema - Mapea a tabla Reporte"""
    id_reporte = models.AutoField(primary_key=True, db_column='Id_Reporte')
    codigo = models.CharField(max_length=50, blank=True, null=True, db_column='Codigo')
    nombre = models.CharField(max_length=150, blank=True, null=True, db_column='Nombre')
    tipo = models.CharField(max_length=100, blank=True, null=True, db_column='Tipo')
    formato = models.CharField(max_length=50, blank=True, null=True, db_column='Formato')
    estado = models.CharField(max_length=50, blank=True, null=True, db_column='Estado', default='Pendiente')
    
    # Relación ManyToMany con Caso a través de la tabla intermedia Caso_Reporte
    casos = models.ManyToManyField(Caso, through='CasoReporte', related_name='reportes')
    
    class Meta:
        db_table = 'Reporte'
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class CasoReporte(models.Model):
    """Tabla intermedia para relación ManyToMany entre Caso y Reporte"""
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, db_column='Id_Caso')
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, db_column='Id_Reporte')
    
    class Meta:
        db_table = 'Caso_Reporte'
        unique_together = [['caso', 'reporte']]
    
    def __str__(self):
        return f"Caso {self.caso.id_caso} - Reporte {self.reporte.id_reporte}"


class TokenVerification(models.Model):
    """Modelo para verificación de identidad en operaciones sensibles - Tabla adicional"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verificaciones')
    token = models.CharField(max_length=100, unique=True)
    operacion = models.CharField(max_length=100)  # Tipo de operación (cambio_rol, etc.)
    datos = models.JSONField(default=dict)  # Datos adicionales de la operación
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Verificación de Token'
        verbose_name_plural = 'Verificaciones de Tokens'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Verificación {self.operacion} - {self.user.username}"
    
    def is_valid(self):
        """Verifica si el token es válido y no ha expirado"""
        return not self.usado and timezone.now() < self.fecha_expiracion
