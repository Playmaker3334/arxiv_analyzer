#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal para el procesamiento de papers de arXiv.
Este script coordina todo el proceso desde la extracción de texto hasta la generación de JSONs.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Import de módulos propios
from config.settings import configure_app, INPUT_DIR, OUTPUT_DIR
from core.pipeline import run_pipeline, process_single_paper
from processing.pdf_extractor import extract_text_from_pdf
from processing.text_preprocessor import preprocess_text
from llm.openai_client import analyze_paper
from output.json_formatter import save_paper_analysis

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parsea los argumentos de línea de comando."""
    parser = argparse.ArgumentParser(description='Analiza papers de arXiv y genera resúmenes en JSON.')
    parser.add_argument('--pdf', help='Ruta a un archivo PDF específico para procesar')
    parser.add_argument('--process-all', action='store_true', help='Procesa todos los PDFs en el directorio de entrada')
    parser.add_argument('--verbose', '-v', action='store_true', help='Activa el modo verbose para más detalles')
    
    return parser.parse_args()

def process_single_pdf(pdf_path):
    """Procesa un solo archivo PDF usando el pipeline completo."""
    try:
        logger.info(f"Procesando archivo: {pdf_path}")
        
        # Obtener nombre de archivo para el resultado
        paper_name = os.path.basename(pdf_path)
        
        # Extraer texto del PDF
        text, metadata = extract_text_from_pdf(pdf_path)
        logger.info(f"Texto extraído con éxito: {len(text)} caracteres")
        logger.info(f"Metadatos extraídos: {metadata}")
        
        # Preprocesar el texto
        logger.info("Preprocesando texto...")
        processed_text = preprocess_text(text, metadata)
        
        # Enviar a OpenAI para análisis
        logger.info("Analizando con OpenAI...")
        analysis = analyze_paper(processed_text, paper_name)
        
        # Formatear y guardar el resultado en JSON
        logger.info("Guardando resultado...")
        output_path = save_paper_analysis(analysis, paper_name, OUTPUT_DIR)
        
        logger.info(f"Procesamiento de {pdf_path} completado. Resultado guardado en {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error procesando {pdf_path}: {e}")
        return False

def process_all_pdfs():
    """Procesa todos los archivos PDF en el directorio de entrada."""
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"No se encontraron archivos PDF en {INPUT_DIR}")
        return
    
    logger.info(f"Encontrados {len(pdf_files)} archivos PDF para procesar")
    
    successful = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        if process_single_pdf(pdf_path):
            successful += 1
    
    logger.info(f"Procesamiento completo: {successful} de {len(pdf_files)} archivos procesados con éxito")

def main():
    """Función principal."""
    # Cargar variables de entorno
    load_dotenv()
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar nivel de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configurar la aplicación
    if not configure_app():
        logger.error("Error en la configuración de la aplicación. Abortando.")
        sys.exit(1)
    
    # Procesar según los argumentos
    if args.pdf:
        if os.path.exists(args.pdf):
            process_single_pdf(args.pdf)
        else:
            logger.error(f"El archivo {args.pdf} no existe")
            sys.exit(1)
    elif args.process_all:
        process_all_pdfs()
    else:
        logger.info("No se especificó ninguna acción. Use --pdf o --process-all")
        parser = argparse.ArgumentParser()
        parser.print_help()

if __name__ == "__main__":
    main()