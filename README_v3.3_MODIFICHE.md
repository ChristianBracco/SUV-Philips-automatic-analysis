# 🔥 SUV Analyzer v3.3 - AGGIORNAMENTO CRITICO

## 📦 MODIFICHE INCLUSE

### ✨ **1. SUPPORTO SECONDARY CAPTURE**
- ✅ Riconoscimento automatico SC tramite SOP Class UID
- ✅ SC visualizzabili nel viewer come serie normali
- ✅ Supporto multi-frame SC

**File modificati:**
- `api_scan_folder.py` - aggiunto riconoscimento SC

### 🎨 **2. PLOT NEMA COMPLETAMENTE RINNOVATI**
- ✅ Stile moderno dark/neon professionale
- ✅ Layout spaziale 2x3 per galleria immagini
- ✅ Griglia **4x4** invece di 15x15 (configurabile)
- ✅ Grafici CV e NU con colori neon e media lines
- ✅ Omogeneità visiva tra PET e CT

**File modificati:**
- `nema_analysis.py` - **RISCRITTURA COMPLETA**
- `suv_analyzer.py` - grid_size 4x4 default + uso dinamico

### 🪟 **3. FIX WINDOWS + TIMEOUT**
- ✅ Supporto **Windows** (`python`) e Linux/Mac (`python3`)
- ✅ Timeout 5 minuti per analisi lunghe
- ✅ Migliore gestione errori Python

**File modificati:**
- `server.ts` - auto-detect platform + timeout

---

## 🚀 INSTALLAZIONE

### **Su Windows:**
```bash
python -m pip install pydicom numpy opencv-python pillow matplotlib --break-system-packages

bun run server.ts
```

### **Su Linux/Mac:**
```bash
python3 -m pip install pydicom numpy opencv-python pillow matplotlib

bun run server.ts
```

---

## 📋 FILE MODIFICATI

```
✅ nema_analysis.py           (NUOVO - plot moderni)
✅ server.ts                   (FIX Windows + timeout)
✅ api_scan_folder.py          (SC support)
✅ suv_analyzer.py             (grid 4x4 default)
```

**File NON modificati** (puoi usare quelli vecchi):
- app.js
- index.html  
- api_load_series.py
- api_analyze.py
- suv_report_generator.py
- package.json

---

## 🐛 PROBLEMI RISOLTI

### ❌ Problema: "Python non trovato" su Windows
**Causa:** Server usava `python3` hardcoded
**Fix:** Auto-detect platform → usa `python` su Windows

### ❌ Problema: HTTP 500 con 105 file
**Causa:** Timeout default troppo breve
**Fix:** Timeout 5 minuti per analisi lunghe

### ❌ Problema: Secondary Capture non riconosciute
**Causa:** Scanner non controllava SOP Class UID
**Fix:** Aggiunto check `1.2.840.10008.5.1.4.1.1.7`

### ❌ Problema: Plot NEMA "schifosi"
**Causa:** Matplotlib default brutto
**Fix:** Stile moderno professionale dark/neon

---

## 🎯 NUOVE FEATURE

### **Griglia Configurabile**
Cambia grid_size nel config:

```python
config = {
    "grid_size": 4,  # Default: 4x4
    # Oppure: 8, 10, 15 per NEMA completo
}
```

### **Plot Moderni**
- Colori neon: ciano (#00F2FE), rosa (#F093FB), rosso (#F5576C)
- Background dark: #1a1a2e
- Grid trasparente con linee tratteggiate
- Media lines con colore oro (#FFD700)

---

## 📸 DIFFERENZE VISIVE

**PRIMA (vecchio):**
```
[ Plot CV ]  [ Plot NU ]
  - Bianco
  - Nessuna griglia
  - Scatter basico
```

**ADESSO (nuovo):**
```
[ CV con media line ]  [ NU con limiti ±15% ]
  - Dark theme
  - Griglia tratteggiata
  - Marker belli + connessioni
  - Colori neon
```

**Galleria immagini:**
```
PRIMA: 1x2 subplot (ROI + griglia)
ADESSO: 2x3 gallery con 6 slice + CV label
```

---

## 💻 COME USARE

### **1. Avvia Server**
```bash
bun run server.ts
```

### **2. Apri Browser**
```
http://localhost:7860
```

### **3. Carica File**
- Drag & drop DICOM (PT + CT + SC supportati)
- Oppure "Scansiona Cartella"

### **4. Analisi**
- Tab "Analisi SUV" → "Avvia Analisi"
- Report con plot moderni appare automaticamente

---

## 🔧 TROUBLESHOOTING

### Errore: "ModuleNotFoundError: No module named 'matplotlib'"
```bash
# Windows
python -m pip install matplotlib --break-system-packages

# Linux/Mac
python3 -m pip install matplotlib
```

### Errore: "Failed to start Python"
**Windows:** Verifica che `python` sia nel PATH
**Linux/Mac:** Verifica che `python3` sia installato

### Analisi timeout
Aumenta timeout in `server.ts`:
```typescript
await runPython('api_analyze.py', folderPaths, 600000);  // 10 minuti
```

---

## 📞 CONTATTI

**Sviluppatore:** Dr. Christian Bracco  
**Email:** cbracco@mauriziano.it  
**Reparto:** S.C. Interaziendale di Fisica Sanitaria  
**Istituzione:** A.O. Ordine Mauriziano - ASL TO3

---

**Versione:** 3.3  
**Data:** 2026-04-08  
**Modifiche:** Plot NEMA moderni + SC support + Windows fix
