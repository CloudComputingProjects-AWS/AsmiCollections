import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Menu, X, ShoppingBag, Heart, User, LogOut, ChevronDown,
} from 'lucide-react';
import useAuthStore from '../../stores/authStore';
import SearchBar from '../catalog/SearchBar';

const NAV_CATEGORIES = [
  { label: 'Men', href: '/shop?gender=men' },
  { label: 'Women', href: '/shop?gender=women' },
  { label: 'Boys', href: '/shop?gender=boys' },
  { label: 'Girls', href: '/shop?gender=girls' },
];

export default function CustomerHeader() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-neutral-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-600 to-rose-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-black text-sm">A</span>
            </div>
            <span className="text-lg font-black text-neutral-900 hidden sm:block">Ashmi</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-6 ml-8">
            {NAV_CATEGORIES.map((cat) => (
              <Link
                key={cat.label}
                to={cat.href}
                className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors"
              >
                {cat.label}
              </Link>
            ))}
            <Link
              to="/categories"
              className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors flex items-center gap-0.5"
            >
              More Categories <ChevronDown size={14} />
            </Link>
          </nav>

          {/* Search Bar (Desktop) */}
          <SearchBar compact className="hidden md:block flex-1 max-w-md mx-6" />

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {user ? (
              <>
                {/* Wishlist */}
                <Link
                  to="/wishlist"
                  className="p-2 text-neutral-500 hover:text-neutral-800 transition-colors"
                  title="Wishlist"
                >
                  <Heart size={20} />
                </Link>

                {/* Cart */}
                <Link
                  to="/cart"
                  className="relative p-2 text-neutral-500 hover:text-neutral-800 transition-colors"
                  title="Cart"
                >
                  <ShoppingBag size={20} />
                  {/* TODO: cart badge count from store */}
                </Link>

                {/* Profile Menu */}
                <div className="relative">
                  <button
                    onClick={() => setProfileOpen(!profileOpen)}
                    className="flex items-center gap-1.5 p-2 text-neutral-500 hover:text-neutral-800 transition-colors" aria-label="Account menu"
                  >
                    <User size={20} />
                    <span className="hidden lg:block text-sm font-medium text-neutral-700">
                      {user.first_name || 'Account'}
                    </span>
                  </button>
                  {profileOpen && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setProfileOpen(false)} />
                      <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-xl border border-neutral-100 z-20 py-1">
                        <Link
                          to="/dashboard"
                          onClick={() => setProfileOpen(false)}
                          className="block px-4 py-2.5 text-sm text-neutral-600 hover:bg-neutral-50"
                        >
                          My Dashboard
                        </Link>
                        <Link
                          to="/orders"
                          onClick={() => setProfileOpen(false)}
                          className="block px-4 py-2.5 text-sm text-neutral-600 hover:bg-neutral-50"
                        >
                          My Orders
                        </Link>
                        <Link
                          to="/wishlist"
                          onClick={() => setProfileOpen(false)}
                          className="block px-4 py-2.5 text-sm text-neutral-600 hover:bg-neutral-50"
                        >
                          Wishlist
                        </Link>
                        <hr className="my-1 border-neutral-100" />
                        <Link
                          to="/profile"
                          onClick={() => setProfileOpen(false)}
                          className="block px-4 py-2.5 text-sm text-neutral-600 hover:bg-neutral-50"
                        >
                          Edit Profile
                        </Link>
                        <Link
                          to="/addresses"
                          onClick={() => setProfileOpen(false)}
                          className="block px-4 py-2.5 text-sm text-neutral-600 hover:bg-neutral-50"
                        >
                          My Addresses
                        </Link>
                        <Link
                          to="/privacy"
                          onClick={() => setProfileOpen(false)}
                          className="block px-4 py-2.5 text-sm text-neutral-600 hover:bg-neutral-50"
                        >
                          Privacy &amp; Consent
                        </Link>
                        <hr className="my-1 border-neutral-100" />
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50"
                        >
                          <LogOut size={14} /> Logout
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-neutral-700 hover:text-neutral-900 transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 transition-colors"
                >
                  Sign Up
                </Link>
              </div>
            )}

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-neutral-500 hover:text-neutral-800" aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {/* Mobile Search */}
        <div className="md:hidden pb-3">
          <SearchBar compact />
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white border-t border-neutral-100">
          <div className="max-w-7xl mx-auto px-4 py-4 space-y-1">
            {NAV_CATEGORIES.map((cat) => (
              <Link
                key={cat.label}
                to={cat.href}
                onClick={() => setMobileMenuOpen(false)}
                className="block px-3 py-2.5 text-base font-medium text-neutral-700 hover:bg-neutral-50 rounded-lg"
              >
                {cat.label}
              </Link>
            ))}
            <Link
              to="/categories"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2.5 text-base font-medium text-neutral-700 hover:bg-neutral-50 rounded-lg"
            >
              All Categories
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}


