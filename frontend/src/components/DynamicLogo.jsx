import React, { useState, useEffect } from 'react';
import NewBuyAnywhereLogo from './NewBuyAnywhereLogo';

export const DynamicLogo = ({ size = "default", className = "" }) => {
  const [customLogo, setCustomLogo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCurrentLogo();
    
    // Listen for logo updates
    const handleLogoUpdate = () => {
      loadCurrentLogo();
    };
    
    window.addEventListener('logoUpdated', handleLogoUpdate);
    
    return () => {
      window.removeEventListener('logoUpdated', handleLogoUpdate);
    };
  }, []);

  const loadCurrentLogo = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/logo/current`);
      
      if (response.ok) {
        const blob = await response.blob();
        const logoUrl = URL.createObjectURL(blob);
        setCustomLogo(logoUrl);
      } else {
        setCustomLogo(null);
      }
    } catch (error) {
      console.log('No custom logo found, using default');
      setCustomLogo(null);
    } finally {
      setLoading(false);
    }
  };

  // Size mappings
  const sizeClasses = {
    small: "h-8 w-auto",
    default: "h-10 w-auto", 
    large: "h-16 w-auto"
  };

  if (loading) {
    return (
      <div className={`${sizeClasses[size]} ${className} bg-gray-200 animate-pulse rounded`}>
        <div className="w-32 h-full"></div>
      </div>
    );
  }

  if (customLogo) {
    return (
      <img 
        src={customLogo}
        alt="BuyAnywhere Logo"
        className={`${sizeClasses[size]} ${className} object-contain`}
        onError={() => {
          // Fallback to default logo on error
          setCustomLogo(null);
        }}
      />
    );
  }

  // Fallback to default logo component
  return <NewBuyAnywhereLogo size={size} className={className} />;
};