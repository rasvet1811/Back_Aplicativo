#!/usr/bin/env python
"""
Script para limpiar tokens duplicados en la base de datos
Ejecutar: python limpiar_tokens_duplicados.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import ExpiringToken, User
from django.db.models import Count

def limpiar_tokens_duplicados():
    """Elimina tokens duplicados, dejando solo el más reciente para cada usuario"""
    print("🔍 Buscando tokens duplicados...\n")
    
    # Encontrar usuarios con múltiples tokens
    usuarios_con_multiples_tokens = (
        ExpiringToken.objects
        .values('user')
        .annotate(count=Count('user'))
        .filter(count__gt=1)
    )
    
    if not usuarios_con_multiples_tokens:
        print("✅ No se encontraron tokens duplicados.")
        return
    
    print(f"⚠️  Se encontraron {len(usuarios_con_multiples_tokens)} usuarios con múltiples tokens.\n")
    
    total_eliminados = 0
    
    for item in usuarios_con_multiples_tokens:
        user_id = item['user']
        count = item['count']
        
        try:
            user = User.objects.get(id=user_id)
            tokens = ExpiringToken.objects.filter(user=user).order_by('-fecha_creacion')
            
            # Mantener solo el más reciente
            token_mas_reciente = tokens.first()
            tokens_a_eliminar = tokens.exclude(id=token_mas_reciente.id)
            
            cantidad_eliminar = tokens_a_eliminar.count()
            tokens_a_eliminar.delete()
            
            total_eliminados += cantidad_eliminar
            
            print(f"  Usuario: {user.username} ({user.nombre})")
            print(f"    Tokens encontrados: {count}")
            print(f"    Tokens eliminados: {cantidad_eliminar}")
            print(f"    Token mantenido: {token_mas_reciente.key[:20]}...")
            print()
            
        except User.DoesNotExist:
            print(f"  ⚠️  Usuario con ID {user_id} no existe, eliminando tokens huérfanos...")
            ExpiringToken.objects.filter(user_id=user_id).delete()
            total_eliminados += count
            print()
    
    print(f"✅ Limpieza completada. Total de tokens eliminados: {total_eliminados}")
    print("\n💡 Ahora puedes hacer login sin problemas.")

if __name__ == '__main__':
    try:
        limpiar_tokens_duplicados()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()




