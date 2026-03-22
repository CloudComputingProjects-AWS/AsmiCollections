/**
 * useIdleTimeout.js - Auto-logout after 15 minutes of inactivity.
 * Tracks: mousemove, mousedown, keydown, touchstart, scroll.
 * Only active when user is logged in (user !== null).
 *
 * Fix history:
 * - Session 47: Added await before logout() to ensure cookies cleared before redirect.
 * - Session 48 (attempt 1): Replaced useCallback chain with useRef for stable logout reference.
 *   Result: Still broken - login/init set() calls produce new user object references,
 *   causing useEffect([user]) to re-run and reset the timer on every store update.
 * - Session 48 (attempt 2): Changed useEffect dependency from [user] to [user?.id].
 *   Primitive comparison (number === number) prevents re-runs on identical user data.
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
  }, [user?.id]);
}
