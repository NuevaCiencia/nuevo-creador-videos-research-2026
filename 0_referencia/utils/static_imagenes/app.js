/* ═══════════════════════════════════════════════════
   PROMPT IMÁGENES — app.js
   ═══════════════════════════════════════════════════ */

'use strict';

// ── Estado global ────────────────────────────────────────────────────────────
let allEntries    = [];    // datos completos cargados del servidor
let activeFilter  = 'all'; // 'all' | 'full' | 'split'
let searchQuery   = '';

// ── Referencias al DOM ──────────────────────────────────────────────────────
const projectSelect = document.getElementById('projectSelect');
const searchInput   = document.getElementById('searchInput');
const statsBar      = document.getElementById('statsBar');
const cardsGrid     = document.getElementById('cardsGrid');
const emptyState    = document.getElementById('emptyState');
const loadingState  = document.getElementById('loadingState');
const errorState    = document.getElementById('errorState');
const errorMsg      = document.getElementById('errorMsg');
const noResults     = document.getElementById('noResults');

const statTotal  = document.getElementById('statTotal').querySelector('.stat-n');
const statFull   = document.getElementById('statFull').querySelector('.stat-n');
const statSplit  = document.getElementById('statSplit').querySelector('.stat-n');
const statSpeech = document.getElementById('statSpeech').querySelector('.stat-n');

const modalOverlay  = document.getElementById('modalOverlay');
const modalBadge    = document.getElementById('modalBadge');
const modalTitle    = document.getElementById('modalTitle');
const modalMeta     = document.getElementById('modalMeta');
const modalPrompt   = document.getElementById('modalPrompt');
const modalSpeech   = document.getElementById('modalSpeech');
const speechSection    = document.getElementById('speechSection');
const copyPromptBtn   = document.getElementById('copyPromptBtn');
const copyCombinedBtn = document.getElementById('copyCombinedBtn');
const fixPromptBtn    = document.getElementById('fixPromptBtn');
const reparadoSection = document.getElementById('reparadoSection');
const modalPromptReparado = document.getElementById('modalPromptReparado');
const copyReparadoBtn = document.getElementById('copyReparadoBtn');
const modalClose       = document.getElementById('modalClose');

let currentEntry      = null; // Para saber qué estamos editando en el modal

// ── Inicialización ───────────────────────────────────────────────────────────
(async function init() {
  await loadProjects();

  // Botones de filtro
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      renderCards();
    });
  });

  // Buscador
  searchInput.addEventListener('input', () => {
    searchQuery = searchInput.value.trim().toLowerCase();
    renderCards();
  });

  // Selector de proyecto
  projectSelect.addEventListener('change', async () => {
    const pid = projectSelect.value;
    if (!pid) {
      allEntries = [];
      showState('empty');
      statsBar.style.display = 'none';
      return;
    }
    await loadProject(pid);
  });

  // Cerrar modal
  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', e => {
    if (e.target === modalOverlay) closeModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  // Copiar prompt
  copyPromptBtn.addEventListener('click', () => {
    copyToClipboard(modalPrompt.textContent, copyPromptBtn);
  });

  // Copiar combinado
  copyCombinedBtn.addEventListener('click', () => {
    const promptText = modalPrompt.textContent;
    const speechText = modalSpeech.textContent || '';
    const combined = `PROMPT: ${promptText}\n\nLOCUCIÓN DEL PROMPT: ${speechText}`;
    copyToClipboard(combined, copyCombinedBtn);
  });

  // Arreglar con IA
  fixPromptBtn.addEventListener('click', async () => {
    if (!currentEntry) return;
    
    const originalText = fixPromptBtn.textContent;
    fixPromptBtn.disabled = true;
    fixPromptBtn.textContent = '🧠 PROCESANDO...';
    
    try {
      const res = await fetch('/api/fix-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectSelect.value,
          image_id: currentEntry.id,
          filename: currentEntry.filename,
          prompt: currentEntry.prompt,
          speech: currentEntry.speech
        })
      });
      
      if (!res.ok) throw new Error('Error en la llamada a la IA');
      
      const data = await res.json();
      const reparado = data.reparado;
      
      // Actualizar UI del modal
      modalPromptReparado.textContent = reparado;
      reparadoSection.style.display = 'flex';
      
      // Actualizar estado local
      currentEntry.prompt_reparado = reparado;
      
      fixPromptBtn.textContent = '✅ REPARADO';
      setTimeout(() => {
        fixPromptBtn.textContent = originalText;
        fixPromptBtn.disabled = false;
      }, 2000);

    } catch (err) {
      alert(`Error al reparar: ${err.message}`);
      fixPromptBtn.textContent = '❌ ERROR';
      setTimeout(() => {
        fixPromptBtn.textContent = originalText;
        fixPromptBtn.disabled = false;
      }, 2000);
    }
  });

  // Copiar reparado
  copyReparadoBtn.addEventListener('click', () => {
    copyToClipboard(modalPromptReparado.textContent, copyReparadoBtn);
  });
})();

// ── Cargar lista de proyectos ─────────────────────────────────────────────────
async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    if (!res.ok) throw new Error('No se pudo obtener la lista de proyectos');
    const projects = await res.json();

    projectSelect.innerHTML = '<option value="">— Seleccionar proyecto —</option>';
    projects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p;
      opt.textContent = p;
      projectSelect.appendChild(opt);
    });

    // Auto-seleccionar si solo hay uno
    if (projects.length === 1) {
      projectSelect.value = projects[0];
      await loadProject(projects[0]);
    }
  } catch (err) {
    console.error('loadProjects:', err);
  }
}

// ── Cargar datos de un proyecto ───────────────────────────────────────────────
async function loadProject(projectId) {
  showState('loading');
  try {
    const res = await fetch(`/api/imagenes/${projectId}`);
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `HTTP ${res.status}`);
    }
    allEntries = await res.json();

    // Actualizar stats
    const stats = computeStats(allEntries);
    updateStatsBar(stats);
    statsBar.style.display = 'flex';

    renderCards();
  } catch (err) {
    showState('error');
    errorMsg.textContent = `Error al cargar el proyecto: ${err.message}`;
    statsBar.style.display = 'none';
  }
}

// ── Calcular estadísticas ─────────────────────────────────────────────────────
function computeStats(entries) {
  return {
    total:      entries.length,
    full:       entries.filter(e => e.kind === 'full').length,
    split:      entries.filter(e => e.kind === 'split').length,
    withSpeech: entries.filter(e => e.speech && e.speech.trim()).length,
  };
}

function updateStatsBar({ total, full, split, withSpeech }) {
  statTotal.textContent  = total;
  statFull.textContent   = full;
  statSplit.textContent  = split;
  statSpeech.textContent = withSpeech;
}

// ── Filtrar entradas ──────────────────────────────────────────────────────────
function filterEntries() {
  return allEntries.filter(e => {
    // Filtro kind
    if (activeFilter !== 'all' && e.kind !== activeFilter) return false;

    // Búsqueda de texto
    if (searchQuery) {
      const haystack = [
        e.id,
        e.filename,
        e.timestamp,
        e.tipo_contenido,
        e.prompt,
        e.speech,
        e.kind,
      ].join(' ').toLowerCase();
      if (!haystack.includes(searchQuery)) return false;
    }

    return true;
  });
}

// ── Renderizar tarjetas ───────────────────────────────────────────────────────
function renderCards() {
  const filtered = filterEntries();

  if (filtered.length === 0 && allEntries.length > 0) {
    showState('noResults');
    return;
  }

  if (filtered.length === 0) {
    showState('empty');
    return;
  }

  showState('grid');
  cardsGrid.innerHTML = '';

  filtered.forEach((entry, idx) => {
    const card = buildCard(entry, idx);
    cardsGrid.appendChild(card);
  });
}

// ── Construir una tarjeta ─────────────────────────────────────────────────────
function buildCard(entry, idx) {
  const card = document.createElement('div');
  card.className = 'card';
  card.style.animationDelay = `${Math.min(idx * 30, 300)}ms`;

  const kindLabel = entry.kind === 'full' ? 'Full' : 'Split';
  const kindClass = entry.kind === 'full' ? 'badge-full' : 'badge-split';
  const tipoLabel = entry.tipo_contenido || '';

  const promptPreview = entry.prompt
    ? truncate(entry.prompt, 240)
    : '<em style="color:var(--text-3)">Sin prompt</em>';

  const speechHTML = entry.speech
    ? `<div class="card-speech-preview">"${truncate(entry.speech, 120)}"</div>`
    : `<div class="card-speech-empty">Sin speech en guion</div>`;

  card.innerHTML = `
    <div class="card-head">
      <span class="card-id">${escapeHtml(entry.filename)}</span>
      <div class="card-badges">
        <span class="badge ${kindClass}">${kindLabel}</span>
        ${tipoLabel ? `<span class="badge badge-tipo">${escapeHtml(tipoLabel)}</span>` : ''}
      </div>
    </div>

    <div class="card-meta">
      <div class="meta-item">
        <span class="meta-label">⏱</span>
        <span class="meta-val">${entry.timestamp ? `[${entry.timestamp}]` : '—'}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">⏳</span>
        <span class="meta-val">${entry.duration ? `${entry.duration}s` : '—'}</span>
      </div>
    </div>

    <div>
      <div class="card-prompt-label">Prompt</div>
      <div class="card-prompt-preview">${promptPreview}</div>
    </div>

    ${speechHTML}
  `;

  card.addEventListener('click', () => openModal(entry));
  return card;
}

// ── Modal de detalle ──────────────────────────────────────────────────────────
function openModal(entry) {
  currentEntry = entry;
  const kindLabel = entry.kind === 'full' ? 'Full' : 'Split';
  const kindClass = entry.kind === 'full' ? 'badge-full' : 'badge-split';

  modalBadge.className = `modal-badge ${kindClass}`;
  modalBadge.textContent = `Imagen ${kindLabel}`;

  modalTitle.textContent = entry.filename;

  // Meta
  const metas = [];
  if (entry.timestamp)      metas.push(`<span>⏱ Segmento: <strong>[${entry.timestamp}]</strong></span>`);
  if (entry.duration)       metas.push(`<span>⏳ Duración: <strong>${entry.duration}s</strong></span>`);
  if (entry.tipo_contenido) metas.push(`<span>🏷 Tipo: <strong>${escapeHtml(entry.tipo_contenido)}</strong></span>`);
  if (entry.asset_ref)      metas.push(`<span>📁 Asset: <strong>${escapeHtml(entry.asset_ref)}</strong></span>`);
  modalMeta.innerHTML = metas.join('');

  // Prompt Original
  modalPrompt.textContent = entry.prompt || '(Sin prompt)';

  // Prompt Reparado (IA)
  if (entry.prompt_reparado && entry.prompt_reparado.trim()) {
    reparadoSection.style.display = 'flex';
    modalPromptReparado.textContent = entry.prompt_reparado;
  } else {
    reparadoSection.style.display = 'none';
    modalPromptReparado.textContent = '';
  }

  // Speech
  if (entry.speech && entry.speech.trim()) {
    speechSection.style.display = 'flex';
    modalSpeech.textContent = entry.speech;
  } else {
    speechSection.style.display = 'none';
  }

  modalOverlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  // Reset botones copiar
  [copyPromptBtn, copyCombinedBtn, copyReparadoBtn].forEach(btn => {
    if (!btn) return;
    const labels = {
        'copyPromptBtn': '📋 Copiar Prompt',
        'copyCombinedBtn': '🔗 Copiar Prompt + Locución',
        'copyReparadoBtn': '📋 Copiar Reparado'
    };
    btn.textContent = labels[btn.id] || 'Copiar';
    btn.classList.remove('copied');
  });
}

function closeModal() {
  modalOverlay.style.display = 'none';
  document.body.style.overflow = '';
}

// ── Gestión de estados de la UI ───────────────────────────────────────────────
function showState(state) {
  emptyState.style.display   = 'none';
  loadingState.style.display = 'none';
  errorState.style.display   = 'none';
  cardsGrid.style.display    = 'none';
  noResults.style.display    = 'none';

  switch (state) {
    case 'empty':     emptyState.style.display   = 'flex';  break;
    case 'loading':   loadingState.style.display = 'flex';  break;
    case 'error':     errorState.style.display   = 'flex';  break;
    case 'grid':      cardsGrid.style.display    = 'grid';  break;
    case 'noResults': noResults.style.display    = 'flex';  break;
  }
}

// ── Utilidades ────────────────────────────────────────────────────────────────
function copyToClipboard(text, btn) {
  const originalText = btn.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '✅ ¡Copiado!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = originalText;
      btn.classList.remove('copied');
    }, 2000);
  });
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '…' : str;
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
