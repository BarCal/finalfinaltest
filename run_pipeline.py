#!/usr/bin/env python3
"""
Pipeline script to run all extraction steps in sequence:
1. rule_extractor.py
2. llm_extractor.py
3. ner_extractor.py
4. database.py
"""

import subprocess
import sys
import time

def run_script(script_name, step_num, total_steps):
    """Run a single script and measure execution time."""
    print(f"[{step_num}/{total_steps}] {script_name.replace('_', ' ').replace('.py', '')}...", end=" ", flush=True)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=False  # We handle non-zero exit codes manually
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode != 0:
            print(f"FAILED ({elapsed_time:.1f}s)")
            print(f"Error output:\n{result.stderr}")
            return False
        else:
            print(f"done ({elapsed_time:.1f}s)")
            # Optionally print script output if needed for debugging
            # if result.stdout:
            #     print(result.stdout)
            return True
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"FAILED ({elapsed_time:.1f}s)")
        print(f"Exception: {str(e)}")
        return False

def main():
    scripts = [
        "rule_extractor.py",
        "llm_extractor.py",
        "ner_extractor.py",
        "database.py"
    ]
    
    total_steps = len(scripts)
    
    print("Starting medical data extraction pipeline...\n")
    
    for i, script in enumerate(scripts, 1):
        success = run_script(script, i, total_steps)
        if not success:
            print(f"\nPipeline aborted at step {i}/{total_steps}.")
            sys.exit(1)
    
    print("\nPipeline complete. Database saved to medical_records.db")

if __name__ == "__main__":
    main()
