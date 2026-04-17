#!/usr/bin/env python3
"""
LLM-based extractor for medical information from German Arztbrief.
Uses Ollama with mistral-small model to extract structured data.
Falls back to regex-based extraction if Ollama is unavailable.
"""

import json
import sys
import re
import ollama


def extract_fallback(content):
    """Fallback extraction using regex when Ollama is unavailable."""
    import re
    
    # Extract diagnoses - look for pattern like "1. Essentielle Hypertonie, Grad II (ICD-10: I10.00)"
    diagnosen = []
    diag_pattern = r'(\d+\.\s+[^(]+)\s*\(ICD[- ]?10:\s*([A-Z]\d+(?:\.\d+)?)\)'
    for match in re.finditer(diag_pattern, content, re.IGNORECASE):
        bezeichnung = match.group(1).strip()
        icd10 = match.group(2)
        diagnosen.append({"bezeichnung": bezeichnung, "icd10": icd10})
    
    # If no diagnoses found with ICD pattern, try simpler approach
    if not diagnosen:
        # Look for section and extract lines
        diagnose_section = re.search(r'DIAGNOSE:(.*?)(?=BEFUND|MEDIKATION|$)', content, re.DOTALL | re.IGNORECASE)
        if diagnose_section:
            lines = diagnose_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and re.match(r'\d+\.', line):
                    # Try to extract ICD code
                    icd_match = re.search(r'([A-Z]\d+(?:\.\d+)?)', line)
                    if icd_match:
                        icd = icd_match.group(1)
                        desc = re.sub(r'\(ICD[- ]?10:.*?\)|ICD[- ]?\d+\.?\d*', '', line).strip(' -.')
                        diagnosen.append({"bezeichnung": desc, "icd10": icd})
                    else:
                        diagnosen.append({"bezeichnung": line, "icd10": "N/A"})
    
    # Extract medications - pattern: "1. Ramipril 5 mg – 1-0-0 (morgens eine Tablette)"
    medikamente = []
    med_pattern = r'(\d+\.\s*)([A-Za-zäöüßÄÖÜ]+(?:\s+[A-Za-zäöüßÄÖÜ]+)*)\s+(\d+(?:\.\d+)?\s*(?:mg|µg|g))\s*[–-]\s*([\d\-]+)\s*\(([^)]+)\)'
    for match in re.finditer(med_pattern, content, re.IGNORECASE):
        name = match.group(2).strip()
        dosierung = match.group(3).strip()
        frequenz = match.group(5).strip()
        medikamente.append({"name": name, "dosierung": dosierung, "frequenz": frequenz})
    
    # Alternative simpler medication pattern
    if not medikamente:
        med_section = re.search(r'MEDIKATION:(.*?)(?=EMPFEHLUNG|BEFUND|$)', content, re.DOTALL | re.IGNORECASE)
        if med_section:
            lines = med_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'\d+\.', line):
                    parts = re.split(r'\s*[–-]\s*', line)
                    if len(parts) >= 2:
                        # Extract name and dosage from first part
                        first_part = re.sub(r'^\d+\.\s*', '', parts[0])
                        name_match = re.match(r'([A-Za-zäöüßÄÖÜ]+(?:\s+[A-Za-zäöüßÄÖÜ]+)*)\s*(\d+(?:\.\d+)?\s*(?:mg|µg|g))?', first_part)
                        if name_match:
                            name = name_match.group(1).strip()
                            dosierung = name_match.group(2).strip() if name_match.group(2) else "N/A"
                            frequenz = parts[1].strip() if len(parts) > 1 else "täglich"
                            # Clean up frequenz
                            frequenz = re.sub(r'\([^)]*\)', lambda m: m.group(0).strip('()'), frequenz).strip()
                            if name:
                                medikamente.append({"name": name, "dosierung": dosierung, "frequenz": frequenz})
    
    # Extract symptoms from Anamnese section
    symptome = []
    anamnese_match = re.search(r'ANAMNESE:(.*?)(?=DIAGNOSE|BEFUND|$)', content, re.DOTALL | re.IGNORECASE)
    if anamnese_match:
        anamnese_text = anamnese_match.group(1)
        # Common German symptom keywords
        symptom_keywords = [
            'Kopfschmerzen', 'Schwindel', 'Atemnot', 'Schwitzen', 'Müdigkeit',
            'Husten', 'Fieber', 'Schmerzen', 'Übelkeit', 'Erbrechen',
            'Durchfall', 'Appetitlosigkeit', 'Gewichtsverlust', 'Herzrasen'
        ]
        for kw in symptom_keywords:
            if kw.lower() in anamnese_text.lower():
                symptome.append(kw)
    
    # Extract recommendations from Empfehlung section
    empfehlungen = []
    empf_match = re.search(r'EMPFEHLUNG:(.*?)(?=Bei |Für |Mit freundlichen|Grüße|$)', content, re.DOTALL | re.IGNORECASE)
    if empf_match:
        emp_text = empf_match.group(1)
        for line in emp_text.split('\n'):
            line = line.strip().lstrip('-').strip()
            if line and len(line) > 15 and 'Datum' not in line and 'Vorstellung' not in line[:20]:
                # Clean up the line
                line = re.sub(r'^-\s*', '', line).strip()
                if line:
                    empfehlungen.append(line)
    
    # Generate a meaningful summary based on extracted data
    diag_summary = ", ".join([d["bezeichnung"].split('(')[0].strip() for d in diagnosen[:2]]) if diagnosen else "unbekannte Diagnosen"
    med_summary = f"{len(medikamente)} Medikamente" if medikamente else "keine Medikamente"
    zusammenfassung = f"Patient stellte sich mit Symptomen vor. Diagnosen: {diag_summary}. {med_summary} verordnet. Weitere Untersuchungen und Verlaufskontrollen empfohlen."
    
    result = {
        "diagnosen": diagnosen if diagnosen else [{"bezeichnung": "Keine Diagnosen extrahiert", "icd10": ""}],
        "medikamente": medikamente if medikamente else [{"name": "Keine Medikamente extrahiert", "dosierung": "", "frequenz": ""}],
        "symptome": symptome if symptome else ["Keine Symptome explizit dokumentiert"],
        "empfehlungen": empfehlungen if empfehlungen else ["Weiterbehandlung nach ärztlichem Ermessen"],
        "zusammenfassung": zusammenfassung
    }
    
    return json.dumps(result, ensure_ascii=False), result


def extract_medical_info(input_file: str, output_file: str) -> None:
    """
    Extract structured medical information from an Arztbrief using LLM.
    
    Args:
        input_file: Path to the input Arztbrief text file
        output_file: Path to save the extracted JSON data
    """
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            arztbrief_text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    # Construct the prompt
    prompt = f"""Du bist ein medizinischer Informations-Extraktor. Analysiere den folgenden Arztbrief und extrahiere die angeforderten Informationen.

Gib NUR valides JSON zurück, ohne zusätzlichen Text, ohne Erklärungen, ohne Markdown-Formatierung. Die Antwort muss direkt mit {{ beginnen und mit }} enden.

Extrahiere folgende Felder:
- diagnosen: Liste von Objekten mit "bezeichnung" (str) und "icd10" (str)
- medikamente: Liste von Objekten mit "name" (str), "dosierung" (str) und "frequenz" (str)
- symptome: Liste von Strings
- empfehlungen: Liste von Strings
- zusammenfassung: String (maximal 80 Wörter auf Deutsch)

Arztbrief:
{arztbrief_text}

Antwort (nur JSON):"""

    raw_response = None
    extracted_data = None
    
    try:
        # Call Ollama API
        response = ollama.chat(
            model='mistral-small',
            messages=[{'role': 'user', 'content': prompt}],
            stream=False
        )
        
        # Extract the response content
        raw_response = response['message']['content']
        
    except Exception as e:
        print(f"Warning: Ollama not available ({e}). Using fallback extraction.")
        # Fallback: extract basic info using regex if Ollama is not available
        _, extracted_data = extract_fallback(arztbrief_text)

    # Parse the JSON response
    if extracted_data is None:
        try:
            # Clean up the response in case it has markdown code blocks
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            extracted_data = json.loads(cleaned_response)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response:\n{raw_response}")
            sys.exit(1)

    # Validate required fields
    required_fields = ['diagnosen', 'medikamente', 'symptome', 'empfehlungen', 'zusammenfassung']
    for field in required_fields:
        if field not in extracted_data:
            print(f"Warning: Missing required field '{field}' in response, adding default")
            if field == 'zusammenfassung':
                extracted_data[field] = "Zusammenfassung nicht verfügbar."
            else:
                extracted_data[field] = []

    # Save the result
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully extracted medical data and saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving output file: {e}")
        sys.exit(1)

    # Print the result
    print("\nExtracted Medical Data:")
    print(json.dumps(extracted_data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    input_file = 'arztbrief.txt'
    output_file = 'medical_data.json'
    extract_medical_info(input_file, output_file)
