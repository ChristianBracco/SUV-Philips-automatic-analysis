#!/usr/bin/env python3
"""
API: Analyze DICOM series
Esegue analisi SUV solo sulle serie selezionate
"""

import sys
import json
from pathlib import Path
import pydicom

# Forza encoding UTF-8 per stdout (fix Windows charmap)
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import SUV analyzer
from suv_analyzer import SUVAnalyzer

def main():
    """Main analysis function"""
    try:
        # Parse arguments
        if len(sys.argv) < 2:
            raise ValueError("Missing folder_path argument")
        
        folder_path = sys.argv[1]
        
        # Check for selected series UIDs (optional)
        selected_series = []
        if len(sys.argv) > 2:
            # Additional args are selected series UIDs
            selected_series = sys.argv[2:]
        
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
        
        # Generate report
        report_html = analyzer.generate_html_report()
        
        # Esporta anche JSON
        json_data = analyzer.export_json()
        
        # Salva report su file
        import os
        from datetime import datetime
        
        # Crea cartella reports se non esiste
        reports_dir = os.path.join('public', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Nome file con timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"SUV_QC_Report_{timestamp}.html"
        json_filename = f"SUV_QC_Report_{timestamp}.json"
        report_path = os.path.join(reports_dir, report_filename)
        json_path = os.path.join(reports_dir, json_filename)
        
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
        pdf_filename = f"SUV_QC_Report_{timestamp}.pdf"
        pdf_path = os.path.join(reports_dir, pdf_filename)
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
