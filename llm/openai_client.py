#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cliente para interactuar con la API de OpenAI.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI  # Importación correcta

from llm.prompt_templates import get_paper_analysis_prompt

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Cliente para interactuar con la API de OpenAI."""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-4", 
                 temperature: float = 0.2,
                 max_tokens: int = 8000,
                 max_retries: int = 3,
                 retry_delay: int = 5):
        """
        Inicializa el cliente de OpenAI.
        
        Args:
            api_key: Clave de API de OpenAI (si no se proporciona, se toma de OPENAI_API_KEY)
            model: Modelo de OpenAI a utilizar
            temperature: Temperatura para la generación (0.0 a 1.0)
            max_tokens: Número máximo de tokens en la respuesta
            max_retries: Número máximo de reintentos en caso de error
            retry_delay: Tiempo de espera entre reintentos (segundos)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("No se ha proporcionado una API key de OpenAI")
            raise ValueError("Se requiere una API key de OpenAI")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Inicializar cliente de OpenAI - Actualizado para la versión actual
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Cliente OpenAI inicializado con modelo {self.model}")
    
    def analyze_paper(self, paper_text: str, paper_name: str) -> Dict[str, Any]:
        """
        Analiza un paper utilizando la API de OpenAI.
        
        Args:
            paper_text: Texto del paper a analizar
            paper_name: Nombre del paper
            
        Returns:
            Diccionario con el análisis del paper
        """
        logger.info(f"Analizando paper: {paper_name}")
        
        # Obtener el prompt para el análisis
        prompt = get_paper_analysis_prompt(paper_text)
        
        # Realizar llamada a la API
        response = self._call_api(prompt)
        
        # Procesar la respuesta
        analysis = self._process_response(response, paper_name)
        
        return analysis
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """
        Realiza una llamada a la API de OpenAI con reintentos.
        
        Args:
            prompt: Texto del prompt
            
        Returns:
            Respuesta de la API
            
        Raises:
            Exception: Si todos los reintentos fallan
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Intentando llamada a API (intento {attempt + 1}/{self.max_retries})")
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Eres un asistente especializado en analizar papers académicos."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                return completion
                
            except Exception as e:
                logger.warning(f"Error en llamada a API: {e}. Reintentando en {self.retry_delay} segundos...")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Máximo de reintentos alcanzado: {e}")
                    raise
    
    def _process_response(self, response: Dict[str, Any], paper_name: str) -> Dict[str, Any]:
        """
        Procesa la respuesta de la API.
        
        Args:
            response: Respuesta de la API de OpenAI
            paper_name: Nombre del paper
            
        Returns:
            Diccionario con la información procesada
        """
        try:
            # Extraer el contenido de la respuesta
            content = response.choices[0].message.content
            
            # Intentar parsearlo como JSON
            try:
                # Buscar contenido JSON en la respuesta, si está envuelto en ```json ... ```
                json_match = content
                if "```json" in content:
                    json_match = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_match = content.split("```")[1].split("```")[0].strip()
                
                # Parsear el JSON
                analysis = json.loads(json_match)
                
                # Asegurar que el nombre del paper esté incluido
                if "nombre" not in analysis or not analysis["nombre"]:
                    analysis["nombre"] = paper_name
                
                return analysis
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"No se pudo parsear la respuesta como JSON: {e}")
                
                # Si no se pudo parsear como JSON, crear un diccionario con el contenido completo
                return {
                    "nombre": paper_name,
                    "resumen": content.strip(),
                    "resultados": "No disponible (error de formato)",
                    "exito": None,
                    "performance": "No disponible (error de formato)"
                }
                
        except Exception as e:
            logger.error(f"Error procesando respuesta de API: {e}")
            
            # En caso de error, devolver un diccionario con información de error
            return {
                "nombre": paper_name,
                "error": f"Error al procesar la respuesta: {str(e)}",
                "resumen": "No disponible debido a un error",
                "resultados": "No disponible debido a un error",
                "exito": None,
                "performance": "No disponible"
            }

# Función de conveniencia
def analyze_paper(paper_text: str, paper_name: str, 
                 model: str = "gpt-4", 
                 temperature: float = 0.2) -> Dict[str, Any]:
    """
    Función auxiliar para analizar un paper con OpenAI.
    
    Args:
        paper_text: Texto del paper
        paper_name: Nombre del paper
        model: Modelo de OpenAI
        temperature: Temperatura para generación
        
    Returns:
        Diccionario con el análisis
    """
    client = OpenAIClient(model=model, temperature=temperature)
    return client.analyze_paper(paper_text, paper_name)