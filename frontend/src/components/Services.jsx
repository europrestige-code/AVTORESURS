import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { 
  ShoppingCart, BookOpen, Star, MapPin, Smartphone, 
  GamepadIcon, ExternalLink, X, Zap, Car, Factory, ArrowRight 
} from 'lucide-react';
import { mockData } from '../utils/mockData';
import { ChinesePlatformsSection } from './ChinesePlatformsSection';
import { CarPartsSection } from './CarPartsSection';
import { BusinessSolutionsSection } from './BusinessSolutionsSection';

export const Services = () => {
  const [selectedService, setSelectedService] = useState(null);
  const [showSpecialSection, setShowSpecialSection] = useState(null);
  
  const services = [
    {
      icon: ShoppingCart,
      title: 'Подписки на сервисы',
      description: 'Netflix, Spotify, Adobe, Disney+, и другие популярные подписки',
      examples: ['Netflix', 'Spotify', 'Adobe Creative', 'Disney+', 'Dropbox'],
      image: 'https://images.unsplash.com/photo-1717295248494-937c3a5655b1',
      category: 'subscriptions'
    },
    {
      icon: BookOpen,
      title: 'Онлайн курсы',
      description: 'Coursera, Udemy, MasterClass и другие образовательные платформы',
      examples: ['Coursera', 'Udemy', 'MasterClass', 'Skillshare', 'LinkedIn Learning'],
      image: 'https://images.unsplash.com/photo-1585832770485-e68a5dbfad52',
      category: 'courses'
    },
    {
      icon: Star,
      title: 'Товары брендов',
      description: 'Louis Vuitton, Gucci, Zara, H&M и тысячи других брендов',
      examples: ['Louis Vuitton', 'Gucci', 'Zara', 'H&M', 'Nike'],
      image: 'https://images.unsplash.com/photo-1483985988355-763728e1935b',
      category: 'brands'
    },
    {
      icon: MapPin,
      title: 'Билеты и проживание',
      description: 'Авиабилеты, отели, аренда жилья по всему миру',
      examples: ['Booking.com', 'Airbnb', 'Expedia', 'Hotels.com', 'Kayak'],
      image: 'https://images.unsplash.com/photo-1664190426315-b3abf1cf07ad',
      category: 'travel'
    },
    {
      icon: Smartphone,
      title: 'Электроника',
      description: 'iPhone, MacBook, игровые консоли и другая техника',
      examples: ['Apple Store', 'Best Buy', 'Amazon', 'Newegg', 'B&H Photo'],
      image: 'https://images.unsplash.com/photo-1742762379583-1a461c76f141',
      category: 'electronics'
    },
    {
      icon: GamepadIcon,
      title: 'Цифровые товары',
      description: 'Игры, программы, приложения и цифровой контент',
      examples: ['Steam', 'Epic Games', 'App Store', 'Google Play', 'Microsoft Store'],
      image: 'https://images.unsplash.com/photo-1589609966838-5c628d5c1aa5',
      category: 'digital'
    },
    // New services
    {
      icon: Zap,
      title: 'Китайские платформы',
      description: 'AliExpress, Taobao, SHEIN, JD.com с ИИ-поиском и проверкой',
      examples: ['AliExpress', 'Taobao', 'SHEIN'],
      image: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800&h=600&fit=crop&crop=center',
      category: 'chinese-platforms',
      isNew: true,
      isSpecial: true
    },
    {
      icon: Car,
      title: 'Автозапчасти OEM',
      description: 'Поиск по VIN, номеру детали с ИИ-определением производителя',
      examples: ['BOSCH', 'Continental', 'Mahle'],
      image: 'https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=800&h=600&fit=crop&crop=center',
      category: 'car-parts',
      isNew: true,
      isSpecial: true
    },
    {
      icon: Factory,
      title: 'Решения для бизнеса',
      description: 'Промышленное оборудование: автоматизация, электротехника, пневматика',
      examples: ['Siemens', 'ABB', 'Schneider Electric'],
      image: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&h=600&fit=crop&crop=center',
      category: 'business-solutions',
      isNew: true,
      isSpecial: true
    }
  ];

  const handleServiceClick = (service) => {
    // Handle special sections
    if (service.category === "chinese-platforms") {
      setShowSpecialSection("chinese");
      return;
    }
    if (service.category === "car-parts") {
      setShowSpecialSection("car-parts");
      return;
    }
    if (service.category === "business-solutions") {
      setShowSpecialSection("business");
      return;
    }
    
    // Handle regular service modal
    setSelectedService(service);
  };

  const closeSpecialSection = () => {
    setShowSpecialSection(null);
  };

  const getPopularLinks = (category) => {
    return mockData.getPopularLinks(category);
  };

  return (
    <>
      {/* Render special sections */}
      {showSpecialSection === "chinese" && (
        <div>
          <ChinesePlatformsSection />
          <div className="text-center py-8">
            <Button onClick={closeSpecialSection} variant="outline" size="lg">
              Вернуться к услугам
            </Button>
          </div>
        </div>
      )}

      {showSpecialSection === "car-parts" && (
        <div>
          <CarPartsSection />
          <div className="text-center py-8">
            <Button onClick={closeSpecialSection} variant="outline" size="lg">
              Вернуться к услугам
            </Button>
          </div>
        </div>
      )}

      {showSpecialSection === "business" && (
        <div>
          <BusinessSolutionsSection />
          <div className="text-center py-8">
            <Button onClick={closeSpecialSection} variant="outline" size="lg">
              Вернуться к услугам
            </Button>
          </div>
        </div>
      )}

      {/* Main services section - only show when no special section is active */}
      {!showSpecialSection && (
        <section className="mobile-spacing bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Что мы можем купить для вас
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
                Покупаем абсолютно всё — от подписок до luxury товаров. 
                Если это можно купить онлайн, мы это сделаем.
              </p>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-w-3xl mx-auto">
                <p className="text-sm text-green-800">
                  <strong>Гарантия оригинальности:</strong> Для премиальных брендов (Apple, Samsung и др.) покупаем у официальных ритейлеров и проверенных поставщиков, предоставляющих документы, подтверждающие подлинность.
                </p>
              </div>
            </div>

            <div className="responsive-grid">
              {services.map((service, index) => {
                const IconComponent = service.icon;
                return (
                  <div key={index}>
                    {service.isSpecial ? (
                      // Special services that open dedicated sections
                      <Card 
                        className="hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:scale-105 group overflow-hidden"
                        onClick={() => handleServiceClick(service)}
                      >
                        <div 
                          className="mobile-service-card bg-cover bg-center relative overflow-hidden flex flex-col justify-between p-4 sm:p-6"
                          style={{ backgroundImage: `url(${service.image}?w=600&h=600&fit=crop)` }}
                        >
                          <div className="absolute inset-0 bg-black bg-opacity-50 group-hover:bg-opacity-40 transition-all duration-300"></div>
                          
                          {/* Top section with icon */}
                          <div className="relative z-10 flex justify-between items-start">
                            <div className="p-3 bg-white bg-opacity-20 backdrop-blur-md rounded-lg border border-white border-opacity-30">
                              <IconComponent className="h-6 w-6 text-white" />
                            </div>
                            <div className="flex flex-col gap-2">
                              {service.isNew && (
                                <Badge className="bg-gray-200 text-blue-600 animate-pulse font-medium">
                                  НОВИНКА
                                </Badge>
                              )}
                              <div className="p-2 bg-blue-600 bg-opacity-80 text-white rounded-full opacity-80 group-hover:opacity-100 transition-opacity backdrop-blur-sm">
                                <ArrowRight className="h-4 w-4" />
                              </div>
                            </div>
                          </div>

                          {/* Bottom section with text content */}
                          <div className="relative z-10">
                            <h3 className="text-responsive-lg font-bold text-white mb-2 sm:mb-3 drop-shadow-lg">
                              {service.title}
                            </h3>
                            <p className="text-white text-opacity-90 mb-3 sm:mb-4 font-medium drop-shadow-md text-sm sm:text-base">
                              {service.description}
                            </p>
                            <div className="flex flex-wrap gap-1 sm:gap-2">
                              {service.examples.slice(0, 3).map((example, i) => (
                                <span
                                  key={i}
                                  className="px-2 sm:px-3 py-1 bg-white bg-opacity-20 backdrop-blur-sm text-white text-xs sm:text-sm rounded-full font-semibold border border-white border-opacity-30"
                                >
                                  {example}
                                </span>
                              ))}
                              {service.examples.length > 3 && (
                                <span className="px-2 sm:px-3 py-1 bg-blue-600 bg-opacity-80 backdrop-blur-sm text-white text-xs sm:text-sm rounded-full font-semibold">
                                  +{service.examples.length - 3} ещё
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </Card>
                    ) : (
                      // Regular services that open dialogs
                      <Dialog>
                        <DialogTrigger asChild>
                          <Card 
                            className="hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:scale-105 group overflow-hidden"
                            onClick={() => handleServiceClick(service)}
                          >
                            <div 
                              className="mobile-service-card bg-cover bg-center relative overflow-hidden flex flex-col justify-between p-4 sm:p-6"
                              style={{ backgroundImage: `url(${service.image}?w=600&h=600&fit=crop)` }}
                            >
                              <div className="absolute inset-0 bg-black bg-opacity-50 group-hover:bg-opacity-40 transition-all duration-300"></div>
                              
                              {/* Top section with icon */}
                              <div className="relative z-10 flex justify-between items-start">
                                <div className="p-3 bg-white bg-opacity-20 backdrop-blur-md rounded-lg border border-white border-opacity-30">
                                  <IconComponent className="h-6 w-6 text-white" />
                                </div>
                                <div className="p-2 bg-blue-600 bg-opacity-80 text-white rounded-full opacity-80 group-hover:opacity-100 transition-opacity backdrop-blur-sm">
                                  <ArrowRight className="h-4 w-4" />
                                </div>
                              </div>

                              {/* Bottom section with text content */}
                              <div className="relative z-10">
                                <h3 className="text-responsive-lg font-bold text-white mb-2 sm:mb-3 drop-shadow-lg">
                                  {service.title}
                                </h3>
                                <p className="text-white text-opacity-90 mb-3 sm:mb-4 font-medium drop-shadow-md text-sm sm:text-base">
                                  {service.description}
                                </p>
                                <div className="flex flex-wrap gap-1 sm:gap-2">
                                  {service.examples.slice(0, 3).map((example, i) => (
                                    <span
                                      key={i}
                                      className="px-2 sm:px-3 py-1 bg-white bg-opacity-20 backdrop-blur-sm text-white text-xs sm:text-sm rounded-full font-semibold border border-white border-opacity-30"
                                    >
                                      {example}
                                    </span>
                                  ))}
                                  {service.examples.length > 3 && (
                                    <span className="px-2 sm:px-3 py-1 bg-blue-600 bg-opacity-80 backdrop-blur-sm text-white text-xs sm:text-sm rounded-full font-semibold">
                                      +{service.examples.length - 3} ещё
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </Card>
                        </DialogTrigger>
                        
                        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                          <DialogHeader>
                            <DialogTitle className="flex items-center text-2xl">
                              <IconComponent className="h-8 w-8 text-blue-600 mr-3" />
                              {service.title}
                            </DialogTitle>
                          </DialogHeader>
                          
                          <div className="mt-6">
                            <div 
                              className="h-64 bg-cover bg-center rounded-lg mb-6"
                              style={{ backgroundImage: `url(${service.image}?w=800&h=400&fit=crop)` }}
                            />
                            
                            <h3 className="text-xl font-semibold mb-4">Популярные сайты и сервисы:</h3>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {getPopularLinks(service.category).map((link, i) => (
                                <div key={i} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center">
                                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg mr-4">
                                        {link.name.charAt(0)}
                                      </div>
                                      <div>
                                        <h4 className="font-semibold text-gray-900">{link.name}</h4>
                                        <p className="text-sm text-gray-600">{link.description}</p>
                                        <p className="text-xs text-blue-600 mt-1">{link.url}</p>
                                      </div>
                                    </div>
                                    <Button 
                                      size="sm" 
                                      className="bg-blue-600 hover:bg-blue-700"
                                      onClick={() => {
                                        // This would normally open the order form with pre-filled URL
                                        console.log('Order from:', link.url);
                                      }}
                                    >
                                      <ExternalLink className="h-4 w-4 mr-1" />
                                      Заказать
                                    </Button>
                                  </div>
                                  {link.price && (
                                    <div className="mt-3 pt-3 border-t">
                                      <div className="flex justify-between text-sm">
                                        <span className="text-gray-600">Примерная стоимость:</span>
                                        <span className="font-semibold text-green-600">{link.price}</span>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                            
                            <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                              <h4 className="font-semibold text-blue-900 mb-2">Как заказать:</h4>
                              <ol className="list-decimal list-inside text-blue-800 space-y-1">
                                <li>Выберите нужный сервис из списка выше</li>
                                <li>Нажмите "Заказать" или скопируйте ссылку</li>
                                <li>Заполните форму расчёта стоимости</li>
                                <li>Получите точную цену в рублях</li>
                                <li>Оплатите и получите доступ к сервису</li>
                              </ol>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="text-center mt-12">
              <p className="text-lg text-gray-600 mb-6">
                Не нашли нужную категорию? Мы покупаем всё, что недоступно в России!
              </p>
              <div className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg">
                <ShoppingCart className="h-5 w-5 mr-2" />
                Минимальная комиссия: 1500 ₽ или 18%
              </div>
            </div>
          </div>
        </section>
      )}
    </>
  );
};