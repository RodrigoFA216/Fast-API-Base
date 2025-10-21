"""
gemini_api.py - Módulo de Integración con Google Gemini API
============================================================
Este módulo proporciona funciones para interactuar con la API de Google Gemini,
incluyendo análisis de texto, imágenes, documentos y otras capacidades de IA.

Funcionalidades principales:
- Análisis de texto con contexto
- Procesamiento de imágenes con Gemini Vision
- Análisis de documentos (PDF, Word, etc.)
- Generación de embeddings
- Chat conversacional con historial
- Análisis de sentimientos
- Extracción de información estructurada
"""

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import List, Dict, Any, Optional, Union
import os
from datetime import datetime
import json
from PIL import Image
import io
import base64
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

# Modelos disponibles de Gemini
GEMINI_MODELS = {
    "pro": "gemini-1.5-pro-latest",
    "flash": "gemini-1.5-flash-latest",
    "vision": "gemini-1.5-pro-latest"  # Soporta multimodal
}

load_dotenv()

# Configuración de seguridad por defecto
DEFAULT_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# Configuración de generación por defecto
DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}


# ============================================================================
# CLASE PRINCIPAL DE GEMINI API
# ============================================================================

class GeminiAPI:
    """
    Clase principal para manejar todas las interacciones con Google Gemini API.
    """
    
    def __init__(self, api_key: str = None):
        """
        Inicializa la conexión con Gemini API.
        
        Args:
            api_key: API key de Google. Si no se proporciona, busca en variable de entorno.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "API key no proporcionada. Usa el parámetro api_key o "
                "establece la variable de entorno GOOGLE_API_KEY"
            )
        
        # Configurar Gemini
        genai.configure(api_key=self.api_key)
        
        # Inicializar modelos
        self.model_pro = genai.GenerativeModel(
            model_name=GEMINI_MODELS["pro"],
            safety_settings=DEFAULT_SAFETY_SETTINGS,
            generation_config=DEFAULT_GENERATION_CONFIG
        )
        
        self.model_flash = genai.GenerativeModel(
            model_name=GEMINI_MODELS["flash"],
            safety_settings=DEFAULT_SAFETY_SETTINGS,
            generation_config=DEFAULT_GENERATION_CONFIG
        )
        
        # Historial de conversación
        self.chat_history: List[Dict[str, str]] = []
    
    
    # ========================================================================
    # 1. ANÁLISIS DE TEXTO SIMPLE
    # ========================================================================
    
    def analyze_text(
        self,
        text: str,
        model: str = "flash",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Analiza texto con Gemini y retorna una respuesta estructurada.
        
        Args:
            text: Texto a analizar
            model: Modelo a usar ("pro" o "flash")
            temperature: Creatividad de la respuesta (0.0 - 1.0)
            
        Returns:
            Dict con la respuesta y metadata
        """
        try:
            # Seleccionar modelo
            selected_model = self.model_pro if model == "pro" else self.model_flash
            
            # Configurar temperatura específica si es diferente
            if temperature != 0.7:
                selected_model._generation_config.temperature = temperature
            
            # Generar respuesta
            response = selected_model.generate_content(text)
            
            return {
                "success": True,
                "response": response.text,
                "model_used": GEMINI_MODELS[model],
                "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 2. CHAT CONVERSACIONAL CON HISTORIAL
    # ========================================================================
    
    def chat(
        self,
        message: str,
        model: str = "flash",
        clear_history: bool = False
    ) -> Dict[str, Any]:
        """
        Mantiene una conversación con historial de contexto.
        
        Args:
            message: Mensaje del usuario
            model: Modelo a usar
            clear_history: Si True, limpia el historial antes de responder
            
        Returns:
            Dict con respuesta y estado del historial
        """
        try:
            if clear_history:
                self.chat_history = []
            
            # Seleccionar modelo
            selected_model = self.model_pro if model == "pro" else self.model_flash
            
            # Iniciar chat con historial
            chat = selected_model.start_chat(history=[
                {"role": msg["role"], "parts": [msg["content"]]}
                for msg in self.chat_history
            ])
            
            # Enviar mensaje
            response = chat.send_message(message)
            
            # Actualizar historial
            self.chat_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.chat_history.append({
                "role": "model",
                "content": response.text,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "success": True,
                "response": response.text,
                "history_length": len(self.chat_history),
                "model_used": GEMINI_MODELS[model],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Obtiene el historial completo de la conversación.
        
        Returns:
            Lista con el historial de mensajes
        """
        return self.chat_history
    
    
    def clear_chat_history(self) -> Dict[str, Any]:
        """
        Limpia el historial de conversación.
        
        Returns:
            Dict confirmando la limpieza
        """
        messages_cleared = len(self.chat_history)
        self.chat_history = []
        
        return {
            "success": True,
            "messages_cleared": messages_cleared,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    
    # ========================================================================
    # 3. ANÁLISIS DE IMÁGENES (VISION)
    # ========================================================================
    
    def analyze_image(
        self,
        image_data: Union[bytes, str],
        prompt: str = "Describe esta imagen en detalle",
        image_format: str = "bytes"
    ) -> Dict[str, Any]:
        """
        Analiza una imagen usando Gemini Vision.
        
        Args:
            image_data: Datos de la imagen (bytes o base64)
            prompt: Instrucciones para el análisis
            image_format: Formato de entrada ("bytes" o "base64")
            
        Returns:
            Dict con el análisis de la imagen
        """
        try:
            # Convertir imagen según formato
            if image_format == "base64":
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            # Abrir imagen con PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Generar análisis
            response = self.model_pro.generate_content([prompt, image])
            
            return {
                "success": True,
                "analysis": response.text,
                "image_size": f"{image.width}x{image.height}",
                "image_format": image.format,
                "prompt_used": prompt,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    def compare_images(
        self,
        image1_data: bytes,
        image2_data: bytes,
        comparison_prompt: str = "Compara estas dos imágenes y describe sus diferencias y similitudes"
    ) -> Dict[str, Any]:
        """
        Compara dos imágenes usando Gemini Vision.
        
        Args:
            image1_data: Datos de la primera imagen
            image2_data: Datos de la segunda imagen
            comparison_prompt: Instrucciones para la comparación
            
        Returns:
            Dict con la comparación de las imágenes
        """
        try:
            # Abrir imágenes
            image1 = Image.open(io.BytesIO(image1_data))
            image2 = Image.open(io.BytesIO(image2_data))
            
            # Generar comparación
            response = self.model_pro.generate_content([
                comparison_prompt,
                image1,
                image2
            ])
            
            return {
                "success": True,
                "comparison": response.text,
                "image1_size": f"{image1.width}x{image1.height}",
                "image2_size": f"{image2.width}x{image2.height}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 4. ANÁLISIS DE DOCUMENTOS
    # ========================================================================
    
    def analyze_document(
        self,
        document_text: str,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analiza documentos de texto con diferentes tipos de análisis.
        
        Args:
            document_text: Contenido del documento
            analysis_type: Tipo de análisis ("summary", "key_points", "sentiment", "entities")
            
        Returns:
            Dict con el análisis del documento
        """
        try:
            # Definir prompts según tipo de análisis
            prompts = {
                "summary": f"Resume el siguiente documento de forma concisa:\n\n{document_text}",
                "key_points": f"Extrae los puntos clave del siguiente documento:\n\n{document_text}",
                "sentiment": f"Analiza el sentimiento y tono del siguiente documento:\n\n{document_text}",
                "entities": f"Identifica las entidades principales (personas, lugares, organizaciones) en el siguiente documento:\n\n{document_text}"
            }
            
            prompt = prompts.get(analysis_type, prompts["summary"])
            
            # Generar análisis
            response = self.model_pro.generate_content(prompt)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "result": response.text,
                "document_length": len(document_text),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 5. EXTRACCIÓN DE INFORMACIÓN ESTRUCTURADA
    # ========================================================================
    
    def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extrae información estructurada de texto según un schema definido.
        
        Args:
            text: Texto del cual extraer información
            schema: Diccionario con los campos a extraer y sus descripciones
            
        Returns:
            Dict con los datos extraídos
        """
        try:
            # Construir prompt con schema
            schema_description = "\n".join([
                f"- {key}: {description}"
                for key, description in schema.items()
            ])
            
            prompt = f"""
Extrae la siguiente información del texto y devuélvela en formato JSON:

{schema_description}

Texto:
{text}

Responde SOLO con el JSON, sin texto adicional.
"""
            
            response = self.model_pro.generate_content(prompt)
            
            # Intentar parsear como JSON
            try:
                extracted_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            except json.JSONDecodeError:
                extracted_data = {"raw_response": response.text}
            
            return {
                "success": True,
                "extracted_data": extracted_data,
                "schema_used": schema,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 6. ANÁLISIS DE SENTIMIENTOS
    # ========================================================================
    
    def analyze_sentiment(
        self,
        text: str,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Analiza el sentimiento de un texto.
        
        Args:
            text: Texto a analizar
            detailed: Si True, proporciona análisis detallado
            
        Returns:
            Dict con el análisis de sentimiento
        """
        try:
            if detailed:
                prompt = f"""
Analiza el sentimiento del siguiente texto y proporciona:
1. Sentimiento general (positivo/negativo/neutral)
2. Score de confianza (0-100)
3. Emociones detectadas
4. Aspectos específicos y su sentimiento

Texto: {text}

Responde en formato JSON.
"""
            else:
                prompt = f"""
Analiza el sentimiento del siguiente texto.
Responde solo con: "positivo", "negativo" o "neutral"

Texto: {text}
"""
            
            response = self.model_flash.generate_content(prompt)
            
            return {
                "success": True,
                "sentiment_analysis": response.text,
                "text_length": len(text),
                "detailed": detailed,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 7. GENERACIÓN DE EMBEDDINGS
    # ========================================================================
    
    def generate_embeddings(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> Dict[str, Any]:
        """
        Genera embeddings para una lista de textos.
        
        Args:
            texts: Lista de textos para generar embeddings
            task_type: Tipo de tarea (retrieval_document, retrieval_query, etc.)
            
        Returns:
            Dict con los embeddings generados
        """
        try:
            embeddings = []
            
            for text in texts:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type=task_type
                )
                embeddings.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "embedding": result['embedding'],
                    "dimensions": len(result['embedding'])
                })
            
            return {
                "success": True,
                "embeddings": embeddings,
                "total_texts": len(texts),
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 8. TRADUCCIÓN DE TEXTO
    # ========================================================================
    
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto"
    ) -> Dict[str, Any]:
        """
        Traduce texto a un idioma específico.
        
        Args:
            text: Texto a traducir
            target_language: Idioma destino
            source_language: Idioma origen (auto para detección automática)
            
        Returns:
            Dict con la traducción
        """
        try:
            if source_language == "auto":
                prompt = f"Traduce el siguiente texto a {target_language}:\n\n{text}"
            else:
                prompt = f"Traduce el siguiente texto de {source_language} a {target_language}:\n\n{text}"
            
            response = self.model_flash.generate_content(prompt)
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": response.text,
                "source_language": source_language,
                "target_language": target_language,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 9. RESUMEN DE TEXTO
    # ========================================================================
    
    def summarize_text(
        self,
        text: str,
        summary_length: str = "medium",
        bullet_points: bool = False
    ) -> Dict[str, Any]:
        """
        Resume un texto con diferentes opciones de longitud.
        
        Args:
            text: Texto a resumir
            summary_length: Longitud del resumen ("short", "medium", "long")
            bullet_points: Si True, devuelve en formato de puntos
            
        Returns:
            Dict con el resumen generado
        """
        try:
            length_instructions = {
                "short": "muy breve (2-3 oraciones)",
                "medium": "moderado (1 párrafo)",
                "long": "detallado (2-3 párrafos)"
            }
            
            format_instruction = "en formato de puntos clave" if bullet_points else "en formato de párrafo"
            
            prompt = f"""
Resume el siguiente texto de forma {length_instructions.get(summary_length, "moderada")} 
{format_instruction}:

{text}
"""
            
            response = self.model_pro.generate_content(prompt)
            
            return {
                "success": True,
                "summary": response.text,
                "original_length": len(text),
                "summary_length_type": summary_length,
                "bullet_points": bullet_points,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 10. GENERACIÓN DE CONTENIDO CREATIVO
    # ========================================================================
    
    def generate_creative_content(
        self,
        prompt: str,
        content_type: str = "general",
        temperature: float = 0.9
    ) -> Dict[str, Any]:
        """
        Genera contenido creativo basado en un prompt.
        
        Args:
            prompt: Descripción del contenido a generar
            content_type: Tipo de contenido ("story", "poem", "article", "code", "general")
            temperature: Nivel de creatividad (0.0 - 1.0)
            
        Returns:
            Dict con el contenido generado
        """
        try:
            type_instructions = {
                "story": "Escribe una historia creativa sobre:",
                "poem": "Escribe un poema sobre:",
                "article": "Escribe un artículo informativo sobre:",
                "code": "Genera código para:",
                "general": ""
            }
            
            full_prompt = f"{type_instructions.get(content_type, '')} {prompt}"
            
            # Usar modelo con temperatura personalizada
            model = genai.GenerativeModel(
                model_name=GEMINI_MODELS["pro"],
                generation_config={
                    **DEFAULT_GENERATION_CONFIG,
                    "temperature": temperature
                }
            )
            
            response = model.generate_content(full_prompt)
            
            return {
                "success": True,
                "content": response.text,
                "content_type": content_type,
                "temperature": temperature,
                "prompt_used": prompt,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 11. VALIDACIÓN Y CORRECCIÓN DE TEXTO
    # ========================================================================
    
    def check_grammar(
        self,
        text: str,
        language: str = "español"
    ) -> Dict[str, Any]:
        """
        Revisa y corrige gramática y ortografía.
        
        Args:
            text: Texto a revisar
            language: Idioma del texto
            
        Returns:
            Dict con texto corregido y sugerencias
        """
        try:
            prompt = f"""
Revisa el siguiente texto en {language} y proporciona:
1. Texto corregido
2. Lista de errores encontrados
3. Sugerencias de mejora

Texto original:
{text}

Responde en formato JSON con las claves: "texto_corregido", "errores", "sugerencias"
"""
            
            response = self.model_pro.generate_content(prompt)
            
            return {
                "success": True,
                "result": response.text,
                "original_text": text,
                "language": language,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    # ========================================================================
    # 12. ANÁLISIS DE DATOS TABULARES (CSV/EXCEL)
    # ========================================================================
    
    def analyze_tabular_data(
        self,
        data_text: str,
        analysis_request: str
    ) -> Dict[str, Any]:
        """
        Analiza datos tabulares y responde preguntas sobre ellos.
        
        Args:
            data_text: Datos en formato texto (CSV, tabla, etc.)
            analysis_request: Pregunta o análisis solicitado
            
        Returns:
            Dict con el análisis de los datos
        """
        try:
            prompt = f"""
Analiza los siguientes datos y responde la pregunta:

Datos:
{data_text}

Pregunta/Análisis solicitado:
{analysis_request}
"""
            
            response = self.model_pro.generate_content(prompt)
            
            return {
                "success": True,
                "analysis": response.text,
                "data_length": len(data_text),
                "request": analysis_request,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_gemini_client(api_key: str = None) -> GeminiAPI:
    """
    Función helper para crear una instancia de GeminiAPI.
    
    Args:
        api_key: API key de Google (opcional)
        
    Returns:
        Instancia de GeminiAPI
    """
    return GeminiAPI(api_key=api_key)


def list_available_models() -> Dict[str, str]:
    """
    Lista los modelos disponibles de Gemini.
    
    Returns:
        Dict con los modelos disponibles
    """
    return GEMINI_MODELS.copy()