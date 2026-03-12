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
      loadCompetitions();
      loadSeasons();
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
  const competitionId = document.getElementById('players-competition')?.value || '';
  const season = document.getElementById('players-season')?.value || '';
  showError('players-error', '');
  showEl('players-loading', true);
  showEl('players-table-wrap', false);
  try {
    const params = {
      page: playersPage,
      limit: 20,
      sort_by: sortBy,
      order,
    };
    if (competitionId) params.competition_id = competitionId;
    if (season) params.season = season;
    const qs = new URLSearchParams(params).toString();
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
    const ctxEl = document.getElementById('players-filter-context');
    if (ctxEl) {
      const parts = [];
      if (competitionId) {
        const opt = document.getElementById('players-competition')?.selectedOptions?.[0];
        parts.push(opt ? opt.textContent : competitionId);
      }
      if (season) parts.push(`season ${season}`);
      ctxEl.textContent = parts.length ? `Stats for ${parts.join(', ')}` : '';
      ctxEl.classList.toggle('hidden', !parts.length);
    }
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
          <td>${renderPlayerImageCell(p.player_image_url, p.player_name)}</td>
          <td>${escapeHtml(p.player_name || '')}</td>
          <td>${p.age ?? '—'}</td>
          <td>${escapeHtml((p.position || p.main_position) || '—')}</td>
          <td>${escapeHtml(p.foot || '—')}</td>
          <td>${formatNumber(p.market_value)}</td>
          <td>${formatNumber(p.minutes_played)}</td>
          <td>${formatNumber(p.total_goals)}</td>
          <td>${p.total_assists ?? '—'}</td>
          <td>${p.total_cards ?? '—'}</td>
          <td>${p.total_clean_sheets ?? '—'}</td>
          <td>${escapeHtml(p.current_club_name || '—')}</td>
        </tr>`
    )
    .join('');
}

function renderPlayerImageCell(url, name) {
  const safeUrl = typeof url === 'string' && url.startsWith('http') ? url : null;
  if (!safeUrl) {
    const initials = (name || '')
      .split(' ')
      .filter(Boolean)
      .map((part) => part[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
    return `<div class="player-avatar placeholder">${escapeHtml(initials || '?')}</div>`;
  }
  return `<img src="${safeUrl}" alt="${escapeHtml(name || '')}" class="player-avatar">`;
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

async function loadCompetitions() {
  const key = getApiKey();
  if (!key) return;
  const sel = document.getElementById('players-competition');
  if (!sel) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/competitions`, { headers: apiHeaders() });
    if (!res.ok) return;
    const list = await res.json();
    const currentValue = sel.value;
    sel.innerHTML = '<option value="">All leagues</option>' + (list || [])
      .map((c) => `<option value="${escapeHtml(c.competition_id)}">${escapeHtml(c.competition_name || c.competition_id)}</option>`)
      .join('');
    if (currentValue) sel.value = currentValue;
  } catch (_) {}
}

async function loadSeasons() {
  const key = getApiKey();
  if (!key) return;
  const sel = document.getElementById('players-season');
  if (!sel) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/seasons`, { headers: apiHeaders() });
    if (!res.ok) return;
    const list = await res.json();
    const currentValue = sel.value;
    sel.innerHTML = '<option value="">All seasons</option>' + (list || [])
      .map((s) => `<option value="${escapeHtml(s.season_name)}">${escapeHtml(s.season_name)}</option>`)
      .join('');
    if (currentValue) sel.value = currentValue;
  } catch (_) {}
}

function initPlayers() {
  document.getElementById('players-load')?.addEventListener('click', () => {
    playersPage = 1;
    loadPlayers();
  });
  document.getElementById('players-competition')?.addEventListener('change', () => {
    playersPage = 1;
    loadPlayers();
  });
  document.getElementById('players-season')?.addEventListener('change', () => {
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
  if (getApiKey()) {
    loadCompetitions();
    loadSeasons();
    loadPlayers();
  }
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
        `<li data-list-id="${l.id}" data-list-name="${escapeHtml(l.name)}">
          <span>${escapeHtml(l.name)}</span>
          <span class="list-actions">
            <button type="button" data-list-id="${l.id}" data-list-name="${escapeHtml(l.name)}" class="btn-delete">Delete</button>
          </span>
        </li>`
    )
    .join('');
  ul.querySelectorAll('li').forEach((li) => {
    li.addEventListener('click', () => {
      const id = parseInt(li.dataset.listId, 10);
      if (!id) return;
      currentListId = id;
      // highlight selection
      ul.querySelectorAll('li').forEach((other) => other.classList.remove('selected'));
      li.classList.add('selected');
      const name = li.dataset.listName || '';
      document.getElementById('list-detail-name').textContent = name;
      document.getElementById('list-detail').classList.remove('hidden');
      const deleteBtn = document.getElementById('list-delete-btn');
      if (deleteBtn) {
        deleteBtn.dataset.listId = String(id);
        deleteBtn.classList.remove('hidden');
      }
      loadListPlayers(currentListId);
    });
  });
  ul.querySelectorAll('.btn-delete').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteList(parseInt(btn.dataset.listId, 10));
    });
  });
}

async function deleteList(listId) {
  showError('lists-error', '');
  try {
    const res = await fetch(`${API_BASE}/api/v1/favourite-lists/${listId}`, {
      method: 'DELETE',
      headers: apiHeaders(),
    });
    if (res.status === 401) {
      showError('lists-error', 'Invalid or missing API key.');
      return;
    }
    if (res.status === 404) {
      showError('lists-error', 'Favourite list not found.');
      return;
    }
    if (!res.ok) {
      showError('lists-error', `Error ${res.status}`);
      return;
    }
    if (currentListId === listId) {
      document.getElementById('list-detail')?.classList.add('hidden');
      currentListId = null;
      const deleteBtn = document.getElementById('list-delete-btn');
      if (deleteBtn) {
        deleteBtn.classList.add('hidden');
        deleteBtn.dataset.listId = '';
      }
    }
    loadLists();
  } catch (e) {
    showError('lists-error', e.message || 'Request failed');
  }
}

async function loadListPlayers(listId) {
  if (!listId) return;
  const res = await fetch(
    `${API_BASE}/api/v1/favourite-lists/${listId}/players?sort_by=name`,
    { headers: apiHeaders() }
  );
  if (!res.ok) return;
  const players = await res.json();
  const tbody = document.getElementById('list-players');
  if (!tbody) return;
  const count = (players || []).length || 0;
  const metaEl = document.getElementById('list-detail-meta');
  if (metaEl) {
    metaEl.textContent = count ? `${count} player${count === 1 ? '' : 's'} in this list` : 'No players in this list yet.';
  }
  tbody.innerHTML = (players || [])
    .map(
      (p) =>
        `<tr>
          <td>${renderPlayerImageCell(p.player_image_url, p.player_name)}</td>
          <td>${escapeHtml(p.player_name || '')}</td>
          <td>${p.age ?? '—'}</td>
          <td>${escapeHtml((p.position || p.main_position) || '—')}</td>
          <td>${escapeHtml(p.foot || '—')}</td>
          <td>${formatNumber(p.market_value)}</td>
          <td>${formatNumber(p.minutes_played)}</td>
          <td>${formatNumber(p.total_goals)}</td>
          <td>${p.total_assists ?? '—'}</td>
          <td>${p.total_cards ?? '—'}</td>
          <td>${p.total_clean_sheets ?? '—'}</td>
          <td>${escapeHtml(p.current_club_name || '—')}</td>
          <td><button type="button" data-player-id="${p.player_id}" class="btn-remove">Remove</button></td>
        </tr>`
    )
    .join('');
  tbody.querySelectorAll('.btn-remove').forEach((b) => {
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

async function searchPlayersByNameForList(query) {
  const key = getApiKey();
  if (!key) return [];
  const term = (query || '').trim();
  if (!term) return [];
  const params = {
    page: 1,
    limit: 10,
    sort_by: 'name',
    order: 'asc',
    search: term,
  };
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/api/v1/players?${qs}`, { headers: apiHeaders() });
  if (!res.ok) return [];
  const data = await res.json();
  return data.data || [];
}

function renderAddByNameResults(players) {
  const container = document.getElementById('add-by-name-results');
  if (!container) return;
  if (!players.length) {
    container.innerHTML = '<p class="muted">No players found.</p>';
    container.classList.remove('hidden');
    return;
  }
  container.innerHTML =
    '<ul class="add-by-name-list">' +
    players
      .map(
        (p) =>
          `<li class="add-by-name-row" data-player-id="${p.player_id}" role="button" tabindex="0">
            <span>${escapeHtml(p.player_name)} <span class="muted">(${p.player_id})</span></span>
            <span class="add-by-name-add-hint">Add to list</span>
          </li>`
      )
      .join('') +
    '</ul>';
  container.classList.remove('hidden');
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

let addByNameSearchTimer = null;
function initAddByNameSearch() {
  const input = document.getElementById('add-player-name-input');
  const container = document.getElementById('add-by-name-results');
  if (!input || !container) return;
  input.addEventListener('input', () => {
    const query = input.value.trim();
    if (addByNameSearchTimer) clearTimeout(addByNameSearchTimer);
    if (!query) {
      container.classList.add('hidden');
      container.innerHTML = '';
      return;
    }
    addByNameSearchTimer = setTimeout(async () => {
      addByNameSearchTimer = null;
      if (!currentListId) return;
      showError('lists-error', '');
      try {
        const players = await searchPlayersByNameForList(query);
        renderAddByNameResults(players);
      } catch (e) {
        showError('lists-error', e.message || 'Request failed');
      }
    }, 280);
  });
  input.addEventListener('blur', () => {
    if (addByNameSearchTimer) clearTimeout(addByNameSearchTimer);
    addByNameSearchTimer = null;
  });
}

async function addPlayerToListFromRow(playerId) {
  if (!currentListId || !playerId) return;
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
    document.getElementById('add-player-name-input').value = '';
    const container = document.getElementById('add-by-name-results');
    container.classList.add('hidden');
    container.innerHTML = '';
    loadListPlayers(currentListId);
  } catch (e) {
    showError('lists-error', e.message || 'Request failed');
  }
}

document.getElementById('add-by-name-results')?.addEventListener('click', async (e) => {
  const row = e.target.closest('.add-by-name-row');
  if (!row || !currentListId) return;
  const playerId = parseInt(row.dataset.playerId, 10);
  if (!playerId) return;
  await addPlayerToListFromRow(playerId);
});

document.getElementById('add-by-name-results')?.addEventListener('keydown', async (e) => {
  if (e.key !== 'Enter' && e.key !== ' ') return;
  const row = e.target.closest('.add-by-name-row');
  if (!row || !currentListId) return;
  e.preventDefault();
  const playerId = parseInt(row.dataset.playerId, 10);
  if (!playerId) return;
  await addPlayerToListFromRow(playerId);
});

function initLists() {
  if (getApiKey()) loadLists();
  initAddByNameSearch();
}

// Hook up list-level delete button in detail header
document.getElementById('list-delete-btn')?.addEventListener('click', (e) => {
  const btn = e.currentTarget;
  const id = parseInt(btn.dataset.listId || '0', 10);
  if (!id) return;
  deleteList(id);
});

// ----- Init -----
document.addEventListener('DOMContentLoaded', () => {
  initApiKeyBar();
  initPlayers();
  initLists();
});
