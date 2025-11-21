#!/usr/bin/env python
"""
Script para generar tokens manualmente para usuarios
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import User, ExpiringToken

def generar_token_para_usuario(username):
    """Genera un token para un usuario específico"""
    try:
        user = User.objects.get(username=username)
        
        # Eliminar token existente si existe
        try:
            old_token = ExpiringToken.objects.get(user=user)
            old_token.delete()
            print(f"Token anterior eliminado para {username}")
        except ExpiringToken.DoesNotExist:
            pass
        
        # Crear nuevo token
        token = ExpiringToken.objects.create(user=user)
        print(f"\n✅ Token generado para usuario: {username}")
        print(f"   Token: {token.key}")
        print(f"   Usuario ID: {user.id}")
        print(f"   Nombre: {user.nombre}")
        print(f"   Rol: {user.rol.tipo if user.rol else 'Sin rol'}")
        print(f"\n   Usa este token en el header:")
        print(f"   Authorization: Token {token.key}")
        
        return token.key
    except User.DoesNotExist:
        print(f"❌ Error: Usuario '{username}' no existe")
        return None

def listar_usuarios_con_tokens():
    """Lista todos los usuarios y sus tokens"""
    print("\n📋 Usuarios y sus tokens:\n")
    usuarios = User.objects.all()
    
    if not usuarios.exists():
        print("No hay usuarios en el sistema")
        return
    
    for user in usuarios:
        try:
            token = ExpiringToken.objects.get(user=user)
            expirado = "❌ EXPIRADO" if token.is_expired() else "✅ Válido"
            print(f"Usuario: {user.username} ({user.nombre})")
            print(f"  Token: {token.key}")
            print(f"  Estado: {expirado}")
            print(f"  Creado: {token.fecha_creacion}")
            print()
        except ExpiringToken.DoesNotExist:
            print(f"Usuario: {user.username} ({user.nombre})")
            print(f"  Token: ❌ No tiene token")
            print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # Generar token para usuario específico
        username = sys.argv[1]
        generar_token_para_usuario(username)
    else:
        # Listar todos los usuarios y tokens
        listar_usuarios_con_tokens()
        print("\n💡 Para generar un token para un usuario específico:")
        print("   python generar_tokens.py nombre_usuario")




