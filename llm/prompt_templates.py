#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plantillas de prompts para interacción con LLMs.
"""

from typing import List, Dict, Any

def get_paper_analysis_prompt(paper_text: str) -> str:
    """
    Genera un prompt para el análisis de papers académicos.
    
    Args:
        paper_text: Texto del paper a analizar
        
    Returns:
        Prompt formateado
    """
    return f"""
Analiza el siguiente paper académico y proporciona un resumen estructurado en formato JSON con la siguiente información:

1. Un resumen conciso del paper (máximo 250 palabras)
2. Los principales resultados y contribuciones
3. Una evaluación de si el paper logró sus objetivos propuestos (true/false)
4. Las métricas de rendimiento reportadas (si aplica)

El paper es el siguiente:

-----
{paper_text}
-----

Responde ÚNICAMENTE con un objeto JSON con los siguientes campos:
- "resumen": string con el resumen del paper
- "resultados": string con los principales resultados y contribuciones
- "exito": boolean indicando si el paper logró sus objetivos
- "performance": string o número con las métricas de rendimiento relevantes
- "nombre": string con el título del paper (si es identificable)

Asegúrate de que tu respuesta sea un JSON válido que pueda ser parseado directamente.
"""

def get_specific_section_prompt(paper_text: str, section: str) -> str:
    """
    Genera un prompt para analizar una sección específica del paper.
    
    Args:
        paper_text: Texto del paper
        section: Sección a analizar (methodology, results, etc.)
        
    Returns:
        Prompt formateado
    """
    section_prompts = {
        "methodology": "Analiza la metodología descrita en este paper. Identifica los principales métodos, algoritmos, datasets y técnicas utilizadas. Explica brevemente el enfoque experimental.",
        "results": "Analiza los resultados presentados en este paper. Identifica los principales hallazgos, las métricas de evaluación utilizadas y los valores obtenidos. Compara con otros métodos si se proporciona esta información.",
        "conclusion": "Resume las principales conclusiones de este paper. Identifica las limitaciones mencionadas y las direcciones futuras propuestas por los autores."
    }
    
    prompt_text = section_prompts.get(
        section,
        f"Analiza la sección '{section}' de este paper y resume sus puntos clave."
    )
    
    return f"""
{prompt_text}

El paper es el siguiente:

-----
{paper_text}
-----

Responde en formato JSON con la siguiente estructura:
{{
  "analisis": "tu análisis detallado aquí",
  "puntos_clave": ["punto clave 1", "punto clave 2", ...]
}}

Asegúrate de que tu respuesta sea un JSON válido.
"""

def get_paper_comparison_prompt(paper1_text: str, paper2_text: str) -> str:
    """
    Genera un prompt para comparar dos papers.
    
    Args:
        paper1_text: Texto del primer paper
        paper2_text: Texto del segundo paper
        
    Returns:
        Prompt formateado
    """
    return f"""
Compara los siguientes dos papers académicos. Identifica similitudes y diferencias en términos de:
1. Objetivos y enfoque
2. Metodologías utilizadas
3. Resultados y conclusiones
4. Fortalezas y debilidades

Primer paper:
-----
{paper1_text}
-----

Segundo paper:
-----
{paper2_text}
-----

Responde en formato JSON con la siguiente estructura:
{{
  "similitudes": ["similitud 1", "similitud 2", ...],
  "diferencias": ["diferencia 1", "diferencia 2", ...],
  "comparacion_resultados": "análisis comparativo de resultados",
  "recomendacion": "qué paper parece más robusto/innovador y por qué"
}}

Asegúrate de que tu respuesta sea un JSON válido.
"""

def get_chunk_initial_prompt(chunk_text: str, chunk_info: str) -> str:
    """
    Genera un prompt para el primer chunk de un paper.
    
    Args:
        chunk_text: Texto del chunk
        chunk_info: Información sobre el chunk
        
    Returns:
        Prompt formateado
    """
    return f"""
Estás analizando un paper académico que ha sido dividido en múltiples partes debido a su longitud.
Esta es la {chunk_info}.

Necesito que analices esta parte y proporciones un resumen parcial, enfocándote en:
1. Los conceptos clave introducidos
2. Los métodos o enfoques presentados
3. Cualquier resultado preliminar mencionado

Texto del chunk:
-----
{chunk_text}
-----

Responde en formato JSON con los siguientes campos:
- "resumen": string con un resumen conciso de esta parte
- "resultados": string con los hallazgos o contribuciones mencionados en esta parte
- "conceptos_clave": array de strings con los conceptos importantes

Asegúrate de que tu respuesta sea un JSON válido que pueda ser parseado directamente.
"""

def get_chunk_middle_prompt(chunk_text: str, chunk_info: str) -> str:
    """
    Genera un prompt para chunks intermedios de un paper.
    
    Args:
        chunk_text: Texto del chunk
        chunk_info: Información sobre el chunk
        
    Returns:
        Prompt formateado
    """
    return f"""
Continúas analizando un paper académico dividido en múltiples partes.
Esta es la {chunk_info}.

Analiza esta parte y proporciona un resumen parcial, enfocándote en:
1. Los métodos detallados o experimentos descritos
2. Los resultados presentados
3. Las discusiones o análisis realizados

Texto del chunk:
-----
{chunk_text}
-----

Responde en formato JSON con los siguientes campos:
- "resumen": string con un resumen conciso de esta parte
- "resultados": string con los hallazgos o contribuciones mencionados en esta parte
- "metodos": array de strings con los métodos o técnicas descritos

Asegúrate de que tu respuesta sea un JSON válido que pueda ser parseado directamente.
"""

def get_chunk_final_prompt(chunk_text: str, chunk_info: str) -> str:
    """
    Genera un prompt para el último chunk de un paper.
    
    Args:
        chunk_text: Texto del chunk
        chunk_info: Información sobre el chunk
        
    Returns:
        Prompt formateado
    """
    return f"""
Estás finalizando el análisis de un paper académico dividido en múltiples partes.
Esta es la {chunk_info}.

Analiza esta parte final y proporciona un resumen, enfocándote en:
1. Las conclusiones presentadas
2. Las limitaciones mencionadas
3. El trabajo futuro propuesto
4. La evaluación general de los resultados

Texto del chunk:
-----
{chunk_text}
-----

Responde en formato JSON con los siguientes campos:
- "resumen": string con un resumen conciso de esta parte
- "conclusiones": string con las conclusiones principales
- "limitaciones": array de strings con las limitaciones mencionadas
- "trabajo_futuro": string con el trabajo futuro propuesto

Asegúrate de que tu respuesta sea un JSON válido que pueda ser parseado directamente.
"""

def get_consolidation_prompt(chunk_results: List[Dict[str, Any]], paper_name: str) -> str:
    """
    Genera un prompt para consolidar los resultados de múltiples chunks.
    
    Args:
        chunk_results: Lista de resultados por chunk
        paper_name: Nombre del paper
        
    Returns:
        Prompt formateado
    """
    # Convertir chunk_results a formato legible
    chunks_text = ""
    for i, chunk in enumerate(chunk_results):
        chunks_text += f"\nPARTE {i+1}:\n"
        chunks_text += f"Resumen: {chunk.get('resumen', 'No disponible')}\n"
        chunks_text += f"Resultados: {chunk.get('resultados', 'No disponible')}\n"
        # Añadir otros campos si están disponibles
        for key, value in chunk.items():
            if key not in ['resumen', 'resultados', 'nombre', 'exito', 'performance']:
                chunks_text += f"{key}: {value}\n"
    
    return f"""
Has analizado el paper "{paper_name}" en múltiples partes.
Ahora necesito que consolides toda la información en un único análisis completo.

A continuación tienes los resúmenes de cada parte analizada:
{chunks_text}

Basándote en toda esta información, proporciona un análisis final completo del paper en formato JSON con los siguientes campos:
- "nombre": string con el título del paper
- "resumen": string con un resumen conciso y completo del paper 
- "resultados": string con los principales resultados y contribuciones (Si puedes da datos numericos y benchmarks)
- "exito": boolean indicando si el paper logró sus objetivos propuestos
- "performance": string o número con las métricas de rendimiento relevantes

Asegúrate de que tu respuesta sea un JSON válido que pueda ser parseado directamente.
"""