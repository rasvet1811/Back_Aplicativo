# ✅ Solución: Conectar Frontend React con Backend Django

## 🎯 El Backend Está Funcionando Correctamente

Si puedes acceder a `http://localhost:8000/api/info/` desde el navegador, el backend está funcionando. El problema está en la configuración del frontend.

## 📋 Configuración Paso a Paso para React

### 1. Instalar Axios

```bash
npm install axios
```

### 2. Crear archivo de configuración de API

Crea `src/api/api.js` o `src/utils/api.js`:

```javascript
import axios from 'axios';

// URL base del backend
const API_BASE_URL = 'http://localhost:8000/api/';

// Crear instancia de Axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Interceptor para agregar token automáticamente
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expirado
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 3. Ejemplo de Login Component

```javascript
import React, { useState } from 'react';
import api from '../api/api';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await api.post('auth/login/', {
        username,
        password
      });

      // Guardar token y usuario
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      console.log('Login exitoso:', response.data.user);
      // Redirigir al dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
      console.error('Error:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      {error && <div style={{color: 'red'}}>{error}</div>}
      <button type="submit">Iniciar Sesión</button>
    </form>
  );
}

export default Login;
```

### 4. Ejemplo de Componente que Obtiene Datos

```javascript
import React, { useState, useEffect } from 'react';
import api from '../api/api';

function EmpleadosList() {
  const [empleados, setEmpleados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarEmpleados();
  }, []);

  const cargarEmpleados = async () => {
    try {
      const response = await api.get('empleados/');
      setEmpleados(response.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar empleados');
      setLoading(false);
      console.error('Error:', err);
    }
  };

  if (loading) return <div>Cargando...</div>;
  if (error) return <div style={{color: 'red'}}>{error}</div>;

  return (
    <div>
      <h1>Lista de Empleados</h1>
      {empleados.map(empleado => (
        <div key={empleado.id}>
          <h3>{empleado.nombre} {empleado.apellido}</h3>
          <p>Cargo: {empleado.cargo}</p>
          <p>Email: {empleado.correo}</p>
        </div>
      ))}
    </div>
  );
}

export default EmpleadosList;
```

## 🔍 Verificar la Conexión desde React

### Opción 1: Desde la Consola del Navegador (F12)

Abre la consola en tu aplicación React y ejecuta:

```javascript
// Probar endpoint público
fetch('http://localhost:8000/api/info/')
  .then(r => r.json())
  .then(data => console.log('✅ Info API:', data))
  .catch(err => console.error('❌ Error:', err));

// Probar login
fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'tu_usuario', password: 'tu_password'})
})
.then(r => r.json())
.then(data => {
  console.log('✅ Login OK:', data);
  localStorage.setItem('token', data.token);
})
.catch(err => console.error('❌ Error:', err));
```

### Opción 2: Verificar en Network Tab

1. Abre DevTools (F12)
2. Ve a la pestaña "Network"
3. Intenta hacer una petición desde tu app
4. Revisa:
   - **Status**: Debe ser 200, 201, etc. (no 401, 403, 404)
   - **Headers**: Debe incluir `Authorization: Token ...` si requiere auth
   - **Response**: Debe mostrar los datos JSON

## 🐛 Errores Comunes y Soluciones

### Error: "CORS policy: No 'Access-Control-Allow-Origin'"

**Solución:**
- Verifica que el servidor Django esté corriendo
- Verifica que `CORS_ALLOW_ALL_ORIGINS = True` en `settings.py`
- **Reinicia el servidor Django** después de cambiar settings.py

### Error: "Network Error" o "Failed to fetch"

**Causas posibles:**
1. El servidor no está corriendo
2. URL incorrecta
3. Firewall bloqueando

**Solución:**
```javascript
// Verifica la URL exacta
console.log('URL:', 'http://localhost:8000/api/auth/login/');

// Prueba con fetch directo
fetch('http://localhost:8000/api/info/')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

### Error: 401 Unauthorized

**Causa:** Token faltante o inválido

**Solución:**
```javascript
// Verifica que el token esté guardado
console.log('Token:', localStorage.getItem('token'));

// Si no hay token, haz login primero
```

### Error: 403 Forbidden

**Causa:** No tienes permisos (rol incorrecto)

**Solución:**
- Verifica que tu usuario tenga el rol correcto
- Los endpoints de empleados, casos, etc. requieren rol "administrador" o "THA"

## ✅ Checklist de Verificación

- [ ] Backend corriendo en `http://localhost:8000`
- [ ] Puedes acceder a `http://localhost:8000/api/info/` desde el navegador
- [ ] Axios instalado en React: `npm install axios`
- [ ] Archivo de configuración de API creado
- [ ] URL base correcta: `http://localhost:8000/api/`
- [ ] Interceptores configurados para agregar token
- [ ] Sin errores en la consola del navegador

## 🚀 Prueba Rápida

1. **Probar endpoint público:**
   ```
   http://localhost:8000/api/info/
   ```
   Debe funcionar sin autenticación.

2. **Hacer login desde React:**
   ```javascript
   const response = await fetch('http://localhost:8000/api/auth/login/', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({username: 'admin', password: 'password'})
   });
   const data = await response.json();
   console.log('Token:', data.token);
   ```

3. **Usar el token para otros endpoints:**
   ```javascript
   const token = localStorage.getItem('token');
   const response = await fetch('http://localhost:8000/api/empleados/', {
     headers: {'Authorization': `Token ${token}`}
   });
   ```

## 📞 Si Aún No Funciona

Comparte:
1. El error exacto de la consola del navegador (F12)
2. La petición que estás intentando hacer
3. El código de tu componente React

¡Con eso podré ayudarte a solucionarlo específicamente!




