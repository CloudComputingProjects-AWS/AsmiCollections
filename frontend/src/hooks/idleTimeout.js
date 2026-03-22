/**
 * idleTimeout.js - Auto-logout after 15 minutes of inactivity.
 *
 * Plain JavaScript module — NOT a React hook.
 * Subscribes to Zustand auth store outside React render cycle.
 *
 * Events tracked: mousedown, keydown, touchstart, pointerdown.
 * mousemove and scroll are excluded — CSS animations (hero banner)
 * trigger synthetic mousemove events continuously, and scroll fires
 * from smooth-scrolling/animations. These caused the timer to reset
 * endlessly, preventing idle logout from ever firing.
 *
 * Throttle: resetTimer only fires once per 60 seconds as a safety net.
 *
 * Usage in App.jsx: import at module level (outside the component).
 *   import './hooks/idleTimeout';
 */
import useAuthStore from '../stores/authStore';

var IDLE_TIMEOUT_MS = 15 * 60 * 1000;
var THROTTLE_MS = 60 * 1000;
var EVENTS = ['mousedown', 'keydown', 'touchstart', 'pointerdown'];

var timerId = null;
var lastReset = 0;
var listeners = null;

async function handleIdleExpiry() {
  if (!useAuthStore.getState().user) return;
  try {
    await useAuthStore.getState().logout();
  } catch (e) {
    // Silent
  }
  window.dispatchEvent(new CustomEvent('auth:expired'));
  window.location.href = '/login?reason=idle';
}

function resetTimer() {
  var now = Date.now();
  if (now - lastReset < THROTTLE_MS) return;
  lastReset = now;
  if (timerId !== null) clearTimeout(timerId);
  timerId = setTimeout(handleIdleExpiry, IDLE_TIMEOUT_MS);
}

function startIdleTracking() {
  stopIdleTracking();
  lastReset = 0;
  resetTimer();
  var handler = function() { resetTimer(); };
  var cleanups = [];
  for (var i = 0; i < EVENTS.length; i++) {
    window.addEventListener(EVENTS[i], handler, { passive: true });
    cleanups.push(EVENTS[i]);
  }
  listeners = { handler: handler, events: cleanups };
}

function stopIdleTracking() {
  if (timerId !== null) {
    clearTimeout(timerId);
    timerId = null;
  }
  if (listeners) {
    for (var i = 0; i < listeners.events.length; i++) {
      window.removeEventListener(listeners.events[i], listeners.handler);
    }
    listeners = null;
  }
  lastReset = 0;
}

// Track user login state
var lastUserId = useAuthStore.getState().user?.id ?? null;
if (lastUserId) {
  startIdleTracking();
}

useAuthStore.subscribe(function(state) {
  var currentUserId = state.user?.id ?? null;
  if (currentUserId === lastUserId) return;
  lastUserId = currentUserId;
  if (currentUserId) {
    startIdleTracking();
  } else {
    stopIdleTracking();
  }
});
