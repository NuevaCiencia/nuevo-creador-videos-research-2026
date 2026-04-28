/* =========================================================
   VIDEO CREATOR — app.js   (Desktop-app layout)
   Navigation: Sidebar tree + Phase tabs
   Views: Course picker → Tree (sections/classes) → Phase workspace
========================================================= */

/* ─── STATE ───────────────────────────────────────────── */
const S = {
  courses: [],
  activeCourse: null,
  sections: [],
  expandedSections: new Set(),
  activeClass: null,
  activePhase: 'guion',
  guionRightTab: 'research',  // 'research' | 'screens'
  guionLocked: true,           // locked after save; unlocked explicitly to edit
  saveStatus: 'saved',
  saveTimer: null,
};

/* ─── API ─────────────────────────────────────────────── */
async function api(method, url, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Error');
  return data;
}

/* ─── ICONS ───────────────────────────────────────────── */
const IC = {
  edit:  `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
  trash: `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>`,
  plus:  `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`,
  chev:  `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>`,
  swap:  `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>`,
};

/* ─── UTILS ───────────────────────────────────────────── */
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function escA(s){ return String(s).replace(/'/g,'&#39;').replace(/"/g,'&quot;'); }

function toast(msg, ok = true) {
  const el = document.createElement('div');
  el.className = `toast ${ok ? 'toast-ok' : 'toast-err'}`;
  el.textContent = msg;
  document.getElementById('toasts').append(el);
  setTimeout(() => el.remove(), 3000);
}

function setStatus(left, right, cls = 'sb-saved') {
  const l = document.getElementById('sbLeft');
  const r = document.getElementById('sbRight');
  if (l && left  !== undefined) l.textContent = left;
  if (r && right !== undefined) { r.textContent = right; r.className = cls; }
}

/* ─── SETTINGS ────────────────────────────────────────── */
function openSettings()  { document.getElementById('settingsPanel').classList.add('open');    document.getElementById('settingsBackdrop').classList.add('open'); }
function closeSettings() { document.getElementById('settingsPanel').classList.remove('open'); document.getElementById('settingsBackdrop').classList.remove('open'); }
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('vc_theme', t);
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.toggle('active', b.dataset.t === t));
}

/* ─── MODAL ───────────────────────────────────────────── */
function openModal(opts) {
  const box = document.getElementById('modalBox');
  box.classList.toggle('wide', !!opts.wide);
  if (opts.html) {
    box.innerHTML = opts.html;
  } else {
    const { title, fields, confirmLabel = 'Guardar', danger = false, onConfirm } = opts;
    box.innerHTML = `
      <div class="modal-title">${esc(title)}</div>
      <div class="modal-body">
        ${fields.map(f => `
          <div class="field">
            <label>${esc(f.label)}</label>
            ${f.textarea
              ? `<textarea id="mf_${f.key}" rows="3">${esc(f.value || '')}</textarea>`
              : `<input id="mf_${f.key}" type="text" value="${escA(f.value || '')}"/>`}
          </div>`).join('')}
      </div>
      <div class="modal-foot">
        <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="mdOk">${esc(confirmLabel)}</button>
      </div>`;
    document.getElementById('mdOk').onclick = async () => {
      const v = {};
      for (const f of fields) {
        v[f.key] = document.getElementById(`mf_${f.key}`).value;
        if (f.required && !v[f.key].trim()) { document.getElementById(`mf_${f.key}`).focus(); return; }
      }
      await onConfirm(v);
    };
  }
  document.getElementById('modalOverlay').classList.add('open');
  const first = box.querySelector('input,textarea,select');
  if (first) setTimeout(() => { first.focus(); if(first.select) first.select(); }, 40);
}

function openConfirm({ title, msg, onConfirm }) {
  const box = document.getElementById('modalBox');
  box.innerHTML = `
    <div class="modal-title" style="color:var(--red)">${esc(title)}</div>
    <p style="font-size:13px;color:var(--tx2);line-height:1.6;margin-bottom:20px">${msg}</p>
    <div class="modal-foot">
      <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
      <button class="btn btn-danger" id="mdOk">Eliminar</button>
    </div>`;
  document.getElementById('modalOverlay').classList.add('open');
  document.getElementById('mdOk').onclick = () => { closeModal(); onConfirm(); };
}

function closeModal() { 
  document.getElementById('modalOverlay').classList.remove('open'); 
  document.getElementById('modalBox').classList.remove('wide');
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR: COURSE PICKER
═══════════════════════════════════════════════════════ */
function showCourseList() {
  // Switch sidebar back to picker
  S.activeCourse = null;
  S.activeClass = null;
  S.sections = [];
  renderSidebarPicker();
  renderContent('welcome');
  updateBreadcrumb();
}

function renderSidebarPicker() {
  document.getElementById('coursePicker').classList.remove('hidden');
  document.getElementById('navTree').classList.add('hidden');
  document.getElementById('phaseBar').classList.add('hidden');
  document.getElementById('sidebarHead').querySelector('.sidebar-title').textContent = 'Proyectos';

  const list = document.getElementById('pickerList');
  if (S.courses.length === 0) {
    list.innerHTML = `<div style="padding:24px 12px;text-align:center;color:var(--tx3);font-size:12px">Sin proyectos todavía.</div>`;
    return;
  }
  list.innerHTML = S.courses.map(c => `
    <div class="picker-item ${S.activeCourse?.id === c.id ? 'active' : ''}" onclick="openCourse(${c.id})">
      <span class="picker-icon">📚</span>
      <div class="picker-info">
        <div class="picker-name">${esc(c.title)}</div>
        <div class="picker-meta">${c.section_count} secc · ${c.class_count} clases</div>
      </div>
      <div class="picker-actions" onclick="event.stopPropagation()">
        <button class="ib" onclick="editCourse(${c.id})" title="Editar">${IC.edit}</button>
        <button class="ib danger" onclick="deleteCourse(${c.id})" title="Eliminar">${IC.trash}</button>
      </div>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR: TREE NAVIGATOR
═══════════════════════════════════════════════════════ */
async function openCourse(id) {
  const c = S.courses.find(x => x.id === id);
  if (!c) return;
  S.activeCourse = c;
  S.activeClass = null;
  S.activePhase = 'guion';
  try {
    S.sections = await api('GET', `/api/courses/${id}/sections`);
    // expand all by default
    S.sections.forEach(s => S.expandedSections.add(s.id));
    renderSidebarTree();
    renderContent('welcome');
    updateBreadcrumb();
    setStatus(c.title, '✓ Listo', 'sb-saved');
  } catch(e) { toast('Error al abrir el proyecto', false); }
}

function renderSidebarTree() {
  document.getElementById('coursePicker').classList.add('hidden');
  document.getElementById('navTree').classList.remove('hidden');
  document.getElementById('phaseBar').classList.add('hidden');

  const hdr = document.getElementById('treeCourseHdr');
  hdr.innerHTML = `
    <button class="tree-back-btn" onclick="showCourseList()" title="Volver a proyectos">← Proyectos</button>
    <span class="tree-course-name" title="${escA(S.activeCourse.title)}">${esc(S.activeCourse.title)}</span>
    <button class="ib" onclick="editCourse(${S.activeCourse.id})" title="Editar proyecto">${IC.edit}</button>`;

  renderTree();
}

function renderTree() {
  const body = document.getElementById('treeBody');
  if (!S.sections.length) {
    body.innerHTML = `<div style="padding:20px 12px;text-align:center;color:var(--tx3);font-size:12px">Sin secciones aún.</div>`;
    return;
  }
  body.innerHTML = S.sections.map(s => {
    const open = S.expandedSections.has(s.id);
    const classes = (s.classes || []);
    return `
      <div class="tree-section">
        <div class="tree-sec-hdr" onclick="toggleSection(${s.id})">
          <span class="tree-chevron ${open ? 'open' : ''}">${IC.chev}</span>
          <span class="tree-sec-name" title="${escA(s.title)}">${esc(s.title)}</span>
          <div class="tree-sec-actions" onclick="event.stopPropagation()">
            <button class="ib" onclick="createClass(${s.id})" title="Nueva clase">${IC.plus}</button>
            <button class="ib" onclick="editSection(${s.id},'${escA(s.title)}')" title="Renombrar">${IC.edit}</button>
            <button class="ib danger" onclick="deleteSection(${s.id})" title="Eliminar">${IC.trash}</button>
          </div>
        </div>
        <div class="tree-classes ${open ? '' : 'hidden'}" id="tc_${s.id}">
          ${classes.map(c => classTreeItem(c)).join('')}
          <button class="tree-add-class" onclick="createClass(${s.id})">${IC.plus} Agregar clase</button>
        </div>
      </div>`;
  }).join('');
}

function classTreeItem(c) {
  const active = S.activeClass?.id === c.id;
  const hasContent = (c.raw_narration || '').trim().length > 0;
  return `
    <div class="tree-class-item ${active ? 'active' : ''} ${hasContent ? 'has-content' : ''}"
         data-cid="${c.id}" onclick="selectClass(${c.id})">
      <span class="tree-class-dot"></span>
      <span class="tree-class-name" title="${escA(c.title)}">${esc(c.title)}</span>
      <div class="tree-class-actions" onclick="event.stopPropagation()">
        <button class="ib" onclick="renameClass(${c.id},'${escA(c.title)}')" title="Renombrar">${IC.edit}</button>
        <button class="ib danger" onclick="deleteClass(${c.id})" title="Eliminar">${IC.trash}</button>
      </div>
    </div>`;
}

function toggleSection(id) {
  const el = document.getElementById(`tc_${id}`);
  const hdr = document.querySelector(`.tree-sec-hdr[onclick="toggleSection(${id})"]`);
  if (!el) return;
  if (S.expandedSections.has(id)) {
    S.expandedSections.delete(id);
    el.classList.add('hidden');
    hdr?.querySelector('.tree-chevron')?.classList.remove('open');
  } else {
    S.expandedSections.add(id);
    el.classList.remove('hidden');
    hdr?.querySelector('.tree-chevron')?.classList.add('open');
  }
}

async function selectClass(id) {
  if (S.saveStatus === 'unsaved') await doSave(true);
  try {
    const cls = await api('GET', `/api/classes/${id}`);
    S.activeClass = cls;
    // Lock by default — requires explicit "Edit" click to modify
    S.guionLocked = (cls.raw_narration || '').trim().length > 0;
    // update active state in tree without full re-render
    document.querySelectorAll('.tree-class-item').forEach(el => {
      el.classList.toggle('active', +el.dataset.cid === id);
    });
    document.getElementById('phaseBar').classList.remove('hidden');
    renderPhase(S.activePhase);
    updateBreadcrumb();
    updateStatusBar();
  } catch(e) { toast('Error al cargar la clase', false); }
}

/* ─── BREADCRUMB ──────────────────────────────────────── */
function updateBreadcrumb() {
  const bc = document.getElementById('breadcrumb');
  const parts = [];
  if (S.activeCourse) parts.push(`<span class="bc-item">${esc(S.activeCourse.title)}</span>`);
  if (S.activeClass)  parts.push(`<span class="bc-sep">›</span><span class="bc-item active">${esc(S.activeClass.title)}</span>`);
  bc.innerHTML = parts.join('');
}

/* ─── STATUS BAR ──────────────────────────────────────── */
function updateStatusBar() {
  if (!S.activeClass) { setStatus('Video Creator', '✓ Listo', 'sb-saved'); return; }
  const w = (S.activeClass.raw_narration||'').trim().split(/\s+/).filter(Boolean).length;
  const c = (S.activeClass.raw_narration||'').length;
  setStatus(`${esc(S.activeClass.title)} · ${w} palabras · ${c} caracteres`, '✓ Guardado', 'sb-saved');
}

/* ═══════════════════════════════════════════════════════
   PHASE TABS
═══════════════════════════════════════════════════════ */
function switchPhase(phase) {
  if (S.saveStatus === 'unsaved') doSave(true);
  S.activePhase = phase;
  document.querySelectorAll('.phase-tab').forEach(t => t.classList.toggle('active', t.dataset.phase === phase));
  renderPhase(phase);
}

function renderPhase(phase) {
  _clearAudioPoll();
  _clearSpellPoll();
  _clearVisualPoll();
  _clearRenderPoll();
  const area = document.getElementById('contentArea');
  if (!S.activeClass) { renderContent('welcome'); return; }
  switch(phase) {
    case 'guion':    renderGuion(area);       break;
    case 'audio':    renderAudio(area);       break;
    case 'fonts':    renderFontsColors(area);  break;
    case 'viz':      renderViz(area);          break;
    case 'visuales': renderVisuales(area);     break;
    case 'video':    renderVideo(area);       break;
  }
}

function renderContent(type) {
  const area = document.getElementById('contentArea');
  
  // Update topbar button active state
  const gmBtn = document.getElementById('globalManagerBtn');
  if (gmBtn) gmBtn.classList.toggle('active', type === 'global_manager');

  if (type === 'welcome') {
    area.innerHTML = `
      <div class="welcome-screen">
        <div class="welcome-icon">🎥</div>
        <h2>Selecciona una clase para comenzar</h2>
        <p>Crea un nuevo proyecto o elige uno existente del panel lateral para gestionar su guion, audio y producción de video.</p>
      </div>`;
    document.getElementById('phaseBar').classList.add('hidden');
  } else if (type === 'global_manager') {
    document.getElementById('phaseBar').classList.add('hidden');
    S.activeClass = null;
    updateBreadcrumb();
    loadGmData().then(() => renderGlobalManager());
  }
}

/* ─── GUION PHASE ─────────────────────────────────────── */
function renderGuion(area) {
  const cls    = S.activeClass;
  const locked = S.guionLocked;
  const tab    = S.guionRightTab;
  if (!locked) S.saveStatus = 'saved';

  area.innerHTML = `
    <div class="guion-view">
      <div class="guion-main">

        <!-- Toolbar -->
        <div class="guion-toolbar">
          <div class="guion-toolbar-left">
            ${locked
              ? `<span class="guion-lock-badge">🔒 Guardado</span>`
              : `<span class="guion-toolbar-label">Locución / Guion</span>`}
            <span id="guionStats" class="guion-stats"></span>
          </div>
          <div class="guion-toolbar-actions">
            ${locked
              ? `<button class="btn btn-sm btn-ghost" onclick="unlockGuion()">✏️ Editar guion</button>`
              : `<button class="btn btn-sm btn-primary" onclick="doSave(false)">Guardar Guion</button>`}
          </div>
        </div>

        <!-- Edit banner (only in edit mode) -->
        ${!locked ? `
        <div class="guion-edit-banner">
          ✏️ Modo edición activo — si realizas cambios significativos, recuerda volver a
          <strong>Verificar con Tavily</strong> y <strong>Re-segmentar las pantallas</strong>.
        </div>` : ''}

        <!-- Editor -->
        <div class="guion-editor-wrap">
          <textarea id="guionTA" class="guion-ta ${locked ? 'guion-ta-locked' : ''}"
            placeholder="Pega aquí tu locución raw..."
            ${locked ? 'readonly' : `oninput="onGuionInput(this)"`}
          >${esc(cls.raw_narration || '')}</textarea>
        </div>
      </div>

      <!-- Right panel -->
      <div class="guion-research-panel" id="rightPanel">
        <div class="rp-tabs">
          <button class="rp-tab ${tab === 'research' ? 'active' : ''}" onclick="switchGuionTab('research')">
            🔍 Investigación${!locked ? '<span class="rp-tab-dot" title="Puede necesitar re-verificación"></span>' : ''}
          </button>
          <button class="rp-tab ${tab === 'screens' ? 'active' : ''}" onclick="switchGuionTab('screens')">
            🎬 Pantallas${!locked ? '<span class="rp-tab-dot" title="Puede necesitar re-segmentación"></span>' : ''}
          </button>
        </div>

        <div id="researchSection" class="${tab === 'research' ? '' : 'hidden'}">
          <div class="rp-tab-toolbar">
            <button class="btn btn-sm btn-ghost" style="width:100%" onclick="runResearch()">🔍 Verificar con Tavily</button>
          </div>
          <div class="rp-body" id="researchBody">
            <div class="rp-empty">Pulsa el botón para analizar el guion.</div>
          </div>
        </div>

        <div id="screensSection" class="${tab === 'screens' ? '' : 'hidden'}">
          <div class="rp-tab-toolbar">
            <button class="btn btn-sm btn-primary" style="width:100%" onclick="runSegmentation()">✦ Segmentar con IA</button>
          </div>
          <div class="rp-body" id="screensBody">
            <div class="rp-empty">Pulsa el botón para que la IA divida el guion en pantallas.</div>
          </div>
        </div>
      </div>
    </div>`;

  _updateGuionStats(cls.raw_narration || '');
  if (tab === 'research') renderResearchItems();
  else renderSegmentCards();
}

function unlockGuion() {
  S.guionLocked = false;
  S.saveStatus  = 'saved';
  renderGuion(document.getElementById('contentArea'));
  setTimeout(() => document.getElementById('guionTA')?.focus(), 50);
}

function switchGuionTab(tab) {
  S.guionRightTab = tab;
  document.querySelectorAll('.rp-tab').forEach(b => b.classList.toggle('active', b.textContent.includes(tab === 'research' ? 'Investigación' : 'Pantallas')));
  const rs = document.getElementById('researchSection');
  const ss = document.getElementById('screensSection');
  if (!rs || !ss) return;
  rs.classList.toggle('hidden', tab !== 'research');
  ss.classList.toggle('hidden', tab !== 'screens');
  if (tab === 'research') renderResearchItems();
  else renderSegmentCards();
}

async function runResearch() {
  const cls = S.activeClass;
  if (!cls.raw_narration && !document.getElementById('guionTA')?.value) {
    return toast('Pega un guion primero', false);
  }
  AIModal.show('🔍 Verificando con Tavily', 'Extrayendo afirmaciones y consultando fuentes académicas…');
  AIModal.update('Analizando el guion con GPT…');
  try {
    const results = await api('POST', `/api/classes/${cls.id}/research`);
    AIModal.done(`✅ ${results.length} afirmaciones procesadas`);
    renderResearchItems(results);
  } catch(e) {
    AIModal.error(e.message);
    renderResearchItems();
  }
}

async function renderResearchItems(providedItems = null) {
  const body = document.getElementById('researchBody');
  if (!body) return;
  
  let items = providedItems;
  if (!items) {
    const res = await api('GET', `/api/classes/${S.activeClass.id}/research`);
    items = res;
  }
  
  if (!items || items.length === 0) {
    body.innerHTML = '<div class="rp-empty">Sin hallazgos.</div>';
    return;
  }
  
  const reexaminable = s => s === 'disputed' || s === 'not_found' || s === 'error';

  body.innerHTML = items.map(i => `
    <div class="research-item status-${i.status}" id="ri_${i.id}">
      <div class="ri-head">
        <span class="ri-badge">${i.status.toUpperCase()}</span>
        ${i.confidence ? `<span class="ri-conf" title="Confianza: ${i.confidence}%">${i.confidence}%</span>` : ''}
        <div style="display:flex;gap:4px;margin-left:auto">
          ${reexaminable(i.status) ? `<button class="ri-reexamine" id="rex_${i.id}" onclick="reexamineItem(${i.id})">↻ Actualizar</button>` : ''}
          <button class="ri-del" onclick="deleteResearchItem(${i.id})">×</button>
        </div>
      </div>
      <div class="ri-claim">${esc(i.claim)}</div>
      ${i.source_url ? `
        <div class="ri-source">
          <a href="${i.source_url}" target="_blank" class="ri-link">${esc(i.source_title || 'Ver fuente')}</a>
          <div class="ri-snippet">${esc(i.source_snippet || '')}</div>
        </div>
      ` : (i.status === 'error' ? `<div class="ri-error">${esc(i.source_snippet)}</div>` : '')}
    </div>
  `).join('');
}

async function reexamineItem(id) {
  AIModal.show('↻ Re-examinando con Tavily', 'Buscando fuentes más actualizadas para este claim…');
  AIModal.update('Generando query alternativo con filtros de recencia 2023–2025…');
  try {
    const updated = await api('POST', `/api/research-items/${id}/reexamine`);
    const msg = updated.status === 'verified'
      ? '✅ Verificado con fuentes actualizadas'
      : `✅ Re-examinado — estado: ${updated.status}`;
    AIModal.done(msg);
    renderResearchItems();
  } catch(e) {
    AIModal.error(e.message);
  }
}

async function deleteResearchItem(id) {
  if (!confirm('¿Eliminar este hallazgo?')) return;
  await api('DELETE', `/api/research-items/${id}`);
  renderResearchItems();
}


/* ─── SCREEN SEGMENTATION ─────────────────────────────── */
async function runSegmentation() {
  const cls = S.activeClass;
  if (!(cls.raw_narration || '').trim() && !document.getElementById('guionTA')?.value.trim()) {
    return toast('Pega un guion primero', false);
  }
  AIModal.show('✦ Segmentando en Pantallas', 'La IA divide el guion y elige el tipo de pantalla más adecuado para cada fragmento…');
  AIModal.update('Enviando guion al modelo…');
  try {
    const segments = await api('POST', `/api/classes/${cls.id}/segment`);
    AIModal.done(`✅ ${segments.length} pantallas generadas`);
    renderSegmentCards(segments);
  } catch(e) {
    AIModal.error(e.message);
    renderSegmentCards();
  }
}

async function renderSegmentCards(providedSegs = null) {
  const body = document.getElementById('screensBody');
  if (!body) return;

  let segs = providedSegs;
  if (!segs) {
    try { segs = await api('GET', `/api/classes/${S.activeClass.id}/segments`); }
    catch(e) { segs = []; }
  }

  if (!segs || segs.length === 0) {
    body.innerHTML = '<div class="rp-empty">Sin pantallas todavía.<br>Pulsa "Segmentar con IA" para generar.</div>';
    return;
  }

  if (!GM.screenTypes.length) await loadGmData();
  const typeMap = {};
  GM.screenTypes.forEach(t => { typeMap[t.name] = t; });

  // Store for export functions
  window._currentSegs = segs;
  window._currentClassName = S.activeClass?.title || 'guion';

  const cards = segs.map(seg => {
    const st = typeMap[seg.screen_type] || {};
    const color = st.color || '#666';
    const icon  = st.icon  || '▪';
    const label = st.label || seg.screen_type;
    return `
      <div class="seg-card">
        <div class="seg-card-head">
          <span class="seg-order">${seg.order + 1}</span>
          <span class="seg-type-badge" style="background:${color}22;color:${color};border-color:${color}44">
            ${icon} ${esc(seg.screen_type)}
          </span>
          <span class="seg-type-label">${esc(label)}</span>
        </div>
        <div class="seg-narration">${esc(seg.narration)}</div>
        ${seg.params ? `<div class="seg-params"><span class="seg-params-label">params</span>${esc(seg.params)}</div>` : ''}
        ${seg.notes  ? `<div class="seg-notes">${esc(seg.notes)}</div>` : ''}
      </div>`;
  }).join('');

  body.innerHTML = `
    <div class="seg-actions-bar">
      <button class="seg-action-btn" onclick="showTaggedScript()">📄 Ver etiquetado</button>
      <button class="seg-action-btn" onclick="copyTaggedScript()">📋 Copiar</button>
      <button class="seg-action-btn" onclick="exportTaggedScript()">⬇ .txt</button>
    </div>
    ${cards}`;
}

function buildTaggedScript(segs) {
  return segs.map(seg => {
    const tag = seg.params
      ? `<!-- type:${seg.screen_type} // ${seg.params} -->`
      : `<!-- type:${seg.screen_type} -->`;
    return `${tag}\n${seg.narration}`;
  }).join('\n\n');
}

function showTaggedScript() {
  const script = buildTaggedScript(window._currentSegs || []);
  openModal({
    wide: true,
    html: `
      <div class="modal-title">Guion Etiquetado — ${esc(window._currentClassName || '')}</div>
      <div class="modal-body">
        <textarea class="tagged-script-ta" readonly>${esc(script)}</textarea>
      </div>
      <div class="modal-foot">
        <button class="btn btn-ghost" onclick="closeModal()">Cerrar</button>
        <button class="btn btn-ghost" onclick="copyTaggedScript()">📋 Copiar</button>
        <button class="btn btn-primary" onclick="exportTaggedScript()">⬇ Exportar .txt</button>
      </div>`
  });
}

async function copyTaggedScript() {
  const script = buildTaggedScript(window._currentSegs || []);
  try {
    await navigator.clipboard.writeText(script);
    toast('Copiado al portapapeles');
  } catch(e) {
    toast('Error al copiar', false);
  }
}

function exportTaggedScript() {
  const script = buildTaggedScript(window._currentSegs || []);
  const name   = (window._currentClassName || 'guion').replace(/[^a-z0-9_\-]/gi, '_');
  const blob   = new Blob([script], { type: 'text/plain;charset=utf-8' });
  const url    = URL.createObjectURL(blob);
  const a      = document.createElement('a');
  a.href = url; a.download = `${name}_etiquetado.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

function _updateGuionStats(text) {
  const w  = text.trim() ? text.trim().split(/\s+/).length : 0;
  const c  = text.length;
  const el = document.getElementById('guionStats');
  if (el) el.textContent = `${w} palabras · ${c} caracteres`;
}

function onGuionInput(el) {
  const text = el.value;
  _updateGuionStats(text);
  const w = text.trim() ? text.trim().split(/\s+/).length : 0;
  const c = text.length;
  setStatus(`${esc(S.activeClass.title)} · ${w} palabras · ${c} chars`, '● Sin guardar', 'sb-unsaved');
  S.saveStatus = 'unsaved';
  if (S.saveTimer) clearTimeout(S.saveTimer);
  S.saveTimer = setTimeout(() => doSave(true), 2000);
}

async function doSave(silent = false) {
  if (!S.activeClass) return;
  const ta = document.getElementById('guionTA');
  if (!ta) { S.saveStatus = 'saved'; return; }
  S.saveStatus = 'saving';
  setStatus(undefined, '↻ Guardando…', 'sb-saving');
  try {
    const updated = await api('PUT', `/api/classes/${S.activeClass.id}`, {
      title: S.activeClass.title,
      raw_narration: ta.value,
    });
    S.activeClass  = updated;
    S.saveStatus   = 'saved';
    S.guionLocked  = true;   // lock after every save
    const w = (updated.raw_narration||'').trim().split(/\s+/).filter(Boolean).length;
    setStatus(`${esc(updated.title)} · ${w} palabras`, '✓ Guardado', 'sb-saved');
    const item = document.querySelector(`.tree-class-item[data-cid="${updated.id}"]`);
    if (item) item.classList.toggle('has-content', (updated.raw_narration||'').trim().length > 0);
    // Re-render guion to show locked state
    if (S.activePhase === 'guion') renderGuion(document.getElementById('contentArea'));
    if (!silent) toast('Guardado');
  } catch(e) {
    S.saveStatus = 'unsaved';
    setStatus(undefined, '⚠ Error al guardar', 'sb-unsaved');
    if (!silent) toast('Error al guardar', false);
  }
}

/* ═══════════════════════════════════════════════════════
   AUDIO PHASE
═══════════════════════════════════════════════════════ */
let _audioPollTimer = null;
const RUNNING_STATUSES = new Set(['loading_model', 'transcribing', 'aligning', 'saving']);

function _clearAudioPoll() {
  if (_audioPollTimer) { clearInterval(_audioPollTimer); _audioPollTimer = null; }
}

async function renderAudio(area) {
  area.innerHTML = `<div class="audio-phase"><div class="rp-loading" style="padding:60px">Cargando estado del audio…</div></div>`;
  let state = null, spell = null, guion = null;
  try { state = await api('GET', `/api/classes/${S.activeClass.id}/audio`); } catch(e) {}
  if (state?.tx_status === 'done') {
    try { spell = await api('GET', `/api/classes/${S.activeClass.id}/spell-correction`); } catch(e) {}
  }
  if (spell?.status === 'done') {
    try { guion = await api('GET', `/api/classes/${S.activeClass.id}/guion-base`); } catch(e) {}
  }
  _buildAudioUI(area, state, spell, guion);
  if (state && RUNNING_STATUSES.has(state.tx_status)) _startAudioPoll();
  if (spell?.status === 'running') _startSpellPoll();
}

function _buildAudioUI(area, state, spell = null, guion = null) {
  const running = state && RUNNING_STATUSES.has(state.tx_status);
  const txDone  = state?.tx_status === 'done';
  const hasErr  = state?.tx_error;
  const spellRunning = spell?.status === 'running';
  const spellDone    = spell?.status === 'done';
  const guionDone    = guion?.status === 'done';

  const modelOptions = ['tiny','base','small','medium','large-v3'].map(m =>
    `<option value="${m}" ${(state?.whisper_model || 'large-v3') === m ? 'selected' : ''}>${m}</option>`
  ).join('');

  area.innerHTML = `<div class="audio-phase">

    <!-- ① Audio Source Card -->
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">🎵 Archivo de Audio</span>
        ${state ? `<button class="audio-ghost-btn" onclick="deleteAudio()" ${running ? 'disabled' : ''}>✕ Quitar</button>` : ''}
      </div>

      <div class="audio-card-body">
        ${state ? `
          <div class="audio-file-info">
            <div class="audio-filename">${esc(state.filename)}</div>
            <div class="audio-meta">
              <span>⏱ ${_fmtDuration(state.duration)}</span>
              <span>·</span>
              <span>📦 ${_fmtSize(state.size_bytes)}</span>
            </div>
          </div>
          <audio controls src="${esc(state.file_url)}" class="audio-player" preload="metadata"></audio>
        ` : `
          <label class="audio-upload-zone" for="audioFileInput">
            <div class="audio-upload-icon">🎵</div>
            <div class="audio-upload-label">Seleccionar archivo de audio</div>
            <div class="audio-upload-sub">MP3, WAV, M4A, AAC, FLAC, OGG</div>
            <input type="file" id="audioFileInput" accept=".mp3,.wav,.m4a,.mp4,.aac,.ogg,.flac" style="display:none"/>
          </label>
        `}
      </div>
    </div>

    <!-- ② Transcripción Card -->
    ${state ? `
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">🎙️ Transcripción con Whisper</span>
      </div>
      <div class="audio-card-body">
        <div class="audio-tx-controls">
          <div class="audio-model-row">
            <label class="audio-model-label">Modelo</label>
            <select id="whisperModel" class="audio-model-select" ${running ? 'disabled' : ''}>
              ${modelOptions}
            </select>
            <span class="audio-device-badge" id="deviceBadge">CPU</span>
          </div>
          <button class="btn btn-primary audio-att-btn" onclick="startWhisperATT()" ${running || !state ? 'disabled' : ''}>
            ${running ? '⏳ Transcribiendo…' : '🎙️ ATT con Whisper'}
          </button>
        </div>

        <!-- Progress -->
        <div class="audio-progress-wrap" id="audioProgressWrap" style="${running || txDone ? '' : 'display:none'}">
          <div class="audio-progress-bar">
            <div class="audio-progress-fill ${running ? 'running' : ''}"
                 id="audioProgressFill"
                 style="width:${state.tx_progress || 0}%"></div>
          </div>
          <div class="audio-progress-foot">
            <span id="audioPhaseLabel" class="audio-phase-label">${esc(state.tx_phase || '')}</span>
            <span id="audioProgressPct" class="audio-progress-pct">${state.tx_progress || 0}%</span>
          </div>
        </div>

        <!-- Error box -->
        ${hasErr ? `
        <div class="audio-error-box" id="audioErrorBox">
          <div class="audio-error-title">⚠️ Error de transcripción</div>
          <pre class="audio-error-pre">${esc(state.tx_error)}</pre>
        </div>` : '<div id="audioErrorBox" style="display:none"></div>'}
      </div>
    </div>
    ` : ''}

    <!-- ③ Transcription summary -->
    ${txDone ? `
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">📄 Transcripción</span>
        <div class="audio-card-head-right">
          <button class="seg-action-btn" onclick="viewTranscription()">👁 Ver</button>
          <button class="seg-action-btn" onclick="copyTranscription()">📋 Copiar</button>
          <button class="seg-action-btn" onclick="exportTranscription()">⬇ .txt</button>
          <button class="seg-action-btn" onclick="exportSRT()">⬇ .srt</button>
        </div>
      </div>
      <div class="audio-card-body">
        <div class="tx-summary-row">
          <div class="tx-summary-stat">
            <span class="tx-stat-val">${state.tx_segments?.length || 0}</span>
            <span class="tx-stat-lbl">bloques</span>
          </div>
          <div class="tx-summary-stat">
            <span class="tx-stat-val">${_countWords(state.tx_raw_text)}</span>
            <span class="tx-stat-lbl">palabras</span>
          </div>
          <div class="tx-summary-stat">
            <span class="tx-stat-val">${_fmtDuration(state.duration)}</span>
            <span class="tx-stat-lbl">duración</span>
          </div>
        </div>
        <details class="tx-preview-details">
          <summary>Ver muestra</summary>
          <pre class="tx-preview-pre">${esc((state.tx_raw_text||'').split('\n').slice(0,6).join('\n'))}</pre>
        </details>
      </div>
    </div>

    <!-- ④ Spell correction -->
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">✏️ Corrección Ortográfica</span>
        ${spellDone ? `<span class="audio-done-badge">✓ Completado</span>` : ''}
      </div>
      <div class="audio-card-body">
        ${spellDone ? `
          <div class="tx-summary-row">
            <div class="tx-summary-stat">
              <span class="tx-stat-val">${spell.segments?.length || 0}</span>
              <span class="tx-stat-lbl">bloques corregidos</span>
            </div>
          </div>
          <div class="audio-exports">
            <button class="seg-action-btn" onclick="exportSpellCorrection()">⬇ .txt corregido</button>
            <button class="seg-action-btn" style="color:var(--tx3)" onclick="startSpellCorrection()">↻ Re-corregir</button>
          </div>
        ` : `
          <p class="audio-card-desc">Corrige errores ortográficos del audio usando el guion original como referencia.<br>
          Modelo: <strong>gpt-5.4-nano-2025-04-14</strong> · batches de 50 bloques.</p>
          <div>
            <button class="btn btn-primary audio-att-btn" onclick="startSpellCorrection()" ${spellRunning ? 'disabled' : ''}>
              ${spellRunning ? '⏳ Corrigiendo…' : '✏️ Corregir con GPT'}
            </button>
          </div>
          ${spellRunning ? `
          <div class="audio-progress-wrap">
            <div class="audio-progress-bar">
              <div class="audio-progress-fill running" id="spellProgressFill" style="width:${spell?.progress||0}%"></div>
            </div>
            <div class="audio-progress-foot">
              <span id="spellPhaseLabel" class="audio-phase-label">${esc(spell?.phase||'')}</span>
              <span id="spellProgressPct" class="audio-progress-pct">${spell?.progress||0}%</span>
            </div>
          </div>` : ''}
          ${spell?.error ? `<div class="audio-error-box"><div class="audio-error-title">⚠️ Error</div><pre class="audio-error-pre">${esc(spell.error)}</pre></div>` : ''}
        `}
      </div>
    </div>

    <!-- ⑤ Alignment -->
    ${spellDone ? `
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">🔗 Alineación y Guion Base</span>
        ${guionDone ? `<span class="audio-done-badge">✓ Completado</span>` : ''}
      </div>
      <div class="audio-card-body">
        ${guionDone ? `
          <div class="tx-summary-row">
            <div class="tx-summary-stat">
              <span class="tx-stat-val">${guion.segments?.length || 0}</span>
              <span class="tx-stat-lbl">segmentos alineados</span>
            </div>
          </div>
          <div class="audio-exports">
            <button class="seg-action-btn" onclick="exportGuionBase()">⬇ guion_base.txt</button>
            <button class="seg-action-btn" style="color:var(--tx3)" onclick="runAlignment()">↻ Re-alinear</button>
          </div>
        ` : `
          <p class="audio-card-desc">Mapea los timestamps de Whisper a cada pantalla del guion etiquetado usando difflib — mismo algoritmo de <code>0_referencia</code>.</p>
          <div>
            <button class="btn btn-primary audio-att-btn" onclick="runAlignment()">🔗 Alinear y generar Guion Base</button>
          </div>
        `}
        ${guion?.error ? `<div class="audio-error-box"><div class="audio-error-title">⚠️ Error</div><pre class="audio-error-pre">${esc(guion.error)}</pre></div>` : ''}
      </div>
    </div>
    ` : ''}
    ` : ''}

  </div>`;

  // Wire up file input
  const fi = document.getElementById('audioFileInput');
  if (fi) fi.addEventListener('change', e => { if (e.target.files[0]) uploadAudio(e.target.files[0]); });
}

function _countWords(rawText) {
  if (!rawText) return 0;
  return rawText.split('\n').filter(Boolean).reduce((acc, line) => {
    const part = line.split(']: ')[1];
    return acc + (part ? part.trim().split(/\s+/).length : 0);
  }, 0);
}

function _fmtDuration(secs) {
  if (!secs) return '—';
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  if (h > 0) return `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  return `${m}:${String(s).padStart(2,'0')}`;
}

function _fmtSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024 * 1024) return `${(bytes/1024).toFixed(1)} KB`;
  return `${(bytes/1024/1024).toFixed(1)} MB`;
}

async function uploadAudio(file) {
  setStatus(undefined, '⬆ Subiendo audio…', 'sb-saving');
  const area = document.getElementById('contentArea');
  area.innerHTML = `<div class="audio-phase"><div class="rp-loading" style="padding:60px">⬆ Subiendo ${esc(file.name)}…</div></div>`;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`/api/classes/${S.activeClass.id}/audio`, { method: 'POST', body: fd });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Error al subir'); }
    const state = await res.json();
    toast('Audio cargado');
    _buildAudioUI(area, state);
  } catch(e) {
    toast(e.message, false);
    _buildAudioUI(area, null);
  }
  setStatus(undefined, '✓ Listo', 'sb-saved');
}

async function deleteAudio() {
  if (!confirm('¿Eliminar el audio y la transcripción?')) return;
  try {
    await api('DELETE', `/api/classes/${S.activeClass.id}/audio`);
    toast('Audio eliminado');
    _clearAudioPoll();
    _buildAudioUI(document.getElementById('contentArea'), null);
  } catch(e) { toast(e.message, false); }
}

async function startWhisperATT() {
  const model = document.getElementById('whisperModel')?.value || 'large-v3';
  try {
    const fd = new FormData();
    fd.append('model', model);
    const res = await fetch(`/api/classes/${S.activeClass.id}/transcription`, { method: 'POST', body: fd });
    if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
    AIModal.show(`🎙️ Transcripción con Whisper (${model})`, 'Procesando audio… esto puede tardar varios minutos según el modelo y la duración.');
    AIModal.update(`Cargando modelo ${model}…`);
    const state = await api('GET', `/api/classes/${S.activeClass.id}/audio`);
    _buildAudioUI(document.getElementById('contentArea'), state);
    _startAudioPoll();
  } catch(e) { AIModal.error(e.message); }
}

function _startAudioPoll() {
  _clearAudioPoll();
  const classId = S.activeClass?.id;
  _audioPollTimer = setInterval(async () => {
    if (S.activeClass?.id !== classId || S.activePhase !== 'audio') { _clearAudioPoll(); return; }
    try {
      const s = await api('GET', `/api/classes/${classId}/audio/status`);

      // Update progress bar and labels without full re-render
      const fill  = document.getElementById('audioProgressFill');
      const phase = document.getElementById('audioPhaseLabel');
      const pct   = document.getElementById('audioProgressPct');
      const wrap  = document.getElementById('audioProgressWrap');
      const errBox= document.getElementById('audioErrorBox');
      const attBtn= document.querySelector('.audio-att-btn');

      if (wrap)  wrap.style.display = '';
      if (fill)  { fill.style.width = `${s.tx_progress}%`; }
      if (phase) phase.textContent = s.tx_phase || '';
      if (pct)   pct.textContent   = `${s.tx_progress}%`;

      if (s.tx_error && errBox) {
        errBox.style.display = '';
        errBox.innerHTML = `<div class="audio-error-title">⚠️ Error de transcripción</div><pre class="audio-error-pre">${esc(s.tx_error)}</pre>`;
      }

      // Mirror progress into AIModal
      AIModal.update(s.tx_phase, s.tx_progress);

      if (!RUNNING_STATUSES.has(s.tx_status)) {
        _clearAudioPoll();
        if (fill) fill.classList.remove('running');
        if (attBtn) { attBtn.disabled = false; attBtn.textContent = '🎙️ ATT con Whisper'; }
        if (s.tx_status === 'done') {
          const full = await api('GET', `/api/classes/${classId}/audio`);
          _buildAudioUI(document.getElementById('contentArea'), full);
          AIModal.done('✅ Transcripción completada');
        } else if (s.tx_status === 'error') {
          AIModal.error(s.tx_error || 'Error desconocido en la transcripción');
          const full = await api('GET', `/api/classes/${classId}/audio`);
          _buildAudioUI(document.getElementById('contentArea'), full);
        }
      }
    } catch(e) { /* network blip — keep polling */ }
  }, 2000);
}

// ── Transcription exports ─────────────────────────────────
let _lastAudioState = null;  // cache for export functions

async function _getAudioState() {
  if (_lastAudioState?.tx_status === 'done') return _lastAudioState;
  try { _lastAudioState = await api('GET', `/api/classes/${S.activeClass.id}/audio`); } catch(e) {}
  return _lastAudioState;
}

async function viewTranscription() {
  const s = await _getAudioState();
  if (!s?.tx_raw_text) return toast('Sin transcripción', false);
  openModal({
    wide: true,
    html: `
      <div class="modal-title">📄 Transcripción — ${esc(S.activeClass?.title || '')}</div>
      <div class="modal-body">
        <pre class="tagged-script-ta" style="height:480px;overflow-y:auto">${esc(s.tx_raw_text)}</pre>
      </div>
      <div class="modal-foot">
        <button class="btn btn-ghost" onclick="closeModal()">Cerrar</button>
        <button class="btn btn-ghost" onclick="copyTranscription()">📋 Copiar</button>
        <button class="btn btn-primary" onclick="exportTranscription()">⬇ Exportar .txt</button>
      </div>`
  });
}

async function copyTranscription() {
  const s = await _getAudioState();
  if (!s?.tx_raw_text) return toast('Sin transcripción', false);
  navigator.clipboard.writeText(s.tx_raw_text).then(() => toast('Copiado'));
}

async function exportTranscription() {
  const s = await _getAudioState();
  if (!s?.tx_raw_text) return toast('Sin transcripción', false);
  const name = (S.activeClass?.title || 'transcripcion').replace(/[^a-z0-9_\-]/gi, '_');
  _download(`${name}_whisper.txt`, s.tx_raw_text);
}

async function exportSRT() {
  const s = await _getAudioState();
  if (!s?.tx_srt) return toast('Sin SRT', false);
  const name = (S.activeClass?.title || 'transcripcion').replace(/[^a-z0-9_\-]/gi, '_');
  _download(`${name}.srt`, s.tx_srt);
}

// ── Spell correction ──────────────────────────────────────
let _spellPollTimer = null;

function _clearSpellPoll() {
  if (_spellPollTimer) { clearInterval(_spellPollTimer); _spellPollTimer = null; }
}

async function startSpellCorrection() {
  try {
    await api('POST', `/api/classes/${S.activeClass.id}/spell-correction`);
    AIModal.show('✏️ Corrección Ortográfica', 'Corrigiendo con gpt-5.4-nano-2025-04-14 en batches de 50 bloques…');
    AIModal.update('Iniciando…');
    const area = document.getElementById('contentArea');
    const state = await api('GET', `/api/classes/${S.activeClass.id}/audio`);
    const spell = { status: 'running', progress: 0, phase: 'Iniciando…' };
    _buildAudioUI(area, state, spell);
    _startSpellPoll();
  } catch(e) { AIModal.error(e.message); }
}

function _startSpellPoll() {
  _clearSpellPoll();
  const classId = S.activeClass?.id;
  _spellPollTimer = setInterval(async () => {
    if (S.activeClass?.id !== classId || S.activePhase !== 'audio') { _clearSpellPoll(); return; }
    try {
      const s = await api('GET', `/api/classes/${classId}/spell-correction/status`);
      AIModal.update(s.phase, s.progress);
      const fill  = document.getElementById('spellProgressFill');
      const phase = document.getElementById('spellPhaseLabel');
      const pct   = document.getElementById('spellProgressPct');
      if (fill)  fill.style.width  = `${s.progress}%`;
      if (phase) phase.textContent = s.phase || '';
      if (pct)   pct.textContent   = `${s.progress}%`;
      if (s.status !== 'running') {
        _clearSpellPoll();
        const state = await api('GET', `/api/classes/${classId}/audio`);
        let spell = null, guion = null;
        try { spell = await api('GET', `/api/classes/${classId}/spell-correction`); } catch(e) {}
        _buildAudioUI(document.getElementById('contentArea'), state, spell, guion);
        if (s.status === 'done') AIModal.done('✅ Corrección ortográfica completada');
        else AIModal.error(s.error || 'Error en corrección ortográfica');
      }
    } catch(e) {}
  }, 2000);
}

async function exportSpellCorrection() {
  try {
    const spell = await api('GET', `/api/classes/${S.activeClass.id}/spell-correction`);
    if (!spell?.raw_text) return toast('Sin corrección disponible', false);
    const name = (S.activeClass?.title || 'clase').replace(/[^a-z0-9_\-]/gi, '_');
    _download(`${name}_corregido.txt`, spell.raw_text);
  } catch(e) { toast(e.message, false); }
}

// ── Alignment ─────────────────────────────────────────────
async function runAlignment() {
  AIModal.show('🔗 Alineación con difflib', 'Mapeando timestamps de Whisper a cada pantalla del guion etiquetado…');
  AIModal.update('Procesando segmentos…');
  try {
    const result = await api('POST', `/api/classes/${S.activeClass.id}/alignment`);
    const state  = await api('GET', `/api/classes/${S.activeClass.id}/audio`);
    const spell  = await api('GET', `/api/classes/${S.activeClass.id}/spell-correction`);
    _buildAudioUI(document.getElementById('contentArea'), state, spell, result);
    AIModal.done(`✅ ${result.segments?.length || 0} segmentos alineados`);
  } catch(e) { AIModal.error(e.message); }
}

async function exportGuionBase() {
  try {
    const guion = await api('GET', `/api/classes/${S.activeClass.id}/guion-base`);
    if (!guion?.content) return toast('Sin guion base disponible', false);
    const name = (S.activeClass?.title || 'clase').replace(/[^a-z0-9_\-]/gi, '_');
    _download(`${name}_guion_base.txt`, guion.content);
  } catch(e) { toast(e.message, false); }
}

// ── Download helper ───────────────────────────────────────
function _download(filename, text) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = filename;
  a.click(); URL.revokeObjectURL(url);
}

/* ═══════════════════════════════════════════════════════
   VISUALES PHASE — FASE 3b (VisualOrchestrator)
═══════════════════════════════════════════════════════ */
let _visualPollTimer = null;

function _clearVisualPoll() {
  if (_visualPollTimer) { clearInterval(_visualPollTimer); _visualPollTimer = null; }
}

async function renderVisuales(area) {
  area.innerHTML = `<div class="audio-phase"><div class="rp-loading" style="padding:60px">Cargando estado visual…</div></div>`;

  let guion = null, visual = null;
  try { guion  = await api('GET', `/api/classes/${S.activeClass.id}/guion-base`);  } catch(e) {}
  if (guion?.status === 'done') {
    try { visual = await api('GET', `/api/classes/${S.activeClass.id}/visual`); } catch(e) {}
  }
  _buildVisualesUI(area, guion, visual);
  if (visual?.status === 'running') _startVisualPoll();
}

function _buildVisualesUI(area, guion, visual) {
  const guionOk      = guion?.status === 'done';
  const visualRunning = visual?.status === 'running';
  const visualDone    = visual?.status === 'done';
  const recursos      = visual?.recursos_json ? JSON.parse(visual.recursos_json) : null;

  const _cnt = (tipo) => recursos?.recursos?.filter(r => r.tipo === tipo).length || 0;
  const splits = recursos?.recursos?.filter(r => r.tipo === 'imagen_split').length   || 0;
  const fulls  = recursos?.recursos?.filter(r => r.tipo === 'imagen_completa').length|| 0;
  const videos = recursos?.recursos?.filter(r => r.tipo === 'video' && r.tipo_contenido !== 'remotion').length || 0;
  const remotion = recursos?.recursos?.filter(r => r.tipo_contenido === 'remotion').length || 0;

  area.innerHTML = `<div class="audio-phase">

    <!-- Prerequisite card -->
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">🧠 Arquitectura Visual</span>
        ${visualDone ? `<span class="audio-done-badge">✓ Completado</span>` : ''}
      </div>
      <div class="audio-card-body">
        ${!guionOk ? `
          <div class="vis-prereq">
            <span class="vis-prereq-icon">${guion?.status === 'stale' ? '⚠️' : '🔒'}</span>
            <div>
              <div style="font-size:13px;font-weight:700;color:var(--tx1);margin-bottom:4px">${guion?.status === 'stale' ? 'Pantallas regeneradas — re-ejecuta la Alineación' : 'Requiere Alineación completada'}</div>
              <div style="font-size:12px;color:var(--tx3)">${guion?.status === 'stale' ? 'Las pantallas cambiaron desde la última alineación. Ve a la fase Audio → Alineación y vuelve a ejecutarla.' : 'Completa Whisper → Corrección → Alineación en la fase Audio.'}</div>
            </div>
          </div>
        ` : visualDone ? `
          <div class="tx-summary-row">
            <div class="tx-summary-stat"><span class="tx-stat-val">${recursos?.total_recursos || 0}</span><span class="tx-stat-lbl">assets total</span></div>
            <div class="tx-summary-stat"><span class="tx-stat-val">${splits}</span><span class="tx-stat-lbl">split imgs</span></div>
            <div class="tx-summary-stat"><span class="tx-stat-val">${fulls}</span><span class="tx-stat-lbl">full imgs</span></div>
            <div class="tx-summary-stat"><span class="tx-stat-val">${videos}</span><span class="tx-stat-lbl">videos</span></div>
            <div class="tx-summary-stat"><span class="tx-stat-val">${remotion}</span><span class="tx-stat-lbl">remotion</span></div>
          </div>
          <div class="audio-exports">
            <button class="seg-action-btn" onclick="exportGuionConsolidado()">⬇ guion_consolidado.txt</button>
            <button class="seg-action-btn" onclick="exportRecursos()">⬇ recursos_visuales.json</button>
            <button class="seg-action-btn" onclick="viewGuionConsolidado()">👁 Ver guion</button>
          </div>
          <div style="margin-top:10px">
            <button class="btn btn-ghost audio-att-btn" onclick="startVisualOrchestration()">↻ Re-generar Arquitectura Visual</button>
          </div>
        ` : `
          <p class="audio-card-desc">
            Diseña la arquitectura visual completa:<br>
            <strong>TEXT=</strong> (texto en pantalla) · <strong>ASSET=</strong> (imagen/video asignado) ·
            <strong>ASSET_DESCRIPCION=</strong> (prompt "Scientific American" para generación) ·
            Remotion data por template.<br>
            Modelo: <strong>gpt-5.4-mini</strong> — misma lógica que <code>0_referencia</code>.
          </p>
          <div>
            <button class="btn btn-primary audio-att-btn" onclick="startVisualOrchestration()" ${visualRunning ? 'disabled' : ''}>
              ${visualRunning ? '⏳ Procesando…' : visual?.error ? '↻ Re-generar Arquitectura Visual' : '✨ Generar Arquitectura Visual'}
            </button>
          </div>
          ${visualRunning ? `
          <div class="audio-progress-wrap">
            <div class="audio-progress-bar">
              <div class="audio-progress-fill running" id="visualProgressFill" style="width:${visual?.progress||0}%"></div>
            </div>
            <div class="audio-progress-foot">
              <span id="visualPhaseLabel" class="audio-phase-label">${esc(visual?.phase||'')}</span>
              <span id="visualProgressPct" class="audio-progress-pct">${visual?.progress||0}%</span>
            </div>
          </div>` : ''}
          ${visual?.error ? `<div class="audio-error-box"><div class="audio-error-title">⚠️ Error</div><pre class="audio-error-pre">${esc(visual.error)}</pre></div>` : ''}
        `}
      </div>
    </div>

    <!-- Asset breakdown (when done) -->
    ${visualDone && recursos?.recursos?.length ? `
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">📦 Assets Identificados</span>
      </div>
      <div class="audio-card-body" style="padding:0">
        <table class="stat-cls-table">
          <thead><tr>
            <th>Archivo</th><th>Tipo</th><th>Segmento</th><th>Duración</th>
          </tr></thead>
          <tbody>
            ${recursos.recursos.map(r => `
              <tr>
                <td class="stat-cls-name" style="font-family:monospace;font-size:11px">${esc(r.nombre)}</td>
                <td><span class="seg-type-badge" style="background:var(--bg3);color:var(--tx2);border-color:var(--border2)">${esc(r.tipo_contenido || r.tipo)}</span></td>
                <td class="stat-cls-num">[${esc(r.segmento)}]</td>
                <td class="stat-cls-num">${parseFloat(r.duracion||0).toFixed(1)}s</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>
    ` : ''}

  </div>`;
}

async function startVisualOrchestration() {
  try {
    await api('POST', `/api/classes/${S.activeClass.id}/visual`);
    AIModal.show('✨ Arquitectura Visual', 'Diseñando TEXT=, ASSET= y prompts de generación para cada pantalla…');
    AIModal.update('Iniciando VisualAssistant…');
    const guion  = await api('GET', `/api/classes/${S.activeClass.id}/guion-base`);
    const visual = { status: 'running', progress: 0, phase: 'Iniciando…' };
    _buildVisualesUI(document.getElementById('contentArea'), guion, visual);
    _startVisualPoll();
  } catch(e) { AIModal.error(e.message); }
}

function _startVisualPoll() {
  _clearVisualPoll();
  const classId = S.activeClass?.id;
  _visualPollTimer = setInterval(async () => {
    if (S.activeClass?.id !== classId || S.activePhase !== 'visuales') { _clearVisualPoll(); return; }
    try {
      const s = await api('GET', `/api/classes/${classId}/visual/status`);
      AIModal.update(s.phase, s.progress);
      const fill  = document.getElementById('visualProgressFill');
      const lbl   = document.getElementById('visualPhaseLabel');
      const pct   = document.getElementById('visualProgressPct');
      if (fill) fill.style.width  = `${s.progress}%`;
      if (lbl)  lbl.textContent   = s.phase || '';
      if (pct)  pct.textContent   = `${s.progress}%`;
      if (s.status !== 'running') {
        _clearVisualPoll();
        const guion  = await api('GET', `/api/classes/${classId}/guion-base`);
        let visual = null;
        try { visual = await api('GET', `/api/classes/${classId}/visual`); } catch(e) {}
        _buildVisualesUI(document.getElementById('contentArea'), guion, visual);
        if (s.status === 'done')  AIModal.done('✅ Arquitectura visual completada');
        else                      AIModal.error(s.error || 'Error en orquestación visual');
      }
    } catch(e) {}
  }, 2000);
}

async function exportGuionConsolidado() {
  try {
    const v = await api('GET', `/api/classes/${S.activeClass.id}/visual`);
    if (!v?.content) return toast('Sin contenido', false);
    _download(`${(S.activeClass?.title||'clase').replace(/[^a-z0-9_\-]/gi,'_')}_guion_consolidado.txt`, v.content);
  } catch(e) { toast(e.message, false); }
}

async function exportRecursos() {
  try {
    const v = await api('GET', `/api/classes/${S.activeClass.id}/visual`);
    if (!v?.recursos_json) return toast('Sin recursos', false);
    _download(`${(S.activeClass?.title||'clase').replace(/[^a-z0-9_\-]/gi,'_')}_recursos_visuales.json`, v.recursos_json);
  } catch(e) { toast(e.message, false); }
}

async function viewGuionConsolidado() {
  try {
    const v = await api('GET', `/api/classes/${S.activeClass.id}/visual`);
    if (!v?.content) return toast('Sin contenido', false);
    openModal({ wide: true, html: `
      <div class="modal-title">📋 Guion Consolidado — ${esc(S.activeClass?.title||'')}</div>
      <div class="modal-body">
        <pre class="tagged-script-ta" style="height:500px;overflow-y:auto;font-size:11px">${esc(v.content)}</pre>
      </div>
      <div class="modal-foot">
        <button class="btn btn-ghost" onclick="closeModal()">Cerrar</button>
        <button class="btn btn-primary" onclick="exportGuionConsolidado()">⬇ Exportar</button>
      </div>`
    });
  } catch(e) { toast(e.message, false); }
}

/* ═══════════════════════════════════════════════════════
   VISUALIZADOR DE PANTALLAS
═══════════════════════════════════════════════════════ */

let _vizData = null;   // { segments, has_guion, course }

async function renderViz(area) {
  area.innerHTML = `<div class="audio-phase"><div class="rp-loading" style="padding:60px">Cargando pantallas…</div></div>`;
  try {
    _vizData = await api('GET', `/api/classes/${S.activeClass.id}/visualizador`);
  } catch(e) {
    area.innerHTML = `<div class="audio-phase"><div class="rp-loading">Error: ${esc(e.message)}</div></div>`;
    return;
  }
  _buildVizUI(area);
}

function _buildVizUI(area) {
  const { segments, has_guion, course } = _vizData;
  const [pW, pH] = (course.resolution || '1920x1080').split('x').map(Number);
  const ratio = pW / pH;
  const TYPES = ["TEXT","SPLIT_LEFT","SPLIT_RIGHT","FULL_IMAGE","VIDEO","LIST","CONCEPT","REMOTION"];

  if (!segments.length) {
    area.innerHTML = `<div class="audio-phase"><div class="audio-card"><div class="audio-card-body">
      <div class="vis-prereq"><span class="vis-prereq-icon">🔒</span>
      <div><div style="font-size:13px;font-weight:700;color:var(--tx1)">Sin pantallas segmentadas</div>
      <div style="font-size:12px;color:var(--tx3)">Genera la segmentación en Guion → Pantallas primero.</div></div></div>
    </div></div></div>`;
    return;
  }

  const cardsHtml = segments.map((seg, i) => {
    const typeOpts = TYPES.map(t =>
      `<option value="${t}" ${t === seg.screen_type ? 'selected' : ''}>${t}</option>`
    ).join('');

    const hasAsset = !!seg.asset;
    const assetUrl = hasAsset ? `/assets/${seg.asset}` : '';
    const isVideo  = assetUrl.endsWith('.mp4');

    return `
    <div class="viz-card" id="viz-card-${i}" data-seg-id="${seg.id}">

      <!-- LEFT: controls -->
      <div class="viz-col-ctrl">
        <div class="viz-screen-num">${i + 1}</div>
        ${seg.timestamp ? `
          <div class="viz-timing">
            <span class="viz-ts">${esc(seg.timestamp)}</span>
            <span class="viz-dur">${parseFloat(seg.duration||0).toFixed(1)}s</span>
          </div>` : `<div class="viz-timing"><span class="viz-ts" style="color:var(--tx3)">sin timing</span></div>`}

        <div class="viz-type-wrap">
          <label class="fc-config-label" style="margin-bottom:4px">Tipo</label>
          <select class="fc-select" style="width:100%" onchange="vizUpdateType(${i}, this.value)">
            ${typeOpts}
          </select>
        </div>

        ${_vizParamsBadges(seg)}
        ${_vizParamsEdit(seg, i)}
      </div>

      <!-- CENTER: narration + text -->
      <div class="viz-col-content">
        <div class="viz-section-label">Narración</div>
        <div class="viz-narration">${esc(seg.narration)}</div>
        ${seg.text_on_screen ? `
          <div class="viz-section-label" style="margin-top:10px">Texto en pantalla</div>
          <div class="viz-text-screen">${esc(seg.text_on_screen)}</div>` : ''}
        ${seg.asset ? `
          <div class="viz-section-label" style="margin-top:10px">Asset</div>
          <div class="viz-asset-chip">
            <span class="viz-asset-tipo">${esc(seg.asset_tipo||'')}</span>
            <span style="font-family:monospace;font-size:11px">${esc(seg.asset)}</span>
          </div>
          ${seg.asset_desc ? `<div class="viz-asset-desc">${esc(seg.asset_desc)}</div>` : ''}` : ''}
      </div>

      <!-- RIGHT: live preview -->
      <div class="viz-col-preview">
        <div class="viz-preview-box" style="aspect-ratio:${ratio};background:${esc(course.background_color)}">
          <div class="viz-preview-canvas" id="viz-canvas-${i}"></div>
        </div>
        <div class="viz-preview-label">${esc(seg.screen_type)} · ${pW}×${pH}</div>
      </div>

    </div>`;
  }).join('');

  area.innerHTML = `<div class="viz-phase">
    <div class="viz-header">
      <div class="viz-header-info">
        <strong>${segments.length}</strong> pantallas
        ${has_guion ? `· <span style="color:#22c55e">con timing ✓</span>` : `· <span style="color:var(--tx3)">sin guion consolidado</span>`}
      </div>
      <div style="font-size:11px;color:var(--tx3)">Cambiar tipo invalida Alineación y Visuales</div>
    </div>
    <div class="viz-list">${cardsHtml}</div>
  </div>`;

  // Render all previews
  segments.forEach((_, i) => vizRenderPreview(i));
}

function _vizParamsBadges(seg) {
  if (!seg.params || ['LIST','CONCEPT','REMOTION'].includes(seg.screen_type)) return '';
  return `<div class="fc-font-weights" style="margin-top:8px">
    ${seg.params.split('//').filter(p=>p.trim()).map(p =>
      `<span class="fc-weight-chip">${esc(p.trim())}</span>`).join('')}
  </div>`;
}

function _vizParamsEdit(seg, i) {
  if (!['LIST','CONCEPT','REMOTION'].includes(seg.screen_type)) return '';
  const parts = (seg.params||'').split('//').map(p => p.trim());

  if (seg.screen_type === 'LIST') {
    const title = parts[0]||'';
    const items = parts.slice(1);
    return `<div class="viz-params-form">
      <div class="fc-config-label">Lista</div>
      <input class="fc-select" style="width:100%;margin-bottom:5px" placeholder="@ Título (opcional)"
        value="${escA(title)}" oninput="vizSyncParams(${i})">
      ${[0,1,2,3,4,5,6].map(j => `
        <input class="fc-select viz-list-item-${i}" style="width:100%;margin-bottom:3px"
          placeholder="Ítem ${j+1}" value="${escA(items[j]||'')}" oninput="vizSyncParams(${i})">`
      ).join('')}
    </div>`;
  }
  if (seg.screen_type === 'CONCEPT') {
    return `<div class="viz-params-form">
      <div class="fc-config-label">Concepto</div>
      <input class="fc-select" style="width:100%;margin-bottom:5px" id="viz-concept-title-${i}"
        placeholder="Nombre del concepto" value="${escA(parts[0]||'')}" oninput="vizSyncParams(${i})">
      <textarea class="fc-select" style="width:100%;min-height:56px;resize:vertical" id="viz-concept-body-${i}"
        placeholder="Definición" oninput="vizSyncParams(${i})">${escA(parts[1]||'')}</textarea>
    </div>`;
  }
  if (seg.screen_type === 'REMOTION') {
    const TEMPLATES = ["TypeWriter","MindMap","LinearSteps","CycleLoop","Timeline","FunnelDiagram","StatCounter","FlipCards","TwoColumns","FourBoxes","MatrixGrid","PyramidLevels","HorizontalBars","PieDonut","RadarChart","WaveTrend","OrgChart","VennDiagram","Spotlight"];
    const selected = (parts[0]||'').replace('$','').trim();
    return `<div class="viz-params-form">
      <div class="fc-config-label">Template Remotion</div>
      <select class="fc-select" style="width:100%" id="viz-remotion-tpl-${i}" onchange="vizSyncParams(${i})">
        <option value="">-- Selecciona --</option>
        ${TEMPLATES.map(t => `<option value="${t}" ${t===selected?'selected':''}>${t}</option>`).join('')}
      </select>
    </div>`;
  }
  return '';
}

async function vizUpdateType(i, newType) {
  const seg = _vizData.segments[i];
  seg.screen_type = newType;
  // Save to DB
  try {
    await api('PUT', `/api/segments/${seg.id}/type`, { screen_type: newType, params: seg.params });
  } catch(e) { toast(e.message, false); }
  // Re-render card (params form may change)
  _buildVizUI(document.getElementById('contentArea'));
}

async function vizSyncParams(i) {
  const seg = _vizData.segments[i];
  let parts = [];
  if (seg.screen_type === 'LIST') {
    const title = document.querySelector(`#viz-card-${i} input[placeholder^="@ Título"]`)?.value?.trim();
    if (title) parts.push(title.startsWith('@') ? title : `@ ${title}`);
    document.querySelectorAll(`.viz-list-item-${i}`).forEach(el => {
      if (el.value.trim()) parts.push(el.value.trim());
    });
  } else if (seg.screen_type === 'CONCEPT') {
    const t = document.getElementById(`viz-concept-title-${i}`)?.value?.trim();
    const b = document.getElementById(`viz-concept-body-${i}`)?.value?.trim();
    if (t) parts.push(t);
    if (b) parts.push(b);
  } else if (seg.screen_type === 'REMOTION') {
    const tpl = document.getElementById(`viz-remotion-tpl-${i}`)?.value;
    if (tpl) parts.push(`$${tpl}`);
  }
  seg.params = parts.join(' // ');
  vizRenderPreview(i);
  try {
    await api('PUT', `/api/segments/${seg.id}/type`, { screen_type: seg.screen_type, params: seg.params });
  } catch(e) {}
}

function vizRenderPreview(i) {
  const canvas = document.getElementById(`viz-canvas-${i}`);
  if (!canvas || !_vizData) return;
  const seg    = _vizData.segments[i];
  const course = _vizData.course;
  const [pW, pH] = (course.resolution || '1920x1080').split('x').map(Number);
  const bg     = course.background_color || '#fefefe';
  const txtCol = course.main_text_color  || '#bd0505';

  canvas.style.backgroundColor = 'transparent';
  const text   = seg.text_on_screen || '';
  const params = (seg.params||'').split('//').map(p => p.trim());
  const assetUrl = seg.asset ? `/assets/${seg.asset}` : '';
  const isVid    = assetUrl.endsWith('.mp4');

  const mediaEl = assetUrl
    ? (isVid
       ? `<video src="${assetUrl}#t=0.001" preload="metadata" style="width:100%;height:100%;object-fit:cover;position:absolute;top:0;left:0"></video>`
       : `<img src="${assetUrl}" style="width:100%;height:100%;object-fit:cover;position:absolute;top:0;left:0" loading="lazy">`)
    : '';

  let html = '';

  if (seg.screen_type === 'TEXT') {
    html = `<div style="display:flex;align-items:center;justify-content:center;height:100%;padding:8%;text-align:center;font-size:6cqh;font-weight:700;color:${esc(txtCol)};font-family:'${esc(course.main_font||'Inter')}';">${esc(text)}</div>`;

  } else if (seg.screen_type === 'SPLIT_LEFT' || seg.screen_type === 'SPLIT_RIGHT') {
    const assetSide = `<div style="width:50%;height:100%;position:relative;overflow:hidden">${mediaEl || '<div style="width:100%;height:100%;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-size:5cqh;opacity:.3">img</div>'}</div>`;
    const textSide  = `<div style="width:50%;height:100%;display:flex;align-items:center;justify-content:center;padding:5%;text-align:center;font-size:4.5cqh;font-weight:600;color:${esc(txtCol)};font-family:'${esc(course.main_font||'Inter')}';">${esc(text)}</div>`;
    html = seg.screen_type === 'SPLIT_LEFT'
      ? assetSide + textSide
      : textSide + assetSide;
    canvas.style.display = 'flex';

  } else if (seg.screen_type === 'FULL_IMAGE') {
    html = `${mediaEl || '<div style="width:100%;height:100%;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-size:5cqh;opacity:.3">img</div>'}
      ${text ? `<div style="position:absolute;bottom:5%;left:0;right:0;text-align:center;font-size:4cqh;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.8);padding:0 5%;z-index:2">${esc(text)}</div>` : ''}`;

  } else if (seg.screen_type === 'VIDEO') {
    html = `${mediaEl || '<div style="width:100%;height:100%;background:#111;display:flex;align-items:center;justify-content:center;font-size:5cqh;color:#555">▶ video</div>'}
      ${text ? `<div style="position:absolute;bottom:5%;left:0;right:0;text-align:center;font-size:4cqh;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.8);padding:0 5%;z-index:2">${esc(text)}</div>` : ''}`;

  } else if (seg.screen_type === 'LIST') {
    canvas.style.backgroundColor = '#2C5F2E';
    let items = [...params];
    let ghost = '';
    if (items[0]?.startsWith('@')) ghost = items.shift().replace('@','').trim();
    html = `
      ${ghost ? `<div style="position:absolute;top:8cqh;left:50%;transform:translateX(-50%);color:#fff;font-size:7cqh;opacity:.15;font-weight:700;white-space:nowrap">${esc(ghost)}</div>` : ''}
      <div style="position:absolute;top:${ghost?'20':'12'}cqh;left:6cqw;right:6cqw;display:flex;flex-direction:column;gap:2cqh">
        ${items.filter(p=>p).map(p => `<div style="font-size:4.5cqh;font-weight:700;color:#fff">• ${esc(p)}</div>`).join('')}
      </div>`;

  } else if (seg.screen_type === 'CONCEPT') {
    const title = params[0]||'Concepto';
    const def   = params[1]||'';
    html = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding:8%;gap:3cqh;text-align:center">
      <div style="font-size:6cqh;font-weight:800;color:${esc(txtCol)}">${esc(title)}</div>
      ${def ? `<div style="font-size:4cqh;color:#1a1a1a;opacity:.8">${esc(def)}</div>` : ''}
    </div>`;

  } else if (seg.screen_type === 'REMOTION') {
    const tpl = (params[0]||'').replace('$','');
    html = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:3cqh;background:linear-gradient(135deg,#1e1b4b,#312e81)">
      <div style="font-size:8cqh">🎬</div>
      <div style="font-size:4cqh;color:#a5b4fc;font-weight:700">${esc(tpl||'Remotion')}</div>
      <div style="font-size:2.5cqh;color:#6366f1;opacity:.7">animación generada</div>
    </div>`;

  } else {
    html = `<div style="display:flex;align-items:center;justify-content:center;height:100%;opacity:.3;font-size:4cqh">${esc(seg.screen_type)}</div>`;
  }

  canvas.innerHTML = html;
}

/* ═══════════════════════════════════════════════════════
   FONTS & COLORS PHASE
═══════════════════════════════════════════════════════ */

async function renderFontsColors(area) {
  area.innerHTML = `<div class="audio-phase"><div class="rp-loading" style="padding:60px">Cargando fonts…</div></div>`;
  let fontsData = null, course = null;
  try { fontsData = await api('GET', '/api/fonts'); } catch(e) {}
  if (S.activeCourse) {
    try { course = await api('GET', `/api/courses`).then(cs => cs.find(c => c.id === S.activeCourse.id)); } catch(e) {}
    if (!course) course = S.activeCourse;
  }
  _buildFontsColorsUI(area, fontsData, course);
}

function _buildFontsColorsUI(area, fontsData, course) {
  const families = fontsData?.families || [];
  const installed = fontsData?.fonts || [];

  // Inject @font-face for preview
  let faceCSS = installed.map(f =>
    `@font-face{font-family:'${f.family}';font-weight:${f.weight==='Bold'?'700':f.weight==='Italic'?'400':'400'};font-style:${f.weight==='Italic'?'italic':'normal'};src:url('${f.url}') format('truetype');}`
  ).join('\n');
  let styleEl = document.getElementById('fc-font-faces');
  if (!styleEl) { styleEl = document.createElement('style'); styleEl.id = 'fc-font-faces'; document.head.appendChild(styleEl); }
  styleEl.textContent = faceCSS;

  const activeFontFamily = course?.main_font || 'Inter';
  const bg     = course?.background_color     || '#fefefe';
  const txtCol = course?.main_text_color      || '#bd0505';
  const hlCol  = course?.highlight_text_color || '#e3943b';

  // Font family options
  const familyNames = [...new Set(installed.map(f => f.family))];
  const fontOpts = familyNames.map(fam =>
    `<option value="${esc(fam)}" ${fam === activeFontFamily ? 'selected' : ''}>${esc(fam)}</option>`
  ).join('');

  area.innerHTML = `<div class="audio-phase">

    <!-- ① Font Library -->
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">🔤 Biblioteca de Fonts</span>
        <label class="btn btn-secondary btn-sm fc-upload-label">
          ⬆ Importar TTF/OTF
          <input type="file" accept=".ttf,.otf" multiple style="display:none" onchange="uploadFonts(this)">
        </label>
      </div>
      <div class="audio-card-body">
        ${installed.length === 0 ? `<p class="audio-card-desc">No hay fonts instalados. Importa archivos TTF/OTF.</p>` : `
        <div class="fc-font-grid">
          ${families.map(fam => `
            <div class="fc-font-card">
              <div class="fc-font-preview" style="font-family:'${esc(fam.family)}'">${esc(fam.family)}</div>
              <div class="fc-font-name">${esc(fam.family)}</div>
              <div class="fc-font-weights">
                ${fam.weights.map(w => `
                  <span class="fc-weight-chip">${esc(w.weight)}
                    <button class="fc-weight-del" onclick="deleteFont('${esc(w.filename)}')" title="Eliminar">×</button>
                  </span>`).join('')}
              </div>
            </div>`).join('')}
        </div>`}
      </div>
    </div>

    <!-- ② Font & Color Config (per course) -->
    ${course ? `
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">⚙️ Configuración del Proyecto — ${esc(course.title)}</span>
        <span id="fc-save-status" style="font-size:11px;color:var(--tx3)"></span>
      </div>
      <div class="audio-card-body">

        <!-- Font selector -->
        <div class="fc-config-section">
          <div class="fc-config-label">Fuente Principal (subtítulos ASS)</div>
          <div class="fc-font-selector-row">
            <select id="fc_font" class="fc-select" onchange="fcPreviewFont(this.value); fcAutoSave()">
              ${fontOpts}
              <option value="Arial" ${activeFontFamily==='Arial'?'selected':''}>Arial (sistema)</option>
              <option value="Helvetica" ${activeFontFamily==='Helvetica'?'selected':''}>Helvetica (sistema)</option>
            </select>
            <div class="fc-font-preview-inline" id="fcFontPreview" style="font-family:'${esc(activeFontFamily)}'">
              Texto de ejemplo — Video Creator 2026
            </div>
          </div>
        </div>

        <!-- Colors -->
        <div class="fc-config-section">
          <div class="fc-config-label">Colores</div>
          <div class="fc-colors-grid">
            <div class="fc-color-item">
              <label>Fondo</label>
              <div class="vc-color-row">
                <input type="color" id="fc_bg_pick" value="${escA(bg)}"
                  oninput="document.getElementById('fc_bg').value=this.value;fcAutoSave()">
                <input type="text" id="fc_bg" class="vc-hex" value="${escA(bg)}"
                  oninput="document.getElementById('fc_bg_pick').value=this.value;fcAutoSave()">
              </div>
              <div class="fc-color-preview" id="fcBgPreview" style="background:${escA(bg)}"></div>
            </div>
            <div class="fc-color-item">
              <label>Texto subtítulos</label>
              <div class="vc-color-row">
                <input type="color" id="fc_txt_pick" value="${escA(txtCol)}"
                  oninput="document.getElementById('fc_txt').value=this.value;fcAutoSave()">
                <input type="text" id="fc_txt" class="vc-hex" value="${escA(txtCol)}"
                  oninput="document.getElementById('fc_txt_pick').value=this.value;fcAutoSave()">
              </div>
              <div class="fc-color-preview" id="fcTxtPreview" style="background:${escA(txtCol)}"></div>
            </div>
            <div class="fc-color-item">
              <label>Highlight</label>
              <div class="vc-color-row">
                <input type="color" id="fc_hl_pick" value="${escA(hlCol)}"
                  oninput="document.getElementById('fc_hl').value=this.value;fcAutoSave()">
                <input type="text" id="fc_hl" class="vc-hex" value="${escA(hlCol)}"
                  oninput="document.getElementById('fc_hl_pick').value=this.value;fcAutoSave()">
              </div>
              <div class="fc-color-preview" id="fcHlPreview" style="background:${escA(hlCol)}"></div>
            </div>
          </div>
        </div>

        <!-- Video config -->
        <div class="fc-config-section">
          <div class="fc-config-label">Video</div>
          <div class="fc-video-grid">
            <div class="fc-video-field">
              <label>FPS</label>
              <input type="number" id="fc_fps" value="${course.fps||30}" min="24" max="60" onchange="fcAutoSave()">
            </div>
            <div class="fc-video-field">
              <label>Resolución</label>
              <input type="text" id="fc_res" value="${escA(course.resolution||'1920x1080')}" onchange="fcAutoSave()">
            </div>
            <div class="fc-video-field">
              <label>Portada (path relativo)</label>
              <input type="text" id="fc_cover" value="${escA(course.cover_asset||'videos/portada.mp4')}" onchange="fcAutoSave()">
            </div>
          </div>
        </div>

        <!-- Live preview -->
        <div class="fc-config-section">
          <div class="fc-config-label">Preview</div>
          <div class="fc-preview-box" id="fcPreviewBox"
            style="background:${escA(bg)};font-family:'${esc(activeFontFamily)}'">
            <div class="fc-preview-sub" id="fcPreviewSub" style="color:${escA(txtCol)}">
              Este es el texto de subtítulo que aparece en el video
            </div>
            <div class="fc-preview-hl" id="fcPreviewHl" style="color:${escA(hlCol)}">
              Texto con highlight — concepto clave
            </div>
          </div>
        </div>

      </div>
    </div>
    ` : `<div class="audio-card"><div class="audio-card-body"><p class="audio-card-desc">Selecciona una clase para editar la configuración de su proyecto.</p></div></div>`}

  </div>`;
}

function fcPreviewFont(fontFamily) {
  ['fcFontPreview','fcPreviewSub','fcPreviewHl','fcPreviewBox'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.fontFamily = `'${fontFamily}'`;
  });
}

let _fcSaveTimer = null;
function fcAutoSave() {
  // Live preview update
  const bg     = document.getElementById('fc_bg')?.value     || '';
  const txtCol = document.getElementById('fc_txt')?.value    || '';
  const hlCol  = document.getElementById('fc_hl')?.value     || '';
  const font   = document.getElementById('fc_font')?.value   || '';

  const previewBox = document.getElementById('fcPreviewBox');
  if (previewBox) previewBox.style.background = bg;
  const previewSub = document.getElementById('fcPreviewSub');
  if (previewSub) { previewSub.style.color = txtCol; previewSub.style.fontFamily = `'${font}'`; }
  const previewHl = document.getElementById('fcPreviewHl');
  if (previewHl)  { previewHl.style.color = hlCol;  previewHl.style.fontFamily = `'${font}'`; }
  document.getElementById('fcBgPreview') &&  (document.getElementById('fcBgPreview').style.background  = bg);
  document.getElementById('fcTxtPreview') && (document.getElementById('fcTxtPreview').style.background = txtCol);
  document.getElementById('fcHlPreview') &&  (document.getElementById('fcHlPreview').style.background  = hlCol);

  // Debounced save
  clearTimeout(_fcSaveTimer);
  _fcSaveTimer = setTimeout(async () => {
    if (!S.activeCourse) return;
    const statusEl = document.getElementById('fc-save-status');
    if (statusEl) statusEl.textContent = 'Guardando…';
    try {
      const payload = {
        title:                S.activeCourse.title,
        description:          S.activeCourse.description || '',
        fps:                  parseInt(document.getElementById('fc_fps')?.value) || 30,
        resolution:           document.getElementById('fc_res')?.value?.trim()   || '1920x1080',
        main_font:            font,
        background_color:     bg,
        main_text_color:      txtCol,
        highlight_text_color: hlCol,
        cover_asset:          document.getElementById('fc_cover')?.value?.trim() || 'videos/portada.mp4',
      };
      const updated = await api('PUT', `/api/courses/${S.activeCourse.id}`, payload);
      S.activeCourse = updated;
      if (statusEl) { statusEl.textContent = '✓ Guardado'; setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 2000); }
    } catch(e) {
      if (statusEl) statusEl.textContent = '⚠ Error guardando';
    }
  }, 700);
}

async function uploadFonts(input) {
  const files = Array.from(input.files);
  if (!files.length) return;
  let ok = 0, fail = 0;
  for (const file of files) {
    const fd = new FormData();
    fd.append('file', file);
    try {
      await fetch('/api/fonts', { method: 'POST', body: fd });
      ok++;
    } catch(e) { fail++; }
  }
  toast(fail === 0 ? `✅ ${ok} font${ok>1?'s':''} importado${ok>1?'s':''}` : `⚠ ${ok} ok · ${fail} error${fail>1?'es':''}`, fail === 0);
  renderFontsColors(document.getElementById('contentArea'));
}

async function deleteFont(filename) {
  if (!confirm(`¿Eliminar ${filename}?`)) return;
  try {
    await api('DELETE', `/api/fonts/${encodeURIComponent(filename)}`);
    toast('Font eliminado');
    renderFontsColors(document.getElementById('contentArea'));
  } catch(e) { toast(e.message, false); }
}

/* ═══════════════════════════════════════════════════════
   VIDEO PHASE — Dummy Builder + Final Render
═══════════════════════════════════════════════════════ */
let _renderPollTimer = null;
function _clearRenderPoll() {
  if (_renderPollTimer) { clearInterval(_renderPollTimer); _renderPollTimer = null; }
}

async function renderVideo(area) {
  _clearRenderPoll();
  area.innerHTML = `<div class="audio-phase"><div class="rp-loading" style="padding:60px">Cargando estado de render…</div></div>`;

  let visual = null, renderStatus = null, assetsStatus = null;
  try { visual = await api('GET', `/api/classes/${S.activeClass.id}/visual`); } catch(e) {}
  try { renderStatus = await api('GET', `/api/classes/${S.activeClass.id}/render/status`); } catch(e) {}
  if (visual?.status === 'done') {
    try { assetsStatus = await api('GET', `/api/classes/${S.activeClass.id}/render/assets-status`); } catch(e) {}
  }
  _buildVideoUI(area, visual, renderStatus, assetsStatus);
  if (renderStatus?.status === 'building_dummies' || renderStatus?.status === 'rendering') {
    _startRenderPoll();
  }
}

function _buildVideoUI(area, visual, renderStatus, assetsStatus) {
  const visualOk      = visual?.status === 'done';
  const st            = renderStatus?.status || 'idle';
  const isBuilding    = st === 'building_dummies';
  const isDummiesDone = st === 'dummies_done';
  const isRendering   = st === 'rendering';
  const isDone        = st === 'done';
  const isError       = st === 'error';
  const isBusy        = isBuilding || isRendering;

  // Assets table rows
  let assetsRows = '';
  let missingCount = assetsStatus?.missing ?? 0;
  let totalCount   = assetsStatus?.total   ?? 0;
  if (assetsStatus?.items) {
    assetsRows = assetsStatus.items.map(item => `
      <tr>
        <td style="font-family:monospace;font-size:11px;padding:6px 10px">${esc(item.nombre)}</td>
        <td style="padding:6px 10px"><span class="seg-type-badge" style="background:var(--bg3);color:var(--tx2);border-color:var(--border2)">${esc(item.tipo)}</span></td>
        <td style="font-family:monospace;font-size:11px;padding:6px 10px;color:var(--tx3)">${esc(item.ubicacion || '')}</td>
        <td style="padding:6px 10px;text-align:center">
          ${item.exists
            ? `<span style="color:#22c55e;font-weight:700">✓</span>`
            : `<span style="color:#ef4444;font-weight:700">✗</span>`}
        </td>
      </tr>`).join('');
  }

  area.innerHTML = `<div class="audio-phase">

    <!-- Prerequisite / status card -->
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">🎬 Render Final</span>
        ${isDone ? `<span class="audio-done-badge">✓ Video listo</span>` : ''}
      </div>
      <div class="audio-card-body">
        ${!visualOk ? `
          <div class="vis-prereq">
            <span class="vis-prereq-icon">🔒</span>
            <div>
              <div style="font-size:13px;font-weight:700;color:var(--tx1);margin-bottom:4px">Requiere Arquitectura Visual completada</div>
              <div style="font-size:12px;color:var(--tx3)">Completa la fase Visual antes de renderizar.</div>
            </div>
          </div>
        ` : isDone ? `
          <div class="tx-summary-row" style="margin-bottom:12px">
            <div class="tx-summary-stat"><span class="tx-stat-val" style="color:#22c55e">✓</span><span class="tx-stat-lbl">completado</span></div>
            <div class="tx-summary-stat"><span class="tx-stat-val">${totalCount}</span><span class="tx-stat-lbl">assets</span></div>
          </div>
          <div class="audio-exports">
            <a href="/api/classes/${S.activeClass.id}/render/download" class="btn btn-primary" download>⬇ Descargar Video</a>
          </div>
          <div style="margin-top:10px">
            <button class="btn btn-ghost audio-att-btn" onclick="startFinalRender()">↻ Re-renderizar</button>
          </div>
        ` : `
          <p class="audio-card-desc">
            Genera el video final mezclando audio, assets (imágenes/videos) y subtítulos ASS con FFmpeg.
            Si faltan assets, construye dummies primero.
          </p>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            ${assetsStatus && missingCount > 0 ? `
              <button class="btn btn-secondary audio-att-btn" onclick="buildDummies()" ${isBusy ? 'disabled' : ''}>
                ${isBuilding ? '⏳ Construyendo dummies…' : `🏗 Construir ${missingCount} dummy${missingCount>1?'s':''}`}
              </button>
            ` : ''}
            <button class="btn btn-primary audio-att-btn" onclick="startFinalRender()" ${isBusy || !assetsStatus ? 'disabled' : ''}>
              ${isRendering ? '⏳ Renderizando…' : '🎬 Renderizar Video'}
            </button>
          </div>
          ${isBusy ? `
          <div class="audio-progress-wrap">
            <div class="audio-progress-bar">
              <div class="audio-progress-fill running" id="renderProgressFill" style="width:${renderStatus?.progress||0}%"></div>
            </div>
            <div class="audio-progress-foot">
              <span id="renderPhaseLabel" class="audio-phase-label">${esc(renderStatus?.phase||'')}</span>
              <span id="renderProgressPct" class="audio-progress-pct">${renderStatus?.progress||0}%</span>
            </div>
          </div>` : ''}
          ${isError ? `<div class="audio-error-box"><div class="audio-error-title">⚠️ Error</div><pre class="audio-error-pre">${esc(renderStatus?.error||'')}</pre></div>` : ''}
        `}
      </div>
    </div>

    <!-- Assets status table -->
    ${visualOk && assetsStatus ? `
    <div class="audio-card">
      <div class="audio-card-head">
        <span class="audio-card-title">📦 Estado de Assets</span>
        <span style="font-size:12px;color:${missingCount>0?'#ef4444':'#22c55e'};font-weight:600">
          ${missingCount > 0 ? `${missingCount} faltantes` : 'Todos presentes ✓'}
        </span>
      </div>
      <div class="audio-card-body" style="padding:0">
        <table class="stat-cls-table">
          <thead><tr>
            <th>Archivo</th><th>Tipo</th><th>Ubicación</th><th style="text-align:center">¿Existe?</th>
          </tr></thead>
          <tbody>${assetsRows}</tbody>
        </table>
      </div>
    </div>
    ` : ''}

  </div>`;
}

async function buildDummies() {
  try {
    await api('POST', `/api/classes/${S.activeClass.id}/render/build-dummies`);
    const area = document.getElementById('contentArea');
    const visual = await api('GET', `/api/classes/${S.activeClass.id}/visual`);
    const rs = { status: 'building_dummies', progress: 0, phase: 'Iniciando…' };
    const as = await api('GET', `/api/classes/${S.activeClass.id}/render/assets-status`);
    _buildVideoUI(area, visual, rs, as);
    _startRenderPoll();
  } catch(e) { toast(e.message, false); }
}

async function startFinalRender() {
  try {
    await api('POST', `/api/classes/${S.activeClass.id}/render`);
    const area = document.getElementById('contentArea');
    const visual = await api('GET', `/api/classes/${S.activeClass.id}/visual`);
    const rs = { status: 'rendering', progress: 0, phase: 'Iniciando render…' };
    const as = await api('GET', `/api/classes/${S.activeClass.id}/render/assets-status`);
    _buildVideoUI(area, visual, rs, as);
    _startRenderPoll();
  } catch(e) { toast(e.message, false); }
}

function _startRenderPoll() {
  _clearRenderPoll();
  const classId = S.activeClass?.id;
  _renderPollTimer = setInterval(async () => {
    if (S.activeClass?.id !== classId || S.activePhase !== 'video') { _clearRenderPoll(); return; }
    try {
      const s = await api('GET', `/api/classes/${classId}/render/status`);
      const fill = document.getElementById('renderProgressFill');
      const lbl  = document.getElementById('renderPhaseLabel');
      const pct  = document.getElementById('renderProgressPct');
      if (fill) fill.style.width = `${s.progress}%`;
      if (lbl)  lbl.textContent  = s.phase || '';
      if (pct)  pct.textContent  = `${s.progress}%`;
      if (s.status !== 'building_dummies' && s.status !== 'rendering') {
        _clearRenderPoll();
        // Full refresh
        const area = document.getElementById('contentArea');
        let visual = null, assetsStatus = null;
        try { visual = await api('GET', `/api/classes/${classId}/visual`); } catch(e) {}
        try { assetsStatus = await api('GET', `/api/classes/${classId}/render/assets-status`); } catch(e) {}
        _buildVideoUI(area, visual, s, assetsStatus);
        if (s.status === 'dummies_done') toast('✅ Dummies construidos');
        else if (s.status === 'done')    toast('✅ Video renderizado');
        else if (s.status === 'error')   toast('❌ Error en render', false);
      }
    } catch(e) {}
  }, 2000);
}

/* ─── PLACEHOLDER PHASES ──────────────────────────────── */
function renderPlaceholder(area, icon, title, sub) {
  area.innerHTML = `
    <div class="phase-placeholder">
      <div class="phase-ph-icon">${icon}</div>
      <div class="phase-ph-title">${title}</div>
      <p class="phase-ph-sub">${sub}</p>
      <p style="font-size:11px;color:var(--tx3);margin-top:16px">🔒 Esta fase se habilitará próximamente</p>
    </div>`;
}

/* ═══════════════════════════════════════════════════════
   CRUD — COURSES
═══════════════════════════════════════════════════════ */
function createCourse() {
  openModal({
    title: 'Nuevo Proyecto',
    fields: [
      { key: 'title',       label: 'Nombre del proyecto', required: true },
      { key: 'description', label: 'Descripción (opcional)', textarea: true },
    ],
    confirmLabel: 'Crear',
    onConfirm: async v => {
      const c = await api('POST', '/api/courses', v);
      S.courses.push(c);
      closeModal();
      renderSidebarPicker();
      toast('Proyecto creado');
    }
  });
}

function editCourse(id) {
  const c = S.courses.find(x => x.id === id) || S.activeCourse;
  if (!c) return;
  openModal({ wide: true, html: `
    <div class="modal-title">Editar Proyecto</div>
    <div class="modal-body">
      <div class="field">
        <label>Nombre del proyecto</label>
        <input id="ec_title" type="text" value="${escA(c.title)}"/>
      </div>
      <div class="field">
        <label>Descripción</label>
        <textarea id="ec_desc" rows="2">${esc(c.description || '')}</textarea>
      </div>

      <div class="vc-section-divider">⚙️ Configuración de Video</div>
      <div class="vc-grid">
        <div class="field">
          <label>FPS</label>
          <input id="ec_fps" type="number" value="${c.fps || 30}" min="24" max="60"/>
        </div>
        <div class="field">
          <label>Resolución</label>
          <input id="ec_res" type="text" value="${escA(c.resolution || '1920x1080')}"/>
        </div>
        <div class="field">
          <label>Fuente principal</label>
          <input id="ec_font" type="text" value="${escA(c.main_font || 'Inter')}"/>
        </div>
        <div class="field">
          <label>Color de fondo</label>
          <div class="vc-color-row">
            <input id="ec_bg_pick" type="color" value="${escA(c.background_color || '#fefefe')}" oninput="document.getElementById('ec_bg').value=this.value"/>
            <input id="ec_bg" type="text"  value="${escA(c.background_color || '#fefefe')}" oninput="document.getElementById('ec_bg_pick').value=this.value" class="vc-hex"/>
          </div>
        </div>
        <div class="field">
          <label>Color de texto</label>
          <div class="vc-color-row">
            <input id="ec_txt_pick" type="color" value="${escA(c.main_text_color || '#bd0505')}" oninput="document.getElementById('ec_txt').value=this.value"/>
            <input id="ec_txt" type="text"  value="${escA(c.main_text_color || '#bd0505')}" oninput="document.getElementById('ec_txt_pick').value=this.value" class="vc-hex"/>
          </div>
        </div>
        <div class="field">
          <label>Color highlight</label>
          <div class="vc-color-row">
            <input id="ec_hl_pick" type="color" value="${escA(c.highlight_text_color || '#e3943b')}" oninput="document.getElementById('ec_hl').value=this.value"/>
            <input id="ec_hl" type="text"  value="${escA(c.highlight_text_color || '#e3943b')}" oninput="document.getElementById('ec_hl_pick').value=this.value" class="vc-hex"/>
          </div>
        </div>
      </div>
      <div class="field">
        <label>Asset de portada</label>
        <input id="ec_cover" type="text" value="${escA(c.cover_asset || 'videos/portada.mp4')}"/>
      </div>
    </div>
    <div class="modal-foot">
      <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
      <button class="btn btn-primary" onclick="saveEditCourse(${id})">Guardar</button>
    </div>`
  });
}

async function saveEditCourse(id) {
  const title = document.getElementById('ec_title')?.value?.trim();
  if (!title) { document.getElementById('ec_title').focus(); return; }
  const payload = {
    title,
    description:          document.getElementById('ec_desc').value,
    fps:                  parseInt(document.getElementById('ec_fps').value) || 30,
    resolution:           document.getElementById('ec_res').value.trim(),
    main_font:            document.getElementById('ec_font').value.trim(),
    background_color:     document.getElementById('ec_bg').value.trim(),
    main_text_color:      document.getElementById('ec_txt').value.trim(),
    highlight_text_color: document.getElementById('ec_hl').value.trim(),
    cover_asset:          document.getElementById('ec_cover').value.trim(),
  };
  try {
    const updated = await api('PUT', `/api/courses/${id}`, payload);
    const c = S.courses.find(x => x.id === id);
    if (c) Object.assign(c, updated);
    if (S.activeCourse?.id === id) {
      S.activeCourse = updated;
      document.querySelector('.tree-course-name').textContent = updated.title;
      updateBreadcrumb();
    }
    closeModal();
    if (!S.activeCourse) renderSidebarPicker();
    toast('Proyecto actualizado');
  } catch(e) { toast(e.message, false); }
}

function deleteCourse(id) {
  const c = S.courses.find(x => x.id === id);
  openConfirm({
    title: 'Eliminar proyecto',
    msg: `¿Eliminar <strong>${esc(c.title)}</strong> con todo su contenido? Esta acción no se puede deshacer.`,
    onConfirm: async () => {
      await api('DELETE', `/api/courses/${id}`);
      S.courses = S.courses.filter(x => x.id !== id);
      if (S.activeCourse?.id === id) showCourseList();
      else renderSidebarPicker();
      toast('Eliminado');
    }
  });
}

/* ─── SECTIONS ────────────────────────────────────────── */
async function refreshSections() {
  S.sections = await api('GET', `/api/courses/${S.activeCourse.id}/sections`);
  renderTree();
}

function createSection() {
  openModal({
    title: 'Nueva Sección',
    fields: [{ key: 'title', label: 'Nombre de la sección', required: true }],
    confirmLabel: 'Crear',
    onConfirm: async v => {
      const s = await api('POST', `/api/courses/${S.activeCourse.id}/sections`, v);
      S.expandedSections.add(s.id);
      closeModal();
      await refreshSections();
      toast('Sección creada');
    }
  });
}

function editSection(id, current) {
  openModal({
    title: 'Editar Sección',
    fields: [{ key: 'title', label: 'Nombre', value: current, required: true }],
    onConfirm: async v => {
      await api('PUT', `/api/sections/${id}`, v);
      closeModal();
      await refreshSections();
    }
  });
}

function deleteSection(id) {
  openConfirm({
    title: 'Eliminar sección',
    msg: 'Se borrarán todas las clases dentro de esta sección.',
    onConfirm: async () => {
      await api('DELETE', `/api/sections/${id}`);
      if (S.activeClass) {
        const sec = S.sections.find(s => s.id === id);
        if (sec?.classes?.some(c => c.id === S.activeClass.id)) {
          S.activeClass = null;
          document.getElementById('phaseBar').classList.add('hidden');
          renderContent('welcome');
          updateBreadcrumb();
          updateStatusBar();
        }
      }
      await refreshSections();
      toast('Sección eliminada');
    }
  });
}

/* ─── CLASSES ─────────────────────────────────────────── */
function createClass(sectionId) {
  openModal({
    title: 'Nueva Clase',
    fields: [{ key: 'title', label: 'Título de la clase', required: true }],
    confirmLabel: 'Crear',
    onConfirm: async v => {
      const cls = await api('POST', `/api/sections/${sectionId}/classes`, v);
      closeModal();
      S.expandedSections.add(sectionId);
      await refreshSections();
      selectClass(cls.id);
      toast('Clase creada');
    }
  });
}

function renameClass(id, current) {
  openModal({
    title: 'Renombrar Clase',
    fields: [{ key: 'title', label: 'Nombre', value: current, required: true }],
    onConfirm: async v => {
      const updated = await api('PUT', `/api/classes/${id}`, {
        title: v.title,
        raw_narration: S.activeClass?.id === id ? (document.getElementById('guionTA')?.value || S.activeClass.raw_narration || '') : undefined,
      });
      if (S.activeClass?.id === id) {
        S.activeClass.title = updated.title;
        updateBreadcrumb();
        updateStatusBar();
        // update toolbar title input if guion phase
        const ta = document.getElementById('guionTA');
        if (ta) { /* no title input in editor, status bar updates */ }
      }
      closeModal();
      await refreshSections();
    }
  });
}

function deleteClass(id) {
  openConfirm({
    title: 'Eliminar clase',
    msg: 'Se eliminará esta clase y su locución. Esta acción no se puede deshacer.',
    onConfirm: async () => {
      await api('DELETE', `/api/classes/${id}`);
      if (S.activeClass?.id === id) {
        S.activeClass = null;
        document.getElementById('phaseBar').classList.add('hidden');
        renderContent('welcome');
        updateBreadcrumb();
        updateStatusBar();
      }
      await refreshSections();
      toast('Clase eliminada');
    }
  });
}

/* ═══════════════════════════════════════════════════════
   GLOBAL MANAGER — Tipos de Pantalla & Templates Remotion
═══════════════════════════════════════════════════════ */
const GM = {
  screenTypes: [],
  remotionTemplates: [],
  activeTab: 'types',
};

async function loadGmData() {
  try {
    const [types, tpls] = await Promise.all([
      api('GET', '/api/screen-types'),
      api('GET', '/api/remotion-templates')
    ]);
    GM.screenTypes = types;
    GM.remotionTemplates = tpls;
  } catch(e) {
    toast('Error cargando datos del gestor', false);
  }
}

function renderGlobalManager() {
  const container = document.getElementById('contentArea');
  container.innerHTML = `
    <div class="gm-container">
      <div class="gm-header">
        <div class="gm-title-area">
          <h1 class="gm-title">Gestor Maestro de Visuales</h1>
          <p class="gm-subtitle">Configuración global de layouts, dinámicos y motores de renderizado</p>
        </div>
        <button class="gm-add-btn" onclick="openEditTypeModal()">
          <span>+</span> Nuevo Tipo de Pantalla
        </button>
      </div>

      <div class="gm-tabs">
        <button class="gm-tab ${GM.activeTab === 'types' ? 'active' : ''}" onclick="switchGmTab('types')">Tipos de Pantalla</button>
        <button class="gm-tab ${GM.activeTab === 'remotion' ? 'active' : ''}" onclick="switchGmTab('remotion')">Templates Remotion</button>
      </div>

      <div id="gmGrid" class="gm-grid"></div>
    </div>
  `;
  renderGmGrid();
}

function switchGmTab(tab) {
  GM.activeTab = tab;
  renderGlobalManager();
}


function renderGmGrid() {
  const grid = document.getElementById('gmGrid');
  if (GM.activeTab === 'types') renderGmTypes(grid);
  else renderGmTemplates(grid);
}

function renderGmTypes(grid) {
  grid.innerHTML = GM.screenTypes.map(t => `
    <div class="gm-card">
      <div class="gm-card-head">
        <div class="gm-card-icon" style="background:${t.color}22;color:${t.color}">${t.icon || '📝'}</div>
        <div class="gm-card-info">
          <div class="gm-card-name">${esc(t.label)}</div>
          <span class="gm-card-tag">${esc(t.name)}</span>
        </div>
      </div>
      <div class="gm-card-desc">${esc(t.description || 'Sin descripción')}</div>
      
      <div class="gm-limits-row">
        ${t.max_items ? `<span class="gm-limit-badge">📦 Max Items: ${t.max_items}</span>` : ''}
        ${t.max_words ? `<span class="gm-limit-badge">💬 Max Words: ${t.max_words}</span>` : ''}
        ${t.max_chars ? `<span class="gm-limit-badge">🔤 Max Chars: ${t.max_chars}</span>` : ''}
      </div>

      <div class="gm-card-meta">Format: ${esc(t.tag_format || '<!-- type:' + t.name + ' -->')}</div>
      ${t.has_params ? `<div class="gm-card-meta">Params: ${esc(t.params_syntax)}</div>` : ''}
      
      <div class="gm-card-actions">
        <button class="gm-btn-sm gm-btn-edit" onclick='openEditTypeModal(${JSON.stringify(t).replace(/'/g, "&apos;")})'>Editar</button>
        ${t.category === 'rendering' ? `<button class="gm-btn-sm" style="background:var(--accent);color:#fff" onclick="switchGmTab('remotion')">Configurar Sub-tipos</button>` : ''}
        <button class="gm-btn-sm gm-btn-del" onclick="deleteScreenType(${t.id})">Eliminar</button>
      </div>
    </div>
  `).join('');
}

function renderGmTemplates(grid) {
  grid.innerHTML = `
    <div style="grid-column: 1/-1; margin-bottom: 12px">
      <button class="gm-add-btn" style="background:var(--bg3);color:var(--tx1)" onclick="openEditTemplateModal()">+ Nuevo Template</button>
    </div>
  ` + GM.remotionTemplates.map(t => `
    <div class="gm-card">
      <div class="gm-card-head">
        <div class="gm-card-icon" style="background:var(--bg3);color:var(--accent)">🎬</div>
        <div class="gm-card-info">
          <div class="gm-card-name">${esc(t.label)}</div>
          <span class="gm-card-tag">$${esc(t.name)}</span>
        </div>
      </div>
      <div class="gm-card-desc">${esc(t.description || 'Sin descripción')}</div>
      <div class="gm-card-meta">Limits: ${esc(t.limits || 'No definidos')}</div>
      <div class="gm-card-actions">
        <button class="gm-btn-sm gm-btn-edit" onclick='openEditTemplateModal(${JSON.stringify(t).replace(/'/g, "&apos;")})'>Editar</button>
        <button class="gm-btn-sm gm-btn-del" onclick="deleteRemotionTemplate(${t.id})">Eliminar</button>
      </div>
    </div>
  `).join('');
}

/* ─── Screen Type Actions ─────────────────────────── */

function openEditTypeModal(t = null) {
  const isNew = !t;
  const title = isNew ? 'Nuevo Tipo de Pantalla' : 'Editar Tipo';
  const html = `
    <div class="modal-title">${esc(title)}</div>
    <div class="modal-body">
      <form id="typeForm" class="gm-form" onsubmit="saveScreenType(event, ${t ? t.id : 'null'})">
        <div class="gm-form-grid">
          <div class="gm-form-row">
            <label class="gm-form-label">Nombre (ID)</label>
            <input type="text" name="name" class="gm-input" value="${t ? t.name : ''}" placeholder="Ej: SPLIT_LEFT" required ${t ? 'readonly' : ''}>
          </div>
          <div class="gm-form-row">
            <label class="gm-form-label">Etiqueta (UI)</label>
            <input type="text" name="label" class="gm-input" value="${t ? t.label : ''}" placeholder="Ej: Split Izquierda" required>
          </div>
        </div>
        <div class="gm-form-grid">
          <div class="gm-form-row">
            <label class="gm-form-label">Categoría</label>
            <select name="category" class="gm-input">
              <option value="layout" ${t?.category === 'layout' ? 'selected' : ''}>Layout</option>
              <option value="dynamic" ${t?.category === 'dynamic' ? 'selected' : ''}>Dynamic</option>
              <option value="rendering" ${t?.category === 'rendering' ? 'selected' : ''}>Rendering Engine</option>
            </select>
          </div>
          <div class="gm-form-row">
            <label class="gm-form-label">Icono (Emoji)</label>
            <input type="text" name="icon" class="gm-input" value="${t ? t.icon : '📝'}">
          </div>
        </div>
        <div class="gm-form-row">
          <label class="gm-form-label">Descripción</label>
          <textarea name="description" class="gm-input" rows="2">${t ? t.description : ''}</textarea>
        </div>
        <div class="gm-form-grid-3">
          <div class="gm-form-row">
            <label class="gm-form-label">Max Items</label>
            <input type="number" name="max_items" class="gm-input" value="${t?.max_items || ''}" placeholder="6">
          </div>
          <div class="gm-form-row">
            <label class="gm-form-label">Max Words</label>
            <input type="number" name="max_words" class="gm-input" value="${t?.max_words || ''}" placeholder="15">
          </div>
          <div class="gm-form-row">
            <label class="gm-form-label">Max Chars</label>
            <input type="number" name="max_chars" class="gm-input" value="${t?.max_chars || ''}" placeholder="80">
          </div>
        </div>
        <div class="gm-form-grid">
          <div class="gm-form-row">
            <label class="gm-form-label">Prefijo Asset</label>
            <input type="text" name="asset_prefix" class="gm-input" value="${t ? t.asset_prefix : ''}" placeholder="S">
          </div>
          <div class="gm-form-row">
            <label class="gm-form-label">Extensión</label>
            <input type="text" name="asset_ext" class="gm-input" value="${t ? t.asset_ext : ''}" placeholder="png">
          </div>
        </div>
        <div class="gm-form-row">
          <label class="gm-form-label">Sintaxis Parámetros</label>
          <input type="text" name="params_syntax" class="gm-input" value="${t ? t.params_syntax : ''}" placeholder="// @ Título">
        </div>
        <div class="modal-foot" style="padding-top:20px">
          <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
          <button type="submit" class="btn btn-primary">${isNew ? 'Crear' : 'Guardar'}</button>
        </div>
      </form>
    </div>
  `;
  openModal({ html, wide: true });
}

async function saveScreenType(e, id) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData.entries());
  data.has_params = !!data.params_syntax;

  try {
    if (id) await api('PUT', `/api/screen-types/${id}`, data);
    else await api('POST', '/api/screen-types', data);
    toast('Tipo guardado');
    closeModal();
    await loadGmData();
    renderGlobalManager();
  } catch(e) { toast('Error al guardar', false); }
}

async function deleteScreenType(id) {
  if (!confirm('¿Eliminar este tipo de pantalla? Esto puede afectar guiones existentes.')) return;
  try {
    await api('DELETE', `/api/screen-types/${id}`);
    toast('Tipo eliminado');
    await loadGmData();
    renderGlobalManager();
  } catch(e) { toast('Error al eliminar', false); }
}

/* ─── Remotion Template Actions ────────────────────── */

function openEditTemplateModal(t = null) {
  const isNew = !t;
  const title = isNew ? 'Nuevo Template Remotion' : 'Editar Template';
  const html = `
    <div class="modal-title">${esc(title)}</div>
    <div class="modal-body">
      <form id="templateForm" class="gm-form" onsubmit="saveRemotionTemplate(event, ${t ? t.id : 'null'})">
        <div class="gm-form-grid">
          <div class="gm-form-row">
            <label class="gm-form-label">Nombre (ID)</label>
            <input type="text" name="name" class="gm-input" value="${t ? t.name : ''}" placeholder="Ej: TypeWriter" required ${t ? 'readonly' : ''}>
          </div>
          <div class="gm-form-row">
            <label class="gm-form-label">Etiqueta (UI)</label>
            <input type="text" name="label" class="gm-input" value="${t ? t.label : ''}" placeholder="Ej: Terminal" required>
          </div>
        </div>
        <div class="gm-form-row">
          <label class="gm-form-label">Descripción</label>
          <textarea name="description" class="gm-input" rows="2">${t ? t.description : ''}</textarea>
        </div>
        <div class="gm-form-row">
          <label class="gm-form-label">Límites / Guía</label>
          <input type="text" name="limits" class="gm-input" value="${t ? t.limits : ''}" placeholder="Ej: min 3 - max 6">
        </div>
        <div class="gm-form-row">
          <label class="gm-form-label">Data Schema (JSON)</label>
          <textarea name="data_schema" class="gm-input" rows="4" style="font-family:monospace">${t ? t.data_schema : ''}</textarea>
        </div>
        <div class="modal-foot" style="padding-top:20px">
          <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
          <button type="submit" class="btn btn-primary">${isNew ? 'Crear' : 'Guardar'}</button>
        </div>
      </form>
    </div>
  `;
  openModal({ html, wide: true });
}

async function saveRemotionTemplate(e, id) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData.entries());

  try {
    if (id) await api('PUT', `/api/remotion-templates/${id}`, data);
    else await api('POST', '/api/remotion-templates', data);
    toast('Template guardado');
    closeModal();
    await loadGmData();
    renderGlobalManager();
  } catch(e) { toast('Error al guardar', false); }
}

async function deleteRemotionTemplate(id) {
  if (!confirm('¿Eliminar este template?')) return;
  try {
    await api('DELETE', `/api/remotion-templates/${id}`);
    toast('Template eliminado');
    await loadGmData();
    renderGlobalManager();
  } catch(e) { toast('Error al eliminar', false); }
}

/* ═══════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════ */
/* ═══════════════════════════════════════════════════════
   AI WORK MODAL — bloquea toda la UI mientras trabaja la IA
═══════════════════════════════════════════════════════ */
const AIModal = (() => {
  let _open = false;

  const $ = id => document.getElementById(id);

  function show(title, subtitle = '') {
    $('aiModalTitle').textContent    = title;
    $('aiModalSubtitle').textContent = subtitle;
    $('aiModalLog').innerHTML        = '';
    $('aiModalProgress').style.display = 'none';
    $('aiModalBarFill').style.width    = '0%';
    $('aiModalPct').textContent        = '0%';
    $('aiModalFoot').style.display     = 'none';
    // Spinner: spinning state
    $('aiSpinnerRing').className  = 'ai-spinner-ring spinning';
    $('aiSpinnerIcon').textContent = '';
    $('aiModalBackdrop').classList.add('open');
    _open = true;
  }

  function update(msg, pct = null) {
    if (!_open) return;
    if (msg) {
      const log  = $('aiModalLog');
      const line = document.createElement('div');
      line.className   = 'ai-log-line';
      line.textContent = msg;
      log.appendChild(line);
      // Keep last 12 lines
      while (log.children.length > 12) log.removeChild(log.firstChild);
      log.scrollTop = log.scrollHeight;
    }
    if (pct !== null) {
      $('aiModalProgress').style.display = 'flex';
      $('aiModalBarFill').style.width    = `${pct}%`;
      $('aiModalPct').textContent        = `${pct}%`;
    }
  }

  function done(msg = '✅ Completado') {
    if (!_open) return;
    $('aiSpinnerRing').className   = 'ai-spinner-ring';
    $('aiSpinnerIcon').textContent = '✅';
    $('aiModalTitle').textContent  = msg;
    $('aiModalProgress').style.display = 'none';
    setTimeout(close, 1400);
  }

  function error(msg) {
    if (!_open) return;
    $('aiSpinnerRing').className   = 'ai-spinner-ring error-ring';
    $('aiSpinnerIcon').textContent = '❌';
    $('aiModalTitle').textContent  = 'Ocurrió un error';
    const log  = $('aiModalLog');
    const line = document.createElement('div');
    line.className   = 'ai-log-line ai-log-error';
    line.textContent = msg;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
    $('aiModalFoot').style.display = 'flex';
  }

  function close() {
    $('aiModalBackdrop').classList.remove('open');
    _open = false;
  }

  return { show, update, done, error, close };
})();

/* ═══════════════════════════════════════════════════════
   STATISTICS MODAL
═══════════════════════════════════════════════════════ */
async function openStats() {
  if (!S.activeCourse) return toast('Abre un proyecto primero', false);
  openModal({ wide: true, html: `
    <div class="modal-title">📊 Estadísticas — ${esc(S.activeCourse.title)}</div>
    <div class="modal-body stats-modal-body">
      <div class="rp-loading" style="padding:40px">Calculando estadísticas…</div>
    </div>
    <div class="modal-foot">
      <button class="btn btn-ghost" onclick="closeModal()">Cerrar</button>
      <button class="btn btn-ghost" onclick="openStats()">↻ Actualizar</button>
    </div>` });

  try {
    const d = await api('GET', `/api/courses/${S.activeCourse.id}/stats`);
    document.querySelector('.stats-modal-body').innerHTML = _renderStats(d);
  } catch(e) {
    document.querySelector('.stats-modal-body').innerHTML =
      `<div class="rp-empty">Error cargando estadísticas: ${esc(e.message)}</div>`;
  }
}

function _pct(v, total) { return total ? Math.round(v / total * 100) : 0; }
function _bar(v, total, color = 'var(--accent)') {
  const p = _pct(v, total);
  return `<div class="stat-bar-wrap">
    <div class="stat-bar-fill" style="width:${p}%;background:${color}"></div>
  </div>`;
}
function _fmtN(n) { return n >= 1000 ? (n/1000).toFixed(1)+'k' : String(n); }

function _renderStats(d) {
  const o  = d.overview;
  const pi = d.pipeline;
  const re = d.research;
  const n  = pi.total;

  const PIPE_STEPS = [
    { key: 'guion',         label: '📝 Guion escrito',       color: '#6366f1' },
    { key: 'segments',      label: '🎬 Pantallas segmentadas', color: '#8b5cf6' },
    { key: 'audio',         label: '🎵 Audio cargado',        color: '#06b6d4' },
    { key: 'transcription', label: '🎙️ Whisper completado',   color: '#0ea5e9' },
    { key: 'spell',         label: '✏️ Corrección ortográfica',color: '#f59e0b' },
    { key: 'alignment',     label: '🔗 Alineación completada', color: '#10b981' },
  ];

  const maxST = d.screen_types.length ? d.screen_types[0].count : 1;

  return `
  <!-- ① OVERVIEW CARDS -->
  <div class="stat-section-label">Vista General</div>
  <div class="stat-cards-row">
    ${_statCard('📝', _fmtN(o.total_words), 'Palabras totales', `${_fmtN(o.avg_words_per_class)} prom/clase`)}
    ${_statCard('⏱', o.narration_fmt, 'Tiempo de locución', `a ${o.wpm_rate} pal/min`)}
    ${_statCard('🎬', o.video_fmt, 'Video estimado', '+15% transiciones')}
    ${_statCard('📚', o.total_sections, 'Secciones', `${o.avg_classes_per_section} clases/secc. prom.`)}
    ${_statCard('🎓', o.total_classes, 'Clases', `${_fmtN(o.avg_words_per_section)} pal/secc. prom.`)}
    ${_statCard('🖼', o.total_screens, 'Pantallas', `${d.screen_types.length} tipos distintos`)}
  </div>

  <!-- ② DETAIL ROW -->
  <div class="stat-two-col">
    <div class="stat-block">
      <div class="stat-section-label">Distribución de palabras</div>
      <div class="stat-kv-grid">
        <span class="stat-kv-k">Mayor clase</span><span class="stat-kv-v">${_fmtN(o.max_words_class)} pal</span>
        <span class="stat-kv-k">Menor clase</span><span class="stat-kv-v">${_fmtN(o.min_words_class)} pal</span>
        <span class="stat-kv-k">Promedio/clase</span><span class="stat-kv-v">${_fmtN(o.avg_words_per_class)} pal</span>
        <span class="stat-kv-k">Total caracteres</span><span class="stat-kv-v">${_fmtN(o.total_chars)}</span>
        <span class="stat-kv-k">Locución/clase prom.</span><span class="stat-kv-v">${Math.round(o.narration_min/Math.max(n,1)*10)/10} min</span>
      </div>
    </div>
    <div class="stat-block">
      <div class="stat-section-label">Investigación Tavily</div>
      ${re.total === 0
        ? `<div class="rp-empty" style="padding:16px 0">Sin claims verificados</div>`
        : `<div class="stat-research-grid">
            ${_resBadge('✓', re.verified,  'Verificados',  'var(--green)')}
            ${_resBadge('⚠', re.disputed,  'Disputados',   'var(--yellow)')}
            ${_resBadge('?', re.not_found, 'No encontrado','var(--tx3)')}
            ${_resBadge('✕', re.error,     'Error',        'var(--red)')}
          </div>
          <div style="font-size:10px;color:var(--tx3);margin-top:8px">${re.total} claims analizados en total</div>`}
    </div>
  </div>

  <!-- ③ PIPELINE -->
  <div class="stat-section-label">Pipeline de Producción</div>
  <div class="stat-block">
    ${PIPE_STEPS.map(step => {
      const v = pi[step.key];
      return `<div class="stat-pipe-row">
        <span class="stat-pipe-label">${step.label}</span>
        ${_bar(v, n, step.color)}
        <span class="stat-pipe-count">${v}/${n}</span>
        <span class="stat-pipe-pct">${_pct(v,n)}%</span>
      </div>`;
    }).join('')}
  </div>

  <!-- ④ SCREEN TYPES -->
  ${d.screen_types.length ? `
  <div class="stat-section-label">Tipos de Pantalla Utilizados</div>
  <div class="stat-block stat-st-grid">
    ${d.screen_types.map(st => `
      <div class="stat-st-row">
        <span class="stat-st-badge" style="background:${st.color}22;color:${st.color};border-color:${st.color}44">${st.icon} ${st.name}</span>
        <div class="stat-bar-wrap" style="flex:1">
          <div class="stat-bar-fill" style="width:${Math.round(st.count/maxST*100)}%;background:${st.color}"></div>
        </div>
        <span class="stat-st-count">${st.count}</span>
      </div>`).join('')}
  </div>` : ''}

  <!-- ⑤ PER-SECTION TABLE -->
  <div class="stat-section-label">Detalle por Sección</div>
  ${d.sections.map(sec => `
    <div class="stat-block stat-section-block">
      <div class="stat-sec-hdr">
        <span class="stat-sec-title">${esc(sec.title)}</span>
        <span class="stat-sec-meta">${sec.class_count} clases · ${_fmtN(sec.words)} pal · ${sec.narration_min}min loc. · ${sec.video_min}min video</span>
      </div>
      <table class="stat-cls-table">
        <thead><tr>
          <th>Clase</th><th>Palabras</th><th>Locución</th><th>Pipeline</th>
        </tr></thead>
        <tbody>
          ${sec.classes.map(cls => `
            <tr>
              <td class="stat-cls-name">${esc(cls.title)}</td>
              <td class="stat-cls-num">${_fmtN(cls.words)}</td>
              <td class="stat-cls-num">${cls.narration_min}min</td>
              <td><div class="stat-stage-dots">${_stageDots(cls.flags)}</div></td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`).join('')}
  `;
}

function _statCard(icon, value, label, sub) {
  return `<div class="stat-card">
    <div class="stat-card-icon">${icon}</div>
    <div class="stat-card-value">${value}</div>
    <div class="stat-card-label">${label}</div>
    <div class="stat-card-sub">${sub}</div>
  </div>`;
}

function _resBadge(icon, count, label, color) {
  return `<div class="stat-res-item">
    <span class="stat-res-icon" style="color:${color}">${icon}</span>
    <span class="stat-res-count">${count}</span>
    <span class="stat-res-label">${label}</span>
  </div>`;
}

function _stageDots(flags) {
  const steps = [
    { key: 'guion',         color: '#6366f1', title: 'Guion' },
    { key: 'segments',      color: '#8b5cf6', title: 'Pantallas' },
    { key: 'transcription', color: '#0ea5e9', title: 'Whisper' },
    { key: 'spell',         color: '#f59e0b', title: 'Corrección' },
    { key: 'alignment',     color: '#10b981', title: 'Alineación' },
  ];
  return steps.map(s =>
    `<span class="stat-dot ${flags[s.key] ? 'done' : ''}" style="${flags[s.key] ? `background:${s.color}` : ''}" title="${s.title}"></span>`
  ).join('');
}

document.addEventListener('DOMContentLoaded', async () => {
  // Theme
  applyTheme(localStorage.getItem('vc_theme') || 'dark');

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); doSave(false); }
    if (e.key === 'Escape') closeModal();
  });

  // Load courses
  try {
    S.courses = await api('GET', '/api/courses');
  } catch(e) { /* ignore on startup */ }

  renderSidebarPicker();
  renderContent('welcome');
  updateBreadcrumb();
});

/* ═══════════════════════════════════════════════════════
   GLOBAL CONFIG — Tipos de Pantalla & Templates Remotion
═══════════════════════════════════════════════════════ */
const GC = { screenTypes: [], remotionTemplates: [], activeTab: 'types' };

async function openGlobalConfig() {
  document.getElementById('globalConfigPanel').classList.add('open');
  document.getElementById('globalConfigBackdrop').classList.add('open');
  document.getElementById('globalConfigBtn').classList.add('active');
  if (!GC.screenTypes.length) {
    try { GC.screenTypes = await api('GET', '/api/screen-types'); } catch(e) {}
  }
  if (!GC.remotionTemplates.length) {
    try { GC.remotionTemplates = await api('GET', '/api/remotion-templates'); } catch(e) {}
  }
  renderGcTab(GC.activeTab);
}

function closeGlobalConfig() {
  document.getElementById('globalConfigPanel').classList.remove('open');
  document.getElementById('globalConfigBackdrop').classList.remove('open');
  document.getElementById('globalConfigBtn').classList.remove('active');
}

function switchGcTab(tab) {
  GC.activeTab = tab;
  document.querySelectorAll('.gc-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  renderGcTab(tab);
}

function renderGcTab(tab) {
  const container = document.getElementById('gcContent');
  if (tab === 'types') renderGcTypes(container);
  else renderGcRemotionTemplates(container);
}

function renderGcTypes(container) {
  const gr = {};
  for (const t of GC.screenTypes) {
    if (!gr[t.category]) gr[t.category] = [];
    gr[t.category].push(t);
  }
  container.innerHTML = '<div class="gc-list" id="gcTypeList"></div>';
  const list = document.getElementById('gcTypeList');
  const CAT_LABELS = { layout: '📐 Layout', dynamic: '⚡ Dynamic', rendering: '🎬 Rendering Engine' };
  for (const cat of ['layout', 'dynamic', 'rendering']) {
    if (!gr[cat]) continue;
    list.insertAdjacentHTML('beforeend', `<div class="gc-category">${CAT_LABELS[cat]}</div>`);
    for (const t of gr[cat]) {
      list.insertAdjacentHTML('beforeend', `
        <div class="gc-row ${t.enabled ? '' : 'disabled'}" id="gcType_${t.id}">
          <div class="gc-badge" style="background:${t.color}22;color:${t.color}">${t.icon}</div>
          <div class="gc-row-info">
            <div class="gc-row-name">${esc(t.label)} <span class="gc-row-tag">${esc(t.name)}</span></div>
            <div class="gc-row-desc">${esc(t.description)}</div>
            ${t.has_params ? `<div class="gc-row-params">${esc(t.params_syntax)}</div>` : ''}
          </div>
          <label class="toggle">
            <input type="checkbox" ${t.enabled ? 'checked' : ''} onchange="toggleScreenType(${t.id}, this.checked)"/>
            <span class="toggle-track"></span>
          </label>
        </div>`);
    }
  }
}

async function toggleScreenType(id, enabled) {
  try {
    const u = await api('PUT', `/api/screen-types/${id}`, { enabled });
    const t = GC.screenTypes.find(x => x.id === id);
    if (t) t.enabled = u.enabled;
    const row = document.getElementById(`gcType_${id}`);
    if (row) row.classList.toggle('disabled', !u.enabled);
    toast(u.enabled ? `${u.label} activado` : `${u.label} desactivado`);
  } catch(e) { toast('Error al actualizar tipo', false); }
}

function renderGcRemotionTemplates(container) {
  const gr = {};
  for (const t of GC.remotionTemplates) {
    const c = t.category || 'otros';
    if (!gr[c]) gr[c] = [];
    gr[c].push(t);
  }
  container.innerHTML = '<div class="gc-list" id="gcTplList"></div>';
  const list = document.getElementById('gcTplList');
  const REM_CAT = { narrativo: '🎭 Narrativos', flujo: '🔀 Flujo / Proceso', datos: '📊 Datos', clasificacion: '🗂 Clasificación' };
  for (const cat of ['narrativo', 'flujo', 'datos', 'clasificacion']) {
    if (!gr[cat]) continue;
    list.insertAdjacentHTML('beforeend', `<div class="gc-tpl-cat">${REM_CAT[cat] || cat}<span></span></div>`);
    for (const t of gr[cat]) {
      list.insertAdjacentHTML('beforeend', `
        <div class="gc-tpl-row ${t.enabled ? '' : 'disabled'}" id="gcTpl_${t.id}">
          <div class="gc-tpl-info">
            <div class="gc-tpl-name">${esc(t.name)} <span class="gc-row-tag" style="font-size:9px">$${esc(t.name)}</span></div>
            <div class="gc-tpl-desc">${esc(t.description)}</div>
            ${t.limits ? `<div class="gc-tpl-limits">📏 ${esc(t.limits)}</div>` : ''}
          </div>
          <label class="toggle">
            <input type="checkbox" ${t.enabled ? 'checked' : ''} onchange="toggleRemotionTemplate(${t.id}, this.checked)"/>
            <span class="toggle-track"></span>
          </label>
        </div>`);
    }
  }
}

async function toggleRemotionTemplate(id, enabled) {
  try {
    const u = await api('PUT', `/api/remotion-templates/${id}`, { enabled });
    const t = GC.remotionTemplates.find(x => x.id === id);
    if (t) t.enabled = u.enabled;
    const row = document.getElementById(`gcTpl_${id}`);
    if (row) row.classList.toggle('disabled', !u.enabled);
    toast(u.enabled ? `${u.name} activado` : `${u.name} desactivado`);
  } catch(e) { toast('Error al actualizar template', false); }
}

