#!/usr/bin/env python3
"""
database.py - Creates a SQLite database and inserts extracted medical data.

Reads patient_info.json, medical_data.json, ner_results.json, and arztbrief.txt
to populate the medical_records.db database.
"""

import sqlite3
import json
from datetime import datetime
import os

DB_NAME = "medical_records.db"

def create_tables(conn):
    """Create the database schema if tables don't exist."""
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            geburtsdatum TEXT,
            address TEXT,
            krankenkasse TEXT,
            versicherungsnummer TEXT,
            UNIQUE(name, geburtsdatum, versicherungsnummer)
        )
    """)
    
    # Create documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER REFERENCES patients(id),
            raw_text TEXT,
            behandlungsdatum TEXT,
            arzt_name TEXT,
            zusammenfassung TEXT,
            created_at TEXT,
            UNIQUE(patient_id, behandlungsdatum, raw_text)
        )
    """)
    
    # Create entities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER REFERENCES documents(id),
            entity_text TEXT,
            entity_type TEXT,
            source TEXT,
            confidence REAL,
            UNIQUE(document_id, entity_text, entity_type, source)
        )
    """)
    
    conn.commit()

def load_json_file(filename):
    """Load a JSON file, return None if not found."""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found.")
        return None
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_text_file(filename):
    """Load a text file, return empty string if not found."""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found.")
        return ""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def insert_patient(conn, patient_data):
    """Insert patient data and return the patient ID."""
    if not patient_data:
        return None
    
    cursor = conn.cursor()
    
    name = patient_data.get('patient_name')
    geburtsdatum = patient_data.get('geburtsdatum')
    address = patient_data.get('address')
    krankenkasse = patient_data.get('krankenkasse')
    versicherungsnummer = patient_data.get('versicherungsnummer')
    
    cursor.execute("""
        INSERT OR IGNORE INTO patients (name, geburtsdatum, address, krankenkasse, versicherungsnummer)
        VALUES (?, ?, ?, ?, ?)
    """, (name, geburtsdatum, address, krankenkasse, versicherungsnummer))
    
    # Get the ID (either newly inserted or existing)
    cursor.execute("""
        SELECT id FROM patients 
        WHERE name = ? AND geburtsdatum = ? AND versicherungsnummer = ?
    """, (name, geburtsdatum, versicherungsnummer))
    
    result = cursor.fetchone()
    conn.commit()
    return result[0] if result else None

def insert_document(conn, patient_id, raw_text, patient_data, medical_data):
    """Insert document data and return the document ID."""
    cursor = conn.cursor()
    
    behandlungsdatum = patient_data.get('behandlungsdatum') if patient_data else None
    arzt_name = patient_data.get('arzt_name') if patient_data else None
    zusammenfassung = medical_data.get('zusammenfassung') if medical_data else None
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR IGNORE INTO documents (patient_id, raw_text, behandlungsdatum, arzt_name, zusammenfassung, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (patient_id, raw_text, behandlungsdatum, arzt_name, zusammenfassung, created_at))
    
    # Get the ID
    cursor.execute("""
        SELECT id FROM documents 
        WHERE patient_id = ? AND behandlungsdatum = ? AND raw_text = ?
    """, (patient_id, behandlungsdatum, raw_text))
    
    result = cursor.fetchone()
    conn.commit()
    return result[0] if result else None

def insert_entities(conn, document_id, medical_data, ner_results):
    """Insert entities from LLM and NER sources."""
    cursor = conn.cursor()
    entities_inserted = 0
    
    if medical_data:
        # Insert diagnoses from LLM
        for diag in medical_data.get('diagnosen', []):
            bezeichnung = diag.get('bezeichnung', '')
            icd10 = diag.get('icd10', '')
            entity_text = f"{bezeichnung} ({icd10})" if icd10 else bezeichnung
            
            cursor.execute("""
                INSERT OR IGNORE INTO entities (document_id, entity_text, entity_type, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, entity_text, 'DIAGNOSIS', 'llm', None))
            entities_inserted += cursor.rowcount
        
        # Insert medications from LLM
        for med in medical_data.get('medikamente', []):
            name = med.get('name', '')
            dosierung = med.get('dosierung', '')
            frequenz = med.get('frequenz', '')
            entity_text = f"{name} ({dosierung}, {frequenz})"
            
            cursor.execute("""
                INSERT OR IGNORE INTO entities (document_id, entity_text, entity_type, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, entity_text, 'MEDICATION', 'llm', None))
            entities_inserted += cursor.rowcount
        
        # Insert symptoms from LLM
        for symptom in medical_data.get('symptome', []):
            cursor.execute("""
                INSERT OR IGNORE INTO entities (document_id, entity_text, entity_type, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, symptom, 'SYMPTOM', 'llm', None))
            entities_inserted += cursor.rowcount
        
        # Insert recommendations from LLM
        for empf in medical_data.get('empfehlungen', []):
            cursor.execute("""
                INSERT OR IGNORE INTO entities (document_id, entity_text, entity_type, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, empf, 'RECOMMENDATION', 'llm', None))
            entities_inserted += cursor.rowcount
    
    if ner_results:
        # Insert NER entities
        for ent in ner_results:
            entity_text = ent.get('word', '')
            entity_type = ent.get('entity_group', 'UNKNOWN')
            confidence = ent.get('score')
            
            cursor.execute("""
                INSERT OR IGNORE INTO entities (document_id, entity_text, entity_type, source, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, entity_text, entity_type, 'ner', confidence))
            entities_inserted += cursor.rowcount
    
    conn.commit()
    return entities_inserted

def print_summary(conn):
    """Print a summary of rows in each table."""
    cursor = conn.cursor()
    
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)
    
    for table in ['patients', 'documents', 'entities']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count} rows")
    
    print("=" * 50)

def main():
    # Load all input files
    print("Loading input files...")
    patient_data = load_json_file('patient_info.json')
    medical_data = load_json_file('medical_data.json')
    ner_results = load_json_file('ner_results.json')
    raw_text = load_text_file('arztbrief.txt')
    
    # Connect to database
    print(f"Connecting to {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    
    try:
        # Create tables
        print("Creating tables...")
        create_tables(conn)
        
        # Insert patient
        print("Inserting patient data...")
        patient_id = insert_patient(conn, patient_data)
        if not patient_id:
            print("Error: Could not insert or find patient.")
            return
        
        # Insert document
        print("Inserting document...")
        document_id = insert_document(conn, patient_id, raw_text, patient_data, medical_data)
        if not document_id:
            print("Error: Could not insert or find document.")
            return
        
        # Insert entities
        print("Inserting entities...")
        entities_count = insert_entities(conn, document_id, medical_data, ner_results)
        
        # Print summary
        print_summary(conn)
        print(f"\nSuccessfully processed {entities_count} entity insertions.")
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
