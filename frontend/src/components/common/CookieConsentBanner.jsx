/**
 * CookieConsentBanner — Phase F5
 * Global cookie consent: essential (always on), analytics (optional), marketing (optional)
 */
import { useState, useEffect } from 'react';
import { Cookie, X, ChevronDown, ChevronUp } from 'lucide-react';

const COOKIE_KEY = 'ashmi_cookie_consent';

export default function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [prefs, setPrefs] = useState({
    essential: true, // always on
    analytics: false,
    marketing: false,
  });

  useEffect(() => {
    const saved = localStorage.getItem(COOKIE_KEY);
    if (!saved) {
      // Show banner after 1s delay for better UX
      const timer = setTimeout(() => setVisible(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const accept = (mode) => {
    let consent;
    if (mode === 'all') {
      consent = { essential: true, analytics: true, marketing: true };
    } else if (mode === 'essential') {
      consent = { essential: true, analytics: false, marketing: false };
    } else {
      consent = { ...prefs, essential: true };
    }
    localStorage.setItem(COOKIE_KEY, JSON.stringify({ ...consent, timestamp: new Date().toISOString() }));
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 p-4 animate-[slideUp_0.3s_ease-out]">
      <div className="max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-2xl p-5">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <Cookie size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 text-sm">We use cookies</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              We use cookies for essential functionality and to improve your experience.
            </p>
          </div>
          <button onClick={() => setVisible(false)} className="text-gray-400 hover:text-gray-600">
            <X size={16} />
          </button>
        </div>

        {/* Expand/Collapse preferences */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-3 transition"
        >
          Manage Preferences {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {expanded && (
          <div className="space-y-2.5 mb-4 pl-1">
            <label className="flex items-center gap-2.5">
              <input type="checkbox" checked disabled className="accent-black w-3.5 h-3.5" />
              <div>
                <span className="text-xs font-medium text-gray-900">Essential</span>
                <span className="text-xs text-gray-400 ml-1">(always on)</span>
                <p className="text-xs text-gray-500">Authentication, cart, security — required for the site to work</p>
              </div>
            </label>
            <label className="flex items-center gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={prefs.analytics}
                onChange={(e) => setPrefs({ ...prefs, analytics: e.target.checked })}
                className="accent-black w-3.5 h-3.5"
              />
              <div>
                <span className="text-xs font-medium text-gray-900">Analytics</span>
                <p className="text-xs text-gray-500">Help us understand how you use the site to improve it</p>
              </div>
            </label>
            <label className="flex items-center gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={prefs.marketing}
                onChange={(e) => setPrefs({ ...prefs, marketing: e.target.checked })}
                className="accent-black w-3.5 h-3.5"
              />
              <div>
                <span className="text-xs font-medium text-gray-900">Marketing</span>
                <p className="text-xs text-gray-500">Personalized recommendations and retargeting</p>
              </div>
            </label>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={() => accept('essential')}
            className="flex-1 border border-gray-300 px-4 py-2 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
          >
            Essential Only
          </button>
          {expanded && (
            <button
              onClick={() => accept('custom')}
              className="flex-1 border border-gray-300 px-4 py-2 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              Save Preferences
            </button>
          )}
          <button
            onClick={() => accept('all')}
            className="flex-1 bg-black text-white px-4 py-2 rounded-lg text-xs font-medium hover:bg-gray-800 transition"
          >
            Accept All
          </button>
        </div>
      </div>

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
