/**
 * SUV Analyzer - Frontend Logic
 * JavaScript per interfaccia web e viewer DICOM
 */

// State globale
const state = {
    currentFolder: '',
    uploadedFolders: [],  // Array di tutte le cartelle caricate
    series: [],
    currentSeries: null,
    currentLUT: 'Rainbow2',  // LUT corrente
    currentSeriesForLUT: null,  // Serie corrente per reload con LUT
    images: [],
    uploadedFiles: [],
    iqcheckData: null,  // Dati IQCheck processati (null = non caricato)
    viewer: {
        currentSlice: 0,
        windowCenter: 40,
        windowWidth: 400,
        zoom: 1.0,
        panX: 0,
        panY: 0,
        dragging: false,
        lastX: 0,
        lastY: 0
    }
};

// ============================================================
// DRAG & DROP SETUP
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔧 Inizializzazione drag & drop...');
    setupDragAndDrop();
});

function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    if (!dropZone) {
        console.error('❌ Drop zone non trovata!');
        return;
    }
    
    console.log('✅ Drop zone trovata:', dropZone);
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            console.log(`📦 Event: ${eventName}`);
            preventDefaults(e);
        }, false);
        
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            console.log('✨ Drag over - highlighting');
            dropZone.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            console.log('🔻 Drag leave/drop - removing highlight');
            dropZone.classList.remove('drag-over');
        }, false);
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        console.log('📥 Drop event!', e);
        handleDrop(e);
    }, false);
    
    // Handle file input change
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            console.log('📁 File input change:', e.target.files);
            handleFiles(e.target.files);
        });
    } else {
        console.error('❌ File input non trovato!');
    }
    
    console.log('✅ Drag & drop setup completato');
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    console.log('🎯 handleDrop chiamato');
    const dt = e.dataTransfer;
    const files = dt.files;
    console.log('📦 File droppati:', files.length, files);
    handleFiles(files);
}

async function handleFiles(files) {
    console.log('🔍 handleFiles chiamato con', files.length, 'file');
    
    if (files.length === 0) {
        console.warn('⚠️ Nessun file ricevuto');
        return;
    }
    
    // Filter only .dcm files
    const dicomFiles = Array.from(files).filter(f => {
        const isDicom = f.name.toLowerCase().endsWith('.dcm');
        console.log(`📄 ${f.name}: ${isDicom ? 'DICOM ✅' : 'Non DICOM ❌'}`);
        return isDicom;
    });
    
    console.log(`✅ File DICOM trovati: ${dicomFiles.length}/${files.length}`);
    
    if (dicomFiles.length === 0) {
        const msg = '❌ Nessun file DICOM (.dcm) trovato';
        console.error(msg);
        showStatus('scan-status', msg, 'error');
        return;
    }
    
    state.uploadedFiles = dicomFiles;
    
    // Show files in drop zone
    displayUploadedFiles(dicomFiles);
    
    // Upload and process
    await uploadAndProcessFiles(dicomFiles);
}

function displayUploadedFiles(files) {
    const container = document.getElementById('drop-zone-files');
    container.innerHTML = '';
    
    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'drop-zone-file-item';
        
        const name = document.createElement('div');
        name.className = 'drop-zone-file-name';
        name.textContent = file.name;
        
        const size = document.createElement('div');
        size.className = 'drop-zone-file-size';
        size.textContent = formatFileSize(file.size);
        
        item.appendChild(name);
        item.appendChild(size);
        container.appendChild(item);
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function uploadAndProcessFiles(files) {
    console.log(`📤 Inizio upload di ${files.length} file...`);
    showStatus('scan-status', `📤 Caricamento ${files.length} file...`, '');
    
    try {
        const formData = new FormData();
        files.forEach((file, index) => {
            console.log(`➕ Aggiunto file ${index + 1}: ${file.name} (${file.size} bytes)`);
            formData.append('files', file);
        });
        
        console.log('🌐 Invio richiesta a /api/upload-dicom...');
        
        const response = await fetch('/api/upload-dicom', {
            method: 'POST',
            body: formData
        });
        
        console.log('📨 Risposta ricevuta:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 Dati ricevuti:', data);
        
        if (data.error) {
            console.error('❌ Errore dal server:', data.error);
            showStatus('scan-status', `❌ Errore: ${data.error}`, 'error');
            return;
        }
        
        // AGGIUNGI cartella alla lista (non sostituire!)
        if (data.uploadPath && !state.uploadedFolders.includes(data.uploadPath)) {
            state.uploadedFolders.push(data.uploadPath);
        }
        
        // AGGIUNGI serie nuove (non sostituire!)
        if (data.series && Array.isArray(data.series)) {
            data.series.forEach(newSerie => {
                // Controlla se serie già presente (per UID)
                const exists = state.series.some(s => s.uid === newSerie.uid);
                if (!exists) {
                    // Aggiungi path della cartella alla serie
                    newSerie.folderPath = data.uploadPath;
                    state.series.push(newSerie);
                }
            });
        }
        
        console.log(`✅ Totale serie disponibili: ${state.series.length}`);
        console.log(`✅ Cartelle caricate: ${state.uploadedFolders.length}`);
        
        showStatus('scan-status', `✅ ${files.length} file caricati - ${state.series.length} serie disponibili`, '');
        
        // MOSTRA CHECKBOX PER SELEZIONE SERIE
        showSeriesSelector();
        
        // CARICA ANCHE LE CARD PER IL VIEWER
        await loadAllSeries();
        
    } catch (error) {
        console.error('💥 Errore durante upload:', error);
        showStatus('scan-status', `❌ Errore: ${error.message}`, 'error');
    }
}

// ============================================================
// TAB SWITCHING
// ============================================================

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Activate tab button
    event.target.classList.add('active');
}

// ============================================================
// FOLDER SCANNING
// ============================================================

async function scanFolder() {
    const folderPath = document.getElementById('folder-path').value.trim();
    
    if (!folderPath) {
        showStatus('scan-status', '❌ Inserisci un path', 'error');
        return;
    }
    
    showStatus('scan-status', '🔍 Scansione in corso...', '');
    
    try {
        const response = await fetch(`/api/scan-folder?path=${encodeURIComponent(folderPath)}`);
        const data = await response.json();
        
        if (data.error) {
            showStatus('scan-status', `❌ Errore: ${data.error}`, 'error');
            return;
        }
        
        // Update state
        state.currentFolder = folderPath;
        state.series = data.series || [];
        
        showStatus('scan-status', `✅ Trovate ${state.series.length} serie, ${data.totalFiles} file - Caricamento...`, '');
        
        // CARICA TUTTE LE SERIE AUTOMATICAMENTE
        await loadAllSeries();
        
    } catch (error) {
        showStatus('scan-status', `❌ Errore: ${error.message}`, 'error');
    }
}

// ============================================================
// LOAD ALL SERIES
// ============================================================

async function loadAllSeries() {
    if (state.series.length === 0) return;
    
    showStatus('scan-status', `📥 Caricamento ${state.series.length} serie...`, '');
    
    // Clear series container
    const seriesContainer = document.getElementById('series-container');
    seriesContainer.innerHTML = '';
    
    // Load each series
    for (let i = 0; i < state.series.length; i++) {
        const series = state.series[i];
        
        showStatus('scan-status', `📥 Caricamento ${i + 1}/${state.series.length}: ${series.description}...`, '');
        
        try {
            const response = await fetch('/api/load-series', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    folderPath: series.folderPath || state.uploadedFolders[0] || state.currentFolder,
                    seriesUid: series.uid
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error(`Errore caricamento ${series.description}:`, data.error);
                continue;
            }
            
            // Store images
            series.images = data.images || [];
            series.loaded = true;
            
            // Create series card
            createSeriesCard(series, i);
            
        } catch (error) {
            console.error(`Errore caricamento serie ${i}:`, error);
        }
    }
    
    showStatus('scan-status', `✅ ${state.series.length} serie caricate!`, '');
    
    // Load first series in viewer
    if (state.series.length > 0 && state.series[0].loaded) {
        loadSeriesInViewer(0);
    }
}

function createSeriesCard(series, index) {
    const container = document.getElementById('series-container');
    
    const card = document.createElement('div');
    card.className = 'series-card';
    card.onclick = () => loadSeriesInViewer(index);
    
    // Badge modalità con fallback
    const modality = series.modality || 'UK';
    const modalityBadge = document.createElement('div');
    modalityBadge.className = `modality-badge modality-${modality.toLowerCase()}`;
    modalityBadge.textContent = modality;
    modalityBadge.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        background: ${modality === 'PT' ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' : 
                     modality === 'CT' ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' : '#999'};
        color: white;
        z-index: 10;
    `;
    
    const title = document.createElement('div');
    title.className = 'series-card-title';
    title.textContent = series.description;
    
    const info = document.createElement('div');
    info.className = 'series-card-info';
    info.textContent = `${series.count} slices`;
    
    card.appendChild(modalityBadge);
    card.appendChild(title);
    card.appendChild(info);
    
    container.appendChild(card);
}

function loadSeriesInViewer(seriesIndex) {
    const series = state.series[seriesIndex];
    
    console.log(`[VIEWER] Loading series ${seriesIndex}:`, series);
    
    if (!series) {
        console.error('[VIEWER] Serie non trovata!');
        showStatus('series-info', '❌ Serie non trovata', 'error');
        return;
    }
    
    if (!series.loaded) {
        console.error('[VIEWER] Serie non caricata!', series);
        showStatus('series-info', '❌ Serie non caricata. Caricamento in corso...', 'error');
        
        // Prova a caricare la serie ora
        loadSeriesImages(series, seriesIndex).then(() => {
            console.log('[VIEWER] Serie caricata, riprovo viewer');
            loadSeriesInViewer(seriesIndex);
        }).catch(err => {
            console.error('[VIEWER] Errore caricamento:', err);
            showStatus('series-info', `❌ Errore: ${err.message}`, 'error');
        });
        return;
    }
    
    if (!series.images || series.images.length === 0) {
        console.error('[VIEWER] Serie senza immagini!', series);
        showStatus('series-info', '❌ Nessuna immagine disponibile', 'error');
        return;
    }
    
    console.log(`[VIEWER] OK: ${series.images.length} immagini`);
    
    state.currentSeries = series;
    state.currentSeriesForLUT = seriesIndex;  // Salva per reload LUT
    state.images = series.images;
    
    // Mostra/nascondi selettore LUT in base a modalità
    const lutSelector = document.getElementById('lut-selector');
    if (lutSelector) {
        if (series.modality === 'PT') {
            lutSelector.style.display = 'block';
        } else {
            lutSelector.style.display = 'none';
        }
    }
    
    // Highlight selected card
    document.querySelectorAll('.series-card').forEach((card, i) => {
        card.classList.toggle('active', i === seriesIndex);
    });
    
    // Initialize viewer
    initViewer();
    
    showStatus('series-info', `✅ ${series.description} (${series.count} slices)`, '');
}

// Funzione helper per caricare immagini di una serie
async function loadSeriesImages(series, index) {
    console.log(`[LOAD] Caricamento serie ${index}: ${series.description}`);
    
    const response = await fetch('/api/load-series', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            folderPath: series.folderPath || state.uploadedFolders[0] || state.currentFolder,
            seriesUid: series.uid,
            lutName: state.currentLUT  // Passa LUT corrente
        })
    });
    
    const data = await response.json();
    
    if (data.error) {
        throw new Error(data.error);
    }
    
    series.images = data.images || [];
    series.loaded = true;
    
    console.log(`[LOAD] OK: ${series.images.length} immagini caricate con LUT ${state.currentLUT}`);
    
    return series;
}

// ============================================================
// SERIES LOADING
// ============================================================

// ============================================================
// DICOM VIEWER
// ============================================================

function initViewer() {
    const viewerDiv = document.getElementById('dicom-viewer');
    
    // Check se ci sono immagini
    if (!state.images || state.images.length === 0) {
        viewerDiv.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #999;">
                <div style="text-align: center;">
                    <h3>Nessuna immagine disponibile</h3>
                    <p>Seleziona una serie dalla lista</p>
                </div>
            </div>
        `;
        console.error('[VIEWER] Nessuna immagine da mostrare');
        return;
    }
    
    console.log(`[VIEWER] Inizializzazione con ${state.images.length} immagini`);
    
    // Preset W/L per modalità
    const isPET = state.currentSeries.modality === 'PT';
    const presetButtons = isPET ? `
        <button class="preset-btn" onclick="applyLUTPreset('rainbow2')">🌈 Rainbow2</button>
        <button class="preset-btn" onclick="applyLUTPreset('hot')">🔥 Hot Iron</button>
        <button class="preset-btn" onclick="applyLUTPreset('pet')">📊 PET</button>
        <button class="preset-btn" onclick="applyLUTPreset('gray')">⬜ Grayscale</button>
    ` : `
        <button class="preset-btn" onclick="applyWLPreset(400, 40)">🫁 Abdomen</button>
        <button class="preset-btn" onclick="applyWLPreset(1500, -600)">💨 Lung</button>
        <button class="preset-btn" onclick="applyWLPreset(2000, 400)">🦴 Bone</button>
        <button class="preset-btn" onclick="applyWLPreset(80, 40)">🧠 Brain</button>
        <button class="preset-btn" onclick="applyWLPreset(400, 50)">💪 Soft</button>
    `;
    
    // Create canvas and overlays
    viewerDiv.innerHTML = `
        <div class="viewer-presets" style="position: absolute; top: 10px; left: 10px; z-index: 100; display: flex; gap: 5px; flex-wrap: wrap; max-width: 600px;">
            ${presetButtons}
        </div>
        <canvas id="dicom-canvas"></canvas>
        <div class="viewer-info">
            <div id="info-series">Serie: ${state.currentSeries.description}</div>
            <div id="info-slice">Slice: 1 / ${state.images.length}</div>
            <div id="info-wl">W/L: 400 / 40</div>
            <div id="info-zoom">Zoom: 100%</div>
            <div id="info-modality">Modalità: ${state.currentSeries.modality}</div>
        </div>
        <div class="viewer-help">
            <div>🖱️ <b>Wheel:</b> Scroll slice</div>
            <div>🖱️ <b>Drag:</b> Adjust W/L</div>
            <div>⌨️ <b>Ctrl+Wheel:</b> Zoom</div>
            <div>🖱️ <b>Double-click:</b> Reset</div>
        </div>
    `;
    
    const canvas = document.getElementById('dicom-canvas');
    const ctx = canvas.getContext('2d', { alpha: false });
    
    // Set canvas size
    canvas.width = viewerDiv.clientWidth - 50;
    canvas.height = viewerDiv.clientHeight - 50;
    
    // Load images
    const imageElements = [];
    const imageMetadata = [];
    let loadedCount = 0;
    
    state.images.forEach((item, index) => {
        // Gestisci sia vecchio formato (string) che nuovo (object)
        const dataUrl = typeof item === 'string' ? item : item.image;
        const itemMetadata = typeof item === 'object' ? item.metadata : null;
        
        const img = new Image();
        img.onload = () => {
            imageElements[index] = img;
            imageMetadata[index] = itemMetadata;
            loadedCount++;
            
            if (loadedCount === state.images.length) {
                // All images loaded
                state.viewer.imageElements = imageElements;
                state.viewer.imageMetadata = imageMetadata;
                state.viewer.currentSlice = Math.floor(imageElements.length / 2);
                
                // Imposta W/L da metadata del primo elemento se disponibili
                const firstMetadata = imageMetadata[0];
                if (firstMetadata && firstMetadata.window_center && firstMetadata.window_width) {
                    state.viewer.windowCenter = firstMetadata.window_center;
                    state.viewer.windowWidth = firstMetadata.window_width;
                }
                
                renderViewer(canvas, ctx);
                setupViewerEvents(canvas, ctx);
            }
        };
        img.src = dataUrl;
    });
}

function renderViewer(canvas, ctx) {
    const images = state.viewer.imageElements;
    
    if (!images || images.length === 0) return;
    
    const img = images[state.viewer.currentSlice];
    if (!img) return;
    
    // Clear
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Calculate size
    const imgRatio = img.width / img.height;
    const canvasRatio = canvas.width / canvas.height;
    
    let w, h;
    if (imgRatio > canvasRatio) {
        w = canvas.width * state.viewer.zoom;
        h = w / imgRatio;
    } else {
        h = canvas.height * state.viewer.zoom;
        w = h * imgRatio;
    }
    
    const x = (canvas.width - w) / 2 + state.viewer.panX;
    const y = (canvas.height - h) / 2 + state.viewer.panY;
    
    // Apply W/L using canvas manipulation
    // Create temporary canvas for W/L processing
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = img.width;
    tempCanvas.height = img.height;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(img, 0, 0);
    
    // Get image data
    const imageData = tempCtx.getImageData(0, 0, img.width, img.height);
    const data = imageData.data;
    
    // Apply W/L transformation
    const ww = state.viewer.windowWidth;
    const wc = state.viewer.windowCenter;
    const minVal = wc - ww / 2;
    const maxVal = wc + ww / 2;
    const range = maxVal - minVal;
    
    if (range > 0) {
        for (let i = 0; i < data.length; i += 4) {
            // Get grayscale value (assume grayscale or use average)
            const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
            
            // Apply window/level
            let newVal;
            if (gray <= minVal) {
                newVal = 0;
            } else if (gray >= maxVal) {
                newVal = 255;
            } else {
                newVal = ((gray - minVal) / range) * 255;
            }
            
            data[i] = newVal;     // R
            data[i + 1] = newVal; // G
            data[i + 2] = newVal; // B
            // Alpha unchanged
        }
        
        tempCtx.putImageData(imageData, 0, 0);
    }
    
    // Draw processed image
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(tempCanvas, x, y, w, h);
    
    // Update info
    updateViewerInfo();
}

function updateViewerInfo() {
    document.getElementById('info-slice').textContent = 
        `Slice: ${state.viewer.currentSlice + 1} / ${state.images.length}`;
    document.getElementById('info-wl').textContent = 
        `W/L: ${Math.round(state.viewer.windowWidth)} / ${Math.round(state.viewer.windowCenter)}`;
    document.getElementById('info-zoom').textContent = 
        `Zoom: ${Math.round(state.viewer.zoom * 100)}%`;
}

function setupViewerEvents(canvas, ctx) {
    // Wheel - scroll or zoom
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        if (e.ctrlKey || e.metaKey) {
            // Zoom
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            state.viewer.zoom = Math.max(0.1, Math.min(10, state.viewer.zoom * delta));
        } else {
            // Scroll slice
            const delta = e.deltaY > 0 ? 1 : -1;
            state.viewer.currentSlice = Math.max(0, Math.min(
                state.images.length - 1,
                state.viewer.currentSlice + delta
            ));
        }
        
        renderViewer(canvas, ctx);
    });
    
    // Mouse drag - W/L
    canvas.addEventListener('mousedown', (e) => {
        state.viewer.dragging = true;
        state.viewer.lastX = e.clientX;
        state.viewer.lastY = e.clientY;
        canvas.style.cursor = 'move';
    });
    
    canvas.addEventListener('mousemove', (e) => {
        if (!state.viewer.dragging) return;
        
        const dx = e.clientX - state.viewer.lastX;
        const dy = e.clientY - state.viewer.lastY;
        
        state.viewer.windowWidth = Math.max(1, state.viewer.windowWidth + dx * 2);
        state.viewer.windowCenter = state.viewer.windowCenter - dy * 2;
        
        state.viewer.lastX = e.clientX;
        state.viewer.lastY = e.clientY;
        
        renderViewer(canvas, ctx);
    });
    
    canvas.addEventListener('mouseup', () => {
        state.viewer.dragging = false;
        canvas.style.cursor = 'crosshair';
    });
    
    canvas.addEventListener('mouseleave', () => {
        state.viewer.dragging = false;
        canvas.style.cursor = 'crosshair';
    });
    
    // Double click - reset
    canvas.addEventListener('dblclick', () => {
        state.viewer.zoom = 1.0;
        state.viewer.panX = 0;
        state.viewer.panY = 0;
        state.viewer.windowCenter = 40;
        state.viewer.windowWidth = 400;
        renderViewer(canvas, ctx);
    });
    
    // Keyboard
    document.addEventListener('keydown', (e) => {
        if (!canvas.matches(':hover')) return;
        
        let changed = false;
        
        switch(e.key) {
            case 'ArrowUp':
            case 'PageUp':
                state.viewer.currentSlice = Math.max(0, state.viewer.currentSlice - 1);
                changed = true;
                break;
            case 'ArrowDown':
            case 'PageDown':
                state.viewer.currentSlice = Math.min(state.images.length - 1, state.viewer.currentSlice + 1);
                changed = true;
                break;
            case 'Home':
                state.viewer.currentSlice = 0;
                changed = true;
                break;
            case 'End':
                state.viewer.currentSlice = state.images.length - 1;
                changed = true;
                break;
            case 'r':
            case 'R':
                state.viewer.zoom = 1.0;
                state.viewer.panX = 0;
                state.viewer.panY = 0;
                changed = true;
                break;
        }
        
        if (changed) {
            e.preventDefault();
            renderViewer(canvas, ctx);
        }
    });
}

// ============================================================
// ANALYSIS
// ============================================================

// ============================================================
// IQCHECK IMPORT
// ============================================================

async function importIQCheck(file) {
    if (!file) return;

    showStatus('iqcheck-status', '⏳ Importazione in corso...', '');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/import-iqcheck', {
            method: 'POST',
            body: formData
        });

        const resp = await response.json();

        if (!resp.success) {
            showStatus('iqcheck-status', `❌ Errore: ${resp.error || 'Import fallito'}`, 'error');
            return;
        }

        // Unwrap: runPython torna {success, iqcheck: {...}}, vogliamo solo la parte interna
        const data = resp.iqcheck;

        // Salva i dati processati nello state
        state.iqcheckData = data;

        // Aggiorna UI: mostra riepilogo
        const overallIcon = data.overall_pass ? '✅' : '❌';
        const date = data.date || '—';
        const headPass = data.evaluations?.head
            ? Object.values(data.evaluations.head).every(v => v === 'pass') ? '✅' : '❌'
            : '—';
        const bodyPass = data.evaluations?.body
            ? Object.values(data.evaluations.body).every(v => v === 'pass') ? '✅' : '❌'
            : '—';

        document.getElementById('iqcheck-summary').textContent =
            `${date} · Head ${headPass} · Body ${bodyPass} · Esito: ${overallIcon}`;

        document.getElementById('iqcheck-empty').style.display  = 'none';
        document.getElementById('iqcheck-loaded').style.display = 'block';

        showStatus('iqcheck-status', '✅ IQCheck importato correttamente', '');

        // Reset dell'input per permettere di ricaricare lo stesso file
        document.getElementById('iqcheck-input').value = '';

    } catch (error) {
        showStatus('iqcheck-status', `❌ Errore: ${error.message}`, 'error');
    }
}

function removeIQCheck() {
    state.iqcheckData = null;
    document.getElementById('iqcheck-empty').style.display  = 'block';
    document.getElementById('iqcheck-loaded').style.display = 'none';
    document.getElementById('iqcheck-status').classList.remove('visible');
}

async function runAnalysis() {
    if (state.uploadedFolders.length === 0 && !state.currentFolder) {
        showStatus('analysis-status', '❌ Carica prima file DICOM o scansiona una cartella', 'error');
        return;
    }
    
    // Usa tutte le cartelle caricate, o currentFolder come fallback
    const foldersToAnalyze = state.uploadedFolders.length > 0 
        ? state.uploadedFolders 
        : [state.currentFolder];
    
    showStatus('analysis-status', `⚡ Analisi in corso su ${foldersToAnalyze.length} cartelle...`, '');
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folderPaths: foldersToAnalyze,
                selectedSeries: getSelectedSeriesUIDs(),
                iqcheckData: state.iqcheckData  // null se non caricato
            })
        });
        
        const data = await response.json();
        
        console.log('Analysis response:', data);
        console.log('Has reportHtml:', !!data.reportHtml);
        console.log('Report length:', data.reportHtml ? data.reportHtml.length : 0);
        
        if (!data.success || data.error) {
            showStatus('analysis-status', `❌ Errore: ${data.error || 'Analisi fallita'}`, 'error');
            return;
        }
        
        // Show report
        const reportElement = document.getElementById('analysis-report');
        
        // Se c'è reportUrl, mostra link al file salvato
        if (data.reportUrl) {
            const pdfLink = data.pdfUrl ? `
                <a href="${data.pdfUrl}" target="_blank" 
                   style="display: inline-block; padding: 12px 25px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                          color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px; margin-left: 15px;">
                    📄 Scarica PDF
                </a>
            ` : '';
            
            reportElement.innerHTML = `
                <div style="padding: 30px; text-align: center; background: rgba(76, 175, 80, 0.1); border-radius: 12px;">
                    <h2 style="color: #4FC3F7; margin-bottom: 15px;">✅ Analisi Completata!</h2>
                    <p style="margin-bottom: 20px; color: #ccc;">Report generato: ${data.ptCount} PET, ${data.ctCount} CT</p>
                    <div>
                        <a href="${data.reportUrl}" target="_blank" 
                           style="display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                            📊 Apri Report Completo
                        </a>
                        ${pdfLink}
                    </div>
                    <p style="margin-top: 15px; font-size: 12px; color: #999;">
                        File salvati: <code style="color: #4FC3F7;">${data.reportUrl}</code>
                        ${data.pdfUrl ? ` | <code style="color: #F093FB;">${data.pdfUrl}</code>` : ''}
                    </p>
                </div>
            `;
        } else if (data.reportHtml && data.reportHtml.length > 0) {
            // Se è solo un filename (corto), crea un link
            if (data.reportHtml.length < 100 && data.reportHtml.endsWith('.html')) {
                reportElement.innerHTML = `
                    <div style="padding: 30px; text-align: center; background: rgba(76, 175, 80, 0.1); border-radius: 12px;">
                        <h2 style="color: #4FC3F7; margin-bottom: 15px;">✅ Analisi Completata!</h2>
                        <p style="margin-bottom: 20px; color: #ccc;">Report generato: ${data.ptCount} PET, ${data.ctCount} CT</p>
                        <a href="${data.reportHtml}" target="_blank" 
                           style="display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                            📊 Apri Report Completo
                        </a>
                        <p style="margin-top: 15px; font-size: 12px; color: #999;">
                            Il report è stato salvato anche in: <code style="color: #4FC3F7;">${data.reportHtml}</code>
                        </p>
                    </div>
                `;
            } else {
                // È HTML completo, inseriscilo direttamente
                reportElement.innerHTML = data.reportHtml;
            }
            
            console.log('Report inserted, element:', reportElement);
            
            // Scroll to report
            reportElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            console.error('No report HTML in response!');
            showStatus('analysis-status', '⚠️ Report vuoto', 'error');
            return;
        }
        
        showStatus('analysis-status', '✅ Analisi completata!', '');
        
    } catch (error) {
        console.error('Analysis error:', error);
        showStatus('analysis-status', `❌ Errore: ${error.message}`, 'error');
    }
}

// ============================================================
// UTILITIES
// ============================================================

function showStatus(elementId, message, type = '') {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = 'status visible';
    
    if (type === 'error') {
        el.classList.add('error');
    }
}

// ============================================================
// SERIES SELECTOR
// ============================================================

function showSeriesSelector() {
    const container = document.getElementById('series-selector-container');
    const list = document.getElementById('series-list');
    
    if (!container || !list) {
        console.error('Series selector elements not found!');
        return;
    }
    
    list.innerHTML = '';
    
    state.series.forEach((series, idx) => {
        const item = document.createElement('div');
        item.className = 'series-item';
        
        const isSecondaryCapture = series.seriesNumber > 40000 || 
                                  series.description.includes('Secondary') ||
                                  series.description.includes('SECONDARY');
        
        const defaultChecked = series.modality === 'PT' && !isSecondaryCapture;
        
        item.innerHTML = `
            <input type="checkbox" id="series_${idx}" value="${series.uid}" 
                   ${defaultChecked ? 'checked' : ''}>
            <div class="series-info">
                <div class="series-desc">${series.description}</div>
                <div class="series-details">
                    Modalità: ${series.modality} | 
                    Serie: ${series.seriesNumber} | 
                    File: ${series.fileCount}
                </div>
                ${isSecondaryCapture ? '<div class="series-warning">⚠️ Secondary Capture - potrebbe causare errori</div>' : ''}
            </div>
        `;
        
        list.appendChild(item);
    });
    
    container.style.display = 'block';
}

function selectAllSeries() {
    document.querySelectorAll('#series-list input[type="checkbox"]').forEach(cb => cb.checked = true);
}

function deselectAllSeries() {
    document.querySelectorAll('#series-list input[type="checkbox"]').forEach(cb => cb.checked = false);
}

function selectOnlyPET() {
    state.series.forEach((series, idx) => {
        const cb = document.getElementById(`series_${idx}`);
        const isSecondaryCapture = series.seriesNumber > 40000 ||
                                  series.description.includes('Secondary') ||
                                  series.description.includes('SECONDARY');
        cb.checked = series.modality === 'PT' && !isSecondaryCapture;
    });
}

function getSelectedSeriesUIDs() {
    const selected = [];
    state.series.forEach((series, idx) => {
        const cb = document.getElementById(`series_${idx}`);
        if (cb && cb.checked) {
            selected.push(series.uid);
        }
    });
    return selected;
}

// ============================================================
// VIEWER PRESETS
// ============================================================

function applyWLPreset(window, level) {
    console.log(`[PRESET] Applying W/L: ${window}/${level}`);
    state.viewer.windowWidth = window;
    state.viewer.windowCenter = level;
    
    // Update info display
    const infoWL = document.getElementById('info-wl');
    if (infoWL) {
        infoWL.textContent = `W/L: ${window} / ${level}`;
    }
    
    // Re-render
    const canvas = document.getElementById('dicom-canvas');
    const ctx = canvas ? canvas.getContext('2d', { alpha: false }) : null;
    if (canvas && ctx) {
        renderViewer(canvas, ctx);
    }
}

function applyLUTPreset(preset) {
    console.log(`[PRESET] Applying LUT: ${preset}`);
    state.viewer.lutPreset = preset;
    
    // LUT presets per PET
    const luts = {
        'rainbow2': 'Rainbow2',  // Già implementato
        'hot': 'Hot Iron',
        'pet': 'PET',
        'gray': 'Grayscale'
    };
    
    // Update info display
    const infoModality = document.getElementById('info-modality');
    if (infoModality) {
        infoModality.textContent = `Modalità: ${state.currentSeries.modality} | LUT: ${luts[preset]}`;
    }
    
    // Re-render con nuovo LUT
    const canvas = document.getElementById('dicom-canvas');
    const ctx = canvas ? canvas.getContext('2d', { alpha: false }) : null;
    if (canvas && ctx) {
        renderViewer(canvas, ctx);
    }
}

// ============================================================
// LUT COLORMAP SWITCHING
// ============================================================

async function changeLUT() {
    const lutSelect = document.getElementById('lut-select');
    const newLUT = lutSelect.value;
    
    console.log(`[LUT] Cambiando da ${state.currentLUT} a ${newLUT}`);
    
    if (!state.currentSeriesForLUT && state.currentSeriesForLUT !== 0) {
        console.error('[LUT] Nessuna serie caricata');
        return;
    }
    
    // Aggiorna LUT corrente
    state.currentLUT = newLUT;
    
    // Ricarica serie con nuova LUT
    const series = state.series[state.currentSeriesForLUT];
    
    // Reset loaded flag per forzare reload
    series.loaded = false;
    series.images = [];
    
    // Mostra loading
    showStatus('series-info', `🎨 Applicando ${newLUT}...`, 'info');
    
    try {
        // Ricarica immagini con nuova LUT
        await loadSeriesImages(series, state.currentSeriesForLUT);
        
        // Ricarica viewer
        loadSeriesInViewer(state.currentSeriesForLUT);
        
        showStatus('series-info', `✅ ${newLUT} applicata!`, 'success');
    } catch (err) {
        console.error('[LUT] Errore cambio LUT:', err);
        showStatus('series-info', `❌ Errore: ${err.message}`, 'error');
    }
}

// ============================================================
// QC HISTORY & COMPARISON
// ============================================================

let qcHistorySessions = [];
let selectedSessionsForComparison = [];

async function loadQCHistory() {
    showStatus('history-table', '⏳ Caricamento storico...', 'info');
    
    try {
        const response = await fetch('/api/list-sessions');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Errore caricamento storico');
        }
        
        qcHistorySessions = data.sessions || [];
        renderHistoryTable();
        
        showStatus('history-table', `✅ ${qcHistorySessions.length} sessioni caricate`, 'success');
        
    } catch (error) {
        console.error('Errore caricamento storico:', error);
        showStatus('history-table', `❌ Errore: ${error.message}`, 'error');
    }
}

function renderHistoryTable() {
    const container = document.getElementById('history-table');
    
    if (qcHistorySessions.length === 0) {
        container.innerHTML = '<p style="color: #999;">Nessuna sessione QC nel database.</p>';
        return;
    }
    
    let html = `
        <table style="width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05);">
            <thead>
                <tr style="background: rgba(79, 195, 247, 0.2); border-bottom: 2px solid #4FC3F7;">
                    <th style="padding: 12px; text-align: left;">
                        <input type="checkbox" onchange="toggleAllSessions(this.checked)">
                    </th>
                    <th style="padding: 12px; text-align: left;">ID</th>
                    <th style="padding: 12px; text-align: left;">Data/Ora</th>
                    <th style="padding: 12px; text-align: left;">Scanner</th>
                    <th style="padding: 12px; text-align: center;">PET Slices</th>
                    <th style="padding: 12px; text-align: center;">CT Slices</th>
                    <th style="padding: 12px; text-align: center;">Report</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    qcHistorySessions.forEach((session, idx) => {
        const bgColor = idx % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)';
        const timestamp = session.timestamp ? session.timestamp.substring(0, 16).replace('T', ' ') : 'N/A';
        
        html += `
            <tr style="background: ${bgColor}; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 10px;">
                    <input type="checkbox" class="session-checkbox" data-session-id="${session.id}" 
                           onchange="toggleSessionSelection(${session.id}, this.checked)">
                </td>
                <td style="padding: 10px; color: #4FC3F7;">${session.id}</td>
                <td style="padding: 10px;">${timestamp}</td>
                <td style="padding: 10px;">${session.scanner_name || 'Unknown'}</td>
                <td style="padding: 10px; text-align: center;">${session.pt_slices || 0}</td>
                <td style="padding: 10px; text-align: center;">${session.ct_slices || 0}</td>
                <td style="padding: 10px; text-align: center;">
                    <a href="/${session.report_html_path}" target="_blank" 
                       style="color: #4FC3F7; text-decoration: none;">📄 HTML</a>
                    ${session.report_json_path ? 
                        `| <a href="/${session.report_json_path}" target="_blank" 
                            style="color: #4FC3F7; text-decoration: none;">📊 JSON</a>` : ''}
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function toggleAllSessions(checked) {
    document.querySelectorAll('.session-checkbox').forEach(cb => {
        cb.checked = checked;
        const sessionId = parseInt(cb.dataset.sessionId);
        if (checked) {
            if (!selectedSessionsForComparison.includes(sessionId)) {
                selectedSessionsForComparison.push(sessionId);
            }
        } else {
            selectedSessionsForComparison = [];
        }
    });
    updateCompareButton();
}

function toggleSessionSelection(sessionId, checked) {
    if (checked) {
        if (!selectedSessionsForComparison.includes(sessionId)) {
            selectedSessionsForComparison.push(sessionId);
        }
    } else {
        const index = selectedSessionsForComparison.indexOf(sessionId);
        if (index > -1) {
            selectedSessionsForComparison.splice(index, 1);
        }
    }
    updateCompareButton();
}

function updateCompareButton() {
    const count = selectedSessionsForComparison.length;
    const button = document.querySelector('button[onclick="compareSelected()"]');
    if (button) {
        button.textContent = `📊 Confronta Selezionate (${count})`;
        button.disabled = count < 2;
        button.style.opacity = count < 2 ? '0.5' : '1';
    }
}

async function compareSelected() {
    if (selectedSessionsForComparison.length < 2) {
        alert('Seleziona almeno 2 sessioni da confrontare');
        return;
    }
    
    const container = document.getElementById('comparison-results');
    container.innerHTML = '<p style="color: #4FC3F7;">⏳ Generazione confronto...</p>';
    
    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sessionIds: selectedSessionsForComparison
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Errore comparazione');
        }
        
        renderComparisonResults(data);
        
    } catch (error) {
        console.error('Errore comparazione:', error);
        container.innerHTML = `<p style="color: #F44336;">❌ Errore: ${error.message}</p>`;
    }
}

function renderComparisonResults(data) {
    const container = document.getElementById('comparison-results');
    
    let html = `
        <div style="background: rgba(79, 195, 247, 0.1); padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="color: #4FC3F7; margin-top: 0;">📊 Risultati Comparazione</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div>
                    <div style="font-size: 12px; color: #999;">Sessioni Confrontate</div>
                    <div style="font-size: 24px; color: white; font-weight: bold;">
                        ${data.statistics.sessions_count}
                    </div>
                </div>
                <div>
                    <div style="font-size: 12px; color: #999;">PET Pass Rate</div>
                    <div style="font-size: 24px; font-weight: bold; color: ${data.statistics.pt_pass_rate >= 80 ? '#4CAF50' : '#F44336'};">
                        ${data.statistics.pt_pass_rate.toFixed(1)}%
                    </div>
                </div>
                <div>
                    <div style="font-size: 12px; color: #999;">CT Pass Rate</div>
                    <div style="font-size: 24px; font-weight: bold; color: ${data.statistics.ct_pass_rate >= 80 ? '#4CAF50' : '#F44336'};">
                        ${data.statistics.ct_pass_rate.toFixed(1)}%
                    </div>
                </div>
                <div>
                    <div style="font-size: 12px; color: #999;">Trend PET CV</div>
                    <div style="font-size: 24px; color: white; font-weight: bold;">
                        ${data.statistics.pt_cv_trend === 'stable' ? '📊 Stabile' : '📈 Variabile'}
                    </div>
                </div>
            </div>
        </div>
        
        <h4 style="color: #4FC3F7; margin-top: 30px;">Grafici Comparativi</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                <h5 style="color: #4FC3F7; margin-top: 0;">PET - Coefficient of Variation</h5>
                <img src="${data.charts.pt_cv_mean}" style="width: 100%; height: auto; border-radius: 4px;">
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                <h5 style="color: #4FC3F7; margin-top: 0;">PET - Non-Uniformity Max</h5>
                <img src="${data.charts.pt_nu_max}" style="width: 100%; height: auto; border-radius: 4px;">
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                <h5 style="color: #4FC3F7; margin-top: 0;">CT - Coefficient of Variation</h5>
                <img src="${data.charts.ct_cv_mean}" style="width: 100%; height: auto; border-radius: 4px;">
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                <h5 style="color: #4FC3F7; margin-top: 0;">CT - Non-Uniformity Max</h5>
                <img src="${data.charts.ct_nu_max}" style="width: 100%; height: auto; border-radius: 4px;">
            </div>
        </div>
        
        <h4 style="color: #4FC3F7;">Tabella Comparativa</h4>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05);">
                <thead>
                    <tr style="background: rgba(79, 195, 247, 0.2); border-bottom: 2px solid #4FC3F7;">
                        <th style="padding: 12px; text-align: left;">Sessione</th>
                        <th style="padding: 12px; text-align: left;">Scanner</th>
                        <th style="padding: 12px; text-align: center;">PET CV</th>
                        <th style="padding: 12px; text-align: center;">PET NU</th>
                        <th style="padding: 12px; text-align: center;">PET Status</th>
                        <th style="padding: 12px; text-align: center;">CT CV</th>
                        <th style="padding: 12px; text-align: center;">CT NU</th>
                        <th style="padding: 12px; text-align: center;">CT Status</th>
                        <th style="padding: 12px; text-align: center;">Report</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    data.comparison_table.forEach((row, idx) => {
        const bgColor = idx % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.05)';
        const timestamp = row.timestamp.substring(0, 16).replace('T', ' ');
        
        html += `
            <tr style="background: ${bgColor}; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 10px;">${timestamp}</td>
                <td style="padding: 10px;">${row.scanner}</td>
                <td style="padding: 10px; text-align: center;">${row.pt_cv_mean.toFixed(2)}</td>
                <td style="padding: 10px; text-align: center;">${row.pt_nu_max.toFixed(2)}</td>
                <td style="padding: 10px; text-align: center;">
                    <span style="color: ${row.pt_pass ? '#4CAF50' : '#F44336'}; font-weight: bold;">
                        ${row.pt_pass ? '✅ PASS' : '❌ FAIL'}
                    </span>
                </td>
                <td style="padding: 10px; text-align: center;">${row.ct_cv_mean.toFixed(2)}</td>
                <td style="padding: 10px; text-align: center;">${row.ct_nu_max.toFixed(2)}</td>
                <td style="padding: 10px; text-align: center;">
                    <span style="color: ${row.ct_pass ? '#4CAF50' : '#F44336'}; font-weight: bold;">
                        ${row.ct_pass ? '✅ PASS' : '❌ FAIL'}
                    </span>
                </td>
                <td style="padding: 10px; text-align: center;">
                    <a href="/${row.html_url}" target="_blank" style="color: #4FC3F7;">📄</a>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    
    container.innerHTML = html;
}

// Auto-carica storico quando si apre tab history
function switchTab(tabName) {
    // Nascond tutti i tab
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Rimuovi active da tutti i bottoni
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Attiva tab selezionato
    const tabContent = document.getElementById(`tab-${tabName}`);
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Attiva bottone
    event.target.classList.add('active');
    
    // Auto-load storico quando si apre tab history
    if (tabName === 'history' && qcHistorySessions.length === 0) {
        loadQCHistory();
    }
}
