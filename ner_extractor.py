#!/usr/bin/env python3
"""
NER Extractor using GerMedBERT/medbert-512 for German medical texts.
Handles 512 token limit by chunking with overlap and merging results.
Falls back to rule-based NER if the model is unavailable (gated repo).
"""

import json
import re
from collections import defaultdict

def chunk_text(text, chunk_size=400, overlap=50):
    """
    Split text into overlapping chunks based on whitespace.
    Returns list of (chunk_text, start_offset) tuples.
    """
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        return [(text, 0)]
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        
        # Calculate character offset for this chunk
        # We need to find where this chunk starts in the original text
        if start == 0:
            char_start = 0
        else:
            # Find the position of the first word of this chunk in original text
            first_word = words[start]
            char_start = text.find(first_word, 0)
            if char_start == -1:
                char_start = 0
        
        chunks.append((chunk_text, char_start))
        
        # Move start pointer, accounting for overlap
        start += chunk_size - overlap
        
        if start >= len(words):
            break
    
    return chunks


def run_ner_on_chunks(chunks, ner_pipeline):
    """
    Run NER on each chunk and adjust character offsets.
    """
    all_entities = []
    
    for chunk_text, offset in chunks:
        try:
            entities = ner_pipeline(chunk_text)
            
            # Adjust start and end positions by the chunk offset
            for entity in entities:
                entity['start'] += offset
                entity['end'] += offset
                all_entities.append(entity)
                
        except Exception as e:
            print(f"Error processing chunk at offset {offset}: {e}")
            continue
    
    return all_entities


def deduplicate_entities(entities):
    """
    Deduplicate entities by their text content and label.
    Keep the one with highest confidence score.
    """
    seen = {}
    
    for entity in entities:
        key = (entity['word'].strip(), entity['entity_group'])
        
        if key not in seen or entity['score'] > seen[key]['score']:
            seen[key] = entity
    
    return list(seen.values())


def rule_based_ner(text):
    """
    Fallback rule-based NER extraction when model is unavailable.
    Extracts common medical entities using regex patterns.
    """
    entities = []
    
    # Patterns for different entity types
    patterns = [
        # Diagnoses / ICD codes
        (r'\b([A-Z]\d{2}\.\d+)\b', 'DIAGNOSIS_CODE', 0.95),
        (r'(Diabetes mellitus|Hypertonie|COPD|Asthma|Infekt)', 'DIAGNOSIS', 0.9),
        
        # Medications
        (r'\b(Metformin|Ramipril|Bisoprolol|Aspirin|Ibuprofen|Paracetamol|Omeprazol|Simvastatin)\b', 'MEDICATION', 0.9),
        (r'\b(\d+\s*mg)\b', 'DOSAGE', 0.85),
        (r'\b(1x|2x|3x|täglich|morgens|abends|nach Bedarf)\b', 'FREQUENCY', 0.8),
        
        # Symptoms
        (r'\b(Husten|Fieber|Schmerzen|Müdigkeit|Übelkeit|Kopfschmerzen|Schwindel|Atemnot)\b', 'SYMPTOM', 0.85),
        
        # Lab values
        (r'\b(\d+,\d+\s*(mg/dl|mmol/l|U/l|g/l))\b', 'LAB_VALUE', 0.8),
        (r'\b(HbA1c|Cholesterin|LDL|HDL|Triglyceride|Kreatinin)\b', 'LAB_TEST', 0.85),
        
        # Body measurements
        (r'\b(\d+\s*cm)\b', 'HEIGHT', 0.75),
        (r'\b(\d+\s*kg)\b', 'WEIGHT', 0.75),
        (r'\b(BMI\s*[:=]?\s*\d+,\d+|\d+,\d+\s*BMI)\b', 'BMI', 0.8),
        
        # Dates
        (r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b', 'DATE', 0.7),
        
        # Names (crude approximation)
        (r'\b(Dr\.\s+(?:med\.)?\s*[A-Z][a-z]+\s+[A-Z][a-z]+)\b', 'DOCTOR_NAME', 0.8),
        (r'\b(?:Herr|Frau)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b', 'PATIENT_NAME', 0.75),
    ]
    
    for pattern, entity_type, base_score in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({
                'word': match.group(0),
                'entity_group': entity_type,
                'score': base_score,
                'start': match.start(),
                'end': match.end()
            })
    
    return entities


def print_entity_table(entities):
    """
    Print a formatted table of entities.
    """
    print("\n" + "=" * 80)
    print(f"{'Entity Text':<40} {'Label':<20} {'Confidence':<10}")
    print("=" * 80)
    
    for entity in sorted(entities, key=lambda x: x['start']):
        word = entity['word'][:38] + ".." if len(entity['word']) > 40 else entity['word']
        label = entity['entity_group']
        score = f"{entity['score']:.4f}"
        print(f"{word:<40} {label:<20} {score:<10}")
    
    print("=" * 80)


def print_summary(entities):
    """
    Print summary of entities per label type.
    """
    counts = defaultdict(int)
    for entity in entities:
        counts[entity['entity_group']] += 1
    
    print("\n" + "=" * 40)
    print("SUMMARY: Entities per Label Type")
    print("=" * 40)
    
    for label, count in sorted(counts.items()):
        print(f"{label:<25} {count:>5}")
    
    print("-" * 40)
    print(f"{'TOTAL':<25} {sum(counts.values()):>5}")
    print("=" * 40)


def main():
    # Read input file
    try:
        with open('arztbrief.txt', 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print("Error: arztbrief.txt not found")
        return
    
    print("Loading GerMedBERT/medbert-512 model...")
    print("(This may take a moment on first run)")
    
    use_fallback = False
    ner = None
    
    try:
        from transformers import pipeline
        ner = pipeline(
            "ner", 
            model="GerMedBERT/medbert-512",
            aggregation_strategy="simple",
            device=-1  # Use CPU; set to 0 for GPU if available
        )
    except Exception as e:
        print(f"Warning: Could not load GerMedBERT model ({e})")
        print("Using fallback rule-based NER extraction...")
        use_fallback = True
    
    if use_fallback:
        print("Running rule-based NER extraction...")
        all_entities = rule_based_ner(text)
    else:
        print("Splitting text into chunks (400 tokens, 50 token overlap)...")
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        print(f"Created {len(chunks)} chunk(s)")
        
        print("Running NER on chunks...")
        all_entities = run_ner_on_chunks(chunks, ner)
    
    print("Deduplicating entities...")
    unique_entities = deduplicate_entities(all_entities)
    
    # Print results
    print_entity_table(unique_entities)
    print_summary(unique_entities)
    
    # Save results to JSON
    output_data = [
        {
            'word': entity['word'],
            'entity_group': entity['entity_group'],
            'score': entity['score'],
            'start': entity['start'],
            'end': entity['end']
        }
        for entity in unique_entities
    ]
    
    # Sort by start position for consistent output
    output_data.sort(key=lambda x: x['start'])
    
    with open('ner_results.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to ner_results.json ({len(output_data)} entities)")


if __name__ == "__main__":
    main()
