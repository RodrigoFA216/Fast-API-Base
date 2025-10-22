"""
ai_routes.py - Router de Endpoints de IA con Google Gemini
===========================================================
Router que contiene todos los endpoints de análisis con IA usando Gemini.
Este archivo debe estar en app/routes/ai_routes.py
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime
from PIL import Image
from io import BytesIO
import json

# Importar el cliente Gemini desde el mismo directorio
from .gemini_api import GeminiAPI, GEMINI_MODELS

# ============================================================================
# CONFIGURACIÓN DEL ROUTER
# ============================================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI - Gemini"]
)

# Inicializar cliente Gemini (se compartirá entre todas las funciones)
try:
    gemini_client = GeminiAPI()
    print("✅ Cliente Gemini inicializado en ai_routes")
except ValueError as e:
    print(f"⚠️  Advertencia en ai_routes: {e}")
    gemini_client = None


# ============================================================================
# FUNCIÓN AUXILIAR PARA VALIDAR SERVICIO
# ============================================================================

def check_gemini_available():
    """Verifica que el servicio de Gemini esté disponible."""
    if not gemini_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de IA no disponible. Configure GOOGLE_API_KEY"
        )


# ============================================================================
# ENDPOINTS DE ANÁLISIS DE TEXTO
# ============================================================================

@router.post("/analyze-text", tags=["AI - Text Analysis"])
async def analyze_text_endpoint(
    text: str = Form(...),
    model: str = Form("flash"),
    temperature: float = Form(0.7)
):
    """
    Analiza texto usando Gemini.
    
    Args:
        text: Texto a analizar
        model: Modelo a usar ("pro" o "flash")
        temperature: Creatividad de la respuesta (0.0 - 1.0)
    """
    check_gemini_available()
    result = gemini_client.analyze_text(text, model, temperature)
    return JSONResponse(content=result)


@router.post("/chat", tags=["AI - Chat"])
async def chat_endpoint(
    message: str = Form(...),
    model: str = Form("flash"),
    clear_history: bool = Form(False)
):
    """
    Chat conversacional con historial.
    
    Args:
        message: Mensaje del usuario
        model: Modelo a usar
        clear_history: Limpiar historial antes de responder
    """
    check_gemini_available()
    result = gemini_client.chat(message, model, clear_history)
    return JSONResponse(content=result)


@router.get("/chat/history", tags=["AI - Chat"])
async def get_chat_history():
    """Obtiene el historial de conversación."""
    check_gemini_available()
    history = gemini_client.get_chat_history()
    return JSONResponse(content={
        "success": True,
        "history": history,
        "total_messages": len(history)
    })


@router.delete("/chat/history", tags=["AI - Chat"])
async def clear_chat_history():
    """Limpia el historial de conversación."""
    check_gemini_available()
    result = gemini_client.clear_chat_history()
    return JSONResponse(content=result)


# ============================================================================
# ENDPOINTS DE ANÁLISIS DE IMÁGENES
# ============================================================================

@router.post("/analyze-image", tags=["AI - Image Analysis"])
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form("Describe esta imagen en detalle")
):
    """
    Analiza una imagen usando Gemini Vision.
    
    Args:
        file: Imagen a analizar
        prompt: Instrucciones para el análisis
    """
    check_gemini_available()
    
    # Validar que sea una imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen"
        )
    
    contents = await file.read()
    result = gemini_client.analyze_image(contents, prompt, "bytes")
    
    return JSONResponse(content=result)


@router.post("/compare-images", tags=["AI - Image Analysis"])
async def compare_images_endpoint(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    comparison_prompt: str = Form("Compara estas dos imágenes")
):
    """
    Compara dos imágenes usando Gemini Vision.
    
    Args:
        image1: Primera imagen
        image2: Segunda imagen
        comparison_prompt: Instrucciones para la comparación
    """
    check_gemini_available()
    
    # Validar que ambos sean imágenes
    if not image1.content_type.startswith("image/") or not image2.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ambos archivos deben ser imágenes"
        )
    
    image1_data = await image1.read()
    image2_data = await image2.read()
    
    result = gemini_client.compare_images(image1_data, image2_data, comparison_prompt)
    
    return JSONResponse(content=result)


# ============================================================================
# ENDPOINTS DE ANÁLISIS DE DOCUMENTOS
# ============================================================================

@router.post("/analyze-document", tags=["AI - Document Analysis"])
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    analysis_type: str = Form("summary")
):
    """
    Analiza un documento de texto.
    
    Args:
        file: Archivo de texto (TXT, CSV, etc.)
        analysis_type: Tipo de análisis ("summary", "key_points", "sentiment", "entities")
    """
    check_gemini_available()
    
    try:
        contents = await file.read()
        text = contents.decode('utf-8')
        
        result = gemini_client.analyze_document(text, analysis_type)
        return JSONResponse(content=result)
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo decodificar el archivo. Use codificación UTF-8"
        )


@router.post("/extract-structured-data", tags=["AI - Document Analysis"])
async def extract_structured_data_endpoint(
    file: UploadFile = File(...),
    schema: str = Form(...)
):
    """
    Extrae información estructurada de un documento según un schema JSON.
    
    Args:
        file: Archivo de texto
        schema: Schema JSON con campos a extraer (formato: {"campo": "descripción"})
    """
    check_gemini_available()
    
    try:
        # Parsear schema
        schema_dict = json.loads(schema)
        
        # Leer archivo
        contents = await file.read()
        text = contents.decode('utf-8')
        
        result = gemini_client.extract_structured_data(text, schema_dict)
        return JSONResponse(content=result)
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schema inválido. Use formato JSON válido"
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo decodificar el archivo"
        )


# ============================================================================
# ENDPOINTS DE ANÁLISIS DE CSV/EXCEL
# ============================================================================

@router.post("/analyze-csv", tags=["AI - Data Analysis"])
async def analyze_csv_endpoint(
    file: UploadFile = File(...),
    question: str = Form("Analiza estos datos y proporciona insights")
):
    """
    Analiza un archivo CSV y responde preguntas sobre los datos.
    
    Args:
        file: Archivo CSV
        question: Pregunta o análisis solicitado
    """
    check_gemini_available()
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un CSV"
        )
    
    try:
        contents = await file.read()
        data_text = contents.decode('utf-8')
        
        result = gemini_client.analyze_tabular_data(data_text, question)
        return JSONResponse(content=result)
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al leer el archivo CSV"
        )


# ============================================================================
# ENDPOINTS DE PROCESAMIENTO DE TEXTO
# ============================================================================

@router.post("/sentiment", tags=["AI - Text Processing"])
async def analyze_sentiment_endpoint(
    text: str = Form(...),
    detailed: bool = Form(False)
):
    """
    Analiza el sentimiento de un texto.
    
    Args:
        text: Texto a analizar
        detailed: Análisis detallado con emociones
    """
    check_gemini_available()
    result = gemini_client.analyze_sentiment(text, detailed)
    return JSONResponse(content=result)


@router.post("/translate", tags=["AI - Text Processing"])
async def translate_endpoint(
    text: str = Form(...),
    target_language: str = Form(...),
    source_language: str = Form("auto")
):
    """
    Traduce texto a otro idioma.
    
    Args:
        text: Texto a traducir
        target_language: Idioma destino
        source_language: Idioma origen (auto para detectar)
    """
    check_gemini_available()
    result = gemini_client.translate_text(text, target_language, source_language)
    return JSONResponse(content=result)


@router.post("/summarize", tags=["AI - Text Processing"])
async def summarize_endpoint(
    text: str = Form(...),
    summary_length: str = Form("medium"),
    bullet_points: bool = Form(False)
):
    """
    Resume un texto.
    
    Args:
        text: Texto a resumir
        summary_length: Longitud ("short", "medium", "long")
        bullet_points: Formato de puntos clave
    """
    check_gemini_available()
    result = gemini_client.summarize_text(text, summary_length, bullet_points)
    return JSONResponse(content=result)


@router.post("/grammar-check", tags=["AI - Text Processing"])
async def grammar_check_endpoint(
    text: str = Form(...),
    language: str = Form("español")
):
    """
    Revisa gramática y ortografía.
    
    Args:
        text: Texto a revisar
        language: Idioma del texto
    """
    check_gemini_available()
    result = gemini_client.check_grammar(text, language)
    return JSONResponse(content=result)


# ============================================================================
# ENDPOINTS DE GENERACIÓN DE CONTENIDO
# ============================================================================

@router.post("/generate-content", tags=["AI - Content Generation"])
async def generate_content_endpoint(
    prompt: str = Form(...),
    content_type: str = Form("general"),
    temperature: float = Form(0.9)
):
    """
    Genera contenido creativo.
    
    Args:
        prompt: Descripción del contenido
        content_type: Tipo ("story", "poem", "article", "code", "general")
        temperature: Nivel de creatividad (0.0 - 1.0)
    """
    check_gemini_available()
    result = gemini_client.generate_creative_content(prompt, content_type, temperature)
    return JSONResponse(content=result)


@router.post("/embeddings", tags=["AI - Content Generation"])
async def generate_embeddings_endpoint(
    texts: List[str] = Form(...),
    task_type: str = Form("retrieval_document")
):
    """
    Genera embeddings para búsqueda semántica.
    
    Args:
        texts: Lista de textos
        task_type: Tipo de tarea
    """
    check_gemini_available()
    result = gemini_client.generate_embeddings(texts, task_type)
    return JSONResponse(content=result)


# ============================================================================
# ENDPOINTS COMBINADOS - ARCHIVO + IA
# ============================================================================

@router.post("/combined/image-analysis", tags=["Combined - File + AI"])
async def combined_image_analysis(
    file: UploadFile = File(...),
    ai_prompt: str = Form("Analiza esta imagen y proporciona insights detallados")
):
    """
    Endpoint combinado: Sube una imagen y la analiza con IA en un solo paso.
    """
    check_gemini_available()
    
    # Validar imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser una imagen"
        )
    
    # Procesar imagen
    contents = await file.read()
    
    # Información de la imagen
    image = Image.open(BytesIO(contents))
    file_info = {
        "filename": file.filename,
        "format": image.format,
        "size": f"{image.width}x{image.height}",
        "size_mb": round(len(contents) / (1024 * 1024), 2)
    }
    
    # Análisis con IA
    ai_result = gemini_client.analyze_image(contents, ai_prompt, "bytes")
    
    return JSONResponse(content={
        "success": True,
        "file_info": file_info,
        "ai_analysis": ai_result,
        "timestamp": datetime.utcnow().isoformat()
    })


@router.post("/combined/document-analysis", tags=["Combined - File + AI"])
async def combined_document_analysis(
    file: UploadFile = File(...),
    analysis_type: str = Form("summary")
):
    """
    Endpoint combinado: Sube un documento y obtén análisis con IA.
    """
    check_gemini_available()
    
    try:
        contents = await file.read()
        text = contents.decode('utf-8')
        
        # Información del archivo
        file_info = {
            "filename": file.filename,
            "size_mb": round(len(contents) / (1024 * 1024), 2),
            "character_count": len(text),
            "word_count": len(text.split())
        }
        
        # Análisis con IA
        ai_result = gemini_client.analyze_document(text, analysis_type)
        
        return JSONResponse(content={
            "success": True,
            "file_info": file_info,
            "ai_analysis": ai_result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al decodificar el archivo"
        )


# ============================================================================
# ENDPOINTS DE INFORMACIÓN
# ============================================================================

@router.get("/models", tags=["AI - Info"])
async def list_models():
    """Lista los modelos disponibles de Gemini."""
    return {
        "success": True,
        "models": GEMINI_MODELS,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status", tags=["AI - Info"])
async def gemini_status():
    """Verifica el estado del servicio de Gemini."""
    return {
        "success": True,
        "gemini_available": gemini_client is not None,
        "timestamp": datetime.utcnow().isoformat()
    }