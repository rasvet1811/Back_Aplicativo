"""
Servicio centralizado para subida, descarga y eliminación de documentos.
- Archivos en ruta privada (no servidos por URL directa).
- Nombre físico UUID; solo metadata en BD.
- Checksum SHA-256 y auditoría obligatoria.
"""
import os
import uuid
import hashlib
import logging
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


def get_document_storage_root():
    """Ruta raíz privada de almacenamiento de documentos (no pública)."""
    root = getattr(settings, 'DOCUMENT_STORAGE_ROOT', None)
    if root is None:
        root = os.path.join(settings.BASE_DIR, 'documentos_privados')
    if isinstance(root, str):
        root = os.path.abspath(root)
    return root


def _ensure_storage_dir():
    """Asegura que exista el directorio de almacenamiento."""
    root = get_document_storage_root()
    os.makedirs(root, exist_ok=True)
    return root


def compute_sha256(file_path_or_content):
    """
    Calcula SHA-256 de un archivo (ruta) o de contenido en memoria.
    Retorna string hex de 64 caracteres.
    """
    hasher = hashlib.sha256()
    if isinstance(file_path_or_content, (str, os.PathLike)) and os.path.isfile(file_path_or_content):
        with open(file_path_or_content, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    else:
        if hasattr(file_path_or_content, 'read'):
            for chunk in iter(lambda: file_path_or_content.read(8192), b''):
                hasher.update(chunk)
            file_path_or_content.seek(0)
        else:
            hasher.update(file_path_or_content)
    return hasher.hexdigest()


def save_uploaded_file(uploaded_file, nombre_logico=None):
    """
    Guarda un archivo subido en la ruta privada con nombre físico UUID.
    No guarda nada en la BD.
    Returns: dict con ruta_relativa, extension, tamano_bytes, checksum_sha256
    """
    if not uploaded_file or not hasattr(uploaded_file, 'read'):
        raise ValueError("Se requiere un archivo subido válido")
    root = _ensure_storage_dir()
    ext = ""
    if nombre_logico and "." in nombre_logico:
        ext = "." + nombre_logico.rsplit(".", 1)[-1].lower()
    elif getattr(uploaded_file, 'name', None) and "." in uploaded_file.name:
        ext = "." + uploaded_file.name.rsplit(".", 1)[-1].lower()
    nombre_fisico = f"{uuid.uuid4().hex}{ext}"
    ruta_completa = os.path.join(root, nombre_fisico)
    # Guardar archivo en disco
    with open(ruta_completa, 'wb') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)
    tamano = os.path.getsize(ruta_completa)
    checksum = compute_sha256(ruta_completa)
    ruta_relativa = nombre_fisico
    extension = ext.lstrip(".") if ext else None
    return {
        "ruta": ruta_relativa,
        "extension": extension,
        "tamano_bytes": tamano,
        "checksum_sha256": checksum,
    }


def get_document_file_path(documento):
    """
    Obtiene la ruta absoluta en disco del archivo de un documento.
    documento.ruta debe ser el nombre relativo (UUID.ext).
    Returns: str path absoluto o None si no existe.
    """
    if not documento or not documento.ruta:
        return None
    root = get_document_storage_root()
    # Evitar path traversal
    nombre = os.path.basename(documento.ruta.strip())
    if not nombre:
        return None
    path = os.path.join(root, nombre)
    if not os.path.abspath(path).startswith(os.path.abspath(root)):
        return None
    return path if os.path.isfile(path) else None


def delete_document_file(documento):
    """
    Elimina el archivo físico del documento si existe.
    No borra el registro en BD ni registra auditoría (eso lo hace la vista).
    """
    path = get_document_file_path(documento)
    if path and os.path.isfile(path):
        try:
            os.remove(path)
            logger.info("Archivo eliminado: %s", path)
        except OSError as e:
            logger.warning("No se pudo eliminar archivo %s: %s", path, e)


def registrar_auditoria_documento(accion, documento, usuario, request=None):
    """
    Registra una acción en Auditoria_Documento.
    accion: 'SUBIDA' | 'DESCARGA' | 'ELIMINADO'
    """
    from .models import AuditoriaDocumento
    ip = None
    if request:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            ip = xff.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
    AuditoriaDocumento.objects.create(
        documento=documento,
        usuario=usuario,
        accion=accion,
        ip_origen=ip,
    )


def user_can_access_document(user, documento):
    """
    Valida permisos usando Rol y Nivel_Sensibilidad.
    - Administrador y THA: autorización total (ver, descargar, eliminar cualquier documento).
    - PUBLICO: cualquier usuario autenticado puede acceder.
    - CONFIDENCIAL: Admin, THA, responsable del caso o creador del documento.
    - RESTRINGIDO: solo Administrador o THA (además del acceso total anterior).
    """
    if not user or not user.is_authenticated:
        return False
    from .models import User
    try:
        user = User.objects.select_related('rol').get(pk=user.pk)
    except User.DoesNotExist:
        return False
    rol_tipo = (user.rol.tipo or '').lower() if user.rol else ''
    is_admin_or_tha = rol_tipo in ('administrador', 'tha')
    # Administrador y THA tienen autorización total sobre todos los documentos
    if is_admin_or_tha:
        return True
    nivel = (documento.nivel_sensibilidad or 'CONFIDENCIAL').upper()
    if nivel == 'PUBLICO':
        return True
    if nivel == 'RESTRINGIDO':
        return False
    if nivel == 'CONFIDENCIAL':
        if documento.caso and documento.caso.responsable_id == user.pk:
            return True
        if documento.usuario_creador_id == user.pk:
            return True
        return False
    return False
