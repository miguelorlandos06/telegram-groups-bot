// ============================================
// DIRECTORIO - MINI APP MINIMALISTA
// ============================================

const tg = window.Telegram?.WebApp;
const haptic = tg?.HapticFeedback;

if (tg) {
  tg.ready();
  tg.expand();
  tg.disableVerticalSwipes?.();
}

// ---------- ESTADO ----------
const state = {
  q: '', type: '', country: '', category: '',
  adult: false, page: 0, per_page: 10, total: 0,
  loading: false, hasMore: true,
  seenIds: new Set(),
};

let meta = null;
let searchTimeout = null;

// ---------- ICONOS SVG (trazo fino) ----------
const ICON = {
  group: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  channel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>',
  lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  globe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
  folder: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
};

// ---------- HELPERS ----------
function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function vibrate(style = 'light') {
  try { haptic?.impactOccurred(style); } catch (e) {}
}

function toast(msg, ms = 1600) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add('hidden'), ms);
}

// ---------- TEMA ----------
function setupTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  applyTheme(theme);

  document.getElementById('themeToggle').addEventListener('click', () => {
    vibrate('light');
    const curr = document.documentElement.getAttribute('data-theme') || 'light';
    const next = curr === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('theme', next);
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (theme === 'dark') {
    icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
    tg?.setHeaderColor('#0a0a0a');
    tg?.setBackgroundColor('#0a0a0a');
  } else {
    icon.innerHTML = '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>';
    tg?.setHeaderColor('#ffffff');
    tg?.setBackgroundColor('#ffffff');
  }
}

// ---------- SEARCH ----------
function setupSearch() {
  const input = document.getElementById('searchInput');
  const clear = document.getElementById('searchClear');

  input.addEventListener('input', (e) => {
    clear.classList.toggle('hidden', !e.target.value);
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.q = e.target.value.trim();
      resetAndLoad();
    }, 280);
  });

  clear.addEventListener('click', () => {
    vibrate('light');
    input.value = '';
    clear.classList.add('hidden');
    state.q = '';
    resetAndLoad();
  });
}

// ---------- TABS / FILTROS ----------
function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      vibrate('light');
      if (tab.dataset.toggle === 'adult') {
        state.adult = !state.adult;
        tab.classList.toggle('active', state.adult);
        resetAndLoad();
        return;
      }
      openSheet(tab.dataset.filter);
    });
  });
}

function openSheet(filter) {
  if (!meta) return;
  const sheet = document.getElementById('sheet');
  const title = document.getElementById('sheetTitle');
  const body = document.getElementById('sheetBody');

  let opts = {}, current = '';

  if (filter === 'type') {
    opts = { '': 'Todos', 'group': 'Grupos', 'channel': 'Canales' };
    current = state.type;
  } else if (filter === 'country') {
    opts = { '': 'Todos', ...meta.countries };
    current = state.country;
  } else if (filter === 'category') {
    opts = { '': 'Todas', ...meta.categories };
    current = state.category;
  }

  title.textContent = { type: 'Tipo', country: 'País', category: 'Categoría' }[filter] || 'Filtrar';

  body.innerHTML = '';
  Object.entries(opts).forEach(([key, label]) => {
    const btn = document.createElement('button');
    btn.className = 'sheet-option' + (key === current ? ' selected' : '');
    btn.textContent = label;
    btn.addEventListener('click', () => {
      vibrate('light');
      state[filter] = key;
      state.page = 0;
      updateTab(filter, key, label);
      closeSheet();
      resetAndLoad();
    });
    body.appendChild(btn);
  });

  sheet.classList.remove('hidden');
}

function updateTab(filter, key, label) {
  const tab = document.querySelector(`.tab[data-filter="${filter}"]`);
  const span = document.getElementById(`tab-${filter}`);
  const defaults = { type: 'Todos', country: 'País', category: 'Categoría' };
  if (key === '') {
    span.textContent = defaults[filter];
    tab.classList.remove('active');
  } else {
    span.textContent = label;
    tab.classList.add('active');
  }
}

function closeSheet() {
  document.getElementById('sheet').classList.add('hidden');
}

function setupSheet() {
  document.getElementById('sheetBackdrop').addEventListener('click', closeSheet);
  document.getElementById('sheetClose').addEventListener('click', closeSheet);
}

// ---------- CARGA ----------
function resetAndLoad() {
  state.page = 0;
  state.hasMore = true;
  state.seenIds.clear();
  document.getElementById('list').innerHTML = '';
  loadGroups(true);
}

async function loadGroups(reset = false) {
  if (state.loading) return;
  state.loading = true;

  const list = document.getElementById('list');
  const skeleton = document.getElementById('skeleton');
  const empty = document.getElementById('empty');
  const spinner = document.getElementById('spinner');
  const status = document.getElementById('status');

  if (reset) {
    skeleton.classList.remove('hidden');
    empty.classList.add('hidden');
    list.innerHTML = '';
  } else {
    spinner.classList.remove('hidden');
  }

  const params = new URLSearchParams({
    q: state.q,
    type: state.type,
    country: state.country,
    category: state.category,
    show_adult: state.adult ? '1' : '0',
    page: state.page.toString(),
  });

  try {
    const res = await fetch(`/api/groups?${params}`);
    const data = await res.json();

    skeleton.classList.add('hidden');
    spinner.classList.add('hidden');

    state.total = data.total;

    if (data.items.length === 0 && state.page === 0) {
      empty.classList.remove('hidden');
      status.textContent = '';
      return;
    }

    status.textContent = `${data.total} ${data.total === 1 ? 'resultado' : 'resultados'}`;

    data.items.forEach((item, idx) => {
      if (state.seenIds.has(item.id)) return;
      state.seenIds.add(item.id);
      list.appendChild(renderCard(item, idx));
    });

    state.hasMore = data.items.length === state.per_page;
  } catch (e) {
    console.error(e);
    skeleton.classList.add('hidden');
    spinner.classList.add('hidden');
    toast('Error al cargar');
  } finally {
    state.loading = false;
  }
}

// ---------- RENDER ----------
function renderCard(g, idx) {
  const el = document.createElement('article');
  const isChannel = g.type === 'channel';
  el.className = 'card' + (g.is_adult ? ' card--adult' : '');
  el.style.animationDelay = `${Math.min(idx * 20, 200)}ms`;

  const iconSvg = g.is_adult ? ICON.lock : (isChannel ? ICON.channel : ICON.group);

  const meta = [];
  if (isChannel) meta.push(`<span class="card__meta-item">${ICON.channel} Canal</span>`);
  else meta.push(`<span class="card__meta-item">${ICON.group} Grupo</span>`);
  if (g.country_label) meta.push(`<span class="card__meta-item">${ICON.globe} ${escapeHtml(g.country_label)}</span>`);
  if (g.members_label) meta.push(`<span class="card__meta-item">${ICON.users} ${escapeHtml(g.members_label)}</span>`);
  if (g.is_adult) meta.push(`<span class="card__meta-item card__meta-item--adult">+18</span>`);

  el.innerHTML = `
    <div class="card__icon">${iconSvg}</div>
    <div class="card__body">
      <a class="card__title" href="${escapeHtml(g.link)}" target="_blank" rel="noopener">${escapeHtml(g.title)}</a>
      <div class="card__meta">${meta.join('')}</div>
      ${g.description ? `<p class="card__desc">${escapeHtml(g.description)}</p>` : ''}
    </div>
    <a class="card__action" href="${escapeHtml(g.link)}" target="_blank" rel="noopener" aria-label="Abrir">
      ${ICON.arrow}
    </a>
  `;

  return el;
}

// ---------- INFINITE SCROLL ----------
function setupInfiniteScroll() {
  const sentinel = document.getElementById('sentinel');
  const io = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && state.hasMore && !state.loading) {
      state.page++;
      loadGroups(false);
    }
  }, { rootMargin: '300px' });
  io.observe(sentinel);
}

// ---------- INIT ----------
async function init() {
  try {
    const res = await fetch('/api/meta');
    meta = await res.json();
  } catch (e) {
    console.error('Meta error', e);
  }

  setupTheme();
  setupSearch();
  setupTabs();
  setupSheet();
  setupInfiniteScroll();
  loadGroups(true);
}

init();
