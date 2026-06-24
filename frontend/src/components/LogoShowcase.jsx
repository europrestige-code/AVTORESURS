import React from 'react';
import NewBuyAnywhereLogo, { BuyAnywhereIcon, BuyAnywhereText } from './NewBuyAnywhereLogo';

const LogoShowcase = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            BuyAnywhere Logo Showcase
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            New brand identity with shopping bag globe icon, featuring black "BuyAnywhere" text, 
            charcoal grey Russian subtitle, and a blue shopping bag globe icon (10% larger, no white background).
          </p>
        </div>

        {/* Logo Variants on Light Background */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Light Background Variants</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Size Variants */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">Size Variants</h3>
              <div className="space-y-6">
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Small</span>
                  <NewBuyAnywhereLogo size="small" />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Default</span>
                  <NewBuyAnywhereLogo size="default" />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Large</span>
                  <NewBuyAnywhereLogo size="large" />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Hero</span>
                  <NewBuyAnywhereLogo size="hero" />
                </div>
              </div>
            </div>

            {/* Individual Components */}
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">Component Variants</h3>
              <div className="space-y-6">
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Icon Only (24px)</span>
                  <BuyAnywhereIcon size={24} />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Icon Only (48px)</span>
                  <BuyAnywhereIcon size={48} />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-600">Text Only</span>
                  <BuyAnywhereText size="default" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Logo Variants on Dark Background */}
        <div className="bg-gray-900 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold text-white mb-6">Dark Background Variants</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium text-white mb-4">Size Variants</h3>
              <div className="space-y-6">
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-400">Small Dark</span>
                  <NewBuyAnywhereLogo size="small" variant="dark" />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-400">Default Dark</span>
                  <NewBuyAnywhereLogo size="default" variant="dark" />
                </div>
                
                <div className="flex flex-col space-y-2">
                  <span className="text-sm text-gray-400">Large Dark</span>
                  <NewBuyAnywhereLogo size="large" variant="dark" />
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-4">Usage Examples</h3>
              <div className="space-y-4 text-gray-300">
                <p className="text-sm">
                  ✓ Header navigation (default size, light variant)
                </p>
                <p className="text-sm">
                  ✓ Footer branding (small size, dark variant)
                </p>
                <p className="text-sm">
                  ✓ Hero sections (hero size, light variant)
                </p>
                <p className="text-sm">
                  ✓ Mobile apps (icon only, various sizes)
                </p>
                <p className="text-sm">
                  ✓ Favicons and social media (icon only, 32px+)
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Usage Guidelines */}
        <div className="bg-blue-50 rounded-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold text-blue-900 mb-6">Brand Guidelines</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium text-blue-800 mb-4">Design Elements</h3>
              <ul className="space-y-2 text-blue-700">
                <li>• <strong>Main Text:</strong> Black "BuyAnywhere" (font-bold)</li>
                <li>• <strong>Subtitle:</strong> Charcoal grey "Персональный Сервис Покупок"</li>
                <li>• <strong>Icon:</strong> Blue shopping bag globe (10% larger scale)</li>
                <li>• <strong>Colors:</strong> Blue (#3B82F6), White, Black, Grey</li>
                <li>• <strong>Globe:</strong> Simplified continents with grid lines</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-medium text-blue-800 mb-4">Usage Rules</h3>
              <ul className="space-y-2 text-blue-700">
                <li>• Use "light" variant on light backgrounds</li>
                <li>• Use "dark" variant on dark backgrounds</li>
                <li>• Maintain minimum clear space around logo</li>
                <li>• Don't modify colors or proportions</li>
                <li>• Use appropriate size for context</li>
                <li>• Icon-only for favicons and small spaces</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Technical Specifications */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Technical Specifications</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">Size Chart</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>Small:</strong> 32px height (logos, mobile)</p>
                <p><strong>Default:</strong> 48px height (headers)</p>
                <p><strong>Large:</strong> 64px height (sections)</p>
                <p><strong>Hero:</strong> 80px height (landing pages)</p>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">Color Codes</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>Primary Blue:</strong> #3B82F6</p>
                <p><strong>Dark Blue:</strong> #2563EB</p>
                <p><strong>Black Text:</strong> #000000</p>
                <p><strong>Grey Subtitle:</strong> #4B5563</p>
                <p><strong>White:</strong> #FFFFFF</p>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-4">Component Props</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>size:</strong> small | default | large | hero</p>
                <p><strong>variant:</strong> light | dark</p>
                <p><strong>className:</strong> Custom CSS classes</p>
                <p><strong>Icon size:</strong> Number (pixels)</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default LogoShowcase;