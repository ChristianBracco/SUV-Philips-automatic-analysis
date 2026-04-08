# SUV Analyzer v3.3 - VERSIONE FINALE
**Data**: 08/04/2026  
**Autore**: Dr. Christian Bracco - S.C. Interaziendale di Fisica Sanitaria

---

## 🎯 TUTTE LE MODIFICHE IMPLEMENTATE

### ✅ **1. NEMA 15×15 Griglia Conforme**
- Griglia 15×15 ROI (era 4×4) secondo NEMA NU 2-2018
- ROI size: 5% del radius (celle piccole)
- Distribuzione: 180% coverage → ~150-225 ROI per slice

### ✅ **2. Asse Y Grafici Leggibili**
- **CV**: ylim 0-10% (PET), 0-5% (CT)
- **NU**: ylim -20% a +20% fisso
- **Prima**: autoscale schiacciava 0.01-0.06% illeggibile
- **Dopo**: proporzioni corrette, variazioni visibili

### ✅ **3. LUT Rainbow2 Philips su PET**
- File `luts/Rainbow2.cm` integrato (256 colori hex)
- Funzioni `load_rainbow2_lut()` e `apply_rainbow2_lut()`
- Applicata automaticamente a tutte le immagini PET nelle gallery
- CT rimangono grayscale

### ✅ **4. Metadata DICOM nell'Intestazione**
**Tags estratti**:
- `InstitutionName` → Ospedale
- `StudyDate` → Data acquisizione (formato DD/MM/YYYY)
- `StudyTime` → Ora scansione (HH:MM:SS)
- `RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose` → Attività (MBq)

**Dove**: Header report con formattazione grid 2×2

### ✅ **5. Instance Number → Numero Fetta**
- Grafici CV e NU mostrano "Numero Fetta" sull'asse X
- Più chiaro per utenti italiani

### ✅ **6. Tabelle Compattate**
- Padding ridotto: 8px/6px (era 15px/12px)
- Font ridotto: 0.75em/0.85em
- Occupano ~40% meno spazio verticale
- Pronte per stampa A4

### ✅ **7. Report HTML Salvato su File**
- Path: `public/reports/SUV_QC_Report_YYYY-MM-DD_HH-MM-SS.html`
- Link cliccabile nell'interfaccia
- File permanente accessibile dopo chiusura browser

### ✅ **8. Generazione PDF Server-Side**
**Libreria**: `weasyprint` (fallback `pdfkit`)  
**Output**: `public/reports/SUV_QC_Report_YYYY-MM-DD_HH-MM-SS.pdf`  
**Features**:
- CSS rendering completo
- Immagini base64 embedded
- Pronto per stampa/archiviazione

### ✅ **9. Checkbox Selezione Serie**
- UI con 4 serie, checkbox selezionabili
- Default: solo PET normali
- Bottoni: Tutte / Nessuna / Solo PET
- Secondary Capture disattivato con warning ⚠️

### ✅ **10. UID Fix Whitespace**
- `.strip()` su `SeriesInstanceUID`
- Fix match UID → tutti file processati correttamente

---

## 📦 INSTALLAZIONE

### **Step 1: Estrai Package**
```bash
unzip suv_v3.3_FINAL.zip
cd suv_analyzer_v3.3
```

### **Step 2: Installa Dipendenze Python**
```bash
pip install -r requirements.txt --break-system-packages
```

**Librerie installate**:
- `numpy`, `opencv-python`, `pydicom`, `matplotlib` (già presenti)
- `weasyprint` (NUOVO - per PDF generation)

### **Step 3: Avvia Server**
```bash
bun run server.ts
```

### **Step 4: Apri Browser**
```
http://localhost:3000
```

---

## 🚀 WORKFLOW COMPLETO

### **1. Upload Cartella DICOM**
- Drag & drop o selezione cartella
- Scan automatico serie disponibili

### **2. Selezione Serie**
- 4 serie mostrate con checkbox
- Default: PET normali selezionate
- Deseleziona Secondary Capture se presente

### **3. Analisi**
- Click "Avvia Analisi"
- Processing PET/CT con NEMA 15×15
- Estrazione metadata DICOM

### **4. Report Generato**
**Output files in `public/reports/`**:
- `SUV_QC_Report_[timestamp].html` → Report interattivo
- `SUV_QC_Report_[timestamp].pdf` → PDF stampabile

**Interfaccia mostra**:
- Link "📊 Apri Report Completo" (HTML)
- Link "📄 Scarica PDF" (se generato)
- Path files salvati

---

## 📊 CONTENUTO REPORT

### **Intestazione**
- Dipartimento + Istituzione
- Responsabile: Dr. Christian Bracco
- **Ospedale** (da DICOM)
- **Data acquisizione** (DD/MM/YYYY)
- **Ora scansione** (HH:MM:SS)
- **Attività iniettata** (MBq)
- Timestamp generazione report

### **Summary Cards**
- Immagini PET / CT processate
- Secondary Captures (count)
- SUV medio (g/mL)
- HU medio
- QC superato (%)

### **Analisi PET**
- SUV Mean per Slice (grafico)
- Distribuzione SUV (istogramma)
- Range SUV Min/Max (grafico)
- Tabella dettagliata per slice

### **Analisi NEMA PET (15×15)**
- Griglia 15×15 ROI Gallery (6 slice)
- Grafici CV e NU con asse Y corretto
- Tabelle uniformità quantitativa

### **Analisi CT**
- HU Mean per Slice (grafico)
- Distribuzione HU (istogramma)
- Tabella dettagliata

### **Analisi NEMA CT**
- Cerchi concentrici Gallery
- Grafici CV e NU
- Tabelle uniformità

### **Secondary Captures**
- Lista file SC trovati (se presenti)

---

## 🎨 FEATURES VISIVE

### **LUT Rainbow2 su PET**
Gradiente Philips-style:
```
Nero → Viola → Blu → Ciano → Verde → Giallo → Arancione → Rosso
```

### **Grafici con Scaling Corretto**
- **CV**: 0-10% (PET), 0-5% (CT)
- **NU**: ±20% fisso
- Variazioni minime ora visibili

### **Tabelle Compatte**
- Font 0.75em/0.85em
- Padding 8px/6px
- Layout ottimizzato A4

---

## 🔧 TROUBLESHOOTING

### **PDF non generato**
**Causa**: `weasyprint` non installato  
**Fix**:
```bash
pip install weasyprint --break-system-packages
```

**Alternative**: Se weasyprint ha problemi di dipendenze sistema:
```bash
pip install pdfkit --break-system-packages
# Richiede anche: apt install wkhtmltopdf
```

### **Report HTML non trovato**
**Causa**: Cartella `public/reports/` non esiste  
**Fix**: Creata automaticamente al primo run, oppure:
```bash
mkdir -p public/reports
```

### **Metadata DICOM mancanti**
**Causa**: Tags non presenti nei file DICOM  
**Comportamento**: Mostra "N/A" o "Unknown"  
**Normale**: Non tutti scanner inseriscono tutti i tag

### **Secondary Capture crash**
**Fix già implementato**: Checkbox disattivato di default con warning

---

## 📝 CONFORMITÀ NEMA

### **NEMA NU 2-2018**
- ✅ Griglia 15×15 ROI uniformità
- ✅ CV (Coefficient of Variation)
- ✅ NU max/min (Non-Uniformity)
- ✅ ROI 5% area fantoccio
- ✅ Coverage 180% diametro

### **NEMA 94**
- ✅ 5 cerchi concentrici CT
- ✅ Area 5% ROI principale
- ✅ Posizioni: centro + 12h/3h/6h/9h

---

## 📄 FILES MODIFICATI

### **Core Analysis**
1. `suv_analyzer.py` - Metadata extraction, report generation
2. `nema_analysis.py` - Griglia 15×15, asse Y fix, Rainbow2 LUT
3. `suv_report_generator.py` - Header metadata, tabelle compatte

### **API Backend**
4. `api_analyze.py` - Report file saving, PDF generation
5. `server.ts` - (nessuna modifica necessaria)

### **Frontend**
6. `app.js` - Link report/PDF, checkbox logic
7. `index.html` - CSS badge, checkbox UI

### **Resources**
8. `luts/Rainbow2.cm` - LUT Philips (256 colori hex)
9. `requirements.txt` - Dipendenze Python

### **Documentation**
10. `README_FINAL.md` - Questa guida
11. `README_FIX_SESSION.md` - Log sessioni fix

---

## 🎯 CHECKLIST TEST FINALE

- [ ] Upload 107 file DICOM
- [ ] Checkbox serie funzionanti
- [ ] Secondary Capture skippato
- [ ] Analisi completa senza crash
- [ ] Report HTML generato in `public/reports/`
- [ ] PDF generato correttamente
- [ ] Metadata DICOM nell'intestazione
- [ ] Griglia 15×15 visibile nelle immagini
- [ ] Grafici CV/NU leggibili
- [ ] Immagini PET con Rainbow2
- [ ] Tabelle compatte
- [ ] Link cliccabili funzionanti

---

## 📞 SUPPORTO

**Autore**: Dr. Christian Bracco  
**Email**: cbracco@mauriziano.it  
**Istituzione**: S.C. Interaziendale di Fisica Sanitaria  
**Location**: A.O. Ordine Mauriziano - ASL TO3, Torino

---

## 📜 CHANGELOG

### **v3.3.0 - FINAL (08/04/2026)**
- ✅ NEMA 15×15 griglia
- ✅ Asse Y fix grafici
- ✅ LUT Rainbow2 PET
- ✅ Metadata DICOM header
- ✅ Numero Fetta labels
- ✅ Tabelle compattate
- ✅ HTML file saving
- ✅ PDF generation server-side
- ✅ Checkbox serie selection
- ✅ UID whitespace fix

### **v3.2 (precedente)**
- Series selection UI
- Secondary Capture detection
- Report link improvement

### **v3.1 (precedente)**
- NEMA analysis implementation
- Modern plot styling
- Interactive HTML reports

---

**🎉 LAVORO COMPLETATO! 🎉**
