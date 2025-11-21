# BackMaaji - Sistema de Gestión de Documentos para Talento Humano

Sistema backend desarrollado con Django REST Framework para la gestión de casos, documentos y archivos del área de talento humano.

## Características

- ✅ Autenticación por tokens con expiración automática (30 minutos)
- ✅ Sistema de roles (Admin, Talento Humano, Usuario)
- ✅ Gestión de personas con fotos e información
- ✅ Gestión de casos (abiertos, cerrados, pendientes)
- ✅ Subida y almacenamiento de documentos y archivos
- ✅ Verificación de identidad para operaciones sensibles (cambio de roles)
- ✅ API REST completa con documentación
- ✅ CORS configurado para React
- ✅ Base de datos MySQL

## Requisitos

- Python 3.8+
- MySQL 5.7+ o MariaDB 10.3+
- pip (gestor de paquetes de Python)

## Instalación

1. **Clonar o navegar al proyecto**
```bash
cd Oficial_backmaaji
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar Base de Datos MySQL**

Crear la base de datos en MySQL:
```sql
CREATE DATABASE backmaaji_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Editar `config/settings.py` y ajustar las credenciales:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'backmaaji_db',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_contraseña',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

4. **Ejecutar migraciones**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crear superusuario**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor de desarrollo**
```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Estructura del Proyecto

```
Oficial_backmaaji/
├── api/                    # Aplicación principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas y endpoints
│   ├── serializers.py     # Serializers de DRF
│   ├── urls.py            # Rutas de la API
│   └── admin.py           # Configuración del admin
├── config/                # Configuración del proyecto
│   ├── settings.py        # Configuración principal
│   └── urls.py            # URLs principales
├── media/                 # Archivos subidos (se crea automáticamente)
├── requirements.txt       # Dependencias
└── manage.py             # Script de gestión de Django
```

## Modelos Principales

- **User**: Usuarios del sistema con roles
- **Persona**: Personas con documentación
- **Caso**: Casos de documentación, formularios, permisos
- **Documento**: Documentos asociados a casos o personas
- **Archivo**: Archivos subidos al sistema
- **TokenVerification**: Tokens para verificación de identidad
- **ExpiringToken**: Tokens con expiración automática

## Endpoints Principales

Ver `API_DOCUMENTATION.md` para la documentación completa de la API.

### Autenticación
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/logout/` - Cerrar sesión
- `GET /api/auth/verificar-token/` - Verificar token
- `POST /api/auth/renovar-token/` - Renovar token

### Recursos
- `/api/usuarios/` - Gestión de usuarios
- `/api/personas/` - Gestión de personas
- `/api/casos/` - Gestión de casos
- `/api/documentos/` - Gestión de documentos
- `/api/archivos/` - Gestión de archivos

## Conexión con React

El backend está configurado para aceptar peticiones desde `http://localhost:3000` (puerto por defecto de React).

Ejemplo de configuración en React:

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
});

// Interceptor para agregar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default api;
```

## Seguridad

- Tokens expiran después de 30 minutos (configurable)
- Verificación de identidad requerida para cambio de roles
- Autenticación requerida para todos los endpoints (excepto login)
- CORS configurado para desarrollo
- Validación de permisos por rol

## Desarrollo

Para desarrollo, asegúrate de:

1. Tener MySQL corriendo
2. Configurar las credenciales en `settings.py`
3. Ejecutar migraciones después de cambios en modelos
4. Verificar que CORS esté configurado para tu frontend

## Producción

Para producción:

1. Cambiar `DEBUG = False` en `settings.py`
2. Configurar `ALLOWED_HOSTS` con tu dominio
3. Configurar servidor web (Nginx + Gunicorn)
4. Configurar SSL/HTTPS
5. Ajustar configuración de CORS para el dominio de producción
6. Configurar backup de base de datos

## Soporte

Para más información sobre los endpoints, consulta `API_DOCUMENTATION.md`.




