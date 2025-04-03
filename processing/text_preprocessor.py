
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
        
        # Dividir en chunks si es necesario (en lugar de truncar)
        chunks = self.split_into_chunks(text, metadata)
        
        # Si solo hay un chunk, devolver el texto procesado
        if len(chunks) == 1:
            return self._structure_text(chunks[0]['text'], metadata)
        
        # Si hay múltiples chunks, usamos el primero para análisis inicial
        # (Esta función ahora devuelve solo el primer chunk,
        # pero process_paper() se encargará de procesar todos)
        logger.info(f"Texto dividido en {len(chunks)} chunks")
        return self._structure_text(chunks[0]['text'], chunks[0]['metadata'])
    
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
    
    def split_into_chunks(self, text: str, metadata: Optional[Dict[str, Any]] = None, 
                       chunk_size: int = 6000) -> List[Dict[str, Any]]:
        """
        Divide el texto en chunks procesables con superposición para mantener contexto.
        
        Args:
            text: Texto completo del paper
            metadata: Metadatos opcionales del paper
            chunk_size: Tamaño objetivo de cada chunk en tokens
            
        Returns:
            Lista de diccionarios con texto y metadatos para cada chunk
        """
        # Estimar número de tokens
        estimated_tokens = len(text) // self.char_to_token_ratio
        
        # Si el texto cabe en un solo chunk, devolverlo
        if estimated_tokens <= chunk_size:
            return [{
                'text': text,
                'metadata': metadata or {}
            }]
        
        # Estimar número de caracteres por chunk
        chars_per_chunk = chunk_size * self.char_to_token_ratio
        
        # Dividir primero por secciones principales
        sections = {}
        section_patterns = {
            'abstract': r'abstract',
            'introduction': r'introduction|1\.?\s+introduction',
            'methodology': r'methodology|method|2\.?\s+',
            'results': r'results|evaluation|3\.?\s+',
            'conclusion': r'conclusion|discussion|4\.?\s+'
        }
        
        # Identificar secciones
        current_text = text
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, current_text, re.IGNORECASE)
            if match:
                start_idx = match.start()
                sections[section_name] = current_text[start_idx:]
                current_text = current_text[:start_idx]
        
        # Si hay texto restante, considerar como "preámbulo"
        if current_text.strip():
            sections['preambulo'] = current_text
        
        # Crear chunks con secciones completas si son pequeñas, o dividiendo si son grandes
        chunks = []
        
        # Añadir metadatos básicos a todos los chunks
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata['total_chunks'] = 0  # Lo actualizaremos después
        
        # Primero tratamos de preservar secciones importantes completas
        priority_sections = ['abstract', 'conclusion']
        for section_name in priority_sections:
            if section_name in sections:
                section_text = sections[section_name]
                if len(section_text) <= chars_per_chunk:
                    # La sección cabe completa
                    chunks.append({
                        'text': section_text,
                        'metadata': {**chunk_metadata, 'section': section_name}
                    })
                    # Eliminar esta sección de la lista pendiente
                    del sections[section_name]
        
        # Ahora dividimos el resto de secciones
        for section_name, section_text in sections.items():
            if len(section_text) <= chars_per_chunk:
                # La sección cabe completa
                chunks.append({
                    'text': section_text,
                    'metadata': {**chunk_metadata, 'section': section_name}
                })
            else:
                # Dividir sección en múltiples chunks con superposición
                overlap = min(500, chars_per_chunk // 10)  # 10% de superposición
                for i in range(0, len(section_text), chars_per_chunk - overlap):
                    chunk_text = section_text[i:i + chars_per_chunk]
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            **chunk_metadata, 
                            'section': section_name,
                            'chunk_part': f"{i // (chars_per_chunk - overlap) + 1}"
                        }
                    })
        
        # Actualizar el número total de chunks en los metadatos
        for chunk in chunks:
            chunk['metadata']['total_chunks'] = len(chunks)
        
        logger.info(f"Texto dividido en {len(chunks)} chunks")
        return chunks
    
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
            if 'section' in metadata:
                header += f"Sección: {metadata['section']}\n"
            if 'chunk_part' in metadata:
                header += f"Parte: {metadata['chunk_part']}\n"
            if 'total_chunks' in metadata:
                header += f"Total de partes: {metadata['total_chunks']}\n"
            
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

# Función de conveniencia para dividir en chunks
def split_text_into_chunks(text: str, metadata: Optional[Dict[str, Any]] = None, chunk_size: int = 6000) -> List[Dict[str, Any]]:
    """
    Función auxiliar para dividir texto en chunks.
    
    Args:
        text: Texto a dividir
        metadata: Metadatos opcionales
        chunk_size: Tamaño objetivo de cada chunk en tokens
        
    Returns:
        Lista de chunks con texto y metadatos
    """
    preprocessor = TextPreprocessor()
    cleaned_text = preprocessor._clean_text(text)
    return preprocessor.split_into_chunks(cleaned_text, metadata, chunk_size)