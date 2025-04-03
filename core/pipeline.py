#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orquestador principal del flujo de procesamiento de papers.
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional

from config.settings import LLM_CONFIG
from input.file_manager import get_paper_files, check_file_processed, get_file_metadata
from processing.pdf_extractor import extract_text_from_pdf
from processing.text_preprocessor import preprocess_text
from llm.openai_client import analyze_paper
from output.json_formatter import save_paper_analysis, format_json_for_human

logger = logging.getLogger(__name__)

class Pipeline:
    """Clase principal para orquestar el flujo de procesamiento de papers."""
    
    def __init__(self, output_dir: Optional[str] = None, skip_processed: bool = True):
        """
        Inicializa el pipeline.
        
        Args:
            output_dir: Directorio de salida (opcional)
            skip_processed: Si se deben omitir archivos ya procesados
        """
        self.output_dir = output_dir
        self.skip_processed = skip_processed
        
        # Configuración para LLM
        self.llm_model = LLM_CONFIG.get("model", "gpt-4")
        self.llm_temperature = LLM_CONFIG.get("temperature", 0.2)
    
    def process_all_papers(self) -> List[Dict[str, Any]]:
        """
        Procesa todos los papers encontrados en el directorio de entrada.
        
        Returns:
            Lista de resultados de procesamiento
        """
        # Obtener archivos disponibles
        pdf_files = get_paper_files()
        
        if not pdf_files:
            logger.warning("No se encontraron archivos PDF para procesar")
            return []
        
        logger.info(f"Iniciando procesamiento de {len(pdf_files)} archivos PDF")
        
        results = []
        for pdf_file in pdf_files:
            # Verificar si ya fue procesado
            if self.skip_processed and check_file_processed(pdf_file, self.output_dir):
                logger.info(f"Omitiendo {pdf_file} (ya procesado)")
                continue
            
            # Procesar paper
            try:
                result = self.process_paper(pdf_file)
                results.append(result)
                
                # Esperar un poco entre papers para prevenir rate limits en la API
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error procesando {pdf_file}: {e}")
                
                # Añadir resultado de error
                results.append({
                    "nombre": os.path.basename(pdf_file),
                    "error": f"Error: {str(e)}",
                    "status": "error"
                })
        
        logger.info(f"Procesamiento completado: {len(results)} resultados")
        return results
    
    def process_paper(self, pdf_path: str) -> Dict[str, Any]:
        """
        Procesa un paper específico.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con el resultado del procesamiento
            
        Raises:
            Exception: Si ocurre un error en alguna etapa del procesamiento
        """
        paper_name = os.path.basename(pdf_path)
        logger.info(f"Procesando paper: {paper_name}")
        
        try:
            # Paso 1: Extraer texto del PDF
            logger.info("Extrayendo texto del PDF")
            text, metadata = extract_text_from_pdf(pdf_path)
            
            # Paso 2: Preprocesar el texto
            logger.info("Preprocesando texto")
            processed_text = preprocess_text(text, metadata)
            
            # Paso 3: Analizar con LLM
            logger.info("Analizando con LLM")
            analysis = analyze_paper(
                processed_text, 
                paper_name,
                model=self.llm_model,
                temperature=self.llm_temperature
            )
            
            # Paso 4: Guardar resultados
            logger.info("Guardando resultados")
            output_path = save_paper_analysis(analysis, paper_name, self.output_dir)
            
            # Añadir metadata al resultado
            result = {
                **analysis,
                "status": "success",
                "output_path": output_path
            }
            
            logger.info(f"Procesamiento de {paper_name} completado con éxito")
            return result
            
        except Exception as e:
            logger.error(f"Error en el procesamiento de {paper_name}: {e}")
            raise
    
    def get_processing_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        Genera un resumen del procesamiento.
        
        Args:
            results: Lista de resultados de procesamiento
            
        Returns:
            Texto con el resumen
        """
        if not results:
            return "No se procesaron archivos."
        
        # Contar éxitos y errores
        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = sum(1 for r in results if r.get("status") == "error")
        
        # Generar resumen
        summary = f"Procesamiento completado.\n"
        summary += f"Total procesados: {len(results)}\n"
        summary += f"Exitosos: {success_count}\n"
        summary += f"Con errores: {error_count}\n\n"
        
        # Listar archivos procesados
        if success_count > 0:
            summary += "Papers procesados exitosamente:\n"
            for result in [r for r in results if r.get("status") == "success"]:
                summary += f"- {result.get('nombre', 'Desconocido')}\n"
        
        # Listar errores
        if error_count > 0:
            summary += "\nPapers con errores:\n"
            for result in [r for r in results if r.get("status") == "error"]:
                summary += f"- {result.get('nombre', 'Desconocido')}: {result.get('error', 'Error desconocido')}\n"
        
        return summary

# Funciones de conveniencia para uso directo
def run_pipeline(output_dir: Optional[str] = None, skip_processed: bool = True) -> List[Dict[str, Any]]:
    """
    Ejecuta el pipeline de procesamiento completo.
    
    Args:
        output_dir: Directorio de salida
        skip_processed: Si se deben omitir archivos ya procesados
        
    Returns:
        Lista de resultados de procesamiento
    """
    pipeline = Pipeline(output_dir=output_dir, skip_processed=skip_processed)
    return pipeline.process_all_papers()

def process_single_paper(pdf_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Procesa un solo paper.
    
    Args:
        pdf_path: Ruta al archivo PDF
        output_dir: Directorio de salida
        
    Returns:
        Diccionario con el resultado del procesamiento
    """
    pipeline = Pipeline(output_dir=output_dir)
    return pipeline.process_paper(pdf_path)