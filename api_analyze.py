#!/usr/bin/env python3
"""
API: Analyze DICOM series
Esegue analisi SUV solo sulle serie selezionate.
Supporta flag opzionale --iqcheck <path.json> per includere i dati IQCheck nel report.
"""

import os
import sys
import json
from pathlib import Path
import pydicom

# Forza encoding UTF-8 per stdout (fix Windows charmap)
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import SUV analyzer e report generator
from suv_analyzer import SUVAnalyzer
from suv_report_generator import HTMLReportGenerator


def _parse_args(argv):
    """
    Separa il flag --iqcheck <path> dagli altri argomenti posizionali.
    Ritorna (positional_args, iqcheck_path_or_None).
    """
    positional = []
    iqcheck_path = None
    i = 0
    while i < len(argv):
        if argv[i] == '--iqcheck' and i + 1 < len(argv):
            iqcheck_path = argv[i + 1]
            i += 2
        else:
            positional.append(argv[i])
            i += 1
    return positional, iqcheck_path


def main():
    """Main analysis function"""
    try:
        # Parse arguments (esclude sys.argv[0] = nome script)
        positional, iqcheck_path = _parse_args(sys.argv[1:])

        if not positional:
            raise ValueError("Missing folder_path argument")

        folder_path = positional[0]
        selected_series = positional[1:]  # UIDs serie selezionate (opzionale)

        # Carica dati IQCheck se presenti
        iqcheck_data = None
        if iqcheck_path:
            with open(iqcheck_path, encoding='utf-8') as f:
                iqcheck_data = json.load(f)
            print(f"IQCheck caricato da: {iqcheck_path}", flush=True)
        
        print(f"Analyzing folder: {folder_path}", flush=True)
        if selected_series:
            print(f"Selected series: {len(selected_series)}", flush=True)
        
        # Filter DICOM files if series selected
        if selected_series:
            # Find only files from selected series
            all_files = list(Path(folder_path).glob('*.dcm'))
            filtered_files = []
            
            for filepath in all_files:
                try:
                    ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                    if hasattr(ds, 'SeriesInstanceUID') and ds.SeriesInstanceUID in selected_series:
                        filtered_files.append(filepath)
                except:
                    continue
            
            print(f"Found {len(all_files)} total files, {len(filtered_files)} in selected series", flush=True)
            
            # Create temp folder with filtered files
            # For now, we'll just modify process_folder to skip non-selected files
            # This is a quick hack - in production we'd copy files to temp folder
        
        # Create analyzer
        analyzer = SUVAnalyzer()
        
        # Pass selected series to analyzer
        analyzer.selected_series = set(selected_series) if selected_series else None
        
        # Process folder
        analyzer.process_folder(folder_path)

        # Analisi NEMA (necessaria per le sezioni uniformità del report)
        print("\nEsecuzione analisi NEMA...", flush=True)
        nema_results = analyzer.analyze_nema_uniformity(
            example_slice_pt=analyzer.config.get('example_slice_pt', 15),
            example_slice_ct=analyzer.config.get('example_slice_ct', 15)
        )

        # Genera report tramite HTMLReportGenerator (include sezione IQCheck se presente)
        report_gen = HTMLReportGenerator(
            analyzer,
            nema_results=nema_results,
            iqcheck_data=iqcheck_data
        )
        report_html = report_gen.generate()
        
        # Esporta anche JSON
        json_data = analyzer.export_json()

        # Salva report su file
        from datetime import datetime
        
        # Crea cartella reports se non esiste
        reports_dir = os.path.join('public', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Costruisci nome file da Manufacturer DICOM + data acquisizione
        # Estrai Manufacturer dal primo file DICOM processato
        scanner_name = "Unknown"
        study_date = "Unknown"
        
        # Prova a estrarre da pt_data o ct_data
        if analyzer.pt_data:
            scanner_name = analyzer.pt_data[0].get('manufacturer', 'Unknown')
            study_date = analyzer.pt_data[0].get('study_date', 'Unknown')
        elif analyzer.ct_data:
            scanner_name = analyzer.ct_data[0].get('manufacturer', 'Unknown')
            study_date = analyzer.ct_data[0].get('study_date', 'Unknown')
        
        # Fallback: prova acquisition_metadata
        if scanner_name == "Unknown":
            scanner_name = analyzer.acquisition_metadata.get('manufacturer', 'Unknown')
        if study_date == "Unknown":
            study_date = analyzer.acquisition_metadata.get('study_date', 'Unknown')
        
        # Sanitizza nome macchina (rimuovi caratteri non validi per filename)
        scanner_name_clean = scanner_name.replace(' ', '_').replace('/', '-').replace('\\', '-')
        
        # Formatta data acquisizione (YYYYMMDD)
        if study_date != 'Unknown' and len(study_date) >= 8:
            date_formatted = f"{study_date[0:4]}-{study_date[4:6]}-{study_date[6:8]}"
        else:
            date_formatted = datetime.now().strftime("%Y-%m-%d")
        
        # Nome file: Macchina_DataAcquisizione
        report_filename = f"{scanner_name_clean}_{date_formatted}_SUV_QC.html"
        json_filename = f"{scanner_name_clean}_{date_formatted}_SUV_QC.json"
        pdf_filename = f"{scanner_name_clean}_{date_formatted}_SUV_QC.pdf"
        
        report_path = os.path.join(reports_dir, report_filename)
        json_path = os.path.join(reports_dir, json_filename)
        pdf_path = os.path.join(reports_dir, pdf_filename)
        
        # Salva HTML su file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        # Salva JSON su file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Salva nel database storico
        try:
            from qc_database import QCDatabase
            db = QCDatabase()
            session_id = db.save_qc_session(
                json_data=json_data,
                html_path=report_url,
                json_path=f"reports/{json_filename}",
                pdf_path=pdf_url,
                notes=None
            )
            print(f"✅ Sessione salvata nel database: ID {session_id}")
        except Exception as e:
            print(f"⚠️  Errore salvataggio database: {e}")
        
        # Genera anche PDF
        pdf_url = f"reports/{pdf_filename}"
        
        try:
            # Prova con weasyprint (migliore qualità)
            from weasyprint import HTML, CSS
            HTML(string=report_html).write_pdf(pdf_path)
            print(f"PDF generato con weasyprint: {pdf_path}")
        except ImportError:
            try:
                # Fallback: pdfkit (richiede wkhtmltopdf installato)
                import pdfkit
                pdfkit.from_string(report_html, pdf_path)
                print(f"PDF generato con pdfkit: {pdf_path}")
            except:
                # Se nessuna libreria disponibile, salta PDF
                print("Nessuna libreria PDF disponibile (weasyprint/pdfkit)")
                pdf_url = None
        except Exception as e:
            print(f"Errore generazione PDF: {e}")
            pdf_url = None
        
        # Path relativo per browser
        report_url = f"reports/{report_filename}"
        json_url = f"reports/{json_filename}"
        pdf_url = f"reports/{pdf_filename}"
        
        # Return results
        result = {
            'success': True,
            'reportHtml': report_html,
            'reportUrl': report_url,  # URL relativo per aprire in browser
            'jsonUrl': json_url,  # URL JSON
            'pdfUrl': pdf_url,  # URL PDF se generato
            'ptCount': len(analyzer.pt_data),
            'ctCount': len(analyzer.ct_data)
        }
        
        print(json.dumps(result), flush=True)
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), flush=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
