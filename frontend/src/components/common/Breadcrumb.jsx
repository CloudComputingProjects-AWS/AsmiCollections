import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

export default function Breadcrumb({ items = [] }) {
  return (
    <nav className="flex items-center gap-1.5 text-sm text-neutral-500 mb-6" aria-label="Breadcrumb">
      <Link to="/" className="hover:text-neutral-800 transition-colors" aria-label="Home">
        <Home size={15} />
      </Link>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          <ChevronRight size={14} className="text-neutral-300" />
          {item.href ? (
            <Link to={item.href} className="hover:text-neutral-800 transition-colors capitalize">
              {item.label}
            </Link>
          ) : (
            <span className="text-neutral-800 font-medium capitalize">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
