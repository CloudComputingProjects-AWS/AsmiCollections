/**
 * useIdleTimeout.js - Auto-logout after 15 minutes of inactivity.
 *
 * Tracks: mousemove, mousedown, keydown, touchstart, scroll.
 * On idle timeout: calls authStore.logout(), dispatches auth:expired,
 * redirects to /login.
 *
 * Only active when user is logged in (user !== null).
 * Timer resets on any user interaction.
 *
 * SECURITY (Updated 01-Mar-2026 S16): No localStorage operations.
 * Tokens are httpOnly cookies — cleared by backend on logout.
 */
import { useEffect, useRef, useCallback } from 'react';
import useAuthStore from '../stores/authStore';
const IDLE_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes
const EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
export default function useIdleTimeout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const timerRef = useRef(null);
  const handleIdle = useCallback(() => {
    if (!useAuthStore.getState().user) return;
    logout();
    window.dispatchEvent(new CustomEvent('auth:expired'));
    window.location.href = '/login?reason=idle';
  }, [logout]);
  const resetTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(handleIdle, IDLE_TIMEOUT_MS);
  }, [handleIdle]);
  useEffect(() => {
    if (!user) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }
    resetTimer();
    const handler = () => resetTimer();
    EVENTS.forEach((e) => window.addEventListener(e, handler, { passive: true }));
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      EVENTS.forEach((e) => window.removeEventListener(e, handler));
    };
  }, [user, resetTimer]);
}
