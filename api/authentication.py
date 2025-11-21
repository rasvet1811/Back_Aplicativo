from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from .models import ExpiringToken


class ExpiringTokenAuthentication(TokenAuthentication):
    """Autenticación personalizada con verificación de expiración"""
    model = ExpiringToken
    
    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Token inválido')
        
        if token.is_expired():
            token.delete()
            raise exceptions.AuthenticationFailed('Token expirado. Por favor, inicie sesión nuevamente.')
        
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('Usuario inactivo')
        
        # Actualizar última actividad
        token.save()
        
        return (token.user, token)

