

"""
Configuraciones globales para la aplicación de análisis de papers de arXiv.
"""

import os
import logging
from typing import Dict, Any

# Configuración de logging
def setup_logging():
    """Configura el sistema de logging de la aplicación."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, log_level.upper(), None)
    
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Rutas de directorios
INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input", "papers")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "results")

# Configuración del LLM
LLM_CONFIG: Dict[str, Any] = {
    "model": os.getenv("LLM_MODEL", "gpt-4"),
    "temperature": float(os.getenv("TEMPERATURE", 0.2)),
    "max_tokens": int(os.getenv("MAX_TOKENS", 8000)),
}

def verify_api_key() -> bool:
    """Verifica que la API key de OpenAI esté configurada."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY no está configurada en el archivo .env")
        return False
    return True

def verify_directories() -> bool:
    """Verifica que los directorios necesarios existan, los crea si no."""
    try:
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error al crear directorios: {e}")
        return False

def configure_app() -> bool:
    """Realiza todas las verificaciones y configuraciones necesarias."""
    if not verify_api_key():
        return False
    
    if not verify_directories():
        return False
    
    logger.info("Aplicación configurada correctamente")
    return True