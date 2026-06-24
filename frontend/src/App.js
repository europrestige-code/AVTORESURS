import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from 'react-helmet-async';
import { AuthProvider } from "./contexts/AuthContext";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { Services } from "./components/Services";
import { OrderForm } from "./components/OrderForm";
import { StatisticsCounter } from "./components/StatisticsCounter";
import { NewsSection } from "./components/NewsSection";
import { PaymentMethods } from "./components/PaymentMethods";
import { Guarantees } from "./components/Guarantees";
import { FAQ } from "./components/FAQ";
import { Footer } from "./components/Footer";
import SEOManager from "./components/SEO/SEOManager";
import { SEODashboard } from "./components/SEO/SEODashboard";
import { CustomerDashboard } from "./components/CustomerDashboard";
import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import LogoShowcase from "./components/LogoShowcase";
import { useAuth } from "./contexts/AuthContext";
import AutoLayout from "./pages/auto/AutoLayout";
import AutoHome from "./pages/auto/AutoHome";
import AutoCatalog from "./pages/auto/AutoCatalog";
import AutoVehicleDetail from "./pages/auto/AutoVehicleDetail";
import AutoDashboard from "./pages/auto/AutoDashboard";
import AutoAdmin from "./pages/auto/AutoAdmin";
import AutoHowItWorks from "./pages/auto/AutoHowItWorks";
import AutoFees from "./pages/auto/AutoFees";
import AutoAustralia from "./pages/auto/AutoAustralia";

const Home = () => {
  return (
    <>
      <SEOManager page="home" />
      <Hero />
      <Services />
      <OrderForm />
      <StatisticsCounter />
      <NewsSection />
      <PaymentMethods />
      <Guarantees />
      <FAQ />
    </>
  );
};

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загружаем...</p>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Необходима авторизация
          </h2>
          <p className="text-gray-600 mb-8">
            Пожалуйста, войдите в систему или зарегистрируйтесь для доступа к личному кабинету
          </p>
          <div className="space-x-4">
            <button 
              onClick={() => window.location.href = '/'}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium"
            >
              На главную
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return children;
};

// Admin components and routing
const AdminApp = () => {
  const [adminUser, setAdminUser] = useState(null);
  
  useEffect(() => {
    // Check for existing admin token
    const token = localStorage.getItem('admin_token');
    if (token) {
      // Set token in API headers
      import('./services/api').then(({ default: api }) => {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        // Verify token validity
        api.get('/api/admin/auth/me')
          .then(response => {
            setAdminUser(response.data);
          })
          .catch(() => {
            localStorage.removeItem('admin_token');
            delete api.defaults.headers.common['Authorization'];
          });
      });
    }
  }, []);

  const handleAdminLogin = (user) => {
    setAdminUser(user);
  };

  const handleAdminLogout = () => {
    localStorage.removeItem('admin_token');
    setAdminUser(null);
    import('./services/api').then(({ default: api }) => {
      delete api.defaults.headers.common['Authorization'];
    });
  };

  if (!adminUser) {
    return <AdminLogin onLogin={handleAdminLogin} />;
  }

  return <AdminDashboard user={adminUser} onLogout={handleAdminLogout} />;
};

function App() {
  return (
    <div className="App">
      <HelmetProvider>
        <BrowserRouter>
          <AuthProvider>
          <div className="min-h-screen bg-white">
            <Routes>
              {/* Admin routes */}
              <Route path="/admin/*" element={<AdminApp />} />

              {/* BuyAnywhere Auto */}
              <Route path="/auto" element={<AutoLayout />}>
                <Route index element={<AutoHome />} />
                <Route path="catalog" element={<AutoCatalog />} />
                <Route path="vehicle/:id" element={<AutoVehicleDetail />} />
                <Route path="dashboard" element={<AutoDashboard />} />
                <Route path="admin" element={<AutoAdmin />} />
                <Route path="how-it-works" element={<AutoHowItWorks />} />
                <Route path="fees" element={<AutoFees />} />
                <Route path="australia" element={<AutoAustralia />} />
              </Route>

              {/* Regular app routes */}
              <Route path="/*" element={
                <>
                  <Header />
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/logo-showcase" element={<LogoShowcase />} />
                    <Route path="/seo-dashboard" element={<SEODashboard />} />
                    <Route 
                      path="/dashboard" 
                      element={
                        <ProtectedRoute>
                          <CustomerDashboard />
                        </ProtectedRoute>
                      } 
                    />
                  </Routes>
                  <Footer />
                </>
              } />
            </Routes>
          </div>
        </AuthProvider>
      </BrowserRouter>
      </HelmetProvider>
    </div>
  );
}

export default App;