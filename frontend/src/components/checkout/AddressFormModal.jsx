/**
 * AddressFormModal - Add/edit shipping address during checkout or profile.
 */
import { useState } from 'react';
import { X } from 'lucide-react';
import useAddressStore from '../../stores/addressStore';
import toast from 'react-hot-toast';

const INDIAN_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh',
  'Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka',
  'Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram',
  'Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu',
  'Telangana','Tripura','Uttar Pradesh','Uttarakhand','West Bengal',
  'Andaman and Nicobar','Chandigarh','Dadra and Nagar Haveli',
  'Daman and Diu','Delhi','Jammu and Kashmir','Ladakh','Lakshadweep','Puducherry',
];

export default function AddressFormModal({ onClose, onSaved, address = null }) {
  const { addAddress, updateAddress } = useAddressStore();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    label: address?.label || 'home',
    full_name: address?.full_name || '',
    phone: address?.phone || '',
    address_line_1: address?.address_line_1 || '',
    address_line_2: address?.address_line_2 || '',
    city: address?.city || '',
    state: address?.state || '',
    postal_code: address?.postal_code || '',
    country: address?.country || 'India',
    is_default: address?.is_default || false,
  });

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.address_line_1 || !form.city || !form.state || !form.postal_code) {
      toast.error('Please fill all required fields');
      return;
    }
    setLoading(true);
    try {
      if (address?.id) {
        const result = await updateAddress(address.id, form);
        if (result) {
          toast.success('Address updated');
          onSaved?.({ ...form, id: address.id });
        } else {
          toast.error('Failed to update address. Please try again.');
        }
      } else {
        const result = await addAddress(form);
        if (result) {
          toast.success('Address added');
          onSaved?.(result);
        } else {
          toast.error('Failed to save address. Please check all fields and try again.');
        }
      }
    } catch (err) {
      toast.error(err?.message || 'An unexpected error occurred');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="font-bold text-lg text-gray-900">
            {address ? 'Edit Address' : 'Add New Address'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Label */}
          <div className="flex gap-2">
            {['home', 'office', 'other'].map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => handleChange('label', l)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
                  form.label === l
                    ? 'bg-black text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {l}
              </button>
            ))}
          </div>

          {/* Name + Phone */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="addr_full_name" className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
              <input
                id="addr_full_name"
                type="text"
                value={form.full_name}
                onChange={(e) => handleChange('full_name', e.target.value)}
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                required
              />
            </div>
            <div>
              <label htmlFor="addr_phone" className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                id="addr_phone"
                type="tel"
                value={form.phone}
                onChange={(e) => handleChange('phone', e.target.value.replace(/\D/g, '').slice(0, 10))}
                placeholder="10-digit mobile number"
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
              />
            </div>
          </div>

          {/* Address Lines */}
          <div>
            <label htmlFor="addr_line1" className="block text-sm font-medium text-gray-700 mb-1">Address Line 1 *</label>
            <input
              id="addr_line1"
              type="text"
              value={form.address_line_1}
              onChange={(e) => handleChange('address_line_1', e.target.value)}
              placeholder="House no., Street, Area"
              className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
              required
            />
          </div>
          <div>
            <label htmlFor="addr_line2" className="block text-sm font-medium text-gray-700 mb-1">Address Line 2</label>
            <input
              id="addr_line2"
              type="text"
              value={form.address_line_2}
              onChange={(e) => handleChange('address_line_2', e.target.value)}
              placeholder="Landmark (optional)"
              className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
            />
          </div>

          {/* City + State + PIN */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label htmlFor="addr_city" className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <input
                id="addr_city"
                type="text"
                value={form.city}
                onChange={(e) => handleChange('city', e.target.value)}
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none"
                required
              />
            </div>
            <div>
              <label htmlFor="addr_state" className="block text-sm font-medium text-gray-700 mb-1">State *</label>
              <select
                id="addr_state"
                value={form.state}
                onChange={(e) => handleChange('state', e.target.value)}
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none bg-white"
                required
              >
                <option value="">Select</option>
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="addr_pincode" className="block text-sm font-medium text-gray-700 mb-1">PIN Code *</label>
              <input
                id="addr_pincode"
                type="text"
                value={form.postal_code}
                onChange={(e) => handleChange('postal_code', e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-black focus:border-transparent outline-none font-mono"
                required
              />
            </div>
          </div>

          {/* Default */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) => handleChange('is_default', e.target.checked)}
              className="accent-black w-4 h-4"
            />
            <span className="text-sm text-gray-700">Set as default address</span>
          </label>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white py-3 rounded-lg font-semibold hover:bg-gray-800 transition disabled:opacity-50"
          >
            {loading ? 'Saving...' : address ? 'Update Address' : 'Save Address'}
          </button>
        </form>
      </div>
    </div>
  );
}