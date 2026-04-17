#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def generate_arztbrief():
    """Generates a realistic synthetic German Arztbrief (doctor's letter)."""
    
    arztbrief = """Dr. med. Thomas Müller
Facharzt für Innere Medizin | Allgemeinmedizin
Gesundheitszentrum am Marktplatz
Marktplatz 15
80331 München

Tel.: 089 / 123 456 78
Fax: 089 / 123 456 79

------------------------------------------------------------

An:
Herrn Michael Weber
Geburtsdatum: 15.03.1968
Hauptstraße 42
80335 München

Krankenkasse: AOK Bayern
Versicherungsnummer: W123456789

München, den 12. Januar 2025

Betreff: Ärztlicher Bericht – Weiterbehandlung und Dokumentation

Sehr geehrte Damen und Herren,
sehr geehrter Herr Weber,

anbei übersende ich Ihnen den aktuellen ärztlichen Bericht bezüglich der 
weiteren Behandlung von Herrn Michael Weber.

ANAMNESE:
Der Patient stellte sich am 08.01.2025 in unserer Praxis vor mit Beschwerden 
von persistierenden Kopfschmerzen, Schwindelgefühlen sowie gelegentlicher 
Atemnot bei Belastung. Zusätzlich berichtete er über nächtliches Schwitzen 
und allgemeine Müdigkeit seit ca. 3 Wochen. Anamnestisch bekannt ist eine 
arterielle Hypertonie seit 2018 sowie ein Typ-2-Diabetes mellitus seit 2020. 
Der Patient ist Nichtraucher, konsumiert gelegentlich Alkohol (ca. 2-3 Bier 
pro Woche). Familienanamnese: Vater verstorben an Myokardinfarkt im Alter 
von 62 Jahren, Mutter leidet an Osteoporose.

DIAGNOSE:
1. Essentielle Hypertonie, Grad II (ICD-10: I10.00)
2. Typ-2-Diabetes mellitus ohne Komplikationen (ICD-10: E11.90)
3. Verdacht auf Schlafapnoe-Syndrom (ICD-10: G47.31) – weitere Abklärung empfohlen

BEFUND:
Allgemeinzustand: reduziert, Ernährungszustand: adipös (BMI 31,2 kg/m²)
Körpergröße: 178 cm, Körpergewicht: 99 kg
Blutdruck: 158/96 mmHg (sitzend, rechter Arm), Puls: 84/min, regelmäßig
Atemfrequenz: 16/min, Temperatur: 36,7°C

Auskultation der Lunge: Vesikuläratmen, keine Rasselgeräusche
Herzaktion: rein, rhythmisch, keine Geräusche
Abdomen: weich, druckdolent, keine Resistenzen palpabel
Neurologisch: orientiert zu allen Qualitäten, Pupillen isokor, Lichtreaktion 
positiv, keine fokalen Defizite

Laborbefunde (vom 08.01.2025):
- HbA1c: 7,8 % (erhöht, Zielwert < 7,0 %)
- Nüchternblutzucker: 142 mg/dl (erhöht)
- Gesamtcholesterin: 245 mg/dl (erhöht)
- LDL-Cholesterin: 158 mg/dl (erhöht)
- HDL-Cholesterin: 38 mg/dl (erniedrigt)
- Triglyzeride: 210 mg/dl (erhöht)
- Kreatinin: 1,1 mg/dl (im Normbereich)
- eGFR: 72 ml/min/1,73m²
- TSH: 2,1 mU/l (normwertig)
- Leberwerte (ALT, AST, GGT): im Normbereich
- Blutbild: Hb 14,2 g/dl, Leukozyten 6.800/µl, Thrombozyten 245.000/µl

EKG: Sinusrhythmus, Frequenz 82/min, Linkstyp, keine Ischämiezeichen

MEDIKATION:
1. Ramipril 5 mg – 1-0-0 (morgens eine Tablette)
2. Metformin 1000 mg – 1-0-1 (morgens und abends je eine Tablette)
3. Atorvastatin 20 mg – 0-0-1 (abends eine Tablette)
4. ASS 100 mg – 1-0-0 (morgens eine Tablette zur Thromboseprophylaxe)

EMPFEHLUNG:
- Regelmäßige Blutdruckselbstmessung (morgens und abends) mit Führung eines 
  Blutdrucktagebuches
- Ernährungsberatung hinsichtlich mediterraner Diät empfohlen
- Gewichtsreduktion durch kalorienarme Ernährung und regelmäßige Bewegung 
  (mindestens 30 Minuten zügiges Gehen täglich)
- Vorstellung zur Polysomnographie beim Pneumologen zum Ausschluss einer 
  Schlafapnoe
- Laborkontrolle (HbA1c, Lipidprofil, Nierenfunktion) in 3 Monaten
- Nächste Vorstellung in unserer Praxis in 4 Wochen zur Verlaufskontrolle

Bei Verschlechterung der Symptomatik oder Auftreten von Brustschmerzen, 
starker Atemnot oder neurologischen Ausfällen bitten wir um sofortige 
Vorstellung.

Für Rückfragen stehen wir Ihnen gerne zur Verfügung.

Mit freundlichen Grüßen,


_________________________
Dr. med. Thomas Müller
Facharzt für Innere Medizin
"""
    
    return arztbrief


def main():
    """Main function to generate and save the Arztbrief."""
    arztbrief_content = generate_arztbrief()
    
    with open("arztbrief.txt", "w", encoding="utf-8") as f:
        f.write(arztbrief_content)
    
    print("Arztbrief wurde erfolgreich als 'arztbrief.txt' gespeichert.")


if __name__ == "__main__":
    main()
