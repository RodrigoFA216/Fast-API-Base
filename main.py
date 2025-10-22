"""
main.py - Aplicación Principal FastAPI + Google Gemini
=======================================================
Punto de entrada principal que integra todos los routers:
- Router de archivos (manejo de 10 tipos de archivos)
- Router de IA (endpoints de análisis con Gemini)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Importar todos los routers
from app.routes.router import router as files_router
from app.routes.ai_routes import router as ai_router

# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================

app = FastAPI(
    title="API REST - Segmentation Endoscope Application + Gemini AI",
    description="Sistema de gestión de archivos con análisis de IA usando Google Gemini",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CONFIGURACIÓN DE CORS
# ============================================================================

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*",  # En producción, reemplaza con dominios específicos
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# INCLUIR ROUTERS
# ============================================================================

# Router de manejo de archivos (10 tipos de archivos)
# Rutas: /files/*
app.include_router(files_router)

# Router de análisis con IA (Gemini)
# Rutas: /ai/*
app.include_router(ai_router)

# ============================================================================
# ENDPOINTS RAÍZ Y SALUD
# ============================================================================

@app.get(
    "/",
    status_code=200,
    response_description="Información de la API",
    tags=["Info"],
)
def root():
    """Endpoint raíz con información general de la API."""
    return {
        "message": "API REST - Segmentation Endoscope Application + Gemini AI",
        "version": "2.0.0",
        "status": "active",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "available_routes": {
            "files": {
                "description": "Manejo de 10 tipos de archivos diferentes",
                "endpoints": [
                    "/files/upload/image",
                    "/files/upload/video",
                    "/files/upload/zip",
                    "/files/upload/pdf",
                    "/files/upload/excel",
                    "/files/upload/csv",
                    "/files/upload/word",
                    "/files/upload/audio",
                    "/files/upload/json",
                    "/files/upload/xml",
                    "/files/upload/multiple",
                    "/files/info"
                ]
            },
            "ai": {
                "description": "Análisis con IA usando Google Gemini",
                "categories": {
                    "text_analysis": [
                        "/ai/analyze-text",
                        "/ai/chat",
                        "/ai/chat/history"
                    ],
                    "image_analysis": [
                        "/ai/analyze-image",
                        "/ai/compare-images"
                    ],
                    "document_analysis": [
                        "/ai/analyze-document",
                        "/ai/extract-structured-data",
                        "/ai/analyze-csv"
                    ],
                    "text_processing": [
                        "/ai/sentiment",
                        "/ai/translate",
                        "/ai/summarize",
                        "/ai/grammar-check"
                    ],
                    "content_generation": [
                        "/ai/generate-content",
                        "/ai/embeddings"
                    ],
                    "combined": [
                        "/ai/combined/image-analysis",
                        "/ai/combined/document-analysis"
                    ]
                }
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/health",
    status_code=200,
    tags=["Health"],
)
def health_check():
    """Verifica el estado de salud de la aplicación y sus servicios."""
    # Verificar si Gemini está disponible
    try:
        from app.routes.ai_routes import gemini_client
        gemini_available = gemini_client is not None
    except:
        gemini_available = False
    
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "file_processing": "operational",
            "gemini_ai": "operational" if gemini_available else "unavailable"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/version",
    status_code=200,
    tags=["Info"],
)
def get_version():
    """Obtiene la versión actual de la API."""
    return {
        "version": "2.0.0",
        "release_date": "2024",
        "features": [
            "File upload and processing (10 types)",
            "Google Gemini AI integration",
            "Image analysis with Vision",
            "Document analysis and extraction",
            "Text processing and generation",
            "Chat with memory",
            "Combined file + AI endpoints"
        ]
    }


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Iniciando API REST - Endoscope Application + Gemini AI")
    print("=" * 70)
    print(f"📚 Documentación Swagger: http://localhost:8000/docs")
    print(f"📖 Documentación ReDoc:   http://localhost:8000/redoc")
    print(f"🏥 Health Check:          http://localhost:8000/health")
    print("=" * 70)
    print("\n📦 Rutas disponibles:")
    print("  • /files/*    - Manejo de archivos (10 tipos)")
    print("  • /ai/*       - Análisis con IA (Gemini)")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )