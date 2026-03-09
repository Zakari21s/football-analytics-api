/**
 * Football Analytics – frontend entry.
 * Will use fetch() with X-API-Key for /api/v1/players and /api/v1/favourite-lists.
 */

// API base URL – set via config or default to same origin
const API_BASE = window.API_BASE || '';

// Placeholder: will be set from env or user input (e.g. prompt or config)
function getApiKey() {
  return window.API_KEY || '';
}

// Example: fetch players (to be wired when endpoints exist)
// async function fetchPlayers(params = {}) {
//   const qs = new URLSearchParams(params).toString();
//   const res = await fetch(`${API_BASE}/api/v1/players?${qs}`, {
//     headers: { 'X-API-Key': getApiKey() },
//   });
//   if (!res.ok) throw new Error(res.statusText);
//   return res.json();
// }

console.log('Football Analytics frontend loaded.');
