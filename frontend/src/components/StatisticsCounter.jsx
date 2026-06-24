import React, { useState, useEffect, useRef } from 'react';
import { Package, ShoppingCart, Users, Star } from 'lucide-react';

export const StatisticsCounter = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [counters, setCounters] = useState({
    orders: 0,
    packages: 0, 
    customers: 0,
    satisfaction: 0
  });
  const sectionRef = useRef(null);

  const finalValues = {
    orders: 12835,
    packages: 9626,
    customers: 5834,
    satisfaction: 92
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          startCountAnimation();
        }
      },
      { threshold: 0.5 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, [isVisible]);

  const startCountAnimation = () => {
    const duration = 2500; // 2.5 seconds
    const steps = 60;
    const stepDuration = duration / steps;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      const progress = currentStep / steps;
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      
      setCounters({
        orders: Math.floor(finalValues.orders * easeOutQuart),
        packages: Math.floor(finalValues.packages * easeOutQuart),
        customers: Math.floor(finalValues.customers * easeOutQuart),
        satisfaction: Math.floor(finalValues.satisfaction * easeOutQuart)
      });

      if (currentStep >= steps) {
        clearInterval(timer);
        setCounters(finalValues);
      }
    }, stepDuration);
  };

  const formatNumber = (num) => {
    return num.toLocaleString('ru-RU');
  };

  const stats = [
    {
      icon: ShoppingCart,
      value: counters.orders,
      label: 'Заказов выполнено',
      suffix: '+',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      icon: Package,
      value: counters.packages,
      label: 'Посылок доставлено',
      suffix: '',
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      icon: Users,
      value: counters.customers,
      label: 'Довольных клиентов',
      suffix: '+',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    {
      icon: Star,
      value: counters.satisfaction,
      label: 'Положительных отзывов',
      suffix: '%',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    }
  ];

  return (
    <section ref={sectionRef} className="py-16 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Нам доверяют тысячи клиентов
          </h2>
          <p className="text-lg text-gray-600">
            Статистика нашего сервиса бьёт новые рекорды каждый день
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => {
            const IconComponent = stat.icon;
            return (
              <div 
                key={index} 
                className="text-center p-8 bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
              >
                <div className={`inline-flex items-center justify-center w-16 h-16 ${stat.bgColor} rounded-full mb-6`}>
                  <IconComponent className={`h-8 w-8 ${stat.color}`} />
                </div>
                
                <div className="mb-4">
                  <div className="text-4xl font-bold text-gray-900 mb-2">
                    {formatNumber(stat.value)}{stat.suffix}
                  </div>
                  <p className="text-gray-600 font-medium">
                    {stat.label}
                  </p>
                </div>
                
                {/* Progress bar for visual effect */}
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-2000 ease-out ${stat.color.replace('text-', 'bg-')}`}
                    style={{ 
                      width: isVisible ? '100%' : '0%',
                      transitionDelay: `${index * 200}ms`
                    }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="text-center mt-12">
          <div className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-blue-600 text-white font-semibold rounded-lg shadow-lg">
            <Star className="h-5 w-5 mr-2" />
            Присоединяйтесь к довольным клиентам уже сегодня!
          </div>
        </div>
      </div>
    </section>
  );
};