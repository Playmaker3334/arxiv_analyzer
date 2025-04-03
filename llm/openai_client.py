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

from llm.prompt_templates import (
    get_paper_analysis_prompt, 
    get_chunk_initial_prompt,
    get_chunk_middle_prompt,
    get_chunk_final_prompt,
    get_consolidation_prompt
)

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Cliente para interactuar con la API de OpenAI."""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "gpt-4", 
                 temperature: float = 0.2,
                 max_tokens: int = 1000,  # Valor por defecto más bajo
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
        # Usar el valor del entorno si está disponible, sino el proporcionado como argumento
        self.max_tokens = int(os.getenv("MAX_TOKENS", max_tokens))
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Inicializar cliente de OpenAI - Actualizado para la versión actual
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Cliente OpenAI inicializado con modelo {self.model}, max_tokens={self.max_tokens}")
    
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
        
        # Truncar el prompt si es demasiado largo
        prompt = self._truncate_prompt(prompt)
        
        # Realizar llamada a la API
        response = self._call_api(prompt)
        
        # Procesar la respuesta
        analysis = self._process_response(response, paper_name)
        
        return analysis
    
    def analyze_paper_in_chunks(self, chunks: List[Dict[str, Any]], paper_name: str) -> Dict[str, Any]:
        """
        Analiza un paper dividido en chunks y consolida los resultados.
        
        Args:
            chunks: Lista de chunks con texto y metadatos
            paper_name: Nombre del paper
            
        Returns:
            Diccionario con el análisis consolidado
        """
        logger.info(f"Analizando paper en {len(chunks)} chunks: {paper_name}")
        
        chunk_results = []
        
        # Obtener un análisis para cada chunk
        for i, chunk in enumerate(chunks):
            chunk_text = chunk['text']
            chunk_metadata = chunk['metadata']
            
            # Adaptar el prompt para indicar que es parte de un documento mayor
            section_info = chunk_metadata.get('section', 'texto')
            part_info = chunk_metadata.get('chunk_part', '')
            chunk_info = f"Parte {i+1}/{len(chunks)} - Sección: {section_info}"
            if part_info:
                chunk_info += f" (Parte {part_info})"
            
            logger.info(f"Procesando {chunk_info}")
            
            # Usar un prompt específico para chunks
            if i == 0:
                # El primer chunk incluye instrucciones de inicio
                prompt = get_chunk_initial_prompt(chunk_text, chunk_info)
            elif i == len(chunks) - 1:
                # El último chunk incluye instrucciones de finalización/resumen
                prompt = get_chunk_final_prompt(chunk_text, chunk_info)
            else:
                # Chunks intermedios
                prompt = get_chunk_middle_prompt(chunk_text, chunk_info)
            
            # Truncar el prompt si es necesario
            prompt = self._truncate_prompt(prompt)
            
            # Realizar llamada a la API
            response = self._call_api(prompt)
            
            # Procesar la respuesta
            chunk_result = self._process_response(response, f"{paper_name}_chunk_{i+1}")
            chunk_results.append(chunk_result)
            
            # Pausa corta para evitar rate limits
            time.sleep(1)
        
        # Solicitar un resumen final consolidado
        consolidation_result = self._request_consolidation(chunk_results, paper_name)
        
        return consolidation_result

    def _request_consolidation(self, chunk_results: List[Dict[str, Any]], paper_name: str) -> Dict[str, Any]:
        """
        Solicita al LLM que consolide los resultados de múltiples chunks.
        
        Args:
            chunk_results: Lista de resultados por chunk
            paper_name: Nombre del paper
            
        Returns:
            Análisis consolidado
        """
        # Extraer información relevante de cada chunk
        consolidated_data = []
        for i, result in enumerate(chunk_results):
            consolidated_data.append({
                "parte": i+1,
                "resumen": result.get("resumen", "No disponible"),
                "resultados": result.get("resultados", "No disponible")
            })
        
        # Crear prompt para consolidación
        consolidation_prompt = get_consolidation_prompt(chunk_results, paper_name)
        
        # Llamar a la API
        response = self._call_api(consolidation_prompt)
        
        # Procesar respuesta
        return self._process_response(response, paper_name)
    
    def _truncate_prompt(self, prompt: str) -> str:
        """
        Trunca el prompt para asegurarse de que está dentro de los límites del modelo.
        
        Args:
            prompt: El prompt original
            
        Returns:
            El prompt truncado
        """
        # Estimar límite de caracteres para prompt (considerando que ~4 caracteres = 1 token)
        # Reservar espacio para 1500 tokens de respuesta (6,000 caracteres aprox.)
        # El total no debe exceder ~8,000 tokens, así que permitimos ~6,500 tokens para el prompt
        max_prompt_chars = 6500 * 4  # ~26,000 caracteres
        
        if len(prompt) <= max_prompt_chars:
            return prompt
            
        logger.warning(f"Prompt demasiado largo ({len(prompt)} caracteres). Truncando...")
        
        # Encontrar las secciones del prompt
        prompt_parts = prompt.split("-----")
        
        if len(prompt_parts) < 3:
            # Si no podemos identificar la estructura, truncamos simplemente
            return prompt[:max_prompt_chars]
        
        # Mantener la introducción y las instrucciones finales
        intro = prompt_parts[0]
        paper_content = prompt_parts[1]
        outro = prompt_parts[2]
        
        # Calcular cuánto espacio tenemos para el contenido del paper
        available_chars = max_prompt_chars - len(intro) - len(outro) - 10  # 10 para los separadores
        
        # Truncar el contenido del paper
        truncated_paper = paper_content[:available_chars] + "... [texto truncado]"
        
        # Reconstruir el prompt
        truncated_prompt = intro + "-----" + truncated_paper + "-----" + outro
        
        logger.debug(f"Prompt truncado a {len(truncated_prompt)} caracteres")
        return truncated_prompt
    
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
        # Asegurarse de que max_tokens no exceda límites seguros
        # Para GPT-4, reservar al menos 6,500 tokens para el input, dejando ~1,500 para output
        safe_max_tokens = min(self.max_tokens, 1000)  # Más restrictivo para asegurar que funcione
        
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
                    max_tokens=safe_max_tokens
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

# Función de conveniencia para análisis por chunks
def analyze_paper_chunks(chunks: List[Dict[str, Any]], paper_name: str,
                        model: str = "gpt-4",
                        temperature: float = 0.2) -> Dict[str, Any]:
    """
    Función auxiliar para analizar un paper dividido en chunks.
    
    Args:
        chunks: Lista de chunks con texto y metadatos
        paper_name: Nombre del paper
        model: Modelo de OpenAI
        temperature: Temperatura para generación
        
    Returns:
        Diccionario con el análisis consolidado
    """
    client = OpenAIClient(model=model, temperature=temperature)
    return client.analyze_paper_in_chunks(chunks, paper_name)