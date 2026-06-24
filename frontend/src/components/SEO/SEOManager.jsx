import React, { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';

// Russian keywords database for international shopping
const RUSSIAN_KEYWORDS = {
  primary: [
    'покупки из-за границы',
    'заказ товаров из-за рубежа', 
    'доставка из-за границы',
    'международная доставка товаров',
    'покупки в зарубежных магазинах',
    'заказ из США в Россию',
    'доставка из Европы',
    'покупки из Китая',
    'сервис доставки из-за рубежа',
    'посредник для покупок за границей'
  ],
  secondary: [
    'выкуп товаров за рубежом',
    'консолидация посылок',
    'таможенное оформление',
    'доставка из Amazon',
    'заказ из eBay',
    'покупки из интернет-магазинов США',
    'доставка брендовых товаров',
    'оригинальная техника из-за границы',
    'Apple из США',
    'Samsung из Европы',
    'международный шопинг',
    'зарубежные покупки онлайн'
  ],
  longTail: [
    'как заказать товары из-за границы в Россию',
    'сколько стоит доставка из-за рубежа',
    'надежный сервис покупок из-за границы',
    'доставка оригинальных товаров из США',
    'покупки из зарубежных магазинов с доставкой в Москву',
    'заказать технику из-за границы дешево',
    'международная доставка с таможенным оформлением',
    'сервис выкупа товаров из интернет-магазинов',
    'доставка товаров из Европы и США в Россию',
    'покупки за рубежом через посредника'
  ],
  branded: [
    'BuyAnywhere покупки',
    'BuyAnywhere доставка',
    'БайЭниВэр сервис',
    'персональный сервис покупок',
    'агентские услуги покупок'
  ],
  cities: [
    'доставка в Москву',
    'доставка в Санкт-Петербург', 
    'доставка в Екатеринбург',
    'доставка в Новосибирск',
    'доставка в Казань',
    'доставка в Нижний Новгород',
    'доставка в Краснодар',
    'доставка в Самару',
    'доставка в Уфу',
    'доставка в Ростов-на-Дону'
  ]
};

// SEO content templates
const SEO_TEMPLATES = {
  home: {
    title: 'Покупки из-за границы | BuyAnywhere - Персональный сервис доставки товаров',
    description: 'Покупаем товары из любых зарубежных интернет-магазинов с доставкой в Россию. Оригинальная техника, одежда, товары из США, Европы, Китая. Таможенное оформление, страхование. Оплата в рублях.',
    keywords: RUSSIAN_KEYWORDS.primary.join(', ')
  },
  services: {
    title: 'Услуги доставки из-за рубежа | Выкуп товаров из зарубежных магазинов',
    description: 'Полный спектр услуг международного шопинга: выкуп товаров, консолидация посылок, таможенное оформление, доставка по России. Покупаем в Amazon, eBay, европейских и китайских магазинах.',
    keywords: RUSSIAN_KEYWORDS.secondary.join(', ')
  },
  calculator: {
    title: 'Калькулятор стоимости доставки из-за границы | Рассчитать цену заказа',
    description: 'Точный расчет стоимости покупки и доставки товаров из-за рубежа. Узнайте полную цену с учетом комиссии, доставки и таможенных пошлин. Прозрачное ценообразование.',
    keywords: 'калькулятор доставки, стоимость доставки из-за границы, рассчитать доставку товаров'
  }
};

export const SEOManager = ({ 
  page = 'home', 
  title, 
  description, 
  keywords,
  product = null,
  category = null,
  canonical = null
}) => {
  // Dynamic keyword generation based on current trends
  const generateDynamicKeywords = () => {
    const currentDate = new Date();
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    
    let seasonalKeywords = [];
    
    // Seasonal keywords
    if (month >= 11 || month <= 1) {
      seasonalKeywords = ['новогодние покупки из-за границы', 'подарки из-за рубежа', 'праздничная доставка'];
    } else if (month >= 6 && month <= 8) {
      seasonalKeywords = ['летние товары из-за границы', 'отпускные покупки'];
    }
    
    // Trending tech keywords
    const techKeywords = [
      `iPhone ${year - 2010} из США`,
      'новейшие гаджеты из-за границы',
      'электроника из Европы',
      'игровые консоли из-за рубежа'
    ];
    
    return [...seasonalKeywords, ...techKeywords];
  };

  // Get template or custom SEO data
  const seoData = SEO_TEMPLATES[page] || {
    title: title || 'BuyAnywhere - Покупки из-за границы',
    description: description || 'Персональный сервис покупок из зарубежных интернет-магазинов',
    keywords: keywords || RUSSIAN_KEYWORDS.primary.join(', ')
  };

  // Enhanced keywords with dynamic content
  const enhancedKeywords = [
    ...seoData.keywords.split(', '),
    ...generateDynamicKeywords(),
    ...(product ? [`купить ${product} из-за границы`, `${product} доставка в Россию`] : []),
    ...(category ? [`${category} из-за рубежа`, `зарубежные ${category}`] : [])
  ].join(', ');

  // Structured data for search engines
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": "https://buyanywhere.ru/#organization",
    "name": "BuyAnywhere",
    "alternateName": "БайЭниВэр",
    "url": "https://buyanywhere.ru",
    "logo": "https://buyanywhere.ru/logo.png",
    "description": "Персональный сервис покупок из зарубежных интернет-магазинов с доставкой в Россию",
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "RU",
      "addressLocality": "Москва"
    },
    "contactPoint": {
      "@type": "ContactPoint",
      "telephone": "+7-495-123-45-67",
      "contactType": "customer service",
      "availableLanguage": "Russian"
    },
    "sameAs": [
      "https://t.me/BuyAnywhereSupport"
    ],
    "offers": {
      "@type": "Offer",
      "description": "Услуги по покупке и доставке товаров из зарубежных интернет-магазинов",
      "priceRange": "от 1500 ₽"
    },
    "serviceType": [
      "Международная доставка",
      "Покупки из-за рубежа",
      "Таможенное оформление",
      "Консолидация посылок"
    ]
  };

  // Website structured data
  const websiteStructuredData = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": "https://buyanywhere.ru/#website",
    "name": "BuyAnywhere",
    "url": "https://buyanywhere.ru",
    "description": "Сервис покупок из зарубежных интернет-магазинов",
    "inLanguage": "ru-RU",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://buyanywhere.ru/search?q={search_term_string}",
      "query-input": "required name=search_term_string"
    }
  };

  // Service structured data
  const serviceStructuredData = {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Покупки из-за границы",
    "description": "Персональный сервис покупок и доставки товаров из зарубежных интернет-магазинов",
    "provider": {
      "@type": "Organization",
      "name": "BuyAnywhere"
    },
    "serviceType": "Международная доставка и покупки",
    "areaServed": {
      "@type": "Country",
      "name": "Россия"
    },
    "offers": {
      "@type": "Offer",
      "priceRange": "от 1500 ₽",
      "priceCurrency": "RUB"
    }
  };

  useEffect(() => {
    // Yandex Metrica integration
    if (typeof window !== 'undefined' && window.ym) {
      window.ym(12345678, 'hit', window.location.href, {
        title: seoData.title
      });
    }

    // Google Analytics 4 integration
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('config', 'G-XXXXXXXXXX', {
        page_title: seoData.title,
        page_location: window.location.href
      });
    }
  }, [page, seoData.title]);

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{seoData.title}</title>
      <meta name="description" content={seoData.description} />
      <meta name="keywords" content={enhancedKeywords} />
      
      {/* Canonical URL */}
      {canonical && <link rel="canonical" href={canonical} />}
      
      {/* Language and Region */}
      <html lang="ru" />
      <meta name="language" content="Russian" />
      <meta name="geo.region" content="RU" />
      <meta name="geo.country" content="Russia" />
      
      {/* Open Graph Tags */}
      <meta property="og:title" content={seoData.title} />
      <meta property="og:description" content={seoData.description} />
      <meta property="og:type" content="website" />
      <meta property="og:url" content={canonical || "https://buyanywhere.ru"} />
      <meta property="og:image" content="https://buyanywhere.ru/og-image.jpg" />
      <meta property="og:image:alt" content="BuyAnywhere - Покупки из-за границы" />
      <meta property="og:locale" content="ru_RU" />
      <meta property="og:site_name" content="BuyAnywhere" />
      
      {/* Twitter Cards */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={seoData.title} />
      <meta name="twitter:description" content={seoData.description} />
      <meta name="twitter:image" content="https://buyanywhere.ru/twitter-image.jpg" />
      
      {/* Yandex Specific Tags */}
      <meta name="yandex-verification" content="your-yandex-verification-code" />
      <meta name="yandex-verification" content="your-yandex-webmaster-code" />
      
      {/* Google Specific Tags */}
      <meta name="google-site-verification" content="your-google-verification-code" />
      
      {/* Mobile and Responsive */}
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      
      {/* Favicons */}
      <link rel="icon" type="image/x-icon" href="/favicon.ico" />
      <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
      
      {/* Structured Data */}
      <script type="application/ld+json">
        {JSON.stringify(structuredData)}
      </script>
      <script type="application/ld+json">
        {JSON.stringify(websiteStructuredData)}
      </script>
      <script type="application/ld+json">
        {JSON.stringify(serviceStructuredData)}
      </script>
      
      {/* Hreflang for multi-language support */}
      <link rel="alternate" hrefLang="ru" href="https://buyanywhere.ru" />
      <link rel="alternate" hrefLang="x-default" href="https://buyanywhere.ru" />
      
      {/* DNS Prefetch and Preconnect */}
      <link rel="dns-prefetch" href="//mc.yandex.ru" />
      <link rel="dns-prefetch" href="//www.google-analytics.com" />
      <link rel="dns-prefetch" href="//fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      
      {/* Robots Meta */}
      <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />
      <meta name="googlebot" content="index, follow" />
      <meta name="yandex" content="index, follow" />
      
      {/* Additional SEO Tags */}
      <meta name="author" content="BuyAnywhere" />
      <meta name="copyright" content="© 2025 BuyAnywhere. Все права защищены." />
      <meta name="revisit-after" content="1 day" />
      <meta name="rating" content="general" />
      <meta name="distribution" content="global" />
    </Helmet>
  );
};

export default SEOManager;