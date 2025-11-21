/**
 * Hook personalizado para manejar la autenticación
 * Proporciona funciones y estado para login, logout y verificación de tokens
 */

import { useState, useEffect, useCallback } from 'react';
import { authService } from '../services/api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Verificar autenticación al cargar
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = authService.getToken();
        if (token) {
          const validation = await authService.verifyToken();
          if (validation.valido) {
            setUser(validation.user);
            setIsAuthenticated(true);
          } else {
            // Token inválido, limpiar
            authService.logout();
            setUser(null);
            setIsAuthenticated(false);
          }
        } else {
          setUser(null);
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Error al verificar autenticación:', error);
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();

    // Escuchar eventos de expiración de token
    const handleTokenExpired = () => {
      setUser(null);
      setIsAuthenticated(false);
    };

    window.addEventListener('token-expired', handleTokenExpired);

    // Validar token periódicamente (cada 5 minutos)
    const validationInterval = setInterval(async () => {
      if (authService.isAuthenticated()) {
        const validation = await authService.verifyToken();
        if (validation.valido) {
          setUser(validation.user);
        } else {
          handleTokenExpired();
        }
      }
    }, 5 * 60 * 1000); // 5 minutos

    return () => {
      window.removeEventListener('token-expired', handleTokenExpired);
      clearInterval(validationInterval);
    };
  }, []);

  /**
   * Función para iniciar sesión
   */
  const login = useCallback(async (username, password) => {
    try {
      setLoading(true);
      const response = await authService.login(username, password);
      setUser(response.user);
      setIsAuthenticated(true);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error en login:', error);
      return {
        success: false,
        error: error.mensaje || error.message || 'Error al iniciar sesión',
      };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Función para cerrar sesión
   */
  const logout = useCallback(async () => {
    try {
      setLoading(true);
      await authService.logout();
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Error en logout:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Función para verificar el token manualmente
   */
  const verifyToken = useCallback(async () => {
    try {
      const validation = await authService.verifyToken();
      if (validation.valido) {
        setUser(validation.user);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
      return validation;
    } catch (error) {
      console.error('Error al verificar token:', error);
      setUser(null);
      setIsAuthenticated(false);
      return { valido: false };
    }
  }, []);

  /**
   * Función para renovar el token
   */
  const renewToken = useCallback(async () => {
    try {
      const response = await authService.renewToken();
      setUser(response.user);
      setIsAuthenticated(true);
      return { success: true, data: response };
    } catch (error) {
      console.error('Error al renovar token:', error);
      setUser(null);
      setIsAuthenticated(false);
      return {
        success: false,
        error: error.mensaje || error.message || 'Error al renovar token',
      };
    }
  }, []);

  return {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    verifyToken,
    renewToken,
  };
};




