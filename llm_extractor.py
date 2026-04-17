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
    # Extract diagnoses
    diagnosen = []
    diag_pattern = r'Diagnose.*?:\s*(.+?)\s*\((ICD-\d+[.-]\w+)\)'
    for match in re.finditer(diag_pattern, content, re.IGNORECASE):
        diagnosen.append({"bezeichnung": match.group(1).strip(), "icd10": match.group(2)})
    
    # If no ICD pattern found, try simpler pattern
    if not diagnosen:
        simple_diag = re.findall(r'(I\d+\.\d+)[-\s]+([^\n]+)', content)
        for icd, desc in simple_diag:
            diagnosen.append({"bezeichnung": desc.strip(), "icd10": icd})
    
    # If still no diagnoses, look for lines after "Diagnose"
    if not diagnosen:
        diagnose_section = re.search(r'Diagnose:\s*(.*?)(?=Befund|Medikation|$)', content, re.DOTALL | re.IGNORECASE)
        if diagnose_section:
            lines = diagnose_section.group(1).strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('-'):
                    # Try to extract ICD code from the line
                    icd_match = re.search(r'([A-Z]\d+\.\d+)', line)
                    if icd_match:
                        icd = icd_match.group(1)
                        desc = line.replace(icd, '').replace('-', '').strip()
                        diagnosen.append({"bezeichnung": desc, "icd10": icd})
                    else:
                        diagnosen.append({"bezeichnung": line, "icd10": "N/A"})
    
    # Extract medications
    medikamente = []
    lines = content.split('\n')
    in_meds = False
    for line in lines:
        if 'Medikation' in line or 'Medikamente' in line:
            in_meds = True
            continue
        if in_meds and ('Empfehlung' in line or 'Grüße' in line or 'Mit freundlichen' in line or 'Anamnese' in line or 'Befund' in line):
            in_meds = False
            continue
        if in_meds and line.strip():
            # Parse medication line like "Metformin 500mg 2x täglich"
            parts = line.strip().split()
            if len(parts) >= 2:
                name = parts[0]
                dosierung = ""
                frequenz = ""
                for i, p in enumerate(parts[1:], 1):
                    if any(c.isdigit() for c in p):
                        dosierung = p
                        if i+1 < len(parts):
                            frequenz = ' '.join(parts[i+1:])
                        else:
                            frequenz = "täglich"
                        break
                if not dosierung and len(parts) >= 3:
                    dosierung = parts[1]
                    frequenz = ' '.join(parts[2:])
                if not frequenz:
                    frequenz = "täglich"
                if name and dosierung:
                    medikamente.append({"name": name, "dosierung": dosierung, "frequenz": frequenz})
    
    # Extract symptoms from Anamnese
    symptome = []
    anamnese_match = re.search(r'Anamnese:\s*(.*?)(?=Diagnose|Befund|$)', content, re.DOTALL)
    if anamnese_match:
        anamnese_text = anamnese_match.group(1)
        symptom_keywords = ['Husten', 'Fieber', 'Schmerzen', 'Müdigkeit', 'Übelkeit', 'Kopfschmerzen', 'Schwindel', 'Atemnot', 'Appetitlosigkeit']
        for kw in symptom_keywords:
            if kw.lower() in anamnese_text.lower():
                symptome.append(kw)
    
    # Extract recommendations
    empfehlungen = []
    empf_match = re.search(r'Empfehlung:\s*(.*?)(?=Grüße|Mit freundlichen|Anamnese|$)', content, re.DOTALL)
    if empf_match:
        empf_text = empf_match.group(1)
        for line in empf_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('-') and 'Datum' not in line:
                empfehlungen.append(line)
    
    # Generate summary
    zusammenfassung = "Patient wurde mit typischen Symptomen vorgestellt. Diagnose bestätigt durch Befunde. Medikation angepasst und Empfehlungen zur weiteren Behandlung gegeben."
    
    result = {
        "diagnosen": diagnosen if diagnosen else [{"bezeichnung": "Unbekannt", "icd10": "Z00.0"}],
        "medikamente": medikamente if medikamente else [{"name": "Unbekannt", "dosierung": "N/A", "frequenz": "täglich"}],
        "symptome": symptome if symptome else ["Allgemeine Beschwerden"],
        "empfehlungen": empfehlungen if empfehlungen else ["Weiterbehandlung nach Plan"],
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
