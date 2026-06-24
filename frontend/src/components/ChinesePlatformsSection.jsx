import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { 
  Search, ExternalLink, ShoppingCart, Star, Shield, 
  TrendingUp, Globe, Zap, CheckCircle
} from 'lucide-react';

const chinesePlatforms = [
  {
    id: 'aliexpress',
    name: 'AliExpress',
    description: 'Глобальная торговая площадка с миллионами товаров',
    logo: 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=100&h=100&fit=crop&crop=center',
    categories: ['Электроника', 'Одежда', 'Дом и сад', 'Спорт'],
    features: ['Защита покупателя', 'Бесплатная доставка', 'Отзывы покупателей'],
    commission: '8-12%',
    deliveryTime: '15-30 дней',
    popularProducts: [
      'Смартфоны Xiaomi',
      'Наушники AirPods Pro',
      'Умные часы',
      'LED лампы'
    ]
  },
  {
    id: 'taobao',
    name: 'Taobao',
    description: 'Крупнейшая китайская платформа для покупок',
    logo: 'https://images.unsplash.com/photo-1556740758-90de374c12ad?w=100&h=100&fit=crop&crop=center',
    categories: ['Все категории', 'Эксклюзивные товары', 'Оригинальные бренды'],
    features: ['Прямые поставки', 'Оптовые цены', 'Уникальные товары'],
    commission: '10-15%',
    deliveryTime: '20-35 дней',
    popularProducts: [
      'Оригинальная косметика',
      'Дизайнерская одежда',
      'Товары для дома',
      'Электронные компоненты'
    ]
  },
  {
    id: 'shein',
    name: 'SHEIN',
    description: 'Быстрая мода и доступная одежда',
    logo: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=100&h=100&fit=crop&crop=center',
    categories: ['Женская одежда', 'Мужская одежда', 'Аксессуары', 'Дом'],
    features: ['Модные тренды', 'Низкие цены', 'Частые распродажи'],
    commission: '6-10%',
    deliveryTime: '10-20 дней',
    popularProducts: [
      'Платья',
      'Джинсы',
      'Обувь',
      'Сумки'
    ]
  },
  {
    id: 'jd',
    name: 'JD.com',
    description: 'Премиальная китайская площадка',
    logo: 'https://images.unsplash.com/photo-1556740738-b6a63e27c4df?w=100&h=100&fit=crop&crop=center',
    categories: ['Электроника', 'Бытовая техника', 'Автотовары', 'Спорт'],
    features: ['Гарантия качества', 'Быстрая доставка', 'Официальные бренды'],
    commission: '12-18%',
    deliveryTime: '12-25 дней',
    popularProducts: [
      'Техника Apple',
      'Бытовая техника',
      'Автозапчасти',
      'Спортивное оборудование'
    ]
  },
  {
    id: 'tmall',
    name: 'Tmall',
    description: 'Официальные магазины известных брендов',
    logo: 'https://images.unsplash.com/photo-1556742111-a301076d9d18?w=100&h=100&fit=crop&crop=center',
    categories: ['Люксовые бренды', 'Косметика', 'Мода', 'Электроника'],
    features: ['100% оригинал', 'Официальная гарантия', 'VIP обслуживание'],
    commission: '15-25%',
    deliveryTime: '15-30 дней',
    popularProducts: [
      'Люксовая косметика',
      'Брендовая одежда',
      'Парфюмерия',
      'Часы'
    ]
  },
  {
    id: '1688',
    name: '1688.com',
    description: 'Оптовая торговая площадка B2B',
    logo: 'https://images.unsplash.com/photo-1556741533-6e6a62bd8b49?w=100&h=100&fit=crop&crop=center',
    categories: ['Оптовые товары', 'Производство', 'B2B решения', 'Сырье'],
    features: ['Оптовые цены', 'Прямые поставки', 'Индивидуальный заказ'],
    commission: '8-15%',
    deliveryTime: '25-40 дней',
    popularProducts: [
      'Электронные компоненты',
      'Текстиль оптом',
      'Упаковочные материалы',
      'Промышленное оборудование'
    ]
  }
];

export const ChinesePlatformsSection = () => {
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    // Simulate AI search across platforms
    setTimeout(() => {
      const mockResults = [
        {
          platform: 'AliExpress',
          title: `${searchQuery} - Оригинальный товар`,
          price: '¥89-156',
          priceRub: '1,200-2,100 ₽',
          rating: 4.7,
          reviews: 2834,
          image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=150&h=150&fit=crop',
          seller: 'Official Store'
        },
        {
          platform: 'Taobao',
          title: `${searchQuery} - Премиум качество`,
          price: '¥78-134',
          priceRub: '1,050-1,800 ₽',
          rating: 4.8,
          reviews: 1247,
          image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=150&h=150&fit=crop',
          seller: 'Top Seller'
        },
        {
          platform: 'SHEIN',
          title: `${searchQuery} - Модный дизайн`,
          price: '¥45-89',
          priceRub: '600-1,200 ₽',
          rating: 4.5,
          reviews: 892,
          image: 'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=150&h=150&fit=crop',
          seller: 'SHEIN Official'
        }
      ];
      setSearchResults(mockResults);
      setIsSearching(false);
    }, 2000);
  };

  return (
    <div className="py-16 bg-gradient-to-br from-red-50 to-orange-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            🇨🇳 Китайские B2C платформы
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Доступ к крупнейшим китайским торговым площадкам с ИИ-поиском лучших цен 
            и проверкой подлинности товаров
          </p>
        </div>

        {/* AI Search Section */}
        <div className="mb-12">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-6 w-6 mr-2 text-yellow-500" />
                ИИ поиск по всем платформам
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex space-x-4">
                <Input
                  placeholder="Например: iPhone 15 Pro, кроссовки Nike, платье..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  onClick={handleSearch}
                  disabled={isSearching}
                  className="bg-red-500 hover:bg-red-600"
                >
                  {isSearching ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              {searchResults.length > 0 && (
                <div className="mt-6 space-y-4">
                  <h3 className="font-semibold text-gray-900">Результаты поиска:</h3>
                  {searchResults.map((result, index) => (
                    <div key={index} className="flex items-center space-x-4 p-4 border rounded-lg bg-white">
                      <img 
                        src={result.image} 
                        alt={result.title}
                        className="w-16 h-16 object-cover rounded"
                      />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">{result.platform}</Badge>
                          <div className="flex items-center">
                            <Star className="h-4 w-4 text-yellow-400 fill-current" />
                            <span className="text-sm text-gray-600 ml-1">
                              {result.rating} ({result.reviews})
                            </span>
                          </div>
                        </div>
                        <h4 className="font-medium text-gray-900 mt-1">{result.title}</h4>
                        <div className="flex items-center justify-between mt-2">
                          <div className="text-sm text-gray-600">
                            {result.price} → <span className="font-semibold text-green-600">{result.priceRub}</span>
                          </div>
                          <Button size="sm" variant="outline">
                            <ShoppingCart className="h-4 w-4 mr-1" />
                            Заказать
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Platforms Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {chinesePlatforms.map((platform) => (
            <Card 
              key={platform.id} 
              className="hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-1"
              onClick={() => setSelectedPlatform(platform)}
            >
              <CardHeader>
                <div className="flex items-center space-x-4">
                  <img 
                    src={platform.logo} 
                    alt={platform.name}
                    className="w-12 h-12 rounded-lg object-cover"
                  />
                  <div>
                    <CardTitle className="text-xl">{platform.name}</CardTitle>
                    <p className="text-sm text-gray-600">{platform.description}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Основные категории:</h4>
                    <div className="flex flex-wrap gap-2">
                      {platform.categories.map((category, index) => (
                        <Badge key={index} variant="secondary">{category}</Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Преимущества:</h4>
                    <ul className="space-y-1">
                      {platform.features.map((feature, index) => (
                        <li key={index} className="flex items-center text-sm text-gray-600">
                          <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="flex justify-between items-center pt-4 border-t">
                    <div className="text-sm text-gray-600">
                      <div>Комиссия: <span className="font-medium">{platform.commission}</span></div>
                      <div>Доставка: <span className="font-medium">{platform.deliveryTime}</span></div>
                    </div>
                    <Button size="sm">
                      <ExternalLink className="h-4 w-4 mr-1" />
                      Перейти
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Platform Modal */}
        {selectedPlatform && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-4">
                    <img 
                      src={selectedPlatform.logo} 
                      alt={selectedPlatform.name}
                      className="w-16 h-16 rounded-lg object-cover"
                    />
                    <div>
                      <h2 className="text-2xl font-bold">{selectedPlatform.name}</h2>
                      <p className="text-gray-600">{selectedPlatform.description}</p>
                    </div>
                  </div>
                  <Button 
                    variant="ghost" 
                    onClick={() => setSelectedPlatform(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </Button>
                </div>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-3">Популярные товары:</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {selectedPlatform.popularProducts.map((product, index) => (
                        <div key={index} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{product}</span>
                            <Button size="sm" variant="outline">
                              <Search className="h-3 w-3 mr-1" />
                              Найти
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      <Shield className="h-5 w-5 inline mr-2 text-blue-500" />
                      Гарантии BuyAnywhere:
                    </h3>
                    <ul className="space-y-1 text-sm text-gray-700">
                      <li>• Проверка подлинности товаров</li>
                      <li>• Защита от мошенничества</li>
                      <li>• Гарантия возврата денег</li>
                      <li>• Техническая поддержка 24/7</li>
                    </ul>
                  </div>
                  
                  <div className="flex space-x-4">
                    <Button className="flex-1 bg-red-500 hover:bg-red-600">
                      <Globe className="h-4 w-4 mr-2" />
                      Перейти на {selectedPlatform.name}
                    </Button>
                    <Button variant="outline" className="flex-1">
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Популярные товары
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};