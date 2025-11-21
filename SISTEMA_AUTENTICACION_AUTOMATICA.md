# Sistema de Autenticación Automática con Tokens

## ✅ Características Implementadas

### Backend (Django)

1. **Generación automática de tokens**
   - Los tokens se generan automáticamente al hacer login
   - Se eliminan tokens expirados antes de crear uno nuevo
   - Un usuario solo puede tener un token activo a la vez

2. **Expiración basada en actividad**
   - Los tokens expiran después de 30 minutos de **inactividad** (no desde la creación)
   - Cada vez que se usa el token, se actualiza la última actividad
   - Esto permite que los usuarios activos no sean desconectados

3. **Endpoint de verificación público**
   - `GET/POST /api/auth/verificar-token/` - Ahora es público
   - Puede validar tokens sin requerir autenticación previa
   - Acepta el token en el header `Authorization: Token {token}` o en el body
   - Retorna información del usuario y tiempo restante

4. **Renovación de tokens**
   - `POST /api/auth/renovar-token/` - Renueva el token actual
   - Útil cuando el token está por expirar

### Frontend (React)

1. **Servicio de API con interceptores automáticos**
   - `frontend/src/services/api.js`
   - Agrega automáticamente el token a todas las peticiones
   - Valida tokens automáticamente antes de cada petición
   - Maneja errores 401 y redirige al login si es necesario

2. **Hook useAuth**
   - `frontend/src/hooks/useAuth.js`
   - Maneja el estado de autenticación
   - Valida tokens periódicamente (cada 5 minutos)
   - Proporciona funciones: `login`, `logout`, `verifyToken`, `renewToken`

3. **Componentes listos para usar**
   - `ProtectedRoute` - Protege rutas que requieren autenticación
   - `Login` - Componente de login con validación automática

## 📁 Archivos Creados/Modificados

### Backend
- ✅ `api/models.py` - Mejorada lógica de expiración basada en última actividad
- ✅ `api/views.py` - Endpoint de verificación ahora es público y mejorado

### Frontend
- ✅ `frontend/src/services/api.js` - Servicio completo con interceptores
- ✅ `frontend/src/hooks/useAuth.js` - Hook para manejo de autenticación
- ✅ `frontend/src/components/ProtectedRoute.jsx` - Componente para proteger rutas
- ✅ `frontend/src/components/Login.jsx` - Componente de login
- ✅ `frontend/EJEMPLO_USO_AUTENTICACION.md` - Guía completa de uso

## 🚀 Cómo Funciona

### 1. Login Automático

```javascript
// El usuario hace login
const result = await authService.login('username', 'password');

// El sistema automáticamente:
// 1. Genera un token en el backend
// 2. Guarda el token en localStorage
// 3. Guarda la información del usuario
// 4. Configura los interceptores de Axios
```

### 2. Validación Automática

```javascript
// Cada vez que haces una petición:
const response = await api.get('/empleados/');

// El interceptor automáticamente:
// 1. Agrega el token al header Authorization
// 2. Si recibe 401, valida el token
// 3. Si el token es válido, reintenta la petición
// 4. Si el token expiró, limpia y redirige al login
```

### 3. Validación Periódica

```javascript
// El hook useAuth valida automáticamente cada 5 minutos:
// 1. Verifica si hay un token
// 2. Llama a /api/auth/verificar-token/
// 3. Si es válido, actualiza la información del usuario
// 4. Si expiró, limpia y redirige al login
```

## 📝 Uso Rápido

### 1. Instalar dependencias

```bash
cd frontend
npm install axios react-router-dom
```

### 2. Configurar variables de entorno

Crear `.env` en la raíz del frontend:

```env
REACT_APP_API_URL=http://localhost:8000/api
```

### 3. Usar en tu aplicación

```jsx
// App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
```

```jsx
// Dashboard.jsx
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';

const Dashboard = () => {
  const { user, logout } = useAuth();

  const fetchData = async () => {
    // El token se agrega automáticamente
    const response = await api.get('/empleados/');
    console.log(response.data);
  };

  return (
    <div>
      <h1>Bienvenido, {user?.nombre}</h1>
      <button onClick={logout}>Cerrar Sesión</button>
      <button onClick={fetchData}>Cargar Datos</button>
    </div>
  );
};
```

## 🔧 Configuración

### Tiempo de expiración del token

En `config/settings.py`:

```python
TOKEN_EXPIRATION_MINUTES = 30  # 30 minutos (default)
# Cambiar a 60 para 1 hora, 120 para 2 horas, etc.
```

### Intervalo de validación

En `frontend/src/hooks/useAuth.js`:

```javascript
// Cambiar de 5 minutos a 10 minutos
const validationInterval = setInterval(async () => {
  // ...
}, 10 * 60 * 1000); // 10 minutos
```

## 🎯 Endpoints Disponibles

### Públicos (sin token)

- `POST /api/auth/login/` - Login (genera token automáticamente)
- `GET/POST /api/auth/verificar-token/` - Verificar token (público)

### Protegidos (requieren token)

- `POST /api/auth/logout/` - Cerrar sesión
- `POST /api/auth/renovar-token/` - Renovar token

## ✨ Ventajas

1. **Sin configuración manual**: Todo funciona automáticamente
2. **Seguridad mejorada**: Tokens expiran por inactividad
3. **Mejor UX**: Los usuarios activos no son desconectados
4. **Fácil de usar**: Solo importa y usa
5. **Validación automática**: No necesitas verificar tokens manualmente

## 🔍 Flujo Completo

```
1. Usuario hace login
   ↓
2. Backend genera token automáticamente
   ↓
3. Frontend guarda token en localStorage
   ↓
4. Usuario hace peticiones API
   ↓
5. Interceptor agrega token automáticamente
   ↓
6. Si token expira → Validar automáticamente
   ↓
7. Si válido → Reintentar petición
   ↓
8. Si expirado → Limpiar y redirigir al login
   ↓
9. Validación periódica cada 5 minutos
   ↓
10. Si expira → Redirigir al login automáticamente
```

## 📚 Documentación Adicional

- Ver `frontend/EJEMPLO_USO_AUTENTICACION.md` para ejemplos completos
- Ver `API_DOCUMENTATION.md` para documentación de endpoints
- Ver `ENDPOINTS_ACTUALIZADOS.md` para lista completa de endpoints

## 🐛 Solución de Problemas

### El token no se guarda
- Verifica que localStorage esté disponible
- Verifica la consola del navegador para errores

### Las peticiones fallan con 401
- Verifica que el token se esté guardando: `localStorage.getItem('token')`
- Verifica la URL de la API en `.env`
- Verifica que el servidor Django esté corriendo

### El token expira muy rápido
- Aumenta `TOKEN_EXPIRATION_MINUTES` en `config/settings.py`
- Verifica que estés haciendo peticiones regularmente (actualiza última actividad)

## ✅ Todo Listo

El sistema está completamente configurado para:
- ✅ Generar tokens automáticamente
- ✅ Validar tokens automáticamente
- ✅ Renovar tokens cuando sea necesario
- ✅ Manejar expiración automáticamente
- ✅ Redirigir al login cuando el token expire

**¡No necesitas hacer nada más! Solo usa los componentes y el hook.**




