#!/usr/bin/env python3
"""
LLM-based extractor for medical information from German Arztbrief.
Uses Ollama with mistral-small model to extract structured data.
"""

import json
import sys
import ollama


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
        print(f"Error calling Ollama API: {e}")
        sys.exit(1)

    # Parse the JSON response
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
            print(f"Error: Missing required field '{field}' in response")
            print(f"Raw response:\n{raw_response}")
            sys.exit(1)

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
