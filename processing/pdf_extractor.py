#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para extracción de texto de archivos PDF.
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple
import PyPDF2

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Clase para extraer y procesar texto de archivos PDF."""
    
    def __init__(self):
        self.section_patterns = {
            'abstract': re.compile(r'abstract', re.IGNORECASE),
            'introduction': re.compile(r'introduction|1\.?\s+introduction', re.IGNORECASE),
            'methodology': re.compile(r'methodology|method|approach|2\.?\s+', re.IGNORECASE),
            'results': re.compile(r'results|evaluation|experiment|3\.?\s+', re.IGNORECASE),
            'conclusion': re.compile(r'conclusion|discussion|4\.?\s+', re.IGNORECASE),
            'references': re.compile(r'references|bibliography', re.IGNORECASE)
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrae todo el texto de un archivo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            PyPDF2.errors.PdfReadError: Si hay problemas al leer el PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
        
        logger.info(f"Extrayendo texto de: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                logger.info(f"El PDF tiene {num_pages} páginas")
                
                # Extraer texto de todas las páginas
                text = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                # Limpiar el texto extraído
                text = self._clean_text(text)
                
                logger.info(f"Extracción completada: {len(text)} caracteres")
                return text
                
        except PyPDF2.errors.PdfReadError as e:
            logger.error(f"Error al leer el PDF {pdf_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al procesar {pdf_path}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia el texto extraído del PDF.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        # Eliminar múltiples espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar caracteres no imprimibles
        text = re.sub(r'[^\x20-\x7E\n]', '', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'[\r\n]+', '\n', text)
        
        return text.strip()
    
    def extract_paper_metadata(self, text: str) -> Dict[str, str]:
        """
        Extrae metadatos básicos del paper basados en el texto.
        
        Args:
            text: Texto completo del paper
            
        Returns:
            Diccionario con metadatos (título, autores, etc.)
        """
        metadata = {
            'title': '',
            'authors': '',
            'arxiv_id': ''
        }
        
        # Intentar extraer el título (primeras líneas, hasta el primer punto)
        first_lines = text.split('\n')[0:3]
        title_text = ' '.join(first_lines)
        title_match = re.search(r'^(.*?)\s*(?:Abstract|\.)', title_text, re.DOTALL)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Intentar extraer ID de arXiv si está presente
        arxiv_match = re.search(r'arXiv:(\d+\.\d+v\d+)', text)
        if arxiv_match:
            metadata['arxiv_id'] = arxiv_match.group(1)
        
        return metadata
    
    def extract_paper_sections(self, text: str) -> Dict[str, str]:
        """
        Intenta dividir el texto en secciones principales del paper.
        
        Args:
            text: Texto completo del paper
            
        Returns:
            Diccionario con las secciones extraídas
        """
        sections = {}
        
        # Encontrar posiciones de los encabezados de sección
        section_positions = {}
        for section_name, pattern in self.section_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                section_positions[match.start()] = section_name
        
        # Ordenar posiciones
        positions = sorted(section_positions.keys())
        
        # Extraer cada sección
        for i, start_pos in enumerate(positions):
            section_name = section_positions[start_pos]
            end_pos = positions[i+1] if i < len(positions)-1 else None
            
            section_text = text[start_pos:end_pos].strip()
            sections[section_name] = section_text
        
        return sections

# Función de conveniencia para usar directamente
def extract_text_from_pdf(pdf_path: str) -> Tuple[str, Dict[str, str]]:
    """
    Función auxiliar para extraer texto y metadatos de un PDF.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        Tupla con (texto_completo, metadatos)
    """
    extractor = PDFExtractor()
    text = extractor.extract_text_from_pdf(pdf_path)
    metadata = extractor.extract_paper_metadata(text)
    return text, metadata