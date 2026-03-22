/**
 * useIdleTimeout.js - Auto-logout after 15 minutes of inactivity.
 * Tracks: mousemove, mousedown, keydown, touchstart, scroll.
 * Only active when user is logged in (user !== null).
 *
 * Fix: Uses useRef for logout function reference instead of useCallback
 * dependency chain. This prevents the render loop where:
 *   logout ref changes → handleIdle recreates → resetTimer recreates →
 *   useEffect re-runs → timer resets → never reaches zero.
 *
 * Now useEffect depends only on [user], so the timer registers once
 * after login and resets only on actual user interaction events.
 */
import { useEffect, useRef } from 'react';
import useAuthStore from '../stores/authStore';

const IDLE_TIMEOUT_MS = 15 * 60 * 1000;
const EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];

export default function useIdleTimeout() {
  const user = useAuthStore((s) => s.user);
  const logoutRef = useRef(useAuthStore.getState().logout);
  const timerRef = useRef(null);

  useEffect(() => {
    logoutRef.current = useAuthStore.getState().logout;
  });

  useEffect(() => {
    if (!user) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }

    const handleIdle = async () => {
      if (!useAuthStore.getState().user) return;
      await logoutRef.current();
      window.dispatchEvent(new CustomEvent('auth:expired'));
      window.location.href = '/login?reason=idle';
    };

    const resetTimer = () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(handleIdle, IDLE_TIMEOUT_MS);
    };

    resetTimer();
    EVENTS.forEach((e) => window.addEventListener(e, resetTimer, { passive: true }));

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      EVENTS.forEach((e) => window.removeEventListener(e, resetTimer));
    };
  }, [user]);
}
