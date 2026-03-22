/**
 * idleTimeout.js - Auto-logout after 15 minutes of inactivity.
 *
 * This is a plain JavaScript module, NOT a React hook.
 * It subscribes to the Zustand auth store directly via subscribe(),
 * which runs outside React's render cycle — completely immune to
 * component re-renders.
 *
 * Usage in App.jsx: import at module level (outside the component).
 *   import './hooks/idleTimeout';
 *
 * Fix history:
 * - Session 47: Added await before logout().
 * - Session 48 (attempt 1): useRef for stable logout ref — still broken.
 * - Session 48 (attempt 2): [user?.id] dependency — still broken.
 *   Root cause: CustomerHeader uses useAuthStore() with no selector,
 *   causing full-store re-renders that cascade to App, re-running useEffect.
 * - Session 48 (final): Moved entirely outside React. Zustand subscribe()
 *   fires on every set() call, but we compare user.id manually — only
 *   start/stop the timer when login/logout actually occurs.
 */
import useAuthStore from '../stores/authStore';

const IDLE_TIMEOUT_MS = 15 * 60 * 1000;
const EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];

let timerId = null;
let activeCleanup = null;
let lastUserId = null;

function clearIdle() {
  if (timerId !== null) {
    clearTimeout(timerId);
    timerId = null;
  }
}

function stopIdleTracking() {
  clearIdle();
  if (activeCleanup) {
    activeCleanup();
    activeCleanup = null;
  }
}

function startIdleTracking() {
  stopIdleTracking();

  const resetTimer = () => {
    clearIdle();
    timerId = setTimeout(async () => {
      if (!useAuthStore.getState().user) return;
      try {
        await useAuthStore.getState().logout();
      } catch {
        // Silent — clear state regardless
      }
      window.dispatchEvent(new CustomEvent('auth:expired'));
      window.location.href = '/login?reason=idle';
    }, IDLE_TIMEOUT_MS);
  };

  resetTimer();
  EVENTS.forEach((e) => window.addEventListener(e, resetTimer, { passive: true }));

  activeCleanup = () => {
    EVENTS.forEach((e) => window.removeEventListener(e, resetTimer));
  };
}

// Initialize from current state (handles page refresh while logged in)
lastUserId = useAuthStore.getState().user?.id ?? null;
if (lastUserId) {
  startIdleTracking();
}

// Subscribe to ALL store changes, but only act on user.id transitions
useAuthStore.subscribe((state) => {
  const currentUserId = state.user?.id ?? null;

  if (currentUserId === lastUserId) return; // No login/logout change — ignore

  lastUserId = currentUserId;

  if (currentUserId) {
    startIdleTracking();   // Logged in
  } else {
    stopIdleTracking();    // Logged out
  }
});
