/**
 * TermsOfServicePage — Phase F5
 */
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function TermsOfServicePage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-black mb-6 transition">
        <ArrowLeft size={16} /> Back to Home
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
      <p className="text-sm text-gray-500 mb-8">Last updated: February 2026 | Version 1.0</p>

      <div className="prose prose-sm prose-gray max-w-none space-y-6">
        <section>
          <h2 className="text-lg font-semibold text-gray-900">1. Acceptance of Terms</h2>
          <p className="text-gray-600">
            By creating an account or making a purchase on Ashmi Store, you agree to these Terms of Service.
            If you do not agree, please do not use our platform.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">2. Account Registration</h2>
          <p className="text-gray-600">
            You must provide accurate information during registration. You are responsible for
            maintaining the confidentiality of your account credentials. You must be at least
            18 years old or have parental consent to create an account.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">3. Products & Pricing</h2>
          <p className="text-gray-600">
            All prices are displayed in Indian Rupees (INR) unless otherwise specified.
            Prices include applicable GST. We reserve the right to modify prices at any time.
            Product images are representative; actual colors may vary slightly.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">4. Orders & Payments</h2>
          <p className="text-gray-600">
            An order is confirmed only after successful payment processing. We accept UPI,
            Net Banking, Debit/Credit Cards via Razorpay (India) and Stripe (Global).
            A GST-compliant tax invoice is generated for every confirmed order.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">5. Shipping & Delivery</h2>
          <p className="text-gray-600">
            Delivery timelines are estimates and may vary based on location and courier availability.
            We ship across India and select international destinations. Shipping charges, if applicable,
            are displayed at checkout before payment.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">6. Returns & Refunds</h2>
          <p className="text-gray-600">
            Returns are accepted within 7 days of delivery for eligible products.
            Items must be unused, unwashed, and in original packaging with tags intact.
            Refunds are processed within 5-7 business days after return receipt.
            A GST credit note is issued for every refund.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">7. Cancellation</h2>
          <p className="text-gray-600">
            Orders can be cancelled before shipment (while in "placed", "confirmed", or "processing" status).
            Once shipped, cancellation is not possible — please initiate a return after delivery.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">8. Intellectual Property</h2>
          <p className="text-gray-600">
            All content on this platform including logos, product images, descriptions, and design
            is the property of Ashmi Store and protected under applicable copyright laws.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">9. Governing Law</h2>
          <p className="text-gray-600">
            These terms are governed by the laws of India. Any disputes shall be subject to the
            exclusive jurisdiction of the courts in Mumbai, Maharashtra.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-gray-900">10. Contact</h2>
          <p className="text-gray-600">
            For questions about these terms, contact us at:{' '}
            <a href="mailto:support@ashmistore.com" className="text-black underline font-medium">support@ashmistore.com</a>
          </p>
        </section>
      </div>
    </div>
  );
}
