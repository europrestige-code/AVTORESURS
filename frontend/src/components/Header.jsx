import React, { useState } from "react";
import { DynamicLogo } from "./DynamicLogo";
import { Button } from "./ui/button";
import { AuthModal } from "./AuthModal";
import { useAuth } from "../contexts/AuthContext";
import { User, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

export const Header = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [authModal, setAuthModal] = useState({ isOpen: false, mode: 'login' });
  const navigate = useNavigate();

  const handleAuthModal = (mode) => {
    setAuthModal({ isOpen: true, mode });
  };

  const closeAuthModal = () => {
    setAuthModal({ isOpen: false, mode: 'login' });
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <>
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Brand */}
            <div 
              className="flex items-center cursor-pointer"
              onClick={() => navigate('/')}
            >
              <DynamicLogo size="default" />
            </div>

            {/* Contact Info and Auth */}
            <div className="flex items-center space-x-3 sm:space-x-6">
              {/* Авто Link */}
              <button
                onClick={() => navigate('/auto')}
                data-testid="header-auto-link"
                className="hidden sm:inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold bg-gray-900 text-white hover:bg-blue-600 transition-colors"
              >
                Авто
              </button>
              {/* Contact Info */}
              <div className="hidden md:block text-right">
                <div className="text-sm font-medium text-gray-900">
                  Звоните: +7 (495) 123-45-67
                </div>
                <div className="text-xs text-gray-500">
                  Работаем 24/7
                </div>
              </div>

              {/* Authentication Section */}
              {isAuthenticated ? (
                <div className="mobile-header-auth">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDashboard}
                    className="mobile-btn flex items-center px-2 sm:px-4"
                  >
                    <User className="h-4 w-4 mr-1 sm:mr-2" />
                    <span className="mobile-user-name hidden sm:inline">
                      {user?.customer_info?.first_name || 'Кабинет'}
                    </span>
                    <span className="sm:hidden">
                      Кабинет
                    </span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLogout}
                    className="mobile-btn flex items-center text-gray-600 hover:text-gray-900 px-2"
                  >
                    <LogOut className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="mobile-header-auth">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAuthModal('login')}
                    className="mobile-btn px-2 sm:px-4 text-xs sm:text-sm"
                  >
                    Войти
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleAuthModal('register')}
                    className="mobile-btn bg-blue-600 hover:bg-blue-700 px-2 sm:px-4 text-xs sm:text-sm"
                  >
                    <span className="sm:hidden">Рег-ция</span>
                    <span className="hidden sm:inline">Регистрация</span>
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModal.isOpen}
        onClose={closeAuthModal}
        initialMode={authModal.mode}
      />
    </>
  );
};