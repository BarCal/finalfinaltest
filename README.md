# Medical Records Extraction Pipeline & Dashboard

A complete NLP pipeline for extracting structured medical information from German doctor's letters (Arztbriefe) with a professional interactive dashboard.

## Overview

This project provides:
1. **Synthetic Data Generation** - Creates realistic German medical letters
2. **Multi-Method Extraction** - Rule-based, LLM-based, and NER-based extraction
3. **SQLite Database** - Structured storage of all extracted data
4. **Interactive Dashboard** - Professional Streamlit visualization

## Installation

### Install Core Dependencies
```bash
pip install dateparser transformers torch ollama
```

### Install Dashboard Dependencies
```bash
pip install streamlit plotly pandas
```

## Usage

### Run the Complete Pipeline
```bash
python run_pipeline.py
```

This executes all extraction steps in sequence:
1. Rule-based extraction (regex)
2. LLM-based extraction (Ollama/mistral-small)
3. NER extraction (GerMedBERT)
4. Database insertion

### Launch the Dashboard
```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Project Structure

```
├── generate_letter.py      # Synthetic Arztbrief generator
├── rule_extractor.py       # Regex-based patient info extraction
├── llm_extractor.py        # LLM-based medical data extraction
├── ner_extractor.py        # BERT-based NER extraction
├── database.py             # SQLite database creation
├── run_pipeline.py         # Pipeline orchestrator
├── dashboard.py            # Streamlit dashboard
├── arztbrief.txt           # Generated medical letter
├── patient_info.json       # Extracted patient data
├── medical_data.json       # Extracted medical data (LLM)
├── ner_results.json        # NER entities
└── medical_records.db      # SQLite database
```

## Dashboard Features

### 1. Overview Page
- Key metrics (patients, documents, entities)
- Entity distribution charts
- Data source breakdown
- Recent documents table

### 2. Patient Details
- Personal information
- Insurance details
- Treatment information

### 3. Medical Analysis
- Diagnoses with ICD-10 codes
- Medications with dosages
- Symptoms and recommendations
- AI-generated summary

### 4. NER Entities
- All extracted entities with confidence scores
- Filterable by entity type
- Interactive visualizations

### 5. Database Stats
- Table sizes
- Entity breakdown by source
- Data previews

### 6. Raw Document
- Original Arztbrief view
- Download capability

## Data Flow

```
Arztbrief (TXT)
    │
    ├──→ Rule Extractor ──→ patient_info.json
    ├──→ LLM Extractor ───→ medical_data.json
    └──→ NER Extractor ───→ ner_results.json
              │
              └──────→ Database (SQLite) ←──────┘
                              │
                              └──→ Dashboard (Streamlit)
```

## Notes

- **Ollama**: Ensure Ollama is running locally (`ollama serve`) for LLM extraction
- **HuggingFace**: GerMedBERT may require authentication for gated models
- **Fallbacks**: The pipeline includes fallback mechanisms for missing dependencies

## Requirements

- Python 3.8+
- Streamlit 1.28+
- Plotly 5.17+
- Pandas 2.0+
- Transformers
- PyTorch
- Ollama Python client
- Dateparser
