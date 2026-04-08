# SUV Analyzer v3.3 - CHECKBOX SERIES SELECTION

## 🎯 PROBLEMA RISOLTO

File #106 (Secondary Capture da 122MB) causava crash durante analisi perché veniva processato come PET normale.

## ✅ SOLUZIONE IMPLEMENTATA

**Checkbox per selezione manuale serie PRIMA dell'analisi**

### MODIFICHE AI FILE

#### 1. **public/index.html**
- ✅ Aggiunto CSS per series selector (line ~459-475)
- ✅ Aggiunto HTML container dopo scan-status (line ~524-536):
  ```html
  <div id="series-selector-container">
    <button onclick="selectAllSeries()">Tutte</button>
    <button onclick="deselectAllSeries()">Nessuna</button>
    <button onclick="selectOnlyPET()">Solo PET</button>
    <div id="series-list"><!-- checkbox qui --></div>
  </div>
  ```

#### 2. **public/app.js**
- ✅ Line ~221: `showSeriesSelector()` invece di `loadAllSeries()`
- ✅ Line ~623: passa `selectedSeries: getSelectedSeriesUIDs()` a /api/analyze
- ✅ Aggiunte funzioni (line 675+):
  - `showSeriesSelector()` - mostra checkbox per ogni serie
  - `selectAllSeries()` / `deselectAllSeries()` / `selectOnlyPET()`
  - `getSelectedSeriesUIDs()` - ritorna array di UIDs selezionati

#### 3. **server.ts**
- ✅ Line ~214: legge `selectedSeries` dal body
- ✅ Line ~226-229: passa selectedSeries come argomenti a api_analyze.py
  ```typescript
  const args = [...folderPaths];
  if (selectedSeries && Array.isArray(selectedSeries)) {
    args.push(...selectedSeries);
  }
  ```

#### 4. **api_analyze.py**
- ✅ Accetta `selectedSeries` UIDs come argomenti aggiuntivi (sys.argv[2:])
- ✅ Passa `analyzer.selected_series = set(selected_series)` a SUVAnalyzer

#### 5. **suv_analyzer.py**
- ✅ `__init__`: aggiunto `self.selected_series = None`
- ✅ `process_folder`: skip file non in `selected_series`
- ✅ `process_folder`: skip Secondary Capture con messaggio chiaro

## 🎬 FLUSSO OPERATIVO

1. **Upload 107 file** → Server scansiona e trova 4 serie:
   - Serie 201 (CT, 60 file)
   - Serie 3195 (PET, 45 file)
   - Serie 49984 (Secondary Capture, 1 file) ⚠️
   - Serie 49994 (Screenshot, 1 file)

2. **UI mostra checkbox** con:
   - ✅ Serie 3195 (PET normale) - PRE-SELEZIONATA
   - ✅ Serie 201 (CT) - PRE-SELEZIONATA
   - ⬜ Serie 49984 (Secondary Capture) - NON selezionata (warning ⚠️)
   - ⬜ Serie 49994 - NON selezionata

3. **User clicca "Analizza Serie Selezionate"**

4. **Frontend invia**:
   ```json
   {
     "folderPaths": ["C:\\...\\upload_123"],
     "selectedSeries": [
       "1.3.12.2.1107.5.8.15.134771.30000026040710585260000000010",
       "1.3.12.2.1107.5.8.15.134771.30000026040710585260000000079"
     ]
   }
   ```

5. **Server chiama**:
   ```bash
   python api_analyze.py C:\...\upload_123 1.3.12.2... 1.3.12.2...
   ```

6. **Analyzer processa SOLO serie selezionate**:
   ```
   [106/107] HS134771.PT.49984.1...
     SKIPPED: not in selected series
   [61/107] HS134771.PT.3195.1...
     Processing as PET...
     ✅ PET processed successfully
   ```

## 🧪 TEST RAPIDO

```bash
# 1. Riavvia server
bun run .\server.ts

# 2. Carica 107 file → vedi 4 checkbox
# 3. Deseleziona "Secondary Capture" (serie 49984)
# 4. Click "Analizza Serie Selezionate"
# 5. ✅ Nessun crash! File #106 skippato
```

## 📊 OUTPUT ATTESO

```
Processing folder: C:\...\upload_123
Selected series: 2
Found 107 total files, 105 in selected series

[1/105] HS134771.CT...
  Modality: CT, is_secondary: False
  Processing as CT...
  ✅ CT processed

[61/105] HS134771.PT.3195.1...
  Modality: PT, is_secondary: False
  Processing as PET...
  ✅ PET processed

[106/107] HS134771.PT.49984.1...
  SKIPPED: not in selected series

Report generato: 45 PET + 60 CT
```

## 🔧 BACKWARD COMPATIBILITY

- ✅ Se `selectedSeries` è vuoto/null → analizza TUTTE le serie (vecchio comportamento)
- ✅ Secondary Capture comunque skippate anche se selezionate per errore
- ✅ Interfaccia funziona anche senza checkbox (se JS fallisce)

## 🚀 PROSSIMI STEP (FUTURO)

- [ ] OCR su Secondary Capture per estrarre valori SUV sovrapposti
- [ ] Multi-frame Secondary Capture support
- [ ] Salvataggio preset selezione serie
