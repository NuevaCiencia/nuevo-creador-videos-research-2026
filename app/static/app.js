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
  const area = document.getElementById('contentArea');
  if (!S.activeClass) { renderContent('welcome'); return; }
  switch(phase) {
    case 'guion':    renderGuion(area);    break;
    case 'audio':    renderPlaceholder(area, '🎙️', 'Fase: Audio', 'Aquí podrás cargar el audio y ejecutar la transcripción con Whisper.'); break;
    case 'visuales': renderPlaceholder(area, '🧠', 'Fase: Visuales', 'Aquí se generará el guion visual enriquecido con IA.'); break;
    case 'video':    renderPlaceholder(area, '🎬', 'Fase: Video', 'Aquí se configurará y lanzará el render final con FFmpeg.'); break;
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
  const cls = S.activeClass;
  S.saveStatus = 'saved';
  area.innerHTML = `
    <div class="guion-view">
      <div class="guion-main">
        <div class="guion-toolbar">
          <div class="guion-toolbar-left">
            <span class="guion-toolbar-label">Locución / Guion</span>
            <span id="guionStats" class="guion-stats">0 palabras · 0 caracteres</span>
          </div>
          <div class="guion-toolbar-actions">
            <button class="btn btn-sm btn-ghost" onclick="runResearch()">🔍 Verificar con IA (Tavily)</button>
            <button class="btn btn-sm btn-primary" onclick="doSave(false)">Guardar Guion</button>
          </div>
        </div>
        <div class="guion-editor-wrap">
          <textarea id="guionTA" class="guion-ta"
            placeholder="Pega aquí tu locución raw..."
            oninput="onGuionInput(this)">${esc(cls.raw_narration || '')}</textarea>
        </div>
      </div>
      <div class="guion-research-panel" id="researchPanel">
        <div class="rp-head">Investigación y Sustento</div>
        <div class="rp-body" id="researchBody">
          <div class="rp-empty">Pulsa "Verificar con IA" para analizar el contenido.</div>
        </div>
      </div>
    </div>`;
  onGuionInput(document.getElementById('guionTA'));
  renderResearchItems();
}

async function runResearch() {
  const cls = S.activeClass;
  if (!cls.raw_narration && !document.getElementById('guionTA').value) {
    return toast('Pega un guion primero', false);
  }
  
  const body = document.getElementById('researchBody');
  body.innerHTML = '<div class="rp-loading">🤖 Analizando y consultando Tavily...</div>';
  
  try {
    const results = await api('POST', `/api/classes/${cls.id}/research`);
    toast('Investigación completada');
    renderResearchItems(results);
  } catch(e) {
    toast('Error en investigación', false);
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
  
  body.innerHTML = items.map(i => `
    <div class="research-item status-${i.status}">
      <div class="ri-head">
        <span class="ri-badge">${i.status.toUpperCase()}</span>
        ${i.confidence ? `<span class="ri-conf" title="Confianza: ${i.confidence}%">${i.confidence}%</span>` : ''}
        <button class="ri-del" onclick="deleteResearchItem(${i.id})">×</button>
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

async function deleteResearchItem(id) {
  if (!confirm('¿Eliminar este hallazgo?')) return;
  await api('DELETE', `/api/research-items/${id}`);
  renderResearchItems();
}


function onGuionInput(el) {
  // update stats
  const text = el.value;
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
    S.activeClass = updated;
    S.saveStatus = 'saved';
    const w = (updated.raw_narration||'').trim().split(/\s+/).filter(Boolean).length;
    setStatus(`${esc(updated.title)} · ${w} palabras`, '✓ Guardado', 'sb-saved');
    // update dot in tree
    const item = document.querySelector(`.tree-class-item[data-cid="${updated.id}"]`);
    if (item) item.classList.toggle('has-content', (updated.raw_narration||'').trim().length > 0);
    if (!silent) toast('Guardado');
  } catch(e) {
    S.saveStatus = 'unsaved';
    setStatus(undefined, '⚠ Error al guardar', 'sb-unsaved');
    if (!silent) toast('Error al guardar', false);
  }
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
  const c = S.courses.find(x => x.id === id);
  openModal({
    title: 'Editar Proyecto',
    fields: [
      { key: 'title',       label: 'Nombre', value: c.title, required: true },
      { key: 'description', label: 'Descripción', value: c.description || '', textarea: true },
    ],
    onConfirm: async v => {
      const updated = await api('PUT', `/api/courses/${id}`, v);
      Object.assign(c, updated);
      if (S.activeCourse?.id === id) {
        S.activeCourse = updated;
        document.querySelector('.tree-course-name').textContent = updated.title;
        updateBreadcrumb();
      }
      closeModal();
      if (!S.activeCourse) renderSidebarPicker();
      toast('Actualizado');
    }
  });
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

