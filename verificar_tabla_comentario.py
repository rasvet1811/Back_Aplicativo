"""
Script para verificar la estructura de la tabla comentario en PostgreSQL
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("=" * 60)
print("VERIFICACIÓN DE TABLA COMENTARIO")
print("=" * 60)

with connection.cursor() as cursor:
    # 1. Verificar columnas de la tabla comentario
    print("\n1. Columnas de la tabla 'comentario':")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'comentario'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    
    # 2. Verificar foreign keys
    print("\n2. Foreign Keys de la tabla 'comentario':")
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'comentario';
    """)
    fks = cursor.fetchall()
    for fk in fks:
        print(f"   - {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]}")
    
    # 3. Verificar si existe el caso 15
    print("\n3. Verificando caso 15:")
    cursor.execute('SELECT "Id_Caso" FROM "Caso" WHERE "Id_Caso" = 15')
    caso_15_mayus = cursor.fetchone()
    print(f"   - En tabla 'Caso' con 'Id_Caso': {caso_15_mayus is not None}")
    
    cursor.execute('SELECT id_caso FROM "Caso" WHERE id_caso = 15')
    caso_15_minus = cursor.fetchone()
    print(f"   - En tabla 'Caso' con 'id_caso': {caso_15_minus is not None}")
    
    # 4. Verificar estructura de tabla Caso
    print("\n4. Columnas de la tabla 'Caso' (primary key):")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'Caso' AND column_name LIKE '%caso%'
        ORDER BY ordinal_position;
    """)
    caso_cols = cursor.fetchall()
    for col in caso_cols:
        print(f"   - {col[0]}: {col[1]}")

print("\n" + "=" * 60)

