const projectSelector = document.getElementById('project-selector');
const scenesContainer = document.getElementById('scenes-container');
const loadingIndicator = document.getElementById('loading');
const saveBtn = document.getElementById('save-btn');
const syncWarning = document.getElementById('sync-warning');
const syncCommand = document.getElementById('sync-command');

let currentProjectData = null;
let originalState = []; 
let editingParamsIndex = null; // Índice de la escena cuyos parámetros estamos editando
let userDismissedWarning = false; // Flag para no volver a mostrar el banner si ya se descartó
let isResyncPending = false; // Flag para mantener el banner activo tras guardar cambios de layout

const SCREEN_TYPES = [
    "VIDEO", "TEXT", "SPLIT_LEFT", "SPLIT_RIGHT", "LIST", "FULL_IMAGE", "CONCEPT", "REMOTION"
];

// Cargar proyectos al iniciar
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const projects = await response.json();
        
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project;
            option.textContent = project;
            projectSelector.appendChild(option);
        });
    } catch (err) {
        console.error("Error cargando proyectos:", err);
    }
}

// Modal de recuperación de borrador
function showDraftModal() {
    return new Promise((resolve) => {
        const modal   = document.getElementById('draft-modal');
        const btnOk   = document.getElementById('draft-btn-recover');
        const btnDel  = document.getElementById('draft-btn-discard');
        const btnCancel = document.getElementById('draft-btn-cancel');

        const close = (result) => {
            modal.classList.add('hidden');
            resolve(result);
        };

        btnOk.onclick     = () => close('recover');
        btnDel.onclick    = () => close('discard');
        btnCancel.onclick = () => close('cancel');

        modal.classList.remove('hidden');
    });
}

// Cargar datos unificados
async function loadUnifiedProject(projectId) {
    loadingIndicator.classList.remove('hidden');
    scenesContainer.innerHTML = '';
    saveBtn.disabled = true;
    syncWarning.classList.add('hidden');
    editingParamsIndex = null;

    try {
        const response = await fetch(`/api/load/${projectId}/unified`);
        const data = await response.json();
        
        let scenesToRender = data.scenes;
        let header_md = data.header_md;
        let header_txt = data.header_txt;

        if (data.has_session && data.session_data) {
            const choice = await showDraftModal();
            if (choice === 'recover') {
                scenesToRender = data.session_data.scenes;
                header_md = data.session_data.header_md;
                header_txt = data.session_data.header_txt;
            } else if (choice === 'discard') {
                // Borrar el borrador del servidor
                await fetch(`/api/cache/${projectId}/unified`, { method: 'DELETE' });
            } else {
                // Cancelar: deseleccionar el combo y salir
                loadingIndicator.classList.add('hidden');
                document.getElementById('project-selector').value = '';
                return;
            }
        }

        currentProjectData = {
            project_id: projectId,
            header_md: header_md,
            header_txt: header_txt,
            scenes: scenesToRender,
            resolution: data.resolution || "1920x1080",
            bg_color: data.bg_color || "#000000",
            text_color: data.text_color || "#FFFFFF"
        };

        originalState = scenesToRender.map(s => s.type);
        renderUnifiedScenes(currentProjectData.scenes);
        saveBtn.disabled = false;
        syncCommand.textContent = `python 01_preparacion.py -p ${projectId} --desde-fase 3`;
        
    } catch (err) {
        console.error("Error cargando datos unificados:", err);
        scenesContainer.innerHTML = `<div class="error-message">Error: ${err.message}</div>`;
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

const TYPES_REQUIRING_TEXT = ["TEXT", "SPLIT_LEFT", "SPLIT_RIGHT"];
const TYPES_FORBIDDING_TEXT = ["VIDEO", "REMOTION", "FULL_IMAGE", "CONCEPT", "LIST"];

function renderUnifiedScenes(scenes) {
    scenesContainer.innerHTML = '';
    
    scenes.forEach((scene, index) => {
        const isForbidden = TYPES_FORBIDDING_TEXT.includes(scene.type);
        const isDisabled = isForbidden ? 'disabled' : '';
        const displayValue = isForbidden ? '' : (scene.text_on_screen || '');

        const card = document.createElement('div');
        card.className = `scene-card type-${scene.type.toLowerCase()}`;
        card.id = `card-${index}`;
        
        // Columna Izquierda: Control
        const leftCol = document.createElement('div');
        leftCol.className = 'card-control';
        
        let controlHtml = `
            <div class="screen-badge">Pantalla</div>
            <div class="screen-index">${index + 1}</div>
            
            <div class="screen-timer">
                <span class="timer-item">⏱ ${scene.timestamp || 'Sin tiempo'}</span>
                <span class="timer-item">⏳ ${scene.duration || '0.0'}s</span>
            </div>

            <div class="type-selector-group">
                <label class="type-label">Tipo de Pantalla</label>
                <select class="scene-type-select" onchange="updateSceneType(${index}, this.value)">
                    ${SCREEN_TYPES.map(t => `<option value="${t}" ${scene.type === t ? 'selected' : ''}>${t}</option>`).join('')}
                </select>
            </div>
        `;

        // Botón Edit para LIST, CONCEPT y REMOTION
        if (scene.type === 'LIST' || scene.type === 'CONCEPT' || scene.type === 'REMOTION') {
            controlHtml += `
                <button class="edit-params-btn" onclick="toggleEditParams(${index})">
                    <span>${editingParamsIndex === index ? 'Cerrar Edición' : '✎ Editar Contenido'}</span>
                </button>
            `;
        }

        // Renderizado de parámetros (form o badges)
        if (editingParamsIndex === index) {
            controlHtml += renderParamsForm(scene, index);
        } else {
            controlHtml += renderParamsBadges(scene);
        }

        leftCol.innerHTML = controlHtml;

        // Columna Derecha: Contenido
        const rightCol = document.createElement('div');
        rightCol.className = 'card-content';
        rightCol.innerHTML = `
            <div class="content-section">
                <span class="section-label">Contexto de Voz (Speech)</span>
                <div class="speech-box">${scene.speech || 'Sin transcripción disponible'}</div>
            </div>

            <div class="content-section">
                <span class="section-label">Texto en Pantalla ${isForbidden ? '(Bloqueado para este tipo)' : '(Editable)'}</span>
                <textarea 
                    class="text-edit-area" 
                    ${isDisabled}
                    oninput="updateSceneText(${index}, this.value)"
                    placeholder="${isForbidden ? 'Este tipo de pantalla no utiliza texto directo.' : 'Escribe aquí el texto que verá el espectador...'}">${displayValue}</textarea>
            </div>
        `;


        // Columna Derecha: Preview Visual (NUEVO)
        const previewCol = document.createElement('div');
        previewCol.className = 'card-preview';
        
        const [pW, pH] = (currentProjectData.resolution || "1920x1080").split('x').map(Number);
        const ratio = pW / pH;
        
        previewCol.innerHTML = `
            <div class="preview-aspect-ratio-box" style="aspect-ratio: ${ratio}; background-color: ${currentProjectData.bg_color || '#000000'};">
                <div class="preview-canvas" id="preview-canvas-${index}" style="color: #1a1a1a; background-color: transparent;">
                    <!-- El contenido se genera dinámicamente -->
                </div>
            </div>
            <div class="preview-label">Live Preview (${pW}x${pH})</div>
        `;

        card.appendChild(leftCol);
        card.appendChild(rightCol);
        card.appendChild(previewCol);
        scenesContainer.appendChild(card);
        
        // Renderizar el primer frame del preview
        updateLivePreview(index);
    });
}

function renderParamsBadges(scene) {
    if (!scene.params) return '';
    // Solo mostrar si el tipo coincide con el original para evitar confusión tras cambio de tipo
    if (scene.type.toUpperCase() !== scene.original_type.toUpperCase()) return '';

    const paramsList = scene.params.split('//').map(p => p.trim()).filter(p => p);
    return `
        <div class="params-shelf">
            ${paramsList.map(p => `<span class="param-badge">${p}</span>`).join('')}
        </div>
    `;
}

function renderParamsForm(scene, index) {
    const parts = scene.params.split('//').map(p => p.trim());
    let formHtml = '<div class="params-edit-form">';

    if (scene.type === 'LIST') {
        formHtml += `
            <div class="list-notice">
                <strong>💡 Tip:</strong> El primer ítem (o el título con @) se sincronizará automáticamente con la locución.
            </div>
            <div class="param-input-group">
                <label class="param-input-label">Título (opcional con @)</label>
                <input type="text" class="param-field" id="param-title-${index}" value="${parts[0] || ''}" oninput="syncParams(${index})">
            </div>
        `;
        // Generar 7 campos para items
        for (let i = 1; i <= 7; i++) {
            formHtml += `
            <div class="param-input-group">
                <label class="param-input-label">Item ${i}</label>
                <input type="text" class="param-field param-item-${index}" value="${parts[i] || ''}" oninput="syncParams(${index})">
            </div>
            `;
        }
    } else if (scene.type === 'CONCEPT') {
        formHtml += `
            <div class="param-input-group">
                <label class="param-input-label">Título del Concepto</label>
                <input type="text" class="param-field" id="param-title-${index}" value="${parts[0] || ''}" oninput="syncParams(${index})">
            </div>
            <div class="param-input-group">
                <label class="param-input-label">Contenido / Definición</label>
                <textarea class="param-field" id="param-body-${index}" rows="3" oninput="syncParams(${index})">${parts[1] || ''}</textarea>
            </div>
        `;
    } else if (scene.type === 'REMOTION') {
        const selected = parts[0] ? parts[0].replace('$', '').trim() : '';
        formHtml += `
            <div class="list-notice" style="margin-bottom:10px;">
                <strong>🤖 IA Remotion:</strong> Selecciona la plantilla visual. El LLM construirá automáticamente los parámetros usando el contexto de voz de este segmento.
            </div>
            <div class="param-input-group">
                <label class="param-input-label">Plantilla Remotion</label>
                <select class="param-field" id="param-template-${index}" onchange="syncParams(${index})">
                    <option value="" ${!selected ? 'selected' : ''}>-- Selecciona --</option>
                    <option value="TypeWriter" ${selected === 'TypeWriter' ? 'selected' : ''}>TypeWriter (Terminal hacker)</option>
                    <option value="MindMap" ${selected === 'MindMap' ? 'selected' : ''}>MindMap (Mapa Conceptual)</option>
                    <option value="LinearSteps" ${selected === 'LinearSteps' ? 'selected' : ''}>LinearSteps (Pasos Lineales)</option>
                    <option value="FlipCards" ${selected === 'FlipCards' ? 'selected' : ''}>FlipCards (Tarjetas con Flip)</option>
                </select>
            </div>
        `;

    }

    formHtml += '</div>';
    return formHtml;
}

window.toggleEditParams = (index) => {
    if (editingParamsIndex === index) {
        editingParamsIndex = null;
    } else {
        editingParamsIndex = index;
    }
    renderUnifiedScenes(currentProjectData.scenes);
};

window.syncParams = (index) => {
    const scene = currentProjectData.scenes[index];
    let newParams = [];

    if (scene.type === 'LIST') {
        let title = document.getElementById(`param-title-${index}`).value.trim();
        if (title) {
            // Asegurar que el título de la lista empiece con @ para el motor de video
            if (!title.startsWith('@')) title = '@ ' + title;
            newParams.push(title);
        }
        
        const items = document.querySelectorAll(`.param-item-${index}`);
        items.forEach(item => {
            const val = item.value.trim();
            if (val) newParams.push(val);
        });
    } else if (scene.type === 'CONCEPT') {
        const title = document.getElementById(`param-title-${index}`).value.trim();
        const body = document.getElementById(`param-body-${index}`).value.trim();
        if (title) newParams.push(title);
        if (body) newParams.push(body);
    } else if (scene.type === 'REMOTION') {
        const template = document.getElementById(`param-template-${index}`).value;
        if (template) newParams.push('$' + template);
    }

    scene.params = newParams.join(' // ');
    updateLivePreview(index);
    autoSaveCache();
};

window.updateSceneType = (index, newType) => {
    currentProjectData.scenes[index].type = newType;
    // Si cambiamos el tipo, cerramos la edición si estaba abierta
    if (editingParamsIndex === index) editingParamsIndex = null;
    
    renderUnifiedScenes(currentProjectData.scenes);
    checkSyncStatus();
    autoSaveCache();
};

window.updateSceneText = (index, newText) => {
    currentProjectData.scenes[index].text_on_screen = newText;
    updateLivePreview(index);
    autoSaveCache();
};

window.updateLivePreview = (index) => {
    const scene = currentProjectData.scenes[index];
    const canvas = document.getElementById(`preview-canvas-${index}`);
    if (!canvas) return;

    // Limpiar clases previas
    canvas.className = `preview-canvas preview-type-${scene.type}`;
    
    // Función auxiliar para renderizar Assets reales
    const renderMedia = (assetPath, isBackground = false) => {
        if (!assetPath) return isBackground ? '' : '<div class="preview-asset-placeholder">Sin Asset</div>';
        
        const projectId = currentProjectData.project_id;
        const fullUrl = `/projects/${projectId}/assets/${assetPath}`;
        const ext = assetPath.split('.').pop().toLowerCase();
        const isVideo = ['mp4', 'webm', 'mov', 'mkv'].includes(ext);
        
        const style = isBackground ? 'width:100%; height:100%; object-fit:cover; position:absolute; top:0; left:0;' : 'width:100%; height:100%; object-fit:contain;';
        
        if (isVideo) {
            // Safari/WebKit requiere #t=0.001 para forzar la visualización del primer frame si no hay autoplay
            return `<video src="${fullUrl}#t=0.001" preload="metadata" controls class="preview-media" style="${style}"></video>`;
        } else {
            return `<img src="${fullUrl}" class="preview-media" style="${style}">`;
        }
    };

    let html = '';
    const text = (scene.text_on_screen || '').trim();
    const params = (scene.params || '').split('//').map(p => p.trim());
    const asset = scene.extra_fields_txt ? scene.extra_fields_txt['ASSET'] : null;

    if (scene.type === 'CONCEPT') {
        const title = params[0] || 'Concepto';
        const def = params[1] || '';
        const hlColor  = currentProjectData.text_color  || '#bd0505'; // MAIN_TEXT_COLOR
        const secColor = '#1a1a1a'; // sec_color fijo igual que en Python
        html = `
            <div class="concept-title" style="color: ${hlColor};">${title}</div>
            <div class="concept-def"   style="color: ${secColor};">${def}</div>
        `;
    } else if (scene.type === 'LIST') {
        const pW = parseInt((currentProjectData.resolution || "1920x1080").split('x')[0]);
        const pH = parseInt((currentProjectData.resolution || "1920x1080").split('x')[1]);

        let ghost = '';
        let items = [...params];
        if (items.length > 0 && items[0].startsWith('@')) {
            ghost = items.shift().replace('@', '').trim();
        }

        const parsedItems = items.map(item => {
            let element = item;
            let subtext = '';
            const match = item.match(/(.*)\[(.*)\]/);
            if (match) {
                element = match[1].trim();
                subtext = match[2].trim();
            }
            return { element, subtext };
        });

        // REPLICA EXACTA DE dynamic_animator.py PARA CALCULOS DE ENCUADRE
        const n_items = Math.max(parsedItems.length, 1);
        const has_sub = parsedItems.some(i => i.subtext !== '');

        let area_top_px = Math.floor(0.12 * pH);
        const area_bot_px = Math.floor(0.88 * pH);
        if (ghost) {
            area_top_px += Math.floor(0.08 * pH); 
        }
        const usable_px = area_bot_px - area_top_px;

        const item_h_max_px = Math.floor((has_sub ? 0.155 : 0.115) * pH);
        const y_offset_prov_px = Math.min(item_h_max_px, Math.floor(usable_px / n_items));
        const bullet_fs_px = Math.max(Math.floor(0.042 * pH), Math.min(Math.floor(0.065 * pH), Math.floor(y_offset_prov_px * 0.55)));
        const sub_fs_px = Math.max(Math.floor(0.032 * pH), Math.min(Math.floor(0.048 * pH), Math.floor(y_offset_prov_px * 0.40)));

        const avail_w_px = Math.floor(pW * 0.84);
        const maxChars = Math.max(15, Math.floor(avail_w_px / (bullet_fs_px * 0.52))); 

        function pythonWrap(text, width) {
            if (!text) return [];
            const words = text.split(/\s+/);
            const lines = [];
            let currentLine = words[0];
            
            for (let i = 1; i < words.length; i++) {
                const word = words[i];
                if (currentLine.length + 1 + word.length <= width) {
                    currentLine += " " + word;
                } else {
                    lines.push(currentLine);
                    currentLine = word;
                }
            }
            if (currentLine) lines.push(currentLine);
            return lines;
        }

        const line_h_px = Math.floor(bullet_fs_px * 1.18);
        const sub_gap_px = Math.floor(pH * 0.012);
        const item_gap_px = Math.floor(pH * 0.022);

        let total_block_h_px = 0;
        const processed = parsedItems.map(i => {
            const wrapped = pythonWrap("• " + i.element, maxChars);
            let h = wrapped.length * line_h_px;
            if (i.subtext) {
                h += Math.floor(sub_fs_px * 1.3) + sub_gap_px;
            }
            total_block_h_px += h;
            return { elementLines: wrapped, subtext: i.subtext, h: h };
        });
        total_block_h_px += item_gap_px * Math.max(n_items - 1, 0);

        const y_base_px = area_top_px + Math.max(0, Math.floor((usable_px - total_block_h_px) / 2));

        // PASADA 2: Renderizar coordenadas exactas como drawtext
        let renderItemsHtml = '';
        let current_y_px = y_base_px;
        const x_start_cqw = 6;
        const x_indent_cqw = 6 + (((bullet_fs_px * 1.1) / pW) * 100);
        
        // LIST siempre es verde pizarrón con colores fijos (igual que dynamic_animator.py)
        const bulletColor  = '#FFFFFF';
        const subtextColor = '#E8D5A3';

        processed.forEach(item => {
            // Render bullet lines
            item.elementLines.forEach((lineText, li) => {
                const y_line_cqh = ((current_y_px + (li * line_h_px)) / pH) * 100;
                const x_line = li === 0 ? x_start_cqw : x_indent_cqw;
                const text = lineText === '• ' ? '&nbsp;' : lineText;
                
                renderItemsHtml += `<div style="position: absolute; top: ${y_line_cqh}cqh; left: ${x_line}cqw; font-size: ${(bullet_fs_px / pH) * 100}cqh; font-weight: bold; color: ${bulletColor}; line-height: 1; white-space: nowrap; margin:0; padding:0; display:flex; align-items:center;">${text}</div>`;
            });

            if (item.subtext) {
                const y_sub_px = current_y_px + (item.elementLines.length * line_h_px) + sub_gap_px;
                const y_sub_cqh = (y_sub_px / pH) * 100;
                renderItemsHtml += `<div style="position: absolute; top: ${y_sub_cqh}cqh; left: ${x_indent_cqw}cqw; font-size: ${(sub_fs_px / pH) * 100}cqh; color: ${subtextColor}; line-height: 1; white-space: nowrap; opacity: 0.85; margin:0; padding:0; display:flex; align-items:center;">${item.subtext}</div>`;
            }

            current_y_px += item.h + item_gap_px;
        });

        // LIST siempre usa su fondo verde, independientemente del proyecto
        canvas.style.backgroundColor = '#2C5F2E';

        html = `
            ${ghost ? `<div class="ghost-title" style="position: absolute; top: 8.5cqh; left: 50%; transform: translateX(-50%); color: ${bulletColor}; font-size: 7.5cqh; opacity: 0.15; font-weight: bold; white-space: nowrap; line-height: 1; margin: 0; padding: 0;">${ghost}</div>` : ''}
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                ${renderItemsHtml}
            </div>
        `;

    } else if (scene.type === 'TEXT') {
        html = `<div class="preview-text-content" style="pointer-events: none;">${text}</div>`;
    } else if (scene.type === 'SPLIT_LEFT' || scene.type === 'SPLIT_RIGHT') {
        const isLeft = scene.type === 'SPLIT_LEFT';
        const assetSide = `<div class="preview-split-asset">${renderMedia(asset)}</div>`;
        const textSide = `<div class="preview-split-text" style="pointer-events: none;">${text}</div>`;
        html = isLeft ? (assetSide + textSide) : (textSide + assetSide);
    } else if (scene.type === 'FULL_IMAGE' || scene.type === 'VIDEO') {
        html = `
            ${renderMedia(asset, true)}
            <div style="margin-top: auto; padding-bottom: 5%; text-align: center; font-size: 0.6em; background: rgba(0,0,0,0.4); pointer-events: none; position: relative; z-index: 1;">
                ${text}
            </div>
        `;
    } else {
        html = `<div style="display:flex; align-items:center; justify-content:center; height:100%; opacity:0.3">Preview no disponible para ${scene.type}</div>`;
    }

    canvas.innerHTML = html;

    // Validación de longitud (Overflow)
    if (scene.type === 'SPLIT_LEFT' || scene.type === 'SPLIT_RIGHT') {
        if (text.length > 60) canvas.classList.add('overflow-warning'); // Aproximación de 22 chars * 3 líneas
    }
};

function checkSyncStatus() {
    let changed = false;
    currentProjectData.scenes.forEach((s, i) => {
        if (s.type !== originalState[i]) changed = true;
    });
    
    if ((changed || isResyncPending) && !userDismissedWarning) {
        syncWarning.classList.remove('hidden');
    } else {
        syncWarning.classList.add('hidden');
    }
}

const closeSyncBtn = document.getElementById('close-sync-btn');
if (closeSyncBtn) {
    closeSyncBtn.addEventListener('click', () => {
        userDismissedWarning = true;
        syncWarning.classList.add('hidden');
    });
}

async function autoSaveCache() {
    if (!currentProjectData) return;
    try {
        await fetch(`/api/cache/${currentProjectData.project_id}/unified`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentProjectData)
        });
    } catch (err) { console.warn("Cache error:", err); }
}

saveBtn.onclick = async () => {
    if (!currentProjectData) return;
    
    // Validaciones de negocio antes de intentar guardar
    const errors = [];
    currentProjectData.scenes.forEach((scene, index) => {
        const type = scene.type.toUpperCase();
        const text = (scene.text_on_screen || '').trim();
        
        if (TYPES_REQUIRING_TEXT.includes(type) && !text) {
            errors.push(`Pantalla ${index + 1}: El tipo ${type} requiere contenido en el campo de texto.`);
        }
        
        // Sanitizar: Si es un tipo prohibido, forzamos que el texto sea vacío
        if (TYPES_FORBIDDING_TEXT.includes(type)) {
            scene.text_on_screen = "";
        }
    });

    if (errors.length > 0) {
        alert("No se puede guardar el proyecto debido a los siguientes errores:\n\n" + errors.join("\n"));
        return;
    }
    
    const confirmMsg = "Se guardarán todos los cambios técnicos y narrativos.\n\n¿Deseas continuar?";
    if (!confirm(confirmMsg)) return;
    
    saveBtn.textContent = 'Guardando Todo...';
    saveBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/save/${currentProjectData.project_id}/unified`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentProjectData)
        });
        
        if (response.ok) {
            alert("¡Éxito! Todos los archivos y backups han sido actualizados.");
            
            // Si el banner estaba activo en el momento de guardar, queremos que persista
            let hasLayoutChanges = false;
            currentProjectData.scenes.forEach((s, i) => {
                if (s.type !== originalState[i]) hasLayoutChanges = true;
            });
            if (hasLayoutChanges) {
                isResyncPending = true;
            }

            // Actualizar estado original
            currentProjectData.scenes.forEach(s => s.original_type = s.type);
            originalState = currentProjectData.scenes.map(s => s.type);
            checkSyncStatus();
            
            editingParamsIndex = null;
            renderUnifiedScenes(currentProjectData.scenes);
        } else {
            throw new Error("Error en el servidor");
        }
    } catch (err) {
        alert("Error al guardar: " + err.message);
    } finally {
        saveBtn.textContent = 'Guardar Todo';
        saveBtn.disabled = false;
    }
};

projectSelector.onchange = (e) => loadUnifiedProject(e.target.value);

loadProjects();
