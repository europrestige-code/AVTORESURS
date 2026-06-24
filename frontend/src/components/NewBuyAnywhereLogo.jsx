import React from 'react';

const NewBuyAnywhereLogo = ({ className = "", size = "default", variant = "light" }) => {
  // Size variants
  const sizeConfig = {
    small: {
      container: "h-8",
      text: "text-lg",
      subtitle: "text-xs",
      icon: "w-7 h-7"
    },
    default: {
      container: "h-12",
      text: "text-2xl",
      subtitle: "text-sm",
      icon: "w-10 h-10"
    },
    large: {
      container: "h-16",
      text: "text-3xl",
      subtitle: "text-base",
      icon: "w-13 h-13"
    },
    hero: {
      container: "h-20",
      text: "text-4xl",
      subtitle: "text-lg",
      icon: "w-16 h-16"
    }
  };

  const config = sizeConfig[size] || sizeConfig.default;

  // Color variants
  const colors = {
    light: {
      mainText: "text-black",
      subtitle: "text-gray-600"
    },
    dark: {
      mainText: "text-white",
      subtitle: "text-gray-300"
    }
  };

  const colorConfig = colors[variant] || colors.light;

  // Shopping Bag Globe Icon Component (10% larger than standard)
  const ShoppingBagGlobeIcon = ({ className: iconClassName }) => (
    <div className={`relative ${iconClassName}`} style={{ transform: 'scale(1.1)' }}>
      {/* Globe Background */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute inset-0 w-full h-full"
      >
        {/* Globe Circle */}
        <circle
          cx="12"
          cy="12"
          r="10"
          fill="#3B82F6"
          stroke="#2563EB"
          strokeWidth="1"
          opacity="0.9"
        />
        
        {/* Globe Grid Lines */}
        <path
          d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
          stroke="white"
          strokeWidth="0.5"
          opacity="0.7"
        />
        
        {/* Additional meridian lines */}
        <path
          d="M12 2v20"
          stroke="white"
          strokeWidth="0.5"
          opacity="0.5"
        />
        
        {/* Continents simplified */}
        <path
          d="M8 8c1-1 2-1 3 0s2 2 1 3-2 1-3 0-2-2-1-3z"
          fill="white"
          opacity="0.6"
        />
        <path
          d="M14 6c1 0 2 1 2 2s-1 2-2 2-2-1-2-2 1-2 2-2z"
          fill="white"
          opacity="0.6"
        />
        <path
          d="M6 14c1-1 3 0 4 1s0 3-1 2-3-2-3-3z"
          fill="white"
          opacity="0.6"
        />
      </svg>
      
      {/* Shopping Bag Overlay */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute inset-0 w-full h-full"
      >
        {/* Shopping bag */}
        <path
          d="M6 6h12l-1 12H7L6 6z"
          fill="white"
          stroke="#2563EB"
          strokeWidth="1.5"
          opacity="0.9"
        />
        
        {/* Shopping bag handles */}
        <path
          d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"
          stroke="#2563EB"
          strokeWidth="1.5"
          fill="none"
          opacity="0.8"
        />
        
        {/* Shopping bag fold */}
        <path
          d="M6 8h12"
          stroke="#2563EB"
          strokeWidth="1"
          opacity="0.6"
        />
      </svg>
    </div>
  );

  return (
    <div className={`flex items-center space-x-3 ${config.container} ${className}`}>
      {/* Icon */}
      <ShoppingBagGlobeIcon className={config.icon} />
      
      {/* Text Content */}
      <div className="flex flex-col justify-center">
        {/* Main Logo Text - Dynamic Color */}
        <div className={`font-bold leading-tight ${config.text} ${colorConfig.mainText}`}>
          BuyAnywhere
        </div>
        
        {/* Subtitle - Dynamic Color */}
        <div className={`font-medium leading-tight ${config.subtitle} ${colorConfig.subtitle}`}>
          Персональный Сервис Покупок
        </div>
      </div>
    </div>
  );
};

// Variant for just the icon (useful for favicons, small spaces)
export const BuyAnywhereIcon = ({ className = "", size = 24 }) => {
  const ShoppingBagGlobeIcon = () => (
    <div className="relative" style={{ width: size, height: size, transform: 'scale(1.1)' }}>
      {/* Globe Background */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute inset-0 w-full h-full"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          fill="#3B82F6"
          stroke="#2563EB"
          strokeWidth="1"
        />
        <path
          d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
          stroke="white"
          strokeWidth="0.5"
          opacity="0.7"
        />
        <path
          d="M12 2v20"
          stroke="white"
          strokeWidth="0.5"
          opacity="0.5"
        />
        <path
          d="M8 8c1-1 2-1 3 0s2 2 1 3-2 1-3 0-2-2-1-3z"
          fill="white"
          opacity="0.6"
        />
        <path
          d="M14 6c1 0 2 1 2 2s-1 2-2 2-2-1-2-2 1-2 2-2z"
          fill="white"
          opacity="0.6"
        />
      </svg>
      
      {/* Shopping Bag Overlay */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute inset-0 w-full h-full"
      >
        <path
          d="M6 6h12l-1 12H7L6 6z"
          fill="white"
          stroke="#2563EB"
          strokeWidth="1.5"
        />
        <path
          d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"
          stroke="#2563EB"
          strokeWidth="1.5"
          fill="none"
        />
        <path
          d="M6 8h12"
          stroke="#2563EB"
          strokeWidth="1"
          opacity="0.6"
        />
      </svg>
    </div>
  );

  return (
    <div className={className}>
      <ShoppingBagGlobeIcon />
    </div>
  );
};

// Text-only variant (for cases where space is very limited)
export const BuyAnywhereText = ({ className = "", size = "default" }) => {
  const sizeConfig = {
    small: { text: "text-lg", subtitle: "text-xs" },
    default: { text: "text-2xl", subtitle: "text-sm" },
    large: { text: "text-3xl", subtitle: "text-base" }
  };

  const config = sizeConfig[size] || sizeConfig.default;

  return (
    <div className={`flex flex-col ${className}`}>
      <div className={`font-bold text-black leading-tight ${config.text}`}>
        BuyAnywhere
      </div>
      <div className={`text-gray-600 font-medium leading-tight ${config.subtitle}`}>
        Персональный Сервис Покупок
      </div>
    </div>
  );
};

export default NewBuyAnywhereLogo;