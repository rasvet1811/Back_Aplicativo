"""
Script para probar la creación de comentarios y diagnosticar errores
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Comentario, Caso, User
from django.db import connection

print("=" * 50)
print("DIAGNÓSTICO DE COMENTARIOS")
print("=" * 50)

# 1. Verificar que la tabla existe
print("\n1. Verificando tabla 'comentario'...")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'comentario'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    if columns:
        print("   ✓ Tabla existe. Columnas:")
        for col in columns:
            print(f"     - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    else:
        print("   ✗ Tabla 'comentario' NO existe en la base de datos")
        exit(1)

# 2. Verificar que hay casos disponibles
print("\n2. Verificando casos disponibles...")
casos = Caso.objects.all()[:5]
if casos.exists():
    print(f"   ✓ Hay {Caso.objects.count()} casos en total. Primeros 5:")
    for caso in casos:
        print(f"     - Caso ID: {caso.id_caso}")
else:
    print("   ✗ No hay casos en la base de datos")
    exit(1)

# 3. Verificar que hay usuarios disponibles
print("\n3. Verificando usuarios disponibles...")
usuarios = User.objects.all()[:5]
if usuarios.exists():
    print(f"   ✓ Hay {User.objects.count()} usuarios en total. Primeros 5:")
    for usuario in usuarios:
        print(f"     - Usuario ID: {usuario.id}, Username: {usuario.username}")
else:
    print("   ✗ No hay usuarios en la base de datos")
    exit(1)

# 4. Intentar crear un comentario directamente
print("\n4. Intentando crear un comentario directamente...")
try:
    primer_caso = Caso.objects.first()
    primer_usuario = User.objects.first()
    
    if not primer_caso:
        print("   ✗ No hay casos disponibles")
        exit(1)
    if not primer_usuario:
        print("   ✗ No hay usuarios disponibles")
        exit(1)
    
    comentario = Comentario.objects.create(
        caso=primer_caso,
        usuario=primer_usuario,
        comentario="Comentario de prueba desde script"
    )
    print(f"   ✓ Comentario creado exitosamente!")
    print(f"     - ID: {comentario.id_comentario}")
    print(f"     - Caso: {comentario.caso.id_caso}")
    print(f"     - Usuario: {comentario.usuario.username if comentario.usuario else 'None'}")
    print(f"     - Comentario: {comentario.comentario[:50]}...")
    
    # Eliminar el comentario de prueba
    comentario.delete()
    print("   ✓ Comentario de prueba eliminado")
    
except Exception as e:
    import traceback
    print(f"   ✗ Error al crear comentario: {str(e)}")
    print(f"   Traceback:")
    traceback.print_exc()
    exit(1)

# 5. Verificar la secuencia de PostgreSQL
print("\n5. Verificando secuencia de id_comentario...")
try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_default 
            FROM information_schema.columns 
            WHERE table_name = 'comentario' 
            AND column_name = 'id_comentario';
        """)
        result = cursor.fetchone()
        if result and result[0]:
            print(f"   ✓ Default: {result[0]}")
        else:
            print("   ⚠ No hay default configurado para id_comentario")
except Exception as e:
    print(f"   ⚠ Error al verificar secuencia: {str(e)}")

print("\n" + "=" * 50)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 50)

