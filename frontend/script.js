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
  const sortBy = document.getElementById('players-sort')?.value || 'market_value';
  const order = document.getElementById('players-order')?.value || 'desc';
  const competitionId = document.getElementById('players-competition')?.value || '';
  const season = document.getElementById('players-season')?.value || '';
  const search = document.getElementById('players-search')?.value || '';
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
    if (search.trim()) params.search = search.trim();
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/api/v1/players/?${qs}`, { headers: apiHeaders() });
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
    const pageText = `Page ${data.page} of ${playersTotalPages} (${data.total_count} total)`;
    const prevDisabled = data.page <= 1;
    const nextDisabled = data.page >= playersTotalPages;
    const pageInfoEl = document.getElementById('players-page-info-bottom');
    if (pageInfoEl) pageInfoEl.textContent = pageText;
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
    const prevBtn = document.getElementById('players-prev-bottom');
    const nextBtn = document.getElementById('players-next-bottom');
    if (prevBtn) prevBtn.disabled = prevDisabled;
    if (nextBtn) nextBtn.disabled = nextDisabled;
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
        `<tr data-player-id="${p.player_id || ''}" class="player-row">
          <td>${renderPlayerImageCell(p.player_image_url, stripIdFromName(p.player_name))}</td>
          <td>${escapeHtml(stripIdFromName(p.player_name) || '')}</td>
          <td>${p.age ?? '—'}</td>
          <td>${escapeHtml(
            formatPositionLabel(p.position || p.main_position)
          )}</td>
          <td>${escapeHtml(p.foot || '—')}</td>
          <td>${formatNumber(p.market_value)}</td>
          <td>${formatNumber(p.minutes_played)}</td>
          <td>${formatNumber(p.total_goals)}</td>
          <td>${p.total_assists ?? '—'}</td>
          <td>${p.total_cards ?? '—'}</td>
          <td>${p.total_clean_sheets ?? '—'}</td>
          <td>${renderClubCell(p.current_club_logo_url, p.current_club_name)}</td>
          <td><button type="button" class="btn-add-to-list" data-player-id="${p.player_id}">Add</button></td>
        </tr>`
    )
    .join('');

  // Make each player row clickable to open details modal
  tbody.querySelectorAll('.player-row').forEach((row) => {
    row.addEventListener('click', () => {
      const id = parseInt(row.dataset.playerId || '0', 10);
      if (!id) return;
      openPlayerDetailsModal(id);
    });
  });

  // Wire "Add" buttons to favourite list (uses currentListId if set)
  tbody.querySelectorAll('.btn-add-to-list').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const playerId = parseInt(btn.dataset.playerId || '0', 10);
      if (!playerId) return;
      openListPickerModal(playerId);
    });
  });
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

/** Render current club with optional logo (logo_url from team_details). */
function renderClubCell(logoUrl, clubName) {
  const name = escapeHtml(stripIdFromName(clubName) || '—');
  if (!logoUrl || !String(logoUrl).trim()) return name;
  const safeUrl = String(logoUrl).replace(/[<>"']/g, '');
  return `<span class="club-cell"><img src="${safeUrl}" alt="" class="club-logo" width="20" height="20" referrerpolicy="no-referrer" loading="lazy">${name}</span>`;
}

/** Strip trailing " (number)" from names so IDs are not shown (e.g. "Bologna FC 1909 (1025)" → "Bologna FC 1909"). */
function stripIdFromName(s) {
  if (!s || typeof s !== 'string') return s;
  return s.replace(/\s*\(\d+\)\s*$/, '').trim();
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

function formatPositionLabel(raw) {
  if (!raw) return '—';
  const s = String(raw).toLowerCase().replace(/[-_]/g, ' ').trim();

  // Goalkeepers
  if (s.includes('goalkeeper') || s === 'gk') return 'GK';

  // Full-backs
  if (s.includes('right back') || s === 'rb') return 'RB';
  if (s.includes('left back') || s === 'lb') return 'LB';

  // Centre / central backs
  if (
    s.includes('centre back') ||
    s.includes('center back') ||
    s.includes('central back') ||
    s === 'cb'
  ) {
    return 'CB';
  }

  // Midfielders
  if (s.includes('defensive midfield') || s === 'cdm') return 'CDM';
  if (s.includes('attacking midfield') || s === 'cam') return 'CAM';
  if (s.includes('central midfield') || s.includes('centre midfield') || s === 'cm') return 'CM';
  if (s.includes('midfield') || s === 'mf') return 'MF';

  // Wingers / wide forwards
  if (s.includes('right wing') || s.includes('right winger') || s === 'rw') return 'RW';
  if (s.includes('left wing') || s.includes('left winger') || s === 'lw') return 'LW';
  if (s.includes('winger') || s === 'w') return 'W';

  // Forwards / strikers
  if (s.includes('striker') || s.includes('centre forward') || s.includes('center forward')) {
    return 'ST';
  }
  if (s.includes('forward') || s === 'fw') return 'FW';

  // Fallback to original string
  return raw;
}

// ----- Player details modal -----

function closePlayerDetailsModal() {
  const modal = document.getElementById('player-details-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

function closeListPickerModal() {
  const modal = document.getElementById('list-picker-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

async function openPlayerDetailsModal(playerId) {
  const modal = document.getElementById('player-details-modal');
  if (!modal) return;

  // basic reset
  document.getElementById('player-details-error')?.classList.add('hidden');
  document.getElementById('player-details-error').textContent = '';
  document.getElementById('player-details-chart').innerHTML = '';
  document.getElementById('player-details-chart-empty').classList.remove('hidden');

  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');

  try {
    const res = await fetch(`${API_BASE}/api/v1/players/${playerId}/details`, {
      headers: apiHeaders(),
    });
    if (res.status === 401) {
      showPlayerDetailsError('Invalid or missing API key.');
      return;
    }
    if (res.status === 404) {
      showPlayerDetailsError('Player not found.');
      return;
    }
    if (!res.ok) {
      showPlayerDetailsError(`Error ${res.status}`);
      return;
    }
    const details = await res.json();
    renderPlayerDetails(details);
  } catch (e) {
    showPlayerDetailsError(e.message || 'Request failed');
  }
}

function openListPickerModal(playerId) {
  const modal = document.getElementById('list-picker-modal');
  const body = document.getElementById('list-picker-body');
  const empty = document.getElementById('list-picker-empty');
  if (!modal || !body || !empty) return;

  // Read available lists from existing cards DOM
  const listItems = Array.from(document.querySelectorAll('#lists-list .fav-list-card'));
  if (!listItems.length) {
    // No lists yet: guide user to create one
    closeListPickerModal();
    showError('lists-error', 'You have no favourite lists yet. Create one, then add players.');
    const favTab = document.querySelector('.tab-link[data-tab-target="favourite-lists"]');
    if (favTab) favTab.click();
    const input = document.getElementById('list-name-input');
    if (input) input.focus();
    return;
  }

  body.innerHTML = listItems
    .map(
      (card) =>
        `<li class="list-picker-item">
          <button type="button" class="list-picker-option" data-list-id="${card.dataset.listId}">
            <span class="list-picker-option-name">${escapeHtml(card.dataset.listName || '')}</span>
            <span class="list-picker-option-action" aria-hidden="true">Add to list</span>
          </button>
        </li>`
    )
    .join('');
  empty.classList.add('hidden');

  modal.dataset.playerId = String(playerId);
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');

  body.querySelectorAll('.list-picker-option').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const listId = parseInt(btn.dataset.listId || '0', 10);
      if (!listId || !playerId) return;

      // Update currentListId and visual selection in cards
      currentListId = listId;
      const cards = document.querySelectorAll('#lists-list .fav-list-card');
      cards.forEach((card) => {
        card.classList.toggle('selected', parseInt(card.dataset.listId || '0', 10) === listId);
      });
      const name = btn.dataset.listName || btn.querySelector('.list-picker-option-name')?.textContent || '';
      const nameEl = document.getElementById('list-detail-name');
      if (nameEl) nameEl.textContent = name.trim();
      document.getElementById('list-detail')?.classList.remove('hidden');

      await addPlayerToListFromRow(playerId);
      closeListPickerModal();
    });
  });
}

function showPlayerDetailsError(message) {
  const el = document.getElementById('player-details-error');
  if (!el) return;
  el.textContent = message || '';
  el.classList.toggle('hidden', !message);
}

function renderPlayerDetails(details) {
  if (!details) return;
  const name = stripIdFromName(details.player_name) || 'Unknown player';
  const clubName = stripIdFromName(details.current_club_name) || '—';
  const clubLogoUrl = details.current_club_logo_url || null;
  const positionRaw = details.position || details.main_position || '';
  const position = formatPositionLabel(positionRaw);
  const age = details.age ?? '—';
  const nationality = details.citizenship || '—';
  const value =
    details.current_market_value != null ? formatNumber(details.current_market_value) : '—';

  const avatarContainer = document.getElementById('player-details-avatar');
  if (avatarContainer) {
    avatarContainer.innerHTML = renderPlayerImageCell(details.player_image_url, name);
  }

  const nameEl = document.getElementById('player-details-name');
  if (nameEl) nameEl.textContent = name;

  const metaEl = document.getElementById('player-details-meta');
  if (metaEl) {
    const parts = [];
    if (age !== '—') parts.push(`${age} yrs`);
    if (position !== '—') parts.push(position);
    if (nationality !== '—') parts.push(nationality);
    metaEl.textContent = parts.length ? parts.join(' • ') : '';
  }

  const clubEl = document.getElementById('player-details-club');
  if (clubEl) clubEl.innerHTML = renderClubCell(clubLogoUrl, clubName);

  const posEl = document.getElementById('player-details-position');
  if (posEl) posEl.textContent = position;

  const ageEl = document.getElementById('player-details-age');
  if (ageEl) ageEl.textContent = age;

  const natEl = document.getElementById('player-details-nationality');
  if (natEl) natEl.textContent = nationality;

  const heightEl = document.getElementById('player-details-height');
  if (heightEl) heightEl.textContent = (details.height != null && details.height > 0) ? details.height + ' cm' : '—';

  const valueEl = document.getElementById('player-details-value');
  if (valueEl) valueEl.textContent = value;

  const career = details.career || {};
  const seasons = career.seasons_played ?? 0;
  const clubs = Array.isArray(career.previous_clubs) ? career.previous_clubs : [];
  const careerTextEl = document.getElementById('player-details-career-text');
  const careerClubsEl = document.getElementById('player-details-career-clubs');
  if (careerTextEl) {
    if (!seasons && !clubs.length) {
      careerTextEl.textContent = 'No career summary available.';
      if (careerClubsEl) careerClubsEl.innerHTML = '';
    } else {
      if (seasons) {
        careerTextEl.textContent = `${seasons} season${seasons === 1 ? '' : 's'} recorded.`;
      } else {
        careerTextEl.textContent = '';
      }
      if (careerClubsEl) {
        if (clubs.length) {
          careerClubsEl.innerHTML =
            '<span class="career-clubs-label">Previously at </span>' +
            clubs
              .map((c) => {
                const name = c && typeof c === 'object' && 'club_name' in c ? c.club_name : String(c);
                const logoUrl = c && typeof c === 'object' && 'logo_url' in c ? c.logo_url : null;
                return renderClubCell(logoUrl, name);
              })
              .join('');
          careerClubsEl.classList.remove('hidden');
        } else {
          careerClubsEl.innerHTML = '';
          careerClubsEl.classList.add('hidden');
        }
      }
    }
  }

  const history = Array.isArray(details.market_value_history)
    ? details.market_value_history
    : [];
  if (!history.length) {
    const emptyEl = document.getElementById('player-details-chart-empty');
    if (emptyEl) emptyEl.classList.remove('hidden');
    return;
  }
  const emptyEl = document.getElementById('player-details-chart-empty');
  if (emptyEl) emptyEl.classList.add('hidden');
  renderMarketValueChart(history);
}

/** Short date for chart x-axis (e.g. "Jan '24"). */
function formatChartDate(d) {
  if (!d || !(d instanceof Date) || isNaN(d.getTime())) return '';
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const y = d.getFullYear();
  const yy = String(y).slice(-2);
  return months[d.getMonth()] + " '" + yy;
}

function renderMarketValueChart(points) {
  const container = document.getElementById('player-details-chart');
  if (!container || !points.length) return;

  // Normalise data
  const parsed = points
    .map((p) => {
      const d = new Date(p.date);
      const v = Number(p.value);
      if (!p.date || isNaN(d.getTime()) || isNaN(v)) return null;
      return { date: d, value: v };
    })
    .filter(Boolean)
    .sort((a, b) => a.date - b.date);
  if (!parsed.length) return;

  const minDate = parsed[0].date.getTime();
  const maxDate = parsed[parsed.length - 1].date.getTime();
  const minValue = parsed.reduce((m, p) => Math.min(m, p.value), parsed[0].value);
  const maxValue = parsed.reduce((m, p) => Math.max(m, p.value), parsed[0].value);

  const width = 600;
  const height = 150;
  const paddingLeft = 30;
  const paddingRight = 10;
  const paddingTop = 10;
  const paddingBottom = 24;

  const xSpan = maxDate - minDate || 1;
  const ySpan = maxValue - minValue || 1;

  const xScale = (t) =>
    paddingLeft +
    ((t - minDate) / xSpan) * (width - paddingLeft - paddingRight);
  const yScale = (v) =>
    paddingTop +
    (1 - (v - minValue) / ySpan) * (height - paddingTop - paddingBottom);

  const pathD = parsed
    .map((p, i) => {
      const x = xScale(p.date.getTime());
      const y = yScale(p.value);
      return `${i === 0 ? 'M' : 'L'}${x},${y}`;
    })
    .join(' ');

  // Choose which dates to show on x-axis: all if ≤6, else first + last + evenly spaced in between
  const n = parsed.length;
  let labelIndices;
  if (n <= 6) {
    labelIndices = parsed.map((_, i) => i);
  } else {
    const first = 0;
    const last = n - 1;
    const mid1 = Math.floor(n * 0.25);
    const mid2 = Math.floor(n * 0.5);
    const mid3 = Math.floor(n * 0.75);
    labelIndices = [first, mid1, mid2, mid3, last];
    labelIndices = [...new Set(labelIndices)].sort((a, b) => a - b);
  }

  const xAxisLabels = labelIndices.map((i) => {
    const p = parsed[i];
    return {
      x: xScale(p.date.getTime()),
      text: formatChartDate(p.date),
    };
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <line class="chart-axis" x1="${paddingLeft}" y1="${paddingTop}" x2="${paddingLeft}" y2="${
        height - paddingBottom
      }" />
      <line class="chart-axis" x1="${paddingLeft}" y1="${height - paddingBottom}" x2="${
        width - paddingRight
      }" y2="${height - paddingBottom}" />
      <path class="chart-line" d="${pathD}" />
      ${parsed
        .map((p) => {
          const x = xScale(p.date.getTime());
          const y = yScale(p.value);
          const label = formatNumber(p.value);
          return `
            <circle class="chart-point" cx="${x}" cy="${y}" r="2.5" />
            <text class="chart-label" x="${x}" y="${y - 6}" text-anchor="middle">${label}</text>
          `;
        })
        .join('')}
      ${xAxisLabels
        .map(
          (l) =>
            `<text class="chart-label chart-axis-label" x="${l.x}" y="${height - 6}" text-anchor="middle">${l.text}</text>`
        )
        .join('')}
    </svg>
  `;
}

async function loadCompetitions() {
  const key = getApiKey();
  if (!key) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/competitions`, { headers: apiHeaders() });
    if (!res.ok) return;
    const list = await res.json();
    const selects = [
      document.getElementById('players-competition'),
      document.getElementById('analytics-competition'),
    ].filter(Boolean);
    selects.forEach((sel) => {
      const currentValue = sel.value;
      sel.innerHTML =
        '<option value="">All leagues</option>' +
        (list || [])
          .map(
            (c) =>
              `<option value="${escapeHtml(c.competition_id)}">${escapeHtml(
                stripIdFromName(c.competition_name) || c.competition_id
              )}</option>`
          )
          .join('');
      if (currentValue) sel.value = currentValue;
    });
  } catch (_) {}
}

async function loadSeasons() {
  const key = getApiKey();
  if (!key) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/seasons`, { headers: apiHeaders() });
    if (!res.ok) return;
    const list = await res.json();
    const selects = [
      document.getElementById('players-season'),
      document.getElementById('analytics-season'),
    ].filter(Boolean);
    selects.forEach((sel) => {
      const currentValue = sel.value;
      sel.innerHTML =
        '<option value="">All seasons</option>' +
        (list || [])
          .map(
            (s) =>
              `<option value="${escapeHtml(s.season_name)}">${escapeHtml(s.season_name)}</option>`
          )
          .join('');
      if (currentValue) sel.value = currentValue;
    });
  } catch (_) {}
}

// ----- Analytics -----

async function loadAnalytics() {
  const key = getApiKey();
  if (!key) {
    document.getElementById('api-key-bar')?.classList.remove('hidden');
    return;
  }
  showError('analytics-error', '');
  showEl('analytics-loading', true);

  const competitionId = document.getElementById('analytics-competition')?.value || '';
  const season = document.getElementById('analytics-season')?.value || '';
  const ageLimitRaw = document.getElementById('analytics-age-limit')?.value || '23';
  const ageLimit = Math.min(40, Math.max(10, parseInt(ageLimitRaw || '23', 10) || 23));
  const youngestSort = document.getElementById('analytics-youngest-sort')?.value || 'minutes_desc';

  try {
    const [topScorers, topAssists, topValues, mostMinutes, youngestStars] = await Promise.all([
      fetchAnalytics(`/api/v1/analytics/top-scorers`, { season, competition_id: competitionId }),
      fetchAnalytics(`/api/v1/analytics/top-assists`, { season, competition_id: competitionId }),
      fetchAnalytics(`/api/v1/analytics/top-market-values`, {}),
      fetchAnalytics(`/api/v1/analytics/most-minutes-played`, {
        season,
        competition_id: competitionId,
      }),
      fetchAnalytics(`/api/v1/analytics/youngest-stars`, {
        season,
        competition_id: competitionId,
        age_limit: ageLimit,
      }),
    ]);

    renderAnalyticsTopScorers(topScorers || []);
    renderAnalyticsTopAssists(topAssists || []);
    renderAnalyticsTopValues(topValues || []);
    renderAnalyticsMostMinutes(mostMinutes || []);
    renderAnalyticsYoungestStars(youngestStars || [], youngestSort);
  } catch (e) {
    showError('analytics-error', e.message || 'Failed to load analytics');
  } finally {
    showEl('analytics-loading', false);
  }
}

async function fetchAnalytics(path, params) {
  const qs = new URLSearchParams(
    Object.entries(params || {}).reduce((acc, [k, v]) => {
      if (v != null && String(v).trim() !== '') acc[k] = String(v).trim();
      return acc;
    }, {})
  ).toString();
  const url = `${API_BASE}${path}${qs ? `?${qs}` : ''}`;
  const res = await fetch(url, { headers: apiHeaders() });
  if (res.status === 401) {
    throw new Error('Invalid or missing API key.');
  }
  if (!res.ok) {
    throw new Error(`Analytics error ${res.status}`);
  }
  return res.json();
}

function renderAnalyticsTopScorers(rows) {
  const tbody = document.getElementById('analytics-top-scorers-body');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="muted">No data.</td></tr>';
    return;
  }
  tbody.innerHTML = rows
    .map(
      (r, idx) =>
        `<tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(stripIdFromName(r.player_name))}</td>
          <td>${formatNumber(r.total_goals)}</td>
        </tr>`
    )
    .join('');
}

function renderAnalyticsTopAssists(rows) {
  const tbody = document.getElementById('analytics-top-assists-body');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="muted">No data.</td></tr>';
    return;
  }
  tbody.innerHTML = rows
    .map(
      (r, idx) =>
        `<tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(stripIdFromName(r.player_name))}</td>
          <td>${r.total_assists}</td>
        </tr>`
    )
    .join('');
}

function renderAnalyticsTopValues(rows) {
  const tbody = document.getElementById('analytics-top-values-body');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="muted">No data.</td></tr>';
    return;
  }
  tbody.innerHTML = rows
    .map(
      (r, idx) =>
        `<tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(stripIdFromName(r.player_name))}</td>
          <td>${formatNumber(r.market_value)}</td>
        </tr>`
    )
    .join('');
}

function renderAnalyticsMostMinutes(rows) {
  const tbody = document.getElementById('analytics-most-minutes-body');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="muted">No data.</td></tr>';
    return;
  }
  tbody.innerHTML = rows
    .map(
      (r, idx) =>
        `<tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(stripIdFromName(r.player_name))}</td>
          <td>${formatNumber(r.total_minutes)}</td>
        </tr>`
    )
    .join('');
}

function renderAnalyticsYoungestStars(rows, sortKey) {
  const tbody = document.getElementById('analytics-youngest-stars-body');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="muted">No data.</td></tr>';
    return;
  }
  const sorted = [...rows];
  sorted.sort((a, b) => {
    const am = Number(a.total_minutes) || 0;
    const bm = Number(b.total_minutes) || 0;
    const ag = Number(a.total_goals) || 0;
    const bg = Number(b.total_goals) || 0;
    switch (sortKey) {
      case 'minutes_asc':
        return am - bm || bg - ag;
      case 'goals_desc':
        return bg - ag || bm - am;
      case 'goals_asc':
        return ag - bg || bm - am;
      case 'minutes_desc':
      default:
        return bm - am || bg - ag;
    }
  });

  tbody.innerHTML = sorted
    .map(
      (r, idx) =>
        `<tr>
          <td>${idx + 1}</td>
          <td>${escapeHtml(stripIdFromName(r.player_name))}</td>
          <td>${r.age ?? '—'}</td>
          <td>${formatNumber(r.total_minutes)}</td>
          <td>${formatNumber(r.total_goals)}</td>
        </tr>`
    )
    .join('');
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
  const searchInput = document.getElementById('players-search');
  if (searchInput) {
    let searchTimer = null;
    searchInput.addEventListener('input', () => {
      const term = searchInput.value.trim();
      if (searchTimer) clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        playersPage = 1;
        loadPlayers();
      }, term ? 250 : 0);
    });
  }
  document.getElementById('players-prev-bottom')?.addEventListener('click', () => {
    if (playersPage > 1) {
      playersPage--;
      loadPlayers();
    }
  });
  document.getElementById('players-next-bottom')?.addEventListener('click', () => {
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

  // Close modal handlers
  document.getElementById('player-details-close')?.addEventListener('click', () => {
    closePlayerDetailsModal();
  });
  document.getElementById('player-details-modal')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      closePlayerDetailsModal();
    }
  });
  document.getElementById('list-picker-close')?.addEventListener('click', () => {
    closeListPickerModal();
  });
  document.getElementById('list-picker-modal')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      closeListPickerModal();
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closePlayerDetailsModal();
      closeListPickerModal();
    }
  });
}

function initTabs() {
  const links = Array.from(document.querySelectorAll('.tab-link'));
  const panels = Array.from(document.querySelectorAll('[data-tab-panel]'));
  if (!links.length || !panels.length) return;

  function setActive(targetId) {
    links.forEach((btn) => {
      const isActive = btn.dataset.tabTarget === targetId;
      btn.classList.toggle('tab-active', isActive);
    });
    panels.forEach((panel) => {
      const isMatch = panel.dataset.tabPanel === targetId;
      panel.classList.toggle('hidden', !isMatch);
    });
  }

  links.forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tabTarget;
      if (!target) return;
      setActive(target);
    });
  });

  // Ensure default tab is visible
  setActive('players');
}
// ----- Favourite lists -----
let currentListId = null;
let currentListView = 'cards'; // 'cards' or 'table'

async function loadLists() {
  const key = getApiKey();
  if (!key) return;
  showError('lists-error', '');
  showEl('lists-loading', true);
  try {
    const res = await fetch(`${API_BASE}/api/v1/favourite-lists/`, { headers: apiHeaders() });
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
  const container = document.getElementById('lists-list');
  if (!container) return;
  container.innerHTML = (lists || [])
    .map(
      (l) =>
        `<div class="fav-list-card" data-list-id="${l.id}" data-list-name="${escapeHtml(l.name)}" role="listitem">
          <div class="fav-list-card-content">
            <span class="fav-list-card-name">${escapeHtml(l.name)}</span>
            <span class="fav-list-card-hint">Click to open</span>
          </div>
          <button type="button" data-list-id="${l.id}" data-list-name="${escapeHtml(l.name)}" class="fav-list-card-delete btn-delete" aria-label="Delete list">Delete</button>
        </div>`
    )
    .join('');
  container.querySelectorAll('.fav-list-card').forEach((card) => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('.fav-list-card-delete')) return;
      const id = parseInt(card.dataset.listId, 10);
      if (!id) return;
      currentListId = id;
      container.querySelectorAll('.fav-list-card').forEach((other) => other.classList.remove('selected'));
      card.classList.add('selected');
      const name = card.dataset.listName || '';
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
  container.querySelectorAll('.fav-list-card-delete').forEach((btn) => {
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
  const grid = document.getElementById('list-players-grid');
  const tableWrap = document.getElementById('list-players-table-wrap');
  const tableBody = document.getElementById('list-players-table-body');
  const emptyState = document.getElementById('list-empty-state');
  if (!grid || !emptyState || !tableWrap || !tableBody) return;
  const count = (players || []).length || 0;
  const metaEl = document.getElementById('list-detail-meta');
  if (metaEl) {
    metaEl.textContent = count
      ? `${count} player${count === 1 ? '' : 's'} in this list`
      : 'No players in this list yet.';
  }
  if (!players.length) {
    grid.innerHTML = '';
    tableBody.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  // Cards view
  grid.innerHTML = (players || [])
    .map((p) => {
      const pos = formatPositionLabel(p.position || p.main_position);
      const metaParts = [];
      if (pos && pos !== '—') metaParts.push(pos);
      if (p.age != null) metaParts.push(`${p.age} yrs`);
      const meta = metaParts.join(' • ');
      const value = formatNumber(p.market_value);
      return `
        <div class="list-player-card">
          <div class="list-player-avatar">
            ${renderPlayerImageCell(p.player_image_url, stripIdFromName(p.player_name))}
          </div>
          <div class="list-player-main">
            <div class="list-player-name">${escapeHtml(stripIdFromName(p.player_name) || '')}</div>
            <div class="list-player-meta">${(p.current_club_name || p.current_club_logo_url) ? renderClubCell(p.current_club_logo_url, p.current_club_name) : escapeHtml(meta || '')}</div>
            <div class="list-player-value">Value: ${value}</div>
          </div>
          <div class="list-player-actions">
            <button type="button" data-player-id="${p.player_id}" class="btn-remove">Remove</button>
          </div>
        </div>
      `;
    })
    .join('');
  grid.querySelectorAll('.btn-remove').forEach((b) => {
    b.addEventListener('click', () =>
      removePlayerFromList(listId, parseInt(b.dataset.playerId, 10))
    );
  });

  // Table view
  tableBody.innerHTML = (players || [])
    .map(
      (p) =>
        `<tr>
          <td>${renderPlayerImageCell(p.player_image_url, stripIdFromName(p.player_name))}</td>
          <td>${escapeHtml(stripIdFromName(p.player_name) || '')}</td>
          <td>${p.age ?? '—'}</td>
          <td>${escapeHtml(formatPositionLabel(p.position || p.main_position))}</td>
          <td>${escapeHtml(p.foot || '—')}</td>
          <td>${formatNumber(p.market_value)}</td>
          <td>${formatNumber(p.minutes_played)}</td>
          <td>${formatNumber(p.total_goals)}</td>
          <td>${p.total_assists ?? '—'}</td>
          <td>${p.total_cards ?? '—'}</td>
          <td>${p.total_clean_sheets ?? '—'}</td>
          <td>${renderClubCell(p.current_club_logo_url, p.current_club_name)}</td>
          <td><button type="button" data-player-id="${p.player_id}" class="btn-remove">Remove</button></td>
        </tr>`
    )
    .join('');
  tableBody.querySelectorAll('.btn-remove').forEach((b) => {
    b.addEventListener('click', () =>
      removePlayerFromList(listId, parseInt(b.dataset.playerId, 10))
    );
  });

  // Apply current view
  applyListView();
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
  const res = await fetch(`${API_BASE}/api/v1/players/?${qs}`, { headers: apiHeaders() });
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
            <span>${escapeHtml(stripIdFromName(p.player_name))}</span>
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
    const res = await fetch(`${API_BASE}/api/v1/favourite-lists/`, {
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
    showToast('Player added to list');
  } catch (e) {
    showError('lists-error', e.message || 'Request failed');
  }
}

function showToast(message) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
  el.style.opacity = '1';
  el.style.transform = 'translateY(0)';
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    setTimeout(() => el.classList.add('hidden'), 220);
  }, 2000);
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

  // View toggle buttons
  const viewButtons = document.querySelectorAll('.list-view-btn');
  viewButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const view = btn.dataset.view;
      if (!view) return;
      currentListView = view;
      viewButtons.forEach((b) =>
        b.classList.toggle('list-view-btn-active', b.dataset.view === view)
      );
      applyListView();
    });
  });
}

function applyListView() {
  const grid = document.getElementById('list-players-grid');
  const tableWrap = document.getElementById('list-players-table-wrap');
  if (!grid || !tableWrap) return;
  if (currentListView === 'table') {
    grid.classList.add('hidden');
    tableWrap.classList.remove('hidden');
  } else {
    grid.classList.remove('hidden');
    tableWrap.classList.add('hidden');
  }
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
  initTabs();
  initPlayers();
  initLists();
  if (getApiKey()) {
    loadAnalytics();
  }
  document.getElementById('analytics-reload')?.addEventListener('click', () => {
    loadAnalytics();
  });
  document.getElementById('analytics-youngest-sort')?.addEventListener('change', () => {
    // Re-render using last-fetched data if present by re-calling loadAnalytics with same params
    loadAnalytics();
  });
});
