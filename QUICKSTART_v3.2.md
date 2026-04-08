# 🚀 SUV Analyzer v3.2 - QUICK START

## ✨ **NUOVE FUNZIONALITÀ**

### 🎯 **Multi-Upload PET + CT**
Ora puoi caricare **più serie contemporaneamente** senza sovrascrivere quelle precedenti!

**Prima (v3.0-3.1)**:
- Upload PET → 1 serie
- Upload CT → **SOSTITUISCE** PET, solo CT visibile ❌

**Adesso (v3.2)**:
- Upload PET → 1 serie
- Upload CT → **AGGIUNGE**, ora hai PET + CT ✅
- Analisi processa **ENTRAMBE** insieme!

---

## 📋 **WORKFLOW TIPICO**

### 1️⃣ **Avvia Server**
```bash
cd ~/Downloads/suv-analyzer-v3
bun run server.ts
```

Vedrai:
```
🚀 Server running at http://localhost:7860
```

### 2️⃣ **Apri Browser**
```
http://localhost:7860
```

### 3️⃣ **Carica File DICOM**

**Opzione A: Drag & Drop** (RACCOMANDATO)
1. Apri cartella PET nel Finder
2. Seleziona tutti i file `.dcm`
3. **Trascina** nella zona blu "Trascina file DICOM qui"
4. Aspetta upload → vedrai "✅ 40 file caricati - 1 serie disponibili"

5. Ripeti per cartella CT:
   - Seleziona file CT
   - Trascina di nuovo
   - Vedrai "✅ 40 file caricati - **2 serie disponibili**"

**Opzione B: Sfoglia File**
1. Click "📁 Seleziona File"
2. Seleziona tutti i `.dcm` da UNA cartella
3. Ripeti per altre cartelle

---

### 4️⃣ **Visualizza Serie**

Nella tab "📊 DICOM Viewer" vedrai **cards per ogni serie**:

```
┌─────────────────────────────┐
│  PT  PET Phantom Uniform    │
│      40 slices              │
└─────────────────────────────┘

┌─────────────────────────────┐
│  CT  CT Phantom Homogeneity │
│      40 slices              │
└─────────────────────────────┘
```

**Click su una card** → Immagini caricano nel viewer

---

### 5️⃣ **Naviga Immagini**

**Mouse**:
- 🖱️ **Wheel**: Scrolla slice avanti/indietro
- 🖱️ **Click + Drag**: Regola Window/Level
- 🖱️ **Ctrl + Wheel**: Zoom in/out
- 🖱️ **Double Click**: Reset W/L e zoom

**Tastiera**:
- ⬆️⬇️ **Frecce**: Slice precedente/successivo
- **PgUp/PgDn**: Slice precedente/successivo
- **Home**: Prima slice
- **End**: Ultima slice
- **R**: Reset tutto

---

### 6️⃣ **Esegui Analisi**

1. Tab "⚡ Analisi SUV"
2. Click **"▶️ Avvia Analisi"**
3. Aspetta... (10-30 secondi per 80 slice)
4. Vedrai "✅ Analisi completata!"

Il **report HTML** appare sotto con:
- 📊 Summary cards (slices PET/CT, SUV medio, HU medio)
- 📈 Grafici interattivi (SUV mean, distribuzione, range)
- 📋 Tabelle dettagliate
- 🖼️ Immagini NEMA analysis
- ✍️ Sezione firme editabili

---

### 7️⃣ **Esporta Report**

**Opzione A: Stampa**
- Click "🖨️ Stampa" nel toolbar del report
- Seleziona "Salva come PDF" nella finestra stampa

**Opzione B: Salva PDF**
- Click "📄 Salva PDF"
- Report scaricato automaticamente

---

## 🐛 **TROUBLESHOOTING**

### Problema: "Errore 500" su scansione
**Soluzione**: Controlla console server (terminale), verifica path file

### Problema: Report non appare
**Verifica**:
1. Apri Console browser (Cmd+Option+J)
2. Cerca `Has reportHtml: true`
3. Se `false` → problema backend, vedi console server
4. Se `true` → problema frontend, controlla errori JS

### Problema: File non caricano
**Controlla**:
- File hanno estensione `.dcm`?
- Console mostra "File DICOM trovati: 40/40"?
- Network tab mostra 200 OK per `/api/upload-dicom`?

### Problema: Analisi torna errore
**Causa comune**: File DICOM corrotti o mancanti metadati SUV
**Fix**: Testa con TEST_DICOM_DATA forniti

---

## 💡 **TIPS & TRICKS**

### 🎯 **Tip 1: Ordine di caricamento**
Non importa! Puoi caricare CT prima di PET, o mescolare.
L'analisi li processa tutti insieme.

### 🎯 **Tip 2: Più serie dello stesso tipo**
Puoi caricare 3 serie PET + 2 serie CT, funziona!
L'analisi unisce tutti i dati PET insieme e tutti i CT insieme.

### 🎯 **Tip 3: Reset completo**
Per ricominciare da zero:
1. Ricarica pagina (Cmd+R)
2. Oppure riavvia server

### 🎯 **Tip 4: Performance**
- Dataset piccoli (<100 file): Istantaneo
- Dataset medi (100-500 file): 10-30 sec
- Dataset grandi (>500 file): 1-2 min

### 🎯 **Tip 5: Viewer PRO**
- Tieni premuto **Ctrl** mentre usi wheel → Zoom preciso
- **Double click** per reset rapido W/L
- Usa **Home/End** per saltare a prima/ultima slice

---

## 📞 **SUPPORTO**

**Sviluppatore**: Christian Bracco  
**Email**: cbracco@mauriziano.it  
**Reparto**: S.C. Interaziendale di Fisica Sanitaria  
**Istituzione**: A.O. Ordine Mauriziano - ASL TO3

---

## 📚 **DOCUMENTAZIONE COMPLETA**

- `README_v3.md` - Setup e architettura
- `CHANGELOG_v3.2.md` - Novità versione 3.2
- `DRAG_DROP_GUIDE.md` - Dettagli drag & drop
- `INSTALLATION.md` - Installazione dipendenze

---

**Buon lavoro!** 🎉
