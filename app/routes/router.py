"""
Router.py - Sistema de Gestión de Archivos para FastAPI
========================================================
Este módulo proporciona endpoints para manejar la carga de 10 tipos diferentes
de archivos con validación y procesamiento específico para cada tipo.

Tipos de archivos soportados:
1. Imágenes (JPG, PNG, GIF)
2. Videos (MP4, AVI, MOV)
3. Archivos ZIP
4. Documentos PDF
5. Archivos Excel (XLSX, XLS)
6. Archivos CSV
7. Documentos Word (DOCX)
8. Audio (MP3, WAV)
9. Archivos JSON
10. Archivos XML
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import zipfile
import csv
import json
import xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image
import mimetypes
from datetime import datetime

# Configuración del router
router = APIRouter(
    prefix="/files",
    tags=["File Management"]
)

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

# Tamaños máximos permitidos por tipo de archivo (en bytes)
MAX_FILE_SIZE = {
    "image": 10 * 1024 * 1024,      # 10 MB para imágenes
    "video": 100 * 1024 * 1024,     # 100 MB para videos
    "zip": 50 * 1024 * 1024,        # 50 MB para archivos ZIP
    "pdf": 20 * 1024 * 1024,        # 20 MB para PDFs
    "excel": 15 * 1024 * 1024,      # 15 MB para Excel
    "csv": 10 * 1024 * 1024,        # 10 MB para CSV
    "word": 15 * 1024 * 1024,       # 15 MB para Word
    "audio": 30 * 1024 * 1024,      # 30 MB para audio
    "json": 5 * 1024 * 1024,        # 5 MB para JSON
    "xml": 5 * 1024 * 1024          # 5 MB para XML
}

# Extensiones permitidas por tipo
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif"],
    "video": [".mp4", ".avi", ".mov", ".mkv"],
    "zip": [".zip"],
    "pdf": [".pdf"],
    "excel": [".xlsx", ".xls"],
    "csv": [".csv"],
    "word": [".docx", ".doc"],
    "audio": [".mp3", ".wav", ".ogg"],
    "json": [".json"],
    "xml": [".xml"]
}

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def validate_file_size(file_content: bytes, file_type: str) -> bool:
    """
    Valida que el tamaño del archivo no exceda el límite establecido.
    
    Args:
        file_content: Contenido del archivo en bytes
        file_type: Tipo de archivo según ALLOWED_EXTENSIONS
        
    Returns:
        bool: True si el tamaño es válido, False en caso contrario
    """
    return len(file_content) <= MAX_FILE_SIZE.get(file_type, 5 * 1024 * 1024)


def validate_file_extension(filename: str, file_type: str) -> bool:
    """
    Valida que la extensión del archivo sea permitida para su tipo.
    
    Args:
        filename: Nombre del archivo
        file_type: Tipo de archivo según ALLOWED_EXTENSIONS
        
    Returns:
        bool: True si la extensión es válida, False en caso contrario
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, [])


def generate_response(
    success: bool,
    message: str,
    data: Dict[str, Any] = None
) -> JSONResponse:
    """
    Genera una respuesta JSON estandarizada.
    
    Args:
        success: Indica si la operación fue exitosa
        message: Mensaje descriptivo
        data: Datos adicionales a incluir en la respuesta
        
    Returns:
        JSONResponse: Respuesta formateada
    """
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data:
        response["data"] = data
    return JSONResponse(content=response)


# ============================================================================
# 1. ENDPOINT PARA IMÁGENES
# ============================================================================

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos de imagen (JPG, PNG, GIF).
    Valida el formato y proporciona información sobre dimensiones.
    
    Args:
        file: Archivo de imagen subido
        
    Returns:
        JSONResponse con información de la imagen procesada
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "image"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS['image'])}"
            )
        
        # Leer contenido del archivo
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "image"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['image'] / (1024*1024)}MB"
            )
        
        # Procesar imagen con PIL
        image = Image.open(BytesIO(contents))
        
        # Extraer información de la imagen
        image_info = {
            "filename": file.filename,
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2)
        }
        
        return generate_response(
            success=True,
            message="Imagen procesada exitosamente",
            data=image_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar imagen: {str(e)}"
        )


# ============================================================================
# 2. ENDPOINT PARA VIDEOS
# ============================================================================

@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos de video (MP4, AVI, MOV).
    Valida el formato y tamaño del archivo.
    
    Args:
        file: Archivo de video subido
        
    Returns:
        JSONResponse con información del video
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "video"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS['video'])}"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "video"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['video'] / (1024*1024)}MB"
            )
        
        video_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2)
        }
        
        return generate_response(
            success=True,
            message="Video cargado exitosamente",
            data=video_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar video: {str(e)}"
        )


# ============================================================================
# 3. ENDPOINT PARA ARCHIVOS ZIP
# ============================================================================

@router.post("/upload/zip")
async def upload_zip(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos ZIP.
    Lista el contenido del archivo comprimido.
    
    Args:
        file: Archivo ZIP subido
        
    Returns:
        JSONResponse con lista de archivos contenidos en el ZIP
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "zip"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos .zip"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "zip"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['zip'] / (1024*1024)}MB"
            )
        
        # Analizar contenido del ZIP
        with zipfile.ZipFile(BytesIO(contents)) as zip_file:
            file_list = []
            for info in zip_file.filelist:
                file_list.append({
                    "filename": info.filename,
                    "size_bytes": info.file_size,
                    "compressed_size": info.compress_size,
                    "compression_ratio": round((1 - info.compress_size / info.file_size) * 100, 2) if info.file_size > 0 else 0
                })
        
        zip_info = {
            "filename": file.filename,
            "total_files": len(file_list),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "files": file_list
        }
        
        return generate_response(
            success=True,
            message="Archivo ZIP procesado exitosamente",
            data=zip_info
        )
        
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo ZIP corrupto o inválido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar ZIP: {str(e)}"
        )


# ============================================================================
# 4. ENDPOINT PARA ARCHIVOS PDF
# ============================================================================

@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos PDF.
    Valida el formato y proporciona información básica del documento.
    
    Args:
        file: Archivo PDF subido
        
    Returns:
        JSONResponse con información del PDF
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos .pdf"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "pdf"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['pdf'] / (1024*1024)}MB"
            )
        
        # Validar que sea un PDF válido (verifica header)
        if not contents.startswith(b'%PDF'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no es un PDF válido"
            )
        
        pdf_info = {
            "filename": file.filename,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "is_valid": True
        }
        
        return generate_response(
            success=True,
            message="PDF cargado exitosamente",
            data=pdf_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar PDF: {str(e)}"
        )


# ============================================================================
# 5. ENDPOINT PARA ARCHIVOS EXCEL
# ============================================================================

@router.post("/upload/excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos Excel (XLSX, XLS).
    Proporciona información sobre hojas y estructura del archivo.
    
    Args:
        file: Archivo Excel subido
        
    Returns:
        JSONResponse con información del archivo Excel
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "excel"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS['excel'])}"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "excel"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['excel'] / (1024*1024)}MB"
            )
        
        excel_info = {
            "filename": file.filename,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "extension": os.path.splitext(file.filename)[1]
        }
        
        return generate_response(
            success=True,
            message="Archivo Excel cargado exitosamente",
            data=excel_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar Excel: {str(e)}"
        )


# ============================================================================
# 6. ENDPOINT PARA ARCHIVOS CSV
# ============================================================================

@router.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos CSV.
    Analiza la estructura y proporciona información sobre columnas y filas.
    
    Args:
        file: Archivo CSV subido
        
    Returns:
        JSONResponse con información del CSV y preview de datos
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos .csv"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "csv"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['csv'] / (1024*1024)}MB"
            )
        
        # Decodificar y analizar CSV
        text_content = contents.decode('utf-8')
        csv_reader = csv.reader(text_content.splitlines())
        
        rows = list(csv_reader)
        headers = rows[0] if rows else []
        
        csv_info = {
            "filename": file.filename,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "total_rows": len(rows),
            "total_columns": len(headers),
            "columns": headers,
            "preview_rows": rows[1:6] if len(rows) > 1 else []  # Primeras 5 filas de datos
        }
        
        return generate_response(
            success=True,
            message="CSV procesado exitosamente",
            data=csv_info
        )
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo CSV tiene una codificación no válida. Use UTF-8"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar CSV: {str(e)}"
        )


# ============================================================================
# 7. ENDPOINT PARA ARCHIVOS WORD
# ============================================================================

@router.post("/upload/word")
async def upload_word(file: UploadFile = File(...)):
    """
    Endpoint para cargar documentos Word (DOCX, DOC).
    Valida el formato y proporciona información básica.
    
    Args:
        file: Archivo Word subido
        
    Returns:
        JSONResponse con información del documento
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "word"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS['word'])}"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "word"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['word'] / (1024*1024)}MB"
            )
        
        word_info = {
            "filename": file.filename,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "extension": os.path.splitext(file.filename)[1]
        }
        
        return generate_response(
            success=True,
            message="Documento Word cargado exitosamente",
            data=word_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar documento Word: {str(e)}"
        )


# ============================================================================
# 8. ENDPOINT PARA ARCHIVOS DE AUDIO
# ============================================================================

@router.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos de audio (MP3, WAV, OGG).
    Valida el formato y proporciona información del archivo.
    
    Args:
        file: Archivo de audio subido
        
    Returns:
        JSONResponse con información del audio
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "audio"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no permitido. Use: {', '.join(ALLOWED_EXTENSIONS['audio'])}"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "audio"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['audio'] / (1024*1024)}MB"
            )
        
        audio_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "extension": os.path.splitext(file.filename)[1]
        }
        
        return generate_response(
            success=True,
            message="Archivo de audio cargado exitosamente",
            data=audio_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar audio: {str(e)}"
        )


# ============================================================================
# 9. ENDPOINT PARA ARCHIVOS JSON
# ============================================================================

@router.post("/upload/json")
async def upload_json(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos JSON.
    Valida la estructura y proporciona información sobre el contenido.
    
    Args:
        file: Archivo JSON subido
        
    Returns:
        JSONResponse con información del JSON y preview
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "json"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos .json"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "json"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['json'] / (1024*1024)}MB"
            )
        
        # Parsear JSON
        try:
            json_data = json.loads(contents.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON inválido: {str(e)}"
            )
        
        # Determinar tipo de estructura
        data_type = type(json_data).__name__
        
        json_info = {
            "filename": file.filename,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "data_type": data_type,
            "is_valid": True
        }
        
        # Agregar información específica según el tipo
        if isinstance(json_data, dict):
            json_info["keys"] = list(json_data.keys())
            json_info["key_count"] = len(json_data.keys())
        elif isinstance(json_data, list):
            json_info["array_length"] = len(json_data)
        
        return generate_response(
            success=True,
            message="JSON procesado exitosamente",
            data=json_info
        )
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo JSON tiene una codificación no válida. Use UTF-8"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar JSON: {str(e)}"
        )


# ============================================================================
# 10. ENDPOINT PARA ARCHIVOS XML
# ============================================================================

@router.post("/upload/xml")
async def upload_xml(file: UploadFile = File(...)):
    """
    Endpoint para cargar archivos XML.
    Valida la estructura y proporciona información sobre el contenido.
    
    Args:
        file: Archivo XML subido
        
    Returns:
        JSONResponse con información del XML
    """
    try:
        # Validar extensión
        if not validate_file_extension(file.filename, "xml"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos .xml"
            )
        
        # Leer contenido
        contents = await file.read()
        
        # Validar tamaño
        if not validate_file_size(contents, "xml"):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE['xml'] / (1024*1024)}MB"
            )
        
        # Parsear XML
        try:
            root = ET.fromstring(contents.decode('utf-8'))
        except ET.ParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"XML inválido: {str(e)}"
            )
        
        # Obtener información del XML
        def count_elements(element):
            """Cuenta recursivamente todos los elementos"""
            count = 1
            for child in element:
                count += count_elements(child)
            return count
        
        xml_info = {
            "filename": file.filename,
            "size_bytes": len(contents),
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "root_tag": root.tag,
            "total_elements": count_elements(root),
            "root_attributes": dict(root.attrib),
            "is_valid": True
        }
        
        return generate_response(
            success=True,
            message="XML procesado exitosamente",
            data=xml_info
        )
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo XML tiene una codificación no válida. Use UTF-8"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar XML: {str(e)}"
        )


# ============================================================================
# ENDPOINT DE INFORMACIÓN GENERAL
# ============================================================================

@router.get("/info")
async def get_upload_info():
    """
    Endpoint que proporciona información sobre los tipos de archivos
    soportados y sus límites de tamaño.
    
    Returns:
        JSONResponse con información de configuración
    """
    info = {
        "supported_types": {
            file_type: {
                "extensions": extensions,
                "max_size_mb": MAX_FILE_SIZE[file_type] / (1024 * 1024)
            }
            for file_type, extensions in ALLOWED_EXTENSIONS.items()
        }
    }
    
    return generate_response(
        success=True,
        message="Información de tipos de archivos soportados",
        data=info
    )


# ============================================================================
# ENDPOINT PARA CARGA MÚLTIPLE
# ============================================================================

@router.post("/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Endpoint para cargar múltiples archivos de cualquier tipo soportado.
    Procesa cada archivo según su tipo.
    
    Args:
        files: Lista de archivos subidos
        
    Returns:
        JSONResponse con el resultado del procesamiento de cada archivo
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 10 archivos por solicitud"
        )
    
    results = []
    
    for file in files:
        try:
            ext = os.path.splitext(file.filename)[1].lower()
            contents = await file.read()
            
            # Determinar tipo de archivo
            file_type = None
            for ftype, extensions in ALLOWED_EXTENSIONS.items():
                if ext in extensions:
                    file_type = ftype
                    break
            
            if not file_type:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "Tipo de archivo no soportado"
                })
                continue
            
            # Validar tamaño
            if not validate_file_size(contents, file_type):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Archivo demasiado grande. Máximo: {MAX_FILE_SIZE[file_type] / (1024*1024)}MB"
                })
                continue
            
            results.append({
                "filename": file.filename,
                "success": True,
                "file_type": file_type,
                "size_mb": round(len(contents) / (1024 * 1024), 2)
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return generate_response(
        success=True,
        message=f"Procesados {len(results)} archivos",
        data={"results": results}
    )