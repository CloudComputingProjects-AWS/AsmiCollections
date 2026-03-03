import { useParams, Link } from 'react-router-dom';
import { Sparkles, ArrowRight } from 'lucide-react';
import { useCategories } from '../../hooks/useCatalog';
import Breadcrumb from '../../components/common/Breadcrumb';

const AGE_GROUPS = [
  { key: 'infant', label: 'Infant (0-2)', emoji: '🍼' },
  { key: 'kids', label: 'Kids (3-12)', emoji: '🎈' },
  { key: 'teen', label: 'Teen (13-17)', emoji: '🎧' },
  { key: 'adult', label: 'Adult (18+)', emoji: '👤' },
  { key: 'senior', label: 'Senior (60+)', emoji: '🌿' },
];

export default function CategoryPage() {
  const { gender, ageGroup } = useParams();
  const { categories, loading } = useCategories(gender, ageGroup);

  const breadcrumbs = [{ label: 'Categories', href: '/categories' }];
  if (gender) breadcrumbs.push({ label: gender, href: `/categories/${gender}` });
  if (ageGroup) breadcrumbs.push({ label: ageGroup });

  // If no gender selected — show gender grid
  if (!gender) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <Breadcrumb items={[{ label: 'Categories' }]} />
        <h1 className="text-3xl font-black text-neutral-900 mb-2">Shop by Category</h1>
        <p className="text-neutral-500 mb-8">Choose a category to start exploring.</p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {['men', 'women', 'boys', 'girls', 'unisex'].map((g) => (
            <Link
              key={g}
              to={`/categories/${g}`}
              className="group bg-white rounded-2xl p-8 text-center shadow-sm hover:shadow-lg border border-neutral-100 hover:border-indigo-200 transition-all"
            >
              <div className="text-5xl mb-4">
                {{ men: '👔', women: '👗', boys: '🧢', girls: '🎀', unisex: '✨' }[g]}
              </div>
              <h3 className="text-lg font-bold text-neutral-800 capitalize group-hover:text-indigo-600 transition-colors">
                {g}
              </h3>
            </Link>
          ))}
        </div>
      </div>
    );
  }

  // If gender selected but no age group — show age groups
  if (!ageGroup) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <Breadcrumb items={breadcrumbs} />
        <h1 className="text-3xl font-black text-neutral-900 mb-2 capitalize">{gender}'s Collection</h1>
        <p className="text-neutral-500 mb-8">Select an age group to narrow your search.</p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {AGE_GROUPS.map((ag) => (
            <Link
              key={ag.key}
              to={`/categories/${gender}/${ag.key}`}
              className="group bg-white rounded-2xl p-6 text-center shadow-sm hover:shadow-lg border border-neutral-100 hover:border-indigo-200 transition-all"
            >
              <div className="text-4xl mb-3">{ag.emoji}</div>
              <h3 className="text-base font-bold text-neutral-800 group-hover:text-indigo-600 transition-colors">
                {ag.label}
              </h3>
            </Link>
          ))}
        </div>

        {/* Also show subcategories if available */}
        {categories.length > 0 && (
          <div className="mt-12">
            <h2 className="text-xl font-bold text-neutral-800 mb-6">All Subcategories</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  to={`/shop?category_id=${cat.id}`}
                  className="group flex items-center gap-4 bg-white rounded-xl p-4 shadow-sm hover:shadow-md border border-neutral-100 transition-all"
                >
                  {cat.image_url ? (
                    <img
                      src={cat.image_url}
                      alt={cat.name}
                      className="w-16 h-16 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-lg bg-neutral-100 flex items-center justify-center">
                      <Sparkles size={20} className="text-neutral-300" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-neutral-800 group-hover:text-indigo-600 truncate transition-colors">
                      {cat.name}
                    </h3>
                    <p className="text-xs text-neutral-400 capitalize">
                      {cat.gender} · {cat.age_group}
                    </p>
                  </div>
                  <ArrowRight size={16} className="text-neutral-300 group-hover:text-indigo-500 transition-colors" />
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Gender + Age selected — show subcategories
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Breadcrumb items={breadcrumbs} />
      <h1 className="text-3xl font-black text-neutral-900 mb-2 capitalize">
        {gender}'s {ageGroup} Collection
      </h1>
      <p className="text-neutral-500 mb-8">Browse subcategories below or view all products.</p>

      <Link
        to={`/shop?gender=${gender}&age_group=${ageGroup}`}
        className="inline-flex items-center gap-2 mb-8 px-5 py-2.5 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
      >
        View All Products <ArrowRight size={16} />
      </Link>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="animate-pulse bg-neutral-100 rounded-2xl h-32" />
          ))}
        </div>
      ) : categories.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              to={`/shop?category_id=${cat.id}`}
              className="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-lg border border-neutral-100 transition-all"
            >
              {cat.image_url ? (
                <div className="aspect-[4/3] overflow-hidden">
                  <img
                    src={cat.image_url}
                    alt={cat.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
              ) : (
                <div className="aspect-[4/3] bg-gradient-to-br from-neutral-50 to-neutral-100 flex items-center justify-center">
                  <Sparkles size={32} className="text-neutral-300" />
                </div>
              )}
              <div className="p-4">
                <h3 className="font-bold text-neutral-800 group-hover:text-indigo-600 transition-colors">
                  {cat.name}
                </h3>
                {cat.description && (
                  <p className="text-xs text-neutral-400 mt-1 line-clamp-2">{cat.description}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-neutral-400">
          No subcategories found. Try viewing all products instead.
        </div>
      )}
    </div>
  );
}
