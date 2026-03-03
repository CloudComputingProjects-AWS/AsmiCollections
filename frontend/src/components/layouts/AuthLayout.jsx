import { Outlet, Link } from 'react-router-dom';
import { ShoppingBag } from 'lucide-react';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center px-4 py-12">
      <Link to="/" className="flex items-center gap-2 mb-8">
        <ShoppingBag className="h-8 w-8 text-brand-600" />
        <span className="font-display text-2xl text-ink">Ashmi</span>
      </Link>
      <main id="main-content" className="w-full max-w-md bg-surface-raised rounded-[var(--radius-xl)] shadow-[var(--shadow-elevated)] p-6 sm:p-8 animate-fade-in">
        <Outlet />
      </main>
    </div>
  );
}
