import { Link } from 'react-router-dom';

const FOOTER_LINKS = {
  Shop: [
    { label: 'Men', href: '/shop?gender=men' },
    { label: 'Women', href: '/shop?gender=women' },
    { label: 'Boys', href: '/shop?gender=boys' },
    { label: 'Girls', href: '/shop?gender=girls' },
    { label: 'New Arrivals', href: '/shop?sort=newest' },
  ],
  Support: [
    { label: 'Contact Us', href: '/contact' },
    { label: 'FAQ', href: '/faq' },
    { label: 'Shipping Info', href: '/shipping' },
    { label: 'Returns Policy', href: '/returns' },
    { label: 'Size Guide', href: '/size-guide' },
  ],
  Company: [
    { label: 'About Us', href: '/about' },
    { label: 'Privacy Policy', href: '/privacy-policy' },
    { label: 'Terms of Service', href: '/terms' },
    { label: 'Cookie Policy', href: '/cookies' },
  ],
};

export default function CustomerFooter() {
  return (
    <footer className="bg-neutral-900 text-neutral-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-rose-400 rounded-lg flex items-center justify-center">
                <span className="text-white font-black text-sm">A</span>
              </div>
              <span className="text-lg font-black text-white">Ashmi</span>
            </div>
            <p className="text-sm text-neutral-400 leading-relaxed">
              Curated apparel for every occasion. Style that speaks your language.
            </p>
          </div>

          {/* Link Groups */}
          {Object.entries(FOOTER_LINKS).map(([title, links]) => (
            <div key={title}>
              <div className="text-sm font-bold text-white uppercase tracking-wider mb-4">{title}</div>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.href}
                      className="text-sm text-neutral-400 hover:text-white transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-neutral-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-neutral-400">
            &copy; {new Date().getFullYear()} Ashmi. All rights reserved.
          </p>
          <div className="flex items-center gap-4 text-xs text-neutral-400">
            <span>Made in India</span>
            <span>·</span>
            <span>Secure Payments</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
