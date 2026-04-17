#!/usr/bin/env python3
"""
Extract structured patient information from a German Arztbrief using regex.
Saves the result as a Python dictionary and JSON file.
"""

import re
import json

try:
    import dateparser
except ImportError:
    print("Installing dateparser...")
    import subprocess
    subprocess.check_call(["pip", "install", "dateparser"])
    import dateparser


def parse_german_date(date_str):
    """Parse a German date string to ISO format YYYY-MM-DD."""
    if not date_str:
        return None
    
    # Try dateparser first (handles various German formats)
    parsed = dateparser.parse(date_str, languages=['de'])
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    
    # Fallback: try common German date patterns manually
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return None


def extract_patient_info(text):
    """Extract structured patient information from Arztbrief text."""
    
    info = {
        "patient_name": None,
        "geburtsdatum": None,
        "address": None,
        "krankenkasse": None,
        "versicherungsnummer": None,
        "behandlungsdatum": None,
        "arzt_name": None,
        "arzt_fachrichtung": None,
    }
    
    # --- Extract Patient Name ---
    # Look for "An:" block with Herr/Frau pattern - name must be on single line
    patient_name_pattern = r'(?:An:\s*\n\s*)?(Herrn?|Frau(?:en)?|Fr\.)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)'
    match = re.search(patient_name_pattern, text)
    if match:
        title = match.group(1)
        name = match.group(2).strip()
        # Only take the first line (stop at newline)
        name = name.split('\n')[0]
        # Normalize title
        if title.lower() in ['herrn', 'herr']:
            info["patient_name"] = f"Herr {name}"
        elif title.lower() in ['frau', 'frauen', 'fr.']:
            info["patient_name"] = f"Frau {name}"
        else:
            info["patient_name"] = name
    
    # --- Extract Geburtsdatum (Date of Birth) ---
    geburtsdatum_pattern = r'Geburtsdatum[:\s]+(\d{1,2}\.\d{1,2}\.\d{4})'
    match = re.search(geburtsdatum_pattern, text)
    if match:
        info["geburtsdatum"] = parse_german_date(match.group(1))
    
    # --- Extract Address ---
    # Find address lines after patient name and birthdate
    # Pattern: street line followed by postal code + city line
    address_pattern = r'Geburtsdatum[:\s]+\d{1,2}\.\d{1,2}\.\d{4}\s*\n([^\n]+\d+[^\n]*\n\d{5}\s+[^\n]+)'
    match = re.search(address_pattern, text)
    if match:
        address_lines = match.group(1).strip().split('\n')
        if len(address_lines) >= 2:
            street = address_lines[0].strip()
            city = address_lines[-1].strip()
            info["address"] = f"{street}, {city}"
        elif len(address_lines) == 1:
            info["address"] = address_lines[0].strip()
    
    # --- Extract Krankenkasse (Health Insurer) ---
    krankenkasse_pattern = r'Krankenkasse[:\s]+([^\n]+)'
    match = re.search(krankenkasse_pattern, text)
    if match:
        info["krankenkasse"] = match.group(1).strip()
    
    # --- Extract Versicherungsnummer ---
    versicherungsnummer_pattern = r'Versicherungsnummer[:\s]+([A-Z]?\d{9,12})'
    match = re.search(versicherungsnummer_pattern, text)
    if match:
        info["versicherungsnummer"] = match.group(1).strip()
    
    # --- Extract Behandlungsdatum (Appointment Date) ---
    # Look for date line like "Muenchen, den 12. Januar 2025"
    behandlungsdatum_pattern = r'([A-Za-z]+),\s*den\s+(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s*\d{4})'
    match = re.search(behandlungsdatum_pattern, text)
    if match:
        date_str = match.group(2)
        info["behandlungsdatum"] = parse_german_date(date_str)
    
    # --- Extract Arzt Name ---
    # First try signature at end: look for underscores followed by doctor name
    arzt_signature_pattern = r'_{3,}\s*\n(Dr\.[^\n]+)'
    match = re.search(arzt_signature_pattern, text)
    if match:
        info["arzt_name"] = match.group(1).strip()
    else:
        # Try sender block at beginning
        arzt_sender_pattern = r'^(Dr\.[^\n]+)'
        match = re.search(arzt_sender_pattern, text, re.MULTILINE)
        if match:
            info["arzt_name"] = match.group(1).strip()
    
    # --- Extract Arzt Fachrichtung (Specialty) ---
    # Look for "Facharzt für ..." pattern - get first occurrence (from header)
    fachrichtung_pattern = r'^(Facharzt\s+für\s+[^\n]+)\s*$'
    match = re.search(fachrichtung_pattern, text, re.MULTILINE)
    if match:
        info["arzt_fachrichtung"] = match.group(1).strip()
    
    return info


def main():
    # Read the Arztbrief file
    input_file = "arztbrief.txt"
    output_json = "patient_info.json"
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return
    
    # Extract patient information
    patient_info = extract_patient_info(text)
    
    # Print the dictionary
    print("Extracted Patient Information:")
    print("=" * 50)
    for key, value in patient_info.items():
        print(f"{key}: {value}")
    
    # Save as JSON
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(patient_info, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully saved to {output_json}")
    except Exception as e:
        print(f"Error saving JSON: {e}")


if __name__ == "__main__":
    main()
