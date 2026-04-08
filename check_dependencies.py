#!/usr/bin/env python3
"""
Test script per verificare dipendenze Python
"""

import sys

def check_module(name):
    try:
        __import__(name)
        print(f"✅ {name} - OK")
        return True
    except ImportError:
        print(f"❌ {name} - MANCANTE")
        return False

print("=" * 50)
print("  SUV Analyzer - Dependency Check")
print("=" * 50)
print()

print(f"Python version: {sys.version}")
print()

modules = [
    'pydicom',
    'numpy',
    'cv2',  # opencv-python
    'PIL',  # pillow
    'matplotlib'
]

all_ok = True
for mod in modules:
    if not check_module(mod):
        all_ok = False

print()
if all_ok:
    print("✅ Tutte le dipendenze sono installate!")
    print()
    print("Puoi avviare il server con:")
    print("  bun run server.ts")
else:
    print("❌ Alcune dipendenze mancano.")
    print()
    print("Installa con:")
    if sys.platform == 'win32':
        print("  python -m pip install pydicom numpy opencv-python pillow matplotlib --break-system-packages")
    else:
        print("  python3 -m pip install pydicom numpy opencv-python pillow matplotlib")

print()
