/**
 * PrivacyPolicyPage — Phase F5
 * DPDP Act 2023 + GDPR compliant privacy policy
 */
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function PrivacyPolicyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
        <ArrowLeft size={16} /> Back to Home
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: February 2026 | Version 1.0</p>

      <div className="prose prose-sm prose-gray max-w-none space-y-6">
        <section>
          <h2 className="text-lg font-semibold text-gray-900">1. Introduction</h2>
          <p className="text-gray-600">
            Ashmi Store ("we", "us", "our") is committed to protecting your personal data.
            This Privacy Policy explains how we collect, use, store, and share your information
            when you use our e-commerce platform, in compliance with the Digital Personal Data Protection Act, 2023
            (DPDP Act) of India and the General Data Protection Regulation (GDPR) of the European Union.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">2. Data We Collect</h2>
          <p className="text-gray-600">We collect the following categories of personal data:</p>
          <p className="text-gray-600">
            <strong>Account Information:</strong> Name, email address, phone number, and password (hashed).
            <br /><strong>Address Information:</strong> Shipping and billing addresses you provide.
            <br /><strong>Order Information:</strong> Purchase history, payment method (we do not store card numbers), order status.
            <br /><strong>Usage Data:</strong> Pages visited, search queries, device information, IP address.
            <br /><strong>Consent Records:</strong> Your consent choices with timestamps for audit compliance.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">3. How We Use Your Data</h2>
          <p className="text-gray-600">
            We process your data for: fulfilling orders and providing customer support,
            generating GST-compliant tax invoices (legal obligation), sending order status updates (transactional),
            sending marketing communications (only with your explicit consent),
            improving our platform and user experience, and preventing fraud and ensuring security.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">4. Data Protection</h2>
          <p className="text-gray-600">
            We protect your personal data using AES-256 encryption for sensitive fields (phone, address)
            at rest. All data in transit is encrypted via TLS/HTTPS. Payment processing is handled by
            PCI-DSS compliant gateways (Razorpay, Stripe) — we never store your card details.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">5. Your Rights</h2>
          <p className="text-gray-600">Under the DPDP Act 2023 and GDPR, you have the right to:</p>
          <p className="text-gray-600">
            <strong>Access:</strong> View your personal data via your account dashboard.
            <br /><strong>Correction:</strong> Update your profile and address information.
            <br /><strong>Erasure:</strong> Request account deletion (30-day grace period applies).
            <br /><strong>Data Portability:</strong> Export your data in machine-readable format (JSON).
            <br /><strong>Withdraw Consent:</strong> Opt out of marketing communications at any time.
          </p>
          <p className="text-gray-600">
            You can exercise these rights from your <Link to="/privacy" className="text-black underline font-medium">Privacy & Consent</Link> settings page.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">6. Data Retention</h2>
          <p className="text-gray-600">
            We retain your personal data for as long as your account is active.
            Upon account deletion, personal data is anonymized after a 30-day grace period.
            Order records and invoices are retained for a minimum of 6 years as required
            by Indian tax law (GST compliance) and the Income Tax Act.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">7. Cookies</h2>
          <p className="text-gray-600">
            We use essential cookies for authentication and cart functionality (always active),
            analytics cookies to understand site usage (with your consent), and
            marketing cookies for personalized recommendations (with your consent).
            You can manage cookie preferences via the banner shown on your first visit.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">8. Contact</h2>
          <p className="text-gray-600">
            For privacy-related queries, contact our Data Protection Officer at:{' '}
            <a href="mailto:privacy@ashmistore.com" className="text-black underline font-medium">privacy@ashmistore.com</a>
          </p>
        </section>
      </div>
    </div>
  );
}
