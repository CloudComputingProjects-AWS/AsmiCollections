import { Outlet, Link, useNavigate } from 'react-router-dom';
import { ShoppingBag, Heart, User, Menu, X, Search, LogOut } from 'lucide-react';
import useAuthStore from '@/stores/authStore';
import useUIStore from '@/stores/uiStore';

export default function CustomerLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-surface">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

function Header() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const { mobileMenuOpen, toggleMobileMenu, closeMobileMenu } = useUIStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 bg-surface-raised/95 backdrop-blur-sm border-b border-ink-faint/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" onClick={closeMobileMenu}>
            <ShoppingBag className="h-7 w-7 text-brand-600" />
            <span className="font-display text-xl text-ink">Ashmi</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-ink-muted">
            <Link to="/shop/men" className="hover:text-brand-600 transition-colors">Men</Link>
            <Link to="/shop/women" className="hover:text-brand-600 transition-colors">Women</Link>
            <Link to="/shop/kids" className="hover:text-brand-600 transition-colors">Kids</Link>
          </nav>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center gap-3">
            <Link to="/search" className="p-2 text-ink-muted hover:text-ink transition-colors">
              <Search size={20} />
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/wishlist" className="p-2 text-ink-muted hover:text-ink transition-colors">
                  <Heart size={20} />
                </Link>
                <Link to="/cart" className="p-2 text-ink-muted hover:text-ink transition-colors">
                  <ShoppingBag size={20} />
                </Link>
                <Link to="/account" className="p-2 text-ink-muted hover:text-ink transition-colors">
                  <User size={20} />
                </Link>
                <button onClick={handleLogout} className="p-2 text-ink-muted hover:text-error transition-colors" title="Logout">
                  <LogOut size={20} />
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="ml-2 px-4 py-1.5 bg-brand-600 text-white text-sm font-medium rounded-[var(--radius-md)] hover:bg-brand-700 transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <button onClick={toggleMobileMenu} className="md:hidden p-2 text-ink-muted">
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-ink-faint/10 bg-surface-raised animate-slide-up">
          <nav className="px-4 py-4 space-y-3">
            <MobileLink to="/shop/men" onClick={closeMobileMenu}>Men</MobileLink>
            <MobileLink to="/shop/women" onClick={closeMobileMenu}>Women</MobileLink>
            <MobileLink to="/shop/kids" onClick={closeMobileMenu}>Kids</MobileLink>
            <hr className="border-ink-faint/10" />
            {isAuthenticated ? (
              <>
                <MobileLink to="/account" onClick={closeMobileMenu}>My Account</MobileLink>
                <MobileLink to="/wishlist" onClick={closeMobileMenu}>Wishlist</MobileLink>
                <MobileLink to="/cart" onClick={closeMobileMenu}>Cart</MobileLink>
                <button onClick={() => { handleLogout(); closeMobileMenu(); }}
                  className="block w-full text-left py-2 text-error font-medium">
                  Logout
                </button>
              </>
            ) : (
              <MobileLink to="/login" onClick={closeMobileMenu}>Sign In</MobileLink>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}

function MobileLink({ to, children, onClick }) {
  return (
    <Link to={to} onClick={onClick}
      className="block py-2 text-sm font-medium text-ink-muted hover:text-brand-600 transition-colors">
      {children}
    </Link>
  );
}

function Footer() {
  return (
    <footer className="bg-surface-dark text-ink-inverse/70 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h3 className="font-display text-lg text-ink-inverse mb-3">Ashmi</h3>
            <p className="text-sm leading-relaxed">Premium apparel for the modern family. India &amp; Global.</p>
          </div>
          <div>
            <h4 className="font-medium text-ink-inverse mb-3 text-sm">Shop</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/shop/men" className="hover:text-brand-400 transition-colors">Men</Link></li>
              <li><Link to="/shop/women" className="hover:text-brand-400 transition-colors">Women</Link></li>
              <li><Link to="/shop/kids" className="hover:text-brand-400 transition-colors">Kids</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-ink-inverse mb-3 text-sm">Support</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/shipping-policy" className="hover:text-brand-400 transition-colors">Shipping</Link></li>
              <li><Link to="/return-policy" className="hover:text-brand-400 transition-colors">Returns</Link></li>
              <li><Link to="/contact" className="hover:text-brand-400 transition-colors">Contact Us</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-ink-inverse mb-3 text-sm">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/privacy-policy" className="hover:text-brand-400 transition-colors">Privacy Policy</Link></li>
              <li><Link to="/terms" className="hover:text-brand-400 transition-colors">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-ink-inverse/10 text-xs text-center">
          &copy; {new Date().getFullYear()} Ashmi. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
