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
    images: [],
    uploadedFiles: [],
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
        
        // CARICA TUTTE LE SERIE
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
    
    const modalityBadge = document.createElement('div');
    modalityBadge.className = `modality-badge modality-${series.modality.toLowerCase()}`;
    modalityBadge.textContent = series.modality;
    
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
    
    if (!series || !series.loaded) {
        showStatus('series-info', '❌ Serie non caricata', 'error');
        return;
    }
    
    state.currentSeries = series;
    state.images = series.images;
    
    // Highlight selected card
    document.querySelectorAll('.series-card').forEach((card, i) => {
        card.classList.toggle('active', i === seriesIndex);
    });
    
    // Initialize viewer
    initViewer();
    
    showStatus('series-info', `✅ ${series.description} (${series.count} slices)`, '');
}

// ============================================================
// SERIES LOADING
// ============================================================

// ============================================================
// DICOM VIEWER
// ============================================================

function initViewer() {
    const viewerDiv = document.getElementById('dicom-viewer');
    
    // Create canvas and overlays
    viewerDiv.innerHTML = `
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
    let loadedCount = 0;
    
    state.images.forEach((dataUrl, index) => {
        const img = new Image();
        img.onload = () => {
            imageElements[index] = img;
            loadedCount++;
            
            if (loadedCount === state.images.length) {
                // All images loaded
                state.viewer.imageElements = imageElements;
                state.viewer.currentSlice = Math.floor(imageElements.length / 2);
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
    
    // Draw
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(img, x, y, w, h);
    
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
                folderPaths: foldersToAnalyze
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
        if (data.reportHtml && data.reportHtml.length > 0) {
            reportElement.innerHTML = data.reportHtml;
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
