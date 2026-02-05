# Migración: documento sin archivo binario, campos Nivel_Sensibilidad/Tamano_Bytes/Checksum_SHA256, tabla Auditoria_Documento
# Si en PostgreSQL ya existen las columnas o la tabla, puedes hacer: python manage.py migrate api 0010 --fake

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_alter_documento_caso'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documento',
            name='archivo',
        ),
        migrations.AddField(
            model_name='documento',
            name='nivel_sensibilidad',
            field=models.CharField(
                choices=[('PUBLICO', 'Público'), ('CONFIDENCIAL', 'Confidencial'), ('RESTRINGIDO', 'Restringido')],
                db_column='Nivel_Sensibilidad',
                default='CONFIDENCIAL',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='documento',
            name='tamano_bytes',
            field=models.BigIntegerField(blank=True, db_column='Tamano_Bytes', null=True),
        ),
        migrations.AddField(
            model_name='documento',
            name='checksum_sha256',
            field=models.CharField(blank=True, db_column='Checksum_SHA256', max_length=64, null=True),
        ),
        migrations.CreateModel(
            name='AuditoriaDocumento',
            fields=[
                ('id_auditoria', models.AutoField(db_column='Id_Auditoria', primary_key=True, serialize=False)),
                ('accion', models.CharField(
                    choices=[('SUBIDA', 'Subida'), ('DESCARGA', 'Descarga'), ('ELIMINADO', 'Eliminado')],
                    db_column='Accion',
                    max_length=20,
                )),
                ('fecha', models.DateTimeField(auto_now_add=True, db_column='Fecha')),
                ('ip_origen', models.GenericIPAddressField(blank=True, db_column='Ip_Origen', null=True)),
                ('documento', models.ForeignKey(
                    db_column='Id_Documento',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='auditorias',
                    to='api.documento',
                )),
                ('usuario', models.ForeignKey(
                    db_column='Id_Usuario',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='auditorias_documento',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'Auditoria_Documento',
                'ordering': ['-fecha'],
                'verbose_name': 'Auditoría de documento',
                'verbose_name_plural': 'Auditorías de documentos',
            },
        ),
    ]
