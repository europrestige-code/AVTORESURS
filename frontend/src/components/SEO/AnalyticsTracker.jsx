import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

// Google Analytics 4 and Yandex Metrica tracking component
export const AnalyticsTracker = () => {
  const location = useLocation();

  useEffect(() => {
    // Google Analytics 4 tracking
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('config', 'G-XXXXXXXXXX', {
        page_title: document.title,
        page_location: window.location.href,
        custom_map: {
          'custom_parameter_1': 'user_type',
          'custom_parameter_2': 'order_value'
        }
      });

      // Track page view
      window.gtag('event', 'page_view', {
        page_title: document.title,
        page_location: window.location.href,
        page_path: location.pathname,
        event_category: 'engagement',
        event_label: 'page_view'
      });
    }

    // Yandex Metrica tracking
    if (typeof window !== 'undefined' && window.ym) {
      window.ym(12345678, 'hit', window.location.href, {
        title: document.title,
        referer: document.referrer,
        params: {
          page_type: getPageType(location.pathname),
          user_language: navigator.language || 'ru',
          screen_resolution: `${screen.width}x${screen.height}`
        }
      });

      // Track Russian-specific events
      window.ym(12345678, 'reachGoal', 'PAGE_VIEW', {
        page: location.pathname,
        timestamp: new Date().toISOString()
      });
    }
  }, [location]);

  // Determine page type for analytics
  const getPageType = (pathname) => {
    if (pathname === '/') return 'homepage';
    if (pathname.includes('/admin')) return 'admin';
    if (pathname.includes('/customer-dashboard')) return 'customer_area';
    if (pathname.includes('/categories')) return 'category';
    if (pathname.includes('/brands')) return 'brand';
    if (pathname.includes('/countries')) return 'country';
    if (pathname.includes('/blog') || pathname.includes('/news')) return 'content';
    return 'other';
  };

  return null; // This component doesn't render anything
};

// Track custom events for SEO and conversion analysis
export const trackSEOEvent = (action, category = 'SEO', label = '', value = 0) => {
  // Google Analytics 4
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', action, {
      event_category: category,
      event_label: label,
      value: value,
      custom_parameter_1: 'seo_tracking',
      send_to: 'G-XXXXXXXXXX'
    });
  }

  // Yandex Metrica
  if (typeof window !== 'undefined' && window.ym) {
    window.ym(12345678, 'reachGoal', `SEO_${action.toUpperCase()}`, {
      category: category,
      label: label,
      value: value,
      timestamp: new Date().toISOString()
    });
  }

  // Custom analytics for internal tracking
  if (typeof window !== 'undefined') {
    const eventData = {
      action,
      category,
      label,
      value,
      timestamp: new Date().toISOString(),
      page: window.location.pathname,
      referrer: document.referrer,
      userAgent: navigator.userAgent
    };

    // Send to custom analytics endpoint
    fetch('/api/analytics/seo-event', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData)
    }).catch(error => {
      console.warn('Failed to send custom analytics:', error);
    });
  }
};

// Track keyword performance
export const trackKeywordPerformance = (keyword, position, clickthrough = false) => {
  const eventData = {
    keyword,
    position,
    clickthrough,
    page: window.location.pathname,
    timestamp: new Date().toISOString()
  };

  trackSEOEvent('keyword_performance', 'SEO_Keywords', keyword, position);

  // Send detailed data to backend
  if (typeof window !== 'undefined') {
    fetch('/api/analytics/keyword-tracking', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData)
    }).catch(error => {
      console.warn('Failed to track keyword performance:', error);
    });
  }
};

// Track search engine referrals
export const trackSearchEngineReferral = () => {
  const referrer = document.referrer;
  let searchEngine = 'direct';
  let query = '';

  if (referrer.includes('google.')) {
    searchEngine = 'google';
    const urlParams = new URLSearchParams(referrer.split('?')[1]);
    query = urlParams.get('q') || '';
  } else if (referrer.includes('yandex.')) {
    searchEngine = 'yandex';
    const urlParams = new URLSearchParams(referrer.split('?')[1]);
    query = urlParams.get('text') || '';
  } else if (referrer.includes('bing.')) {
    searchEngine = 'bing';
    const urlParams = new URLSearchParams(referrer.split('?')[1]);
    query = urlParams.get('q') || '';
  }

  if (searchEngine !== 'direct') {
    trackSEOEvent('organic_visit', 'Traffic_Source', searchEngine);
    
    if (query) {
      trackSEOEvent('search_query', 'Organic_Keywords', query);
    }
  }
};

// Initialize analytics when component loads
export const initializeAnalytics = () => {
  // Track initial page load
  trackSearchEngineReferral();
  
  // Track user engagement metrics
  let startTime = Date.now();
  let maxScroll = 0;

  // Track scroll depth
  const trackScrollDepth = () => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollPercent = Math.round((scrollTop + windowHeight) / documentHeight * 100);
    
    if (scrollPercent > maxScroll) {
      maxScroll = scrollPercent;
      
      // Track milestone scroll depths
      if (scrollPercent >= 25 && maxScroll < 25) {
        trackSEOEvent('scroll_depth', 'Engagement', '25_percent');
      } else if (scrollPercent >= 50 && maxScroll < 50) {
        trackSEOEvent('scroll_depth', 'Engagement', '50_percent');
      } else if (scrollPercent >= 75 && maxScroll < 75) {
        trackSEOEvent('scroll_depth', 'Engagement', '75_percent');
      } else if (scrollPercent >= 90 && maxScroll < 90) {
        trackSEOEvent('scroll_depth', 'Engagement', '90_percent');
      }
    }
  };

  // Track time on page
  const trackTimeOnPage = () => {
    const timeSpent = Math.round((Date.now() - startTime) / 1000);
    
    // Track significant time milestones
    if (timeSpent === 30) {
      trackSEOEvent('time_on_page', 'Engagement', '30_seconds', 30);
    } else if (timeSpent === 60) {
      trackSEOEvent('time_on_page', 'Engagement', '1_minute', 60);
    } else if (timeSpent === 180) {
      trackSEOEvent('time_on_page', 'Engagement', '3_minutes', 180);
    } else if (timeSpent === 300) {
      trackSEOEvent('time_on_page', 'Engagement', '5_minutes', 300);
    }
  };

  // Add event listeners
  if (typeof window !== 'undefined') {
    window.addEventListener('scroll', trackScrollDepth, { passive: true });
    
    // Track time intervals
    setInterval(trackTimeOnPage, 30000); // Check every 30 seconds
    
    // Track page exit
    window.addEventListener('beforeunload', () => {
      const finalTimeSpent = Math.round((Date.now() - startTime) / 1000);
      trackSEOEvent('page_exit', 'Engagement', 'time_spent', finalTimeSpent);
    });
  }
};

// Russian-specific SEO tracking
export const trackRussianSEOMetrics = () => {
  const metrics = {
    yandex_region: 'moscow', // Default to Moscow, can be detected
    language: 'ru',
    currency: 'RUB',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    user_agent: navigator.userAgent,
    screen_resolution: `${screen.width}x${screen.height}`,
    connection_type: navigator.connection ? navigator.connection.effectiveType : 'unknown'
  };

  // Send Russian-specific metrics
  trackSEOEvent('russian_user_metrics', 'Demographics', 'session_start');

  // Track Yandex-specific events
  if (typeof window !== 'undefined' && window.ym) {
    window.ym(12345678, 'userParams', {
      region: metrics.yandex_region,
      language: metrics.language,
      currency: metrics.currency,
      UserID: localStorage.getItem('user_id') || 'anonymous'
    });
  }

  return metrics;
};

export default AnalyticsTracker;