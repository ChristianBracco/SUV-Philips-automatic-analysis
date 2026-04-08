#!/usr/bin/env python3
"""
Verifica versione SUV Analyzer
"""
import hashlib

# Calcola MD5 di suv_analyzer.py
with open('suv_analyzer.py', 'rb') as f:
    file_hash = hashlib.md5(f.read()).hexdigest()

print(f"✅ MD5 Hash: {file_hash}")
print(f"✅ Expected:  [nuovo hash per v3.3 FINAL]")

# Verifica presenza try-catch in process_secondary_capture
with open('suv_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'except Exception as e:' in content and 'Skipping frame' in content:
    print("✅ Try-catch su frame processing: PRESENTE")
else:
    print("❌ Try-catch su frame processing: MANCANTE")

if 'Skipping SC processing' in content:
    print("✅ Try-catch su single-frame SC: PRESENTE")
else:
    print("❌ Try-catch su single-frame SC: MANCANTE")

print("\n📋 Se vedi ❌, devi aggiornare suv_analyzer.py dal ZIP!")
