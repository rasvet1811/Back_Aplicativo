import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
superusers = User.objects.filter(is_superuser=True)

if superusers.exists():
    print("\n=== SUPERUSUARIOS ENCONTRADOS ===\n")
    for user in superusers:
        print(f"Username: {user.username}")
        print(f"Nombre: {user.nombre or 'Sin nombre'}")
        print(f"Email: {user.email or 'Sin email'}")
        print(f"Es superusuario: {user.is_superuser}")
        print("-" * 40)
else:
    print("\n⚠️ No se encontraron superusuarios.")
    print("Necesitas crear uno con: python manage.py createsuperuser\n")

