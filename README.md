# 🏥 SUV Analyzer - Sistema di Analisi Quantitativa PET/CT

**Sistema completo per analisi di Standardized Uptake Values (SUV) e generazione report HTML interattivi**

Autore: Dr. Christian Bracco  
Istituzione: S.C. Interaziendale di Fisica Sanitaria - A.O. Ordine Mauriziano / ASL TO3

---

## 📋 Caratteristiche

### ✨ Funzionalità Principali

- **Analisi SUV Automatica**: Calcolo automatico di SUV da DICOM PET originali
- **Supporto Multi-Modalità**: Gestione PET, CT e Secondary Captures
- **Report HTML Interattivi**: Report professionali con grafici Chart.js
- **Calcolo ROI Circolare**: ROI automatica con frazione configurabile (default 80%)
- **Statistiche Complete**: Mean, Std, Min, Max, CV, Non-Uniformity
- **Grafici Interattivi**: Visualizzazione dinamica con Chart.js
- **Batch Processing**: Elaborazione multipla di cartelle DICOM
- **Configurazione Flessibile**: Parametri QC personalizzabili

### 🎨 Report HTML Features

- Design moderno e responsive
- Grafici interattivi con Chart.js
- Tabelle dati con ordinamento
- Badge status (OK/Warning/Error)
- Immagini embedded base64
- Esportazione PDF via print
- Mobile-friendly

---

## 🚀 Quick Start

### Installazione Dipendenze

```bash
pip install pydicom numpy opencv-python pillow
```

### Uso Base

**1. Singolo file DICOM:**
```bash
python3 suv_analyzer.py input.dcm -o report.html
```

**2. Cartella con DICOM:**
```bash
python3 suv_analyzer.py /path/to/dicom/folder -o report.html
```

**3. Con file di configurazione:**
```bash
python3 suv_analyzer.py input.dcm -o report.html -c suv_config.txt
```

**4. Batch processing:**
```bash
python3 batch_processor.py /path/dir1 /path/dir2 -o /output/dir -c config.txt
```

---

## 📁 Struttura File

```
suv_analyzer/
├── suv_analyzer.py          # Modulo principale analisi
├── suv_report_generator.py  # Generatore report HTML
├── batch_processor.py        # Processing batch cartelle
├── suv_config.txt           # File configurazione esempio
└── README.md                # Questa documentazione
```

---

## ⚙️ Configurazione

Il file `suv_config.txt` permette di personalizzare i parametri di controllo qualità:

```
# ROI Configuration
Frazione area ROI: 0.80

# SUV Tolerance
Limite superiore tolleranza SUV: 1.10
Limite inferiore tolleranza SUV: 0.90

# Non-Uniformity Limits
Limite superiore NU PET: 15.0
Limite inferiore NU PET: -15.0
Limite superiore NU CT: 15.0
Limite inferiore NU CT: -15.0

# Coefficient of Variation
Limite superiore CV CT: 15.0

# Personnel
Specialista fisica medica: Dr. Christian Bracco
```

---

## 🔬 Calcolo SUV

### Formula Standard

```
SUV = (Activity_concentration * Patient_weight) / Injected_dose
```

### Tag DICOM Philips

Il sistema supporta il tag privato Philips:
- `(7053,1000)` - SUV Scale Factor

Se non disponibile, calcola manualmente da:
- RadiopharmaceuticalInformationSequence
- PatientWeight
- Decay correction

### ROI Circolare

1. Segmentazione automatica con Otsu
2. Identificazione contorno più grande
3. Calcolo centro (momenti)
4. ROI ridotta per frazione (default 80%)
5. Estrazione statistiche

---

## 📊 Output Report

### Sezioni Report HTML

1. **Header**
   - Titolo e istituzione
   - Data/ora generazione
   - Informazioni paziente

2. **Summary Cards**
   - Numero immagini PET/CT
   - SUV medio globale
   - HU medio globale
   - Percentuale QC superato

3. **Analisi PET**
   - Grafici SUV Mean, Min, Max
   - Tabella dati per slice
   - Statistiche (CV, Non-Uniformity)
   - Status badges per QC

4. **Analisi CT**
   - Grafici HU Mean
   - Tabella Hounsfield Units
   - Statistiche uniformità

5. **Secondary Captures**
   - Gallery screenshot scanner
   - Frame multipli visualizzati

---

## 🖥️ Esempi Uso

### Esempio 1: Analisi QC Giornaliero

```bash
# Processa acquisizione giornaliera
python3 suv_analyzer.py \
    /data/qc/20260407_phantom \
    -o /reports/qc_20260407.html \
    -c /config/qc_daily.txt
```

### Esempio 2: Batch Processing Mensile

```bash
# Processa tutte le acquisizioni del mese
python3 batch_processor.py \
    /data/qc/202601* \
    -o /reports/gennaio_2026 \
    -c /config/qc_monthly.txt
```

### Esempio 3: Secondary Capture Analysis

```bash
# Analizza screenshot scanner Philips
python3 suv_analyzer.py \
    screenshot_suv.dcm \
    -o secondary_capture_report.html
```

### Esempio 4: Uso Programmatico

```python
from suv_analyzer import SUVAnalyzer

# Crea analyzer
analyzer = SUVAnalyzer()

# Carica configurazione
analyzer.load_config_file('config.txt')

# Processa cartella
analyzer.process_folder('/path/to/dicom')

# Genera report
analyzer.generate_html_report('output.html')

# Accedi ai dati
for data in analyzer.pt_data:
    print(f"Slice {data['instance_number']}: "
          f"SUV = {data['suv_mean']:.2f}")
```

---

## 🔧 API Reference

### Classe `SUVAnalyzer`

**Metodi principali:**

```python
__init__()
    Inizializza analyzer con configurazione default

load_config_file(config_path)
    Carica parametri da file configurazione

read_dicom_file(filepath)
    Legge file DICOM e determina tipo

process_secondary_capture(dicom_info)
    Processa DICOM secondary capture

calculate_suv_from_dicom(dicom_info, roi_fraction=0.8)
    Calcola SUV da DICOM PET originale

calculate_hu_from_dicom(dicom_info, roi_fraction=0.8)
    Calcola HU da DICOM CT

process_folder(folder_path)
    Processa cartella con file DICOM

process_single_dicom(filepath)
    Processa singolo file DICOM

generate_html_report(output_path='suv_report.html')
    Genera report HTML interattivo
```

**Attributi:**

```python
pt_data          # Lista dati PET
ct_data          # Lista dati CT
secondary_captures  # Lista secondary captures
config           # Dizionario configurazione
```

---

## 📈 Statistiche Calcolate

### PET (SUV)
- **SUV Mean**: Media valori SUV nella ROI
- **SUV Std**: Deviazione standard
- **SUV Min/Max**: Valori minimo/massimo
- **CV**: Coefficiente di variazione (%)
- **NU**: Non-uniformity (%)

### CT (HU)
- **HU Mean**: Media Hounsfield Units
- **HU Std**: Deviazione standard
- **HU Min/Max**: Valori minimo/massimo
- **CV**: Coefficiente di variazione (%)
- **NU**: Non-uniformity (%)

---

## 🎯 Controlli Qualità

### Criteri Accettabilità

**PET SUV:**
- Tolleranza: ±10% dal valore medio
- Non-Uniformity: < 15%
- Coefficient of Variation: < 15%

**CT HU:**
- Water phantom: 102.1 - 114.1 HU
- Non-Uniformity: ±8.0 HU
- Coefficient of Variation: < 15%

### Status Badges

- 🟢 **OK**: Dentro tolleranze
- 🟡 **Warning**: Fuori tolleranza ma accettabile
- 🔴 **Error**: Fuori limiti critici

---

## 🔍 Troubleshooting

### Problema: "No contours found"
**Soluzione**: Verifica qualità immagine, regola threshold Otsu

### Problema: "SUV Scale Factor not found"
**Soluzione**: Tag privato Philips non disponibile, verrà calcolato manualmente

### Problema: "Empty ROI"
**Soluzione**: Riduci `roi_fraction` nel config (es. 0.70 invece di 0.80)

### Problema: Report HTML non mostra grafici
**Soluzione**: Verifica connessione internet (Chart.js CDN) o usa versione offline

---

## 📝 Note Tecniche

### Compatibilità DICOM

- **Modalità supportate**: PT, CT, Secondary Capture
- **Manufacturer**: Philips (tag privati), GE, Siemens (standard)
- **Transfer Syntax**: Tutti i comuni

### Performance

- **Singolo file**: ~0.5s
- **Cartella 100 file**: ~30s
- **Report HTML**: generazione <1s

### Memoria

- **ROI processing**: ~50MB per immagine
- **Report generation**: ~10MB per 100 immagini

---

## 📜 Changelog

### v1.0 (Aprile 2026)
- ✅ Release iniziale
- ✅ Supporto PET/CT/Secondary Capture
- ✅ Report HTML con Chart.js
- ✅ Batch processing
- ✅ Configurazione personalizzabile

---

## 👨‍⚕️ Contatti

**Dr. Christian Bracco**  
Fisico Medico  
S.C. Interaziendale di Fisica Sanitaria  
A.O. Ordine Mauriziano - ASL TO3  
Email: cbracco@mauriziano.it

---

## 📄 Licenza

Uso interno ospedaliero per controllo qualità PET/CT.  
Non distribuire senza autorizzazione.

---

## 🙏 Riconoscimenti

Basato su workflow di QC esistente (AutomaticSUVReport.py)  
Grafici: Chart.js  
DICOM processing: pydicom  
Image processing: OpenCV

---

**⚡ Powered by Python + Medical Physics**
