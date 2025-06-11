# 📄 arxiv_analyzer

A modular pipeline for extracting, preprocessing and analyzing arXiv papers using LangChain-style workflows.

---

## Overview

This project lets you:

- 🔍 **Extract** raw text and basic metadata (title, authors, arXiv ID) from PDF files  
- 🧹 **Clean & chunk** long documents into LLM-friendly pieces  
- 🤖 **Run downstream analyses** (summaries, Q&A, embeddings, etc.)  
- 💾 **Save** structured JSON reports and human-readable summaries  

---

## Key Components

### 1. `PDFExtractor`  
- **Input:** path to a PDF  
- **Returns:**  
  - `text` (str): full cleaned text  
  - `metadata` (dict): `{ title, authors, arxiv_id }`

### 2. `TextPreprocessor`  
- **Input:** raw `text` + optional `metadata`  
- **Returns:**  
  - a single structured prompt block (str) or  
  - a list of `{ text: ..., metadata: { section, chunk_part, total_chunks } }`

### 3. JSON Formatter & Saver  
- **Functions:**  
  - `save_paper_analysis(analysis: dict, paper_name: str) → output_path`  
    - Writes a JSON file with analysis + `__metadata__` (timestamp, source)  
    - **Returns:** path to the saved JSON  
  - `format_json_for_human(analysis: dict) → str`  
    - Strips internal metadata and builds a readable report  

### 4. `merge_results(results_list: list[dict]) → dict`  
- Combines multiple partial analyses into one unified dictionary

---

## Basic Usage

```bash
# (Assumes you have a Python 3.8+ environment)
pip install -r requirements.txt
