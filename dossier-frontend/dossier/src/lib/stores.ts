import { writable } from 'svelte/store';

// currentUser holds a small user object saved to localStorage on login (or null)
export const currentUser = writable<any>(null);

// setupRequired mirrors the API /setup response. True means "no users exist yet".
export const setupRequired = writable<boolean>(false);

// appReady controls whether the app should show user-visible UI.
// Set to true only after initial checks (localStorage + /setup API) complete.
export const appReady = writable<boolean>(false);

// Helper to initialize currentUser from localStorage (used by layout onMount)
export function initCurrentUserFromStorage() {
  try {
    const raw = localStorage.getItem('dossier_user');
    if (raw) currentUser.set(JSON.parse(raw));
  } catch (e) {
    // ignore parsing errors
  }
}

export function markAppReady() {
  appReady.set(true);
  try { document.documentElement.dataset.appReady = 'true'; } catch(e) { /* ignore */ }
}
