/**
 * Football Analytics – minimal frontend.
 * Uses fetch() with X-API-Key for /api/v1/players and /api/v1/favourite-lists.
 */

const API_BASE = window.API_BASE || '';
const API_KEY_STORAGE = 'football_api_key';

function getApiKey() {
  return localStorage.getItem(API_KEY_STORAGE) || window.API_KEY || '';
}

function setApiKey(key) {
  if (key && key.trim()) {
    localStorage.setItem(API_KEY_STORAGE, key.trim());
    return true;
  }
  return false;
}

function apiHeaders() {
  const key = getApiKey();
  const h = { 'Content-Type': 'application/json' };
  if (key) h['X-API-Key'] = key;
  return h;
}

function showEl(id, show) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle('hidden', !show);
}

function showError(containerId, message) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.textContent = message || '';
  el.classList.toggle('hidden', !message);
}

// ----- API key bar -----
function initApiKeyBar() {
  const bar = document.getElementById('api-key-bar');
  const input = document.getElementById('api-key-input');
  const saveBtn = document.getElementById('api-key-save');
  const status = document.getElementById('api-key-status');
  if (!bar || !input || !saveBtn) return;
  if (getApiKey()) {
    bar.classList.add('hidden');
  } else {
    bar.classList.remove('hidden');
  }
  saveBtn.addEventListener('click', () => {
    if (setApiKey(input.value)) {
      status.textContent = 'Saved. Reload or use the app.';
      bar.classList.add('hidden');
      loadPlayers();
      loadLists();
    }
  });
}

// ----- Players -----
let playersPage = 1;
let playersTotalPages = 1;

async function loadPlayers() {
  const key = getApiKey();
  if (!key) {
    document.getElementById('api-key-bar')?.classList.remove('hidden');
    return;
  }
  const sortBy = document.getElementById('players-sort')?.value || 'name';
  const order = document.getElementById('players-order')?.value || 'asc';
  showError('players-error', '');
  showEl('players-loading', true);
  showEl('players-table-wrap', false);
  try {
    const qs = new URLSearchParams({
      page: playersPage,
      limit: 20,
      sort_by: sortBy,
      order,
    }).toString();
    const res = await fetch(`${API_BASE}/api/v1/players?${qs}`, { headers: apiHeaders() });
    if (res.status === 401) {
      showError('players-error', 'Invalid or missing API key.');
      return;
    }
    if (!res.ok) {
      showError('players-error', `Error ${res.status}`);
      return;
    }
    const data = await res.json();
    playersTotalPages = data.total_pages || 1;
    renderPlayersTable(data.data || []);
    document.getElementById('players-page-info').textContent =
      `Page ${data.page} of ${playersTotalPages} (${data.total_count} total)`;
    const prevBtn = document.getElementById('players-prev');
    const nextBtn = document.getElementById('players-next');
    if (prevBtn) prevBtn.disabled = data.page <= 1;
    if (nextBtn) nextBtn.disabled = data.page >= playersTotalPages;
    showEl('players-table-wrap', true);
  } catch (e) {
    showError('players-error', e.message || 'Request failed');
  } finally {
    showEl('players-loading', false);
  }
}

function renderPlayersTable(rows) {
  const tbody = document.getElementById('players-tbody');
  if (!tbody) return;
  tbody.innerHTML = rows
    .map(
      (p) =>
        `<tr>
          <td>${p.player_id}</td>
          <td>${escapeHtml(p.player_name || '')}</td>
          <td>${p.age ?? '—'}</td>
          <td>${escapeHtml((p.position || p.main_position) || '—')}</td>
          <td>${formatNumber(p.market_value)}</td>
          <td>${formatNumber(p.minutes_played)}</td>
        </tr>`
    )
    .join('');
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function formatNumber(n) {
  if (n == null) return '—';
  const num = Number(n);
  if (isNaN(num)) return '—';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'k';
  return String(num);
}

function initPlayers() {
  document.getElementById('players-load')?.addEventListener('click', () => {
    playersPage = 1;
    loadPlayers();
  });
  document.getElementById('players-prev')?.addEventListener('click', () => {
    if (playersPage > 1) {
      playersPage--;
      loadPlayers();
    }
  });
  document.getElementById('players-next')?.addEventListener('click', () => {
    if (playersPage < playersTotalPages) {
      playersPage++;
      loadPlayers();
    }
  });
  if (getApiKey()) loadPlayers();
}

// ----- Favourite lists -----
let currentListId = null;

async function loadLists() {
  const key = getApiKey();
  if (!key) return;
  showError('lists-error', '');
  showEl('lists-loading', true);
  try {
    const res = await fetch(`${API_BASE}/api/v1/favourite-lists`, { headers: apiHeaders() });
    if (res.status === 401) {
      showError('lists-error', 'Invalid or missing API key.');
      return;
    }
    if (!res.ok) {
      showError('lists-error', `Error ${res.status}`);
      return;
    }
    const lists = await res.json();
    renderLists(lists);
  } catch (e) {
    showError('lists-error', e.message || 'Request failed');
  } finally {
    showEl('lists-loading', false);
  }
}

function renderLists(lists) {
  const ul = document.getElementById('lists-list');
  if (!ul) return;
  ul.innerHTML = (lists || [])
    .map(
      (l) =>
        `<li>
          <span>${escapeHtml(l.name)}</span>
          <button type="button" data-list-id="${l.id}" data-list-name="${escapeHtml(l.name)}" class="btn-view">View players</button>
        </li>`
    )
    .join('');
  ul.querySelectorAll('.btn-view').forEach((btn) => {
    btn.addEventListener('click', () => {
      currentListId = parseInt(btn.dataset.listId, 10);
      document.getElementById('list-detail-name').textContent = btn.dataset.listName || '';
      document.getElementById('list-detail').classList.remove('hidden');
      loadListPlayers(currentListId);
    });
  });
}

async function loadListPlayers(listId) {
  if (!listId) return;
  const res = await fetch(
    `${API_BASE}/api/v1/favourite-lists/${listId}/players?sort_by=name`,
    { headers: apiHeaders() }
  );
  if (!res.ok) return;
  const players = await res.json();
  const ul = document.getElementById('list-players');
  if (!ul) return;
  ul.innerHTML = (players || [])
    .map(
      (p) =>
        `<li>
          ${escapeHtml(p.player_name)} (${p.player_id})
          <button type="button" data-player-id="${p.player_id}" class="btn-remove">Remove</button>
        </li>`
    )
    .join('');
  ul.querySelectorAll('.btn-remove').forEach((b) => {
    b.addEventListener('click', () => removePlayerFromList(listId, parseInt(b.dataset.playerId, 10)));
  });
}

async function removePlayerFromList(listId, playerId) {
  const res = await fetch(
    `${API_BASE}/api/v1/favourite-lists/${listId}/players/${playerId}`,
    { method: 'DELETE', headers: apiHeaders() }
  );
  if (res.ok) loadListPlayers(listId);
}

document.getElementById('list-create')?.addEventListener('click', async () => {
  const input = document.getElementById('list-name-input');
  const name = input?.value?.trim();
  if (!name) return;
  showError('lists-error', '');
  try {
    const res = await fetch(`${API_BASE}/api/v1/favourite-lists`, {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({ name }),
    });
    if (res.status === 401) {
      showError('lists-error', 'Invalid or missing API key.');
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showError('lists-error', err.detail?.message || `Error ${res.status}`);
      return;
    }
    input.value = '';
    loadLists();
  } catch (e) {
    showError('lists-error', e.message);
  }
});

document.getElementById('add-player-btn')?.addEventListener('click', async () => {
  if (!currentListId) return;
  const input = document.getElementById('add-player-id');
  const playerId = parseInt(input?.value, 10);
  if (!playerId) return;
  showError('lists-error', '');
  try {
    const res = await fetch(
      `${API_BASE}/api/v1/favourite-lists/${currentListId}/players`,
      {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify({ player_id: playerId }),
      }
    );
    if (res.status === 401) {
      showError('lists-error', 'Invalid or missing API key.');
      return;
    }
    if (res.status === 404) {
      showError('lists-error', 'List or player not found.');
      return;
    }
    if (res.status === 409) {
      showError('lists-error', 'Player already in list.');
      return;
    }
    if (!res.ok) {
      showError('lists-error', `Error ${res.status}`);
      return;
    }
    input.value = '';
    loadListPlayers(currentListId);
  } catch (e) {
    showError('lists-error', e.message);
  }
});

function initLists() {
  if (getApiKey()) loadLists();
}

// ----- Init -----
document.addEventListener('DOMContentLoaded', () => {
  initApiKeyBar();
  initPlayers();
  initLists();
});
