import React, { useState } from 'react';
import { X } from 'lucide-react';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

export const AuthModal = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState(initialMode);

  if (!isOpen) return null;

  const handleSwitchToRegister = () => setMode('register');
  const handleSwitchToLogin = () => setMode('login');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="relative max-w-md w-full">
        <button
          onClick={onClose}
          className="absolute -top-4 -right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 z-10"
        >
          <X className="h-5 w-5 text-gray-600" />
        </button>
        
        {mode === 'login' ? (
          <LoginForm 
            onSwitchToRegister={handleSwitchToRegister}
            onClose={onClose}
          />
        ) : (
          <RegisterForm 
            onSwitchToLogin={handleSwitchToLogin}
            onClose={onClose}
          />
        )}
      </div>
    </div>
  );
};