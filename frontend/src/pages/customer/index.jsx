// Customer-facing placeholder pages — Phase F1

export function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-16 text-center animate-fade-in">
      <h1 className="font-display text-4xl sm:text-5xl mb-4">Welcome to Ashmi</h1>
      <p className="text-ink-muted text-lg max-w-xl mx-auto">
        Premium apparel for the modern family. Browse our collection for Men, Women, and Kids.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        <a href="/shop/men"
          className="px-6 py-3 bg-brand-600 text-white font-medium rounded-[var(--radius-md)] hover:bg-brand-700 transition-colors">
          Shop Men
        </a>
        <a href="/shop/women"
          className="px-6 py-3 border border-ink-faint/30 text-ink font-medium rounded-[var(--radius-md)] hover:bg-surface-sunken transition-colors">
          Shop Women
        </a>
      </div>
    </div>
  );
}

export function AccountPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <h1 className="font-display text-2xl mb-4">My Account</h1>
      <p className="text-ink-muted">Account dashboard — profile, orders, addresses will be added in Phase F2.</p>
    </div>
  );
}

export function NotFoundPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-20 text-center">
      <h1 className="font-display text-6xl text-ink-faint mb-4">404</h1>
      <p className="text-ink-muted text-lg mb-6">Page not found</p>
      <a href="/"
        className="px-6 py-3 bg-brand-600 text-white font-medium rounded-[var(--radius-md)] hover:bg-brand-700 transition-colors">
        Go Home
      </a>
    </div>
  );
}
