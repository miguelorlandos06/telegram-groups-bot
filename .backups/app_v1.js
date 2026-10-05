// ============================================
// DIRECTORIO TELEGRAM - MINI APP
// ============================================

const tg = window.Telegram?.WebApp;
const haptic = tg?.HapticFeedback;

if (tg) {
  tg.ready();
  tg.expand();
  tg.setHeaderColor('#0a0e1a');
  tg.setBackgroundColor('#0a0e1a');
  tg.disableVerticalSwipes?.();
}

// ---------- ESTADO ----------
const state = {
  q: '',
  type: '',
  country: '',
  category: '',
  members_range: '',
  adult: false,
  page: 0,
  per_page: 10,
  total: 0,
  loading: false,
  hasMore: true,
  seenIds: new Set(),
};

let meta = null;
let searchTimeout = null;
let currentFilter = null;

// ---------- ICONOS SVG REUTILIZABLES ----------
const ICON = {
  group: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  channel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg>',
  lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  globe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
  users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
  folder: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
  share: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
};

// ---------- HELPERS ----------
function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function vibrate(style = 'light') {
  try {
    haptic?.impactOccurred(style);
  } catch (e) {}
}

function notify(type = 'success') {
  try {
    haptic?.notificationOccurred(type);
  } catch (e) {}
}

function toast(msg, duration = 1800) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add('hidden'), duration);
}

// ---------- TEMA ----------
function setupTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = saved || (prefersDark ? 'dark' : 'light');
  applyTheme(theme);

  document.getElementById('themeToggle').addEventListener('click', () => {
    vibrate('light');
    const curr = document.documentElement.getAttribute('data-theme');
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
    tg?.setHeaderColor('#0a0e1a');
    tg?.setBackgroundColor('#0a0e1a');
  } else {
    icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
    tg?.setHeaderColor('#f8fafc');
    tg?.setBackgroundColor('#f8fafc');
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
    }, 300);
  });

  clear.addEventListener('click', () => {
    vibrate('light');
    input.value = '';
    clear.classList.add('hidden');
    state.q = '';
    resetAndLoad();
  });
}

// ---------- FILTROS (CHIPS) ----------
function setupChips() {
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      vibrate('light');
      if (chip.dataset.toggle === 'adult') {
        state.adult = !state.adult;
        chip.classList.toggle('active', state.adult);
        resetAndLoad();
        return;
      }
      openSheet(chip.dataset.filter);
    });
  });
}

function openSheet(filter) {
  if (!meta) return;

  const sheet = document.getElementById('sheet');
  const title = document.getElementById('sheetTitle');
  const body = document.getElementById('sheetBody');

  let opts = {};
  let current = '';

  if (filter === 'type') {
    opts = { '': 'Todos', 'group': 'Grupos', 'channel': 'Canales' };
    current = state.type;
  } else if (filter === 'country') {
    opts = { '': 'Todos', ...meta.countries };
    current = state.country;
  } else if (filter === 'category') {
    opts = { '': 'Todas', ...meta.categories };
    current = state.category;
  } else if (filter === 'members_range') {
    opts = { '': 'Todos', ...meta.members_ranges };
    current = state.members_range;
  }

  const labels = {
    type: 'Tipo',
    country: 'País',
    category: 'Categoría',
    members_range: 'Miembros',
  };
  title.textContent = labels[filter] || 'Filtrar';
  currentFilter = filter;

  body.innerHTML = '';
  Object.entries(opts).forEach(([key, label]) => {
    const btn = document.createElement('button');
    btn.className = 'sheet-option' + (key === current ? ' selected' : '');
    btn.textContent = label;
    btn.addEventListener('click', () => {
      vibrate('light');
      state[filter] = key;
      state.page = 0;
      updateChip(filter, key, label);
      closeSheet();
      resetAndLoad();
    });
    body.appendChild(btn);
  });

  sheet.classList.remove('hidden');
}

function updateChip(filter, key, label) {
  const chip = document.querySelector(`.chip[data-filter="${filter}"]`);
  const span = document.getElementById(`chip-${filter}`);
  const defaults = { type: 'Tipo', country: 'País', category: 'Categoría', members_range: 'Miembros' };
  if (key === '') {
    span.textContent = defaults[filter];
    chip.classList.remove('active');
  } else {
    span.textContent = label;
    chip.classList.add('active');
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
  const loadMore = document.getElementById('loadMore');
  const countInfo = document.getElementById('countInfo');

  if (reset) {
    skeleton.classList.remove('hidden');
    empty.classList.add('hidden');
    list.innerHTML = '';
  } else {
    loadMore.classList.remove('hidden');
  }

  const params = new URLSearchParams({
    q: state.q,
    type: state.type,
    country: state.country,
    category: state.category,
    members_range: state.members_range,
    show_adult: state.adult ? '1' : '0',
    page: state.page.toString(),
  });

  try {
    const res = await fetch(`/api/groups?${params}`);
    const data = await res.json();

    skeleton.classList.add('hidden');
    loadMore.classList.add('hidden');

    state.total = data.total;

    if (data.items.length === 0 && state.page === 0) {
      empty.classList.remove('hidden');
      countInfo.textContent = 'Sin resultados';
      return;
    }

    countInfo.textContent = `${data.total} resultados`;

    data.items.forEach((item, idx) => {
      if (state.seenIds.has(item.id)) return;
      state.seenIds.add(item.id);
      const card = renderCard(item, idx);
      list.appendChild(card);
    });

    state.hasMore = data.items.length === state.per_page;
    if (!state.hasMore && state.page > 0) {
      countInfo.textContent = `${data.total} resultados · fin`;
    }
  } catch (e) {
    console.error(e);
    skeleton.classList.add('hidden');
    loadMore.classList.add('hidden');
    toast('Error al cargar');
  } finally {
    state.loading = false;
  }
}

// ---------- RENDER CARD ----------
function renderCard(g, idx) {
  const el = document.createElement('article');
  const isChannel = g.type === 'channel';
  el.className = 'card' + (g.is_adult ? ' card--adult' : '');
  el.style.animationDelay = `${Math.min(idx * 30, 300)}ms`;

  const iconSvg = g.is_adult ? ICON.lock : (isChannel ? ICON.channel : ICON.group);

  const tags = [];
  if (isChannel) tags.push(`<span class="tag tag--channel">${ICON.channel} Canal</span>`);
  else tags.push(`<span class="tag">${ICON.group} Grupo</span>`);
  if (g.country_label) tags.push(`<span class="tag">${ICON.globe} ${escapeHtml(g.country_label)}</span>`);
  if (g.category_label) tags.push(`<span class="tag">${ICON.folder} ${escapeHtml(g.category_label)}</span>`);
  if (g.members_label) tags.push(`<span class="tag">${ICON.users} ${escapeHtml(g.members_label)}</span>`);
  if (g.is_adult) tags.push(`<span class="tag tag--adult">+18</span>`);

  el.innerHTML = `
    <div class="card__header">
      <div class="card__icon">${iconSvg}</div>
      <div class="card__title-wrap">
        <span class="card__title">${escapeHtml(g.title)}</span>
        <div class="card__subtitle">${ICON.users} ${escapeHtml(g.members_label || 'Sin datos')}</div>
      </div>
    </div>
    ${g.description ? `<p class="card__desc">${escapeHtml(g.description)}</p>` : ''}
    <div class="card__tags">${tags.join('')}</div>
    <div class="card__actions">
      <a class="btn" href="${escapeHtml(g.link)}" target="_blank" rel="noopener">
        Abrir en Telegram ${ICON.arrow}
      </a>
      <button class="btn btn--ghost" data-share="${escapeHtml(g.link)}" data-title="${escapeHtml(g.title)}" aria-label="Compartir">
        ${ICON.share}
      </button>
    </div>
  `;

  el.querySelector('[data-share]').addEventListener('click', (e) => {
    e.stopPropagation();
    vibrate('medium');
    const link = e.currentTarget.dataset.share;
    const title = e.currentTarget.dataset.title;
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(title)}`;
    if (tg) {
      tg.openTelegramLink(shareUrl);
    } else {
      window.open(shareUrl, '_blank');
    }
  });

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
  }, { rootMargin: '200px' });
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
  setupChips();
  setupSheet();
  setupInfiniteScroll();
  loadGroups(true);
}

init();
