#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plantillas de prompts para interacción con LLMs.
"""

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