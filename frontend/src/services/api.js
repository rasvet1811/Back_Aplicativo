const BASE_URL = 'http://localhost:8000/api';

// ==================== GESTIÓN DE TOKEN ====================

const TOKEN_KEY = 'authToken';
const USER_KEY = 'user';

const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

const setToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
};

const getUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  return userStr ? JSON.parse(userStr) : null;
};

const setUser = (user) => {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
};

const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

// ==================== SERVICIO DE AUTENTICACIÓN ====================

export const authService = {
  // POST /api/auth/login/
  login: async (username, password) => {
    try {
      const response = await fetch(`${BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { message: `Error ${response.status}: ${response.statusText}` };
        }
        
        // Manejo específico de errores 500
        if (response.status === 500) {
          throw new Error('Error interno del servidor. Por favor, contacta al administrador o verifica los logs del backend.');
        }
        
        throw new Error(errorData.message || errorData.detail || errorData.error || `Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.token) {
        console.log('[Auth] Token recibido del servidor, guardando...', data.token.substring(0, 20) + '...');
        setToken(data.token);
        const savedToken = getToken();
        console.log('[Auth] Token guardado correctamente:', savedToken ? savedToken.substring(0, 20) + '...' : 'NO SE GUARDÓ');
        if (data.user) {
          setUser(data.user);
          console.log('[Auth] Usuario guardado:', data.user);
        }
      } else {
        console.error('[Auth] ⚠️ No se recibió token en la respuesta del login');
      }
      
      return data;
    } catch (error) {
      console.error('[Auth] Login error:', error);
      if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
        throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté corriendo en http://localhost:8000 y que CORS esté configurado correctamente.');
      }
      throw error;
    }
  },

  // POST /api/auth/logout/
  logout: async () => {
    try {
      const token = getToken();
      if (token) {
        await fetch(`${BASE_URL}/auth/logout/`, {
          method: 'POST',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('[Auth] Logout error:', error);
    } finally {
      clearAuth();
    }
  },

  // GET /api/auth/verificar-token/
  verifyToken: async () => {
    try {
      const token = getToken();
      if (!token) {
        return { valido: false, user: null, tiempo_restante: 0 };
      }

      const response = await fetch(`${BASE_URL}/auth/verificar-token/`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return { valido: false, user: null, tiempo_restante: 0 };
      }

      return await response.json();
    } catch (error) {
      console.error('[Auth] Verify token error:', error);
      return { valido: false, user: null, tiempo_restante: 0 };
    }
  },

  // POST /api/auth/renovar-token/
  renewToken: async () => {
    try {
      const token = getToken();
      if (!token) {
        throw new Error('No hay token para renovar');
      }

      const response = await fetch(`${BASE_URL}/auth/renovar-token/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Error al renovar el token');
      }

      const data = await response.json();
      if (data.token) {
        setToken(data.token);
      }
      
      return data;
    } catch (error) {
      console.error('[Auth] Renew token error:', error);
      throw error;
    }
  },

  // Utilidades
  getToken: () => getToken(),
  getUser: () => getUser(),
  isAuthenticated: () => !!getToken(),
};

// ==================== INTERCEPTOR PARA PETICIONES ====================

const makeRequest = async (endpoint, options = {}) => {
  const { requiresAuth = true, ...fetchOptions } = options;
  
  const headers = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };

  // Agregar token automáticamente si requiere autenticación
  if (requiresAuth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Token ${token}`;
      console.log(`[API] Token encontrado, agregando a headers para ${endpoint}`);
    } else {
      console.warn(`[API] ⚠️ No hay token disponible para ${endpoint}. La petición fallará con 401.`);
    }
  }

  const config = {
    ...fetchOptions,
    headers,
  };

  try {
    console.log(`[API] ${config.method || 'GET'} ${BASE_URL}${endpoint}`, {
      method: config.method || 'GET',
      headers: config.headers,
      hasAuth: !!config.headers['Authorization']
    });
    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    
    console.log(`[API] Response status: ${response.status} para ${endpoint}`);

    // Si el token expiró, intentar renovarlo
    if (response.status === 401 && requiresAuth) {
      try {
        await authService.renewToken();
        // Reintentar la petición con el nuevo token
        const newToken = getToken();
        if (newToken) {
          headers['Authorization'] = `Token ${newToken}`;
          const retryResponse = await fetch(`${BASE_URL}${endpoint}`, {
            ...config,
            headers,
          });
          
          if (!retryResponse.ok) {
            const errorData = await retryResponse.json().catch(() => ({}));
            throw new Error(errorData.message || errorData.detail || `Error ${retryResponse.status}`);
          }
          
          return await retryResponse.json();
        }
      } catch (renewError) {
        // Si no se puede renovar, limpiar auth
        clearAuth();
        window.dispatchEvent(new CustomEvent('token-expired'));
        throw new Error('Token expirado. Por favor, inicia sesión nuevamente.');
      }
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { message: `Error ${response.status}: ${response.statusText}` };
      }
      
      // Manejo específico de errores 500
      if (response.status === 500) {
        throw new Error('Error interno del servidor. Por favor, contacta al administrador o verifica los logs del backend.');
      }
      
      throw new Error(errorData.message || errorData.detail || errorData.error || errorData.non_field_errors?.[0] || `Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('[API] Success response:', data);
    return data;
  } catch (error) {
    console.error('[API] Request error:', error);
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté corriendo en http://localhost:8000 y que CORS esté configurado correctamente.');
    }
    throw error;
  }
};

// ==================== PETICIONES CON FORMDATA ====================

const makeFormDataRequest = async (endpoint, formData, options = {}) => {
  const { requiresAuth = true, ...fetchOptions } = options;
  
  const headers = {
    ...fetchOptions.headers,
  };

  // Agregar token automáticamente si requiere autenticación
  if (requiresAuth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }
  }

  const config = {
    ...fetchOptions,
    headers,
    body: formData,
  };

  try {
    console.log(`[API] ${config.method || 'POST'} ${BASE_URL}${endpoint} (FormData)`);
    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { message: `Error ${response.status}: ${response.statusText}` };
      }
      
      // Manejo específico de errores 500
      if (response.status === 500) {
        throw new Error('Error interno del servidor. Por favor, contacta al administrador o verifica los logs del backend.');
      }
      
      throw new Error(errorData.message || errorData.detail || errorData.error || `Error ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[API] FormData request error:', error);
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      throw new Error('No se pudo conectar con el servidor. Verifica que el backend esté corriendo en http://localhost:8000 y que CORS esté configurado correctamente.');
    }
    throw error;
  }
};

// ==================== API SERVICE (ESTILO AXIOS) ====================

const api = {
  // GET
  get: async (endpoint, options = {}) => {
    return makeRequest(endpoint, { ...options, method: 'GET' });
  },

  // POST
  post: async (endpoint, data = null, options = {}) => {
    if (data instanceof FormData) {
      return makeFormDataRequest(endpoint, data, { ...options, method: 'POST' });
    }
    return makeRequest(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  // PUT
  put: async (endpoint, data = null, options = {}) => {
    if (data instanceof FormData) {
      return makeFormDataRequest(endpoint, data, { ...options, method: 'PUT' });
    }
    return makeRequest(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  // DELETE
  delete: async (endpoint, options = {}) => {
    return makeRequest(endpoint, { ...options, method: 'DELETE' });
  },

  // PATCH
  patch: async (endpoint, data = null, options = {}) => {
    if (data instanceof FormData) {
      return makeFormDataRequest(endpoint, data, { ...options, method: 'PATCH' });
    }
    return makeRequest(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  },
};

// ==================== EXPORTAR ====================

export default api;

// Exportar también funciones específicas para compatibilidad

export const empleadosAPI = {
  getAll: (search = '', estado = null) => {
    let url = '/empleados/';
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (estado !== null) params.append('estado', estado);
    if (params.toString()) url += `?${params.toString()}`;
    // CORREGIDO: requiere autenticación
    return api.get(url);
  },

  getById: (id) => api.get(`/empleados/${id}/`),

  create: (empleadoData, foto = null) => {
    const formData = new FormData();
    Object.keys(empleadoData).forEach(key => {
      if (empleadoData[key] !== null && empleadoData[key] !== undefined) {
        formData.append(key, empleadoData[key]);
      }
    });
    if (foto) formData.append('foto', foto);
    return api.post('/empleados/', formData);
  },

  update: (id, empleadoData, foto = null) => {
    const formData = new FormData();
    Object.keys(empleadoData).forEach(key => {
      if (empleadoData[key] !== null && empleadoData[key] !== undefined) {
        formData.append(key, empleadoData[key]);
      }
    });
    if (foto) formData.append('foto', foto);
    return api.put(`/empleados/${id}/`, formData);
  },

  delete: (id) => api.delete(`/empleados/${id}/`),

  getHistorial: (id) => api.get(`/empleados/${id}/historial/`),
};

export const casosAPI = {
  getAll: (estado = null, empleado = null, tipo_fuero = null) => {
    let url = '/casos/';
    const params = new URLSearchParams();
    if (estado) params.append('estado', estado);
    if (empleado) params.append('empleado', empleado);
    if (tipo_fuero) params.append('tipo_fuero', tipo_fuero);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },

  getById: (id) => api.get(`/casos/${id}/`),

  create: (casoData) => api.post('/casos/', casoData),

  update: (id, casoData) => api.put(`/casos/${id}/`, casoData),

  delete: (id) => api.delete(`/casos/${id}/`),

  cerrar: (id) => api.post(`/casos/${id}/cerrar/`),
};

export const documentosAPI = {
  getAll: (caso = null, tipo = null) => {
    let url = '/documentos/';
    const params = new URLSearchParams();
    if (caso) params.append('caso', caso);
    if (tipo) params.append('tipo', tipo);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },

  getById: (id) => api.get(`/documentos/${id}/`),

  create: (documentoData, archivo) => {
    const formData = new FormData();
    Object.keys(documentoData).forEach(key => {
      if (documentoData[key] !== null && documentoData[key] !== undefined) {
        formData.append(key, documentoData[key]);
      }
    });
    if (archivo) formData.append('ruta', archivo);
    return api.post('/documentos/', formData);
  },

  update: (id, documentoData, archivo = null) => {
    const formData = new FormData();
    Object.keys(documentoData).forEach(key => {
      if (documentoData[key] !== null && documentoData[key] !== undefined) {
        formData.append(key, documentoData[key]);
      }
    });
    if (archivo) formData.append('ruta', archivo);
    return api.put(`/documentos/${id}/`, formData);
  },

  delete: (id) => api.delete(`/documentos/${id}/`),
};

export const alertasAPI = {
  getAll: (caso = null, estado = null, tipo = null) => {
    let url = '/alertas/';
    const params = new URLSearchParams();
    if (caso) params.append('caso', caso);
    if (estado) params.append('estado', estado);
    if (tipo) params.append('tipo', tipo);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },

  getById: (id) => api.get(`/alertas/${id}/`),

  create: (alertaData) => api.post('/alertas/', alertaData),

  update: (id, alertaData) => api.put(`/alertas/${id}/`, alertaData),

  delete: (id) => api.delete(`/alertas/${id}/`),
};

export const seguimientosAPI = {
  getAll: (caso = null, usuario = null) => {
    let url = '/seguimientos/';
    const params = new URLSearchParams();
    if (caso) params.append('caso', caso);
    if (usuario) params.append('usuario', usuario);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },

  getById: (id) => api.get(`/seguimientos/${id}/`),

  create: (seguimientoData) => api.post('/seguimientos/', seguimientoData),

  update: (id, seguimientoData) => api.put(`/seguimientos/${id}/`, seguimientoData),

  delete: (id) => api.delete(`/seguimientos/${id}/`),
};

export const reportesAPI = {
  getAll: (tipo = null, estado = null, formato = null) => {
    let url = '/reportes/';
    const params = new URLSearchParams();
    if (tipo) params.append('tipo', tipo);
    if (estado) params.append('estado', estado);
    if (formato) params.append('formato', formato);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },

  getById: (id) => api.get(`/reportes/${id}/`),

  create: (reporteData) => api.post('/reportes/', reporteData),

  update: (id, reporteData) => api.put(`/reportes/${id}/`, reporteData),

  delete: (id) => api.delete(`/reportes/${id}/`),
};

export const rolesAPI = {
  getAll: () => api.get('/roles/'),

  getById: (id) => api.get(`/roles/${id}/`),

  create: (tipo) => api.post('/roles/', { tipo }),

  update: (id, tipo) => api.put(`/roles/${id}/`, { tipo }),

  delete: (id) => api.delete(`/roles/${id}/`),
};

export const usuariosAPI = {
  getAll: () => api.get('/usuarios/'),

  getMe: () => api.get('/usuarios/me/'),

  getById: (id) => api.get(`/usuarios/${id}/`),

  create: (usuarioData) => api.post('/usuarios/', usuarioData),

  update: (id, usuarioData) => api.put(`/usuarios/${id}/`, usuarioData),

  delete: (id) => api.delete(`/usuarios/${id}/`),

  cambiarRol: async (id, user_id, nuevo_rol_id) => {
    // Primero solicitar token de verificación
    const verifResponse = await api.post('/auth/solicitar-verificacion-rol/');
    // Luego cambiar rol
    return api.post(`/usuarios/${id}/cambiar_rol/`, {
      user_id,
      nuevo_rol_id,
      token_verificacion: verifResponse.token,
    });
  },
};
