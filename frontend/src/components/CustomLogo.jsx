import React from 'react';

export const CustomLogo = ({ className = "h-8 w-8" }) => {
  return (
    <div className={`${className} relative flex items-center justify-center`}>
      {/* Main blue circle background */}
      <div className="absolute inset-0 bg-blue-600 rounded-full shadow-lg">
      </div>
      
      {/* Globe with shopping bag handle design */}
      <svg 
        viewBox="0 0 32 32" 
        className="relative z-10 w-full h-full p-1"
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Shopping bag handle at the top */}
        <path 
          d="M12 7C12 5.5 13.5 4 16 4C18.5 4 20 5.5 20 7" 
          stroke="white" 
          strokeWidth="2.5" 
          strokeLinecap="round"
          fill="none"
        />
        
        {/* Main globe circle */}
        <circle 
          cx="16" 
          cy="18" 
          r="11" 
          stroke="white" 
          strokeWidth="2.5" 
          fill="none"
        />
        
        {/* Vertical center meridian line */}
        <path 
          d="M16 7L16 29" 
          stroke="white" 
          strokeWidth="1.8"
        />
        
        {/* Horizontal equator line */}
        <path 
          d="M5 18L27 18" 
          stroke="white" 
          strokeWidth="1.8"
        />
        
        {/* Left curved meridian */}
        <path 
          d="M16 7C16 7 10 10 10 18C10 26 16 29 16 29" 
          stroke="white" 
          strokeWidth="1.5" 
          fill="none"
        />
        
        {/* Right curved meridian */}
        <path 
          d="M16 7C16 7 22 10 22 18C22 26 16 29 16 29" 
          stroke="white" 
          strokeWidth="1.5" 
          fill="none"
        />
        
        {/* Upper latitude line */}
        <path 
          d="M7 13C7 13 10.5 12 16 12C21.5 12 25 13 25 13" 
          stroke="white" 
          strokeWidth="1.4" 
          fill="none"
        />
        
        {/* Lower latitude line */}
        <path 
          d="M7 23C7 23 10.5 24 16 24C21.5 24 25 23 25 23" 
          stroke="white" 
          strokeWidth="1.4" 
          fill="none"
        />
        
        {/* Additional subtle latitude lines */}
        <path 
          d="M9 10C9 10 12 9.5 16 9.5C20 9.5 23 10 23 10" 
          stroke="white" 
          strokeWidth="1" 
          fill="none"
          opacity="0.7"
        />
        
        <path 
          d="M9 26C9 26 12 26.5 16 26.5C20 26.5 23 26 23 26" 
          stroke="white" 
          strokeWidth="1" 
          fill="none"
          opacity="0.7"
        />
        
        {/* Outer meridian curves for more globe detail */}
        <path 
          d="M16 7C16 7 8 11 8 18C8 25 16 29 16 29" 
          stroke="white" 
          strokeWidth="1" 
          fill="none"
          opacity="0.5"
        />
        
        <path 
          d="M16 7C16 7 24 11 24 18C24 25 16 29 16 29" 
          stroke="white" 
          strokeWidth="1" 
          fill="none"
          opacity="0.5"
        />
      </svg>
      
      {/* Subtle shine effect */}
      <div className="absolute top-1 left-1.5 w-2.5 h-2.5 bg-white rounded-full opacity-25"></div>
    </div>
  );
};