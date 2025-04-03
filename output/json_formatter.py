#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para formatear y guardar resultados en formato JSON.
"""

import os
import json
import logging
from typing import Dict, Any, Union, Optional
from datetime import datetime

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)

def save_paper_analysis(analysis: Dict[str, Any], paper_name: str, output_dir: Optional[str] = None) -> str:
    """
    Guarda el análisis de un paper en un archivo JSON.
    
    Args:
        analysis: Diccionario con el análisis del paper
        paper_name: Nombre del paper
        output_dir: Directorio de salida (opcional, usa OUTPUT_DIR por defecto)
        
    Returns:
        Ruta al archivo JSON generado
    """
    # Usar directorio por defecto si no se especifica
    output_dir = output_dir or OUTPUT_DIR
    
    # Asegurar que el directorio exista
    os.makedirs(output_dir, exist_ok=True)
    
    # Limpiar nombre para el archivo
    clean_name = os.path.splitext(os.path.basename(paper_name))[0]
    
    # Ruta del archivo de salida
    output_path = os.path.join(output_dir, f"{clean_name}.json")
    
    try:
        # Añadir metadatos del procesamiento
        analysis_with_meta = {
            **analysis,
            "__metadata__": {
                "processed_date": datetime.now().isoformat(),
                "source_file": paper_name,
            }
        }
        
        # Guardar en archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_with_meta, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Análisis guardado en: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error al guardar el análisis en {output_path}: {e}")
        raise

def format_json_for_human(analysis: Dict[str, Any]) -> str:
    """
    Formatea el JSON para presentación al usuario.
    
    Args:
        analysis: Diccionario con el análisis
        
    Returns:
        Texto formateado para presentación
    """
    try:
        # Eliminar metadatos internos para presentación
        if "__metadata__" in analysis:
            analysis = {k: v for k, v in analysis.items() if k != "__metadata__"}
        
        # Obtener elementos básicos
        title = analysis.get("nombre", "Paper sin título")
        summary = analysis.get("resumen", "No hay resumen disponible")
        results = analysis.get("resultados", "No hay resultados disponibles")
        success = analysis.get("exito", None)
        performance = analysis.get("performance", "No especificado")
        
        # Formatear texto para mostrar al usuario
        formatted_text = f"""
ANÁLISIS DEL PAPER: {title}
======================================================

RESUMEN:
{summary}

PRINCIPALES RESULTADOS:
{results}

ÉXITO DEL PAPER: {"Sí" if success else "No" if success is not None else "No determinado"}

MÉTRICAS DE RENDIMIENTO:
{performance}
"""
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error al formatear JSON para presentación: {e}")
        return f"Error al formatear el análisis: {e}"

def merge_results(results_list: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combina múltiples resultados en un solo diccionario.
    Útil para combinar análisis parciales de diferentes secciones.
    
    Args:
        results_list: Lista de diccionarios con resultados parciales
        
    Returns:
        Diccionario combinado
    """
    try:
        # Inicializar diccionario combinado
        combined = {}
        
        # Combinar todos los diccionarios
        for result in results_list:
            for key, value in result.items():
                # Si la clave ya existe, concatenar valores de texto
                if key in combined and isinstance(value, str) and isinstance(combined[key], str):
                    combined[key] = f"{combined[key]}\n\n{value}"
                else:
                    combined[key] = value
        
        return combined
        
    except Exception as e:
        logger.error(f"Error al combinar resultados: {e}")
        return {"error": f"Error al combinar resultados: {e}"}