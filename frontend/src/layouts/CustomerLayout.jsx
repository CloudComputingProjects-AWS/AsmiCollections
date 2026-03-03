import { Outlet } from 'react-router-dom';
import CustomerHeader from '../components/layout/CustomerHeader';
import CustomerFooter from '../components/layout/CustomerFooter';

export default function CustomerLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <CustomerHeader />
      <main id="main-content" className="flex-1">
        <Outlet />
      </main>
      <CustomerFooter />
    </div>
  );
}
