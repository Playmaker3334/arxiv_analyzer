#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para preprocesamiento de texto extraído de papers.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Clase para preprocesar texto de papers académicos."""
    
    def __init__(self, max_tokens: int = 8000):
        """
        Inicializa el preprocesador.
        
        Args:
            max_tokens: Límite aproximado de tokens para el texto procesado
        """
        self.max_tokens = max_tokens
        # Ratio aproximado de tokens por caracter (varía según el texto)
        self.char_to_token_ratio = 4
        
    def preprocess(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Preprocesa el texto completo de un paper.
        
        Args:
            text: Texto completo del paper
            metadata: Metadatos opcionales del paper
            
        Returns:
            Texto preprocesado y optimizado para el LLM
        """
        logger.info("Iniciando preprocesamiento de texto")
        
        # Aplicar limpieza básica
        text = self._clean_text(text)
        
        # Truncar si es necesario
        text = self._truncate_text(text)
        
        # Estructurar el texto para mejor comprensión del LLM
        text = self._structure_text(text, metadata)
        
        logger.info(f"Preprocesamiento completado: {len(text)} caracteres")
        return text
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia el texto aplicando varias transformaciones.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        # Reemplazar múltiples espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'[\r\n]+', '\n', text)
        
        # Eliminar caracteres no imprimibles
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        
        # Eliminar números de página
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Eliminar encabezados y pies de página repetitivos
        text = re.sub(r'\n.{1,50}arXiv.{1,50}\n', '\n', text)
        
        return text.strip()
    
    def _truncate_text(self, text: str) -> str:
        """
        Trunca el texto si excede el límite aproximado de tokens.
        Intenta hacerlo de manera inteligente preservando secciones importantes.
        
        Args:
            text: Texto a truncar
            
        Returns:
            Texto truncado
        """
        # Estimar número de tokens
        estimated_tokens = len(text) // self.char_to_token_ratio
        
        if estimated_tokens <= self.max_tokens:
            return text
        
        logger.warning(f"Texto demasiado largo ({estimated_tokens} tokens estimados). Truncando...")
        
        # Identificar secciones importantes
        sections = {
            'abstract': r'abstract',
            'introduction': r'introduction|1\.?\s+introduction',
            'methodology': r'methodology|method|2\.?\s+',
            'results': r'results|evaluation|3\.?\s+',
            'conclusion': r'conclusion|discussion|4\.?\s+'
        }
        
        # Prioridad de secciones (de más a menos importante)
        section_priority = ['abstract', 'conclusion', 'results', 'introduction', 'methodology']
        
        # Dividir en secciones
        section_texts = {}
        remaining_text = text
        
        for section, pattern in sections.items():
            match = re.search(pattern, remaining_text, re.IGNORECASE)
            if match:
                start_idx = match.start()
                section_texts[section] = remaining_text[start_idx:]
                remaining_text = remaining_text[:start_idx]
        
        # Reconstruir texto preservando secciones importantes según prioridad
        max_chars = self.max_tokens * self.char_to_token_ratio
        result_text = ""
        
        for section in section_priority:
            if section in section_texts and len(result_text) < max_chars:
                section_content = section_texts[section]
                
                # Si añadir toda la sección excede el límite, truncar la sección
                available_chars = max_chars - len(result_text)
                if len(section_content) > available_chars:
                    section_content = section_content[:available_chars] + "...[truncado]"
                
                result_text += section_content + "\n\n"
        
        # Si queda espacio, añadir el texto restante
        if len(result_text) < max_chars and remaining_text:
            available_chars = max_chars - len(result_text)
            if len(remaining_text) > available_chars:
                remaining_text = remaining_text[:available_chars] + "...[truncado]"
            
            result_text = remaining_text + "\n\n" + result_text
        
        logger.info(f"Texto truncado a aproximadamente {len(result_text) // self.char_to_token_ratio} tokens")
        return result_text.strip()
    
    def _structure_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Estructura el texto para optimizar el análisis del LLM.
        
        Args:
            text: Texto a estructurar
            metadata: Metadatos del paper
            
        Returns:
            Texto estructurado
        """
        # Añadir metadatos si están disponibles
        if metadata:
            header = ""
            if 'title' in metadata and metadata['title']:
                header += f"Título: {metadata['title']}\n"
            if 'authors' in metadata and metadata['authors']:
                header += f"Autores: {metadata['authors']}\n"
            if 'arxiv_id' in metadata and metadata['arxiv_id']:
                header += f"ArXiv ID: {metadata['arxiv_id']}\n"
            
            if header:
                text = f"{header}\n\n{text}"
        
        return text

# Función de conveniencia
def preprocess_text(text: str, metadata: Optional[Dict[str, Any]] = None, max_tokens: int = 8000) -> str:
    """
    Función auxiliar para preprocesar texto.
    
    Args:
        text: Texto a preprocesar
        metadata: Metadatos opcionales
        max_tokens: Límite de tokens
        
    Returns:
        Texto preprocesado
    """
    preprocessor = TextPreprocessor(max_tokens=max_tokens)
    return preprocessor.preprocess(text, metadata)