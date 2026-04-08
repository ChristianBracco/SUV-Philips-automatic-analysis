# SUV Analyzer v3.3 - REPORT FIX SESSION

## ✅ FIX IMPLEMENTATI (in questo package)

### 1. **Griglia NEMA 15×15** ✅
**File**: `nema_analysis.py` line 57
- Cambiato da `grid_size=4` a `grid_size=15` 
- Conforme NEMA NU 2-2018 standard
- ROI size: 5% del radius (celle più piccole)
- Spacing: copre 180% del radius

### 2. **Asse Y Fix - Grafici CV/NU** ✅
**File**: `nema_analysis.py` lines 365-368, 395-397
- **CV plot**: ylim(0, max(10% per PET, 5% per CT))
- **NU plot**: ylim(-20%, +20%) fisso
- **Problema risolto**: Prima l'autoscale schiacciava 0.01-0.06% su tutto l'asse

### 3. **Checkbox Serie Selection** ✅
**Files**: `index.html`, `app.js`, `server.ts`, `api_analyze.py`, `suv_analyzer.py`
- UI con checkbox per selezionare serie prima analisi
- Default: solo PET normali (no Secondary Capture)
- Bottoni: Tutte / Nessuna / Solo PET

### 4. **UID Fix** ✅
**Files**: `suv_analyzer.py` line 104, `api_scan_folder.py` line 38
- `.strip()` su SeriesInstanceUID per rimuovere spazi trailing
- **Problema risolto**: Match UID falliva → tutti file skippati

### 5. **Link Report Cliccabile** ✅
**File**: `app.js` lines 641-660
- Bottone "📊 Apri Report Completo" invece di testo filename
- Mostra conteggio PET/CT processati

---

## ⚠️ TODO - RICHIESTE NON IMPLEMENTATE

### 📋 **Intestazione Report Completa**
**Dati mancanti dai DICOM**:
- ❌ **Ospedale**: dove sono state acquisite le immagini?
- ❌ **Data acquisizione**: StudyDate/SeriesDate?
- ❌ **Attività somministrata**: RadiopharmaceuticalInformationSequence?
- ❌ **Ora scansione**: StudyTime/SeriesTime?

**DOMANDA**: Quali tag DICOM devo leggere per questi dati?

```python
# Esempio - dove li trovo?
ds.StudyDate  # Data acquisizione?
ds.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose  # Attività?
ds.InstitutionName  # Ospedale?
```

---

### 📊 **Zoom Immagini nel Report**
**File da modificare**: `suv_report_generator.py`
- Immagini gallery troppo piccole
- **Soluzione**: Aumentare dimensioni + controlli zoom/pan interattivi
- **Domanda**: Preferisci zoom inline o lightbox popup?

---

### 🌈 **LUT Rainbow2 per PET**
**File da modificare**: `suv_report_generator.py` o `nema_analysis.py`
- Attualmente: grayscale
- Richiesto: Colormap Rainbow2 (Philips-style)

**Opzioni**:
1. Matplotlib: `plt.cm.jet` o `plt.cm.turbo`
2. Custom Rainbow2 LUT da Philips
3. OpenCV: `cv2.applyColorMap(img, cv2.COLORMAP_JET)`

**DOMANDA**: Hai un file LUT .txt di Rainbow2 da Philips?

---

### 🖼️ **Window/Level Presets**
**File da modificare**: `suv_analyzer.py` + `nema_analysis.py`
- Attualmente: auto-normalization
- Richiesto: W/L presets (es. PET: W=5 L=2.5, CT: W=400 L=40)

**Domanda**: Quali W/L vuoi come default?

---

### 📄 **Impaginazione A4 Print-Ready**
**File da modificare**: `suv_report_generator.py` CSS
- Aggiungere `@media print` rules
- Page breaks intelligenti
- Margini A4 (210×297mm)

---

### 📊 **Tabelle Compatte**
**File da modificare**: `suv_report_generator.py`
- Ridurre padding
- Font più piccolo
- Layout a 2-3 colonne invece di 1

---

### 📏 **SUV Medio - Unità di Misura**
**Verifica**: SUV è **adimensionale** (g/mL è sbagliato)
- SUV = (activity concentration / injected dose) × patient weight
- Unità corretta: **nessuna** oppure **[dimensionless]**

**Fix necessario**: Rimuovere "g/mL" dal report

---

## 🎯 PRIORITÀ PROSSIMI FIX

**URGENTE (richieste esplicite)**:
1. ✅ Griglia 15×15 - FATTO
2. ✅ Asse Y fix - FATTO
3. ❌ Intestazione completa (serve input DICOM tags)
4. ❌ LUT Rainbow2 (serve LUT file o scelta matplotlib)
5. ❌ Zoom immagini
6. ❌ W/L presets (serve valori desiderati)
7. ❌ Tabelle compatte
8. ❌ SUV unità misura fix
9. ❌ Impaginazione A4

**IMPORTANTE (best practices)**:
- Verifica procedure NEMA NU 2-2018 per griglia 15×15
- Test stampa PDF/A4
- Color blindness: verificare LUT accessibilità

---

## 📝 DOMANDE PER CHRISTIAN

1. **DICOM Tags**: Quali tag per ospedale/data/attività/ora?
2. **LUT Rainbow2**: Hai file LUT .txt? O uso matplotlib turbo/jet?
3. **W/L Presets**: Valori default per PET e CT?
4. **Zoom immagini**: Inline zoom o popup lightbox?
5. **SUV unità**: Confermi adimensionale (nessuna unità)?

---

## 🚀 COME USARE QUESTO PACKAGE

```bash
# 1. Estrai e sovrascrivi
# 2. Riavvia server
bun run .\server.ts

# 3. Testa con 107 file
# 4. Verifica:
#    - Griglia 15×15 (molte ROI piccole)
#    - Asse Y grafici non schiacciato
#    - Checkbox serie funzionanti
```

---

## 📊 OUTPUT ATTESO

**ROI Gallery PET (15×15)**:
```
Slice 1 | CV = 1.83%    ← CV più leggibile
Slice 11 | CV = 1.78%
Slice 15 | CV = 1.45%
...
```

**Grafici CV/NU**:
- CV: asse Y 0-10% (non 0-0.06%)
- NU: asse Y -20% a +20% (non -1% a +1%)

**Checkbox**:
- 4 serie disponibili
- Solo PET normale selezionata (no SC)
- File #106 skippato → nessun crash

---

## 🛠️ FILES MODIFICATI

1. `nema_analysis.py` - Griglia 15×15, asse Y fix, ROI size
2. `suv_analyzer.py` - UID strip, series selection
3. `api_scan_folder.py` - UID strip
4. `api_analyze.py` - Series selection support
5. `server.ts` - Pass selectedSeries to Python
6. `app.js` - Checkbox UI, link report
7. `index.html` - Checkbox HTML/CSS

**NON modificati** (TODO):
- `suv_report_generator.py` - serve per LUT/W/L/zoom/header/tabelle

---

## 📅 VERSIONE

**v3.3.1 - NEMA 15×15 + Asse Y Fix**
- Data: 08/04/2026
- Changelog: Griglia 15×15, asse Y leggibile, checkbox serie
