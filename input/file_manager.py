#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para gestionar archivos de entrada.
"""

import os
import logging
from typing import List, Dict, Optional
from config.settings import INPUT_DIR

logger = logging.getLogger(__name__)

def get_paper_files() -> List[str]:
    """
    Obtiene la lista de archivos PDF disponibles en el directorio de entrada.
    
    Returns:
        Lista de rutas completas a los archivos PDF
    """
    try:
        if not os.path.exists(INPUT_DIR):
            logger.warning(f"El directorio {INPUT_DIR} no existe")
            return []
        
        pdf_files = [
            os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR)
            if f.lower().endswith('.pdf')
        ]
        
        logger.info(f"Encontrados {len(pdf_files)} archivos PDF en {INPUT_DIR}")
        return pdf_files
    
    except Exception as e:
        logger.error(f"Error al buscar archivos PDF: {e}")
        return []

def check_file_processed(file_path: str, output_dir: str) -> bool:
    """
    Verifica si un archivo ya ha sido procesado previamente.
    
    Args:
        file_path: Ruta del archivo a verificar
        output_dir: Directorio de salida donde se guardan los JSONs
        
    Returns:
        True si ya existe un JSON para este archivo, False en caso contrario
    """
    try:
        # Obtener nombre base del archivo
        base_name = os.path.basename(file_path)
        file_name = os.path.splitext(base_name)[0]
        
        # Verificar si existe un JSON con el mismo nombre
        json_path = os.path.join(output_dir, f"{file_name}.json")
        
        return os.path.exists(json_path)
    
    except Exception as e:
        logger.error(f"Error al verificar si el archivo fue procesado: {e}")
        return False

def get_file_metadata(file_path: str) -> Dict[str, str]:
    """
    Obtiene metadatos básicos del archivo.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Diccionario con metadatos del archivo
    """
    try:
        stat_info = os.stat(file_path)
        base_name = os.path.basename(file_path)
        
        return {
            'name': base_name,
            'base_name': os.path.splitext(base_name)[0],
            'size': stat_info.st_size,
            'modified': stat_info.st_mtime,
            'path': file_path
        }
    
    except Exception as e:
        logger.error(f"Error al obtener metadatos del archivo {file_path}: {e}")
        return {'name': os.path.basename(file_path), 'path': file_path}