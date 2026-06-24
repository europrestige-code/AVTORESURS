import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { TrendingUp, Search, BarChart3, Target, Zap, Globe } from 'lucide-react';

// Russian keyword research and suggestion system
export const KeywordResearch = () => {
  const [keywords, setKeywords] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  // Comprehensive Russian keyword database for international shopping
  const KEYWORD_DATABASE = {
    highVolume: [
      { keyword: 'покупки из-за границы', volume: 50000, competition: 'высокая', cpc: 45 },
      { keyword: 'доставка из-за рубежа', volume: 45000, competition: 'высокая', cpc: 52 },
      { keyword: 'заказ товаров из-за границы', volume: 35000, competition: 'средняя', cpc: 38 },
      { keyword: 'международная доставка', volume: 40000, competition: 'высокая', cpc: 48 },
      { keyword: 'покупки в США', volume: 25000, competition: 'средняя', cpc: 35 },
      { keyword: 'доставка из Китая', volume: 30000, competition: 'средняя', cpc: 28 },
      { keyword: 'заказ из Европы', volume: 20000, competition: 'средняя', cpc: 42 }
    ],
    mediumVolume: [
      { keyword: 'сервис доставки из-за рубежа', volume: 15000, competition: 'средняя', cpc: 55 },
      { keyword: 'выкуп товаров за рубежом', volume: 12000, competition: 'низкая', cpc: 48 },
      { keyword: 'посредник для покупок', volume: 18000, competition: 'средняя', cpc: 52 },
      { keyword: 'консолидация посылок', volume: 8000, competition: 'низкая', cpc: 45 },
      { keyword: 'таможенное оформление', volume: 22000, competition: 'высокая', cpc: 38 },
      { keyword: 'доставка брендов', volume: 10000, competition: 'средняя', cpc: 65 },
      { keyword: 'оригинальная техника из-за границы', volume: 7500, competition: 'низкая', cpc: 75 }
    ],
    longTail: [
      { keyword: 'как заказать из США в Россию', volume: 5000, competition: 'низкая', cpc: 35 },
      { keyword: 'надежный сервис покупок из-за границы', volume: 3500, competition: 'низкая', cpc: 68 },
      { keyword: 'доставка Apple из США официально', volume: 4200, competition: 'средняя', cpc: 85 },
      { keyword: 'покупки из Amazon с доставкой в Москву', volume: 6000, competition: 'средняя', cpc: 58 },
      { keyword: 'сколько стоит доставка из-за границы', volume: 8500, competition: 'низкая', cpc: 42 },
      { keyword: 'лучший посредник для покупок за рубежом', volume: 2800, competition: 'низкая', cpc: 72 },
      { keyword: 'быстрая доставка товаров из Европы', volume: 4500, competition: 'средняя', cpc: 48 }
    ],
    seasonal: [
      { keyword: 'новогодние подарки из-за границы', volume: 12000, competition: 'высокая', cpc: 65, season: 'зима' },
      { keyword: 'летние покупки из Европы', volume: 6000, competition: 'средняя', cpc: 45, season: 'лето' },
      { keyword: 'школьные товары из-за рубежа', volume: 8000, competition: 'средняя', cpc: 38, season: 'осень' },
      { keyword: 'пасхальные товары из-за границы', volume: 3000, competition: 'низкая', cpc: 42, season: 'весна' }
    ],
    trending: [
      { keyword: 'iPhone 15 из США', volume: 25000, competition: 'высокая', cpc: 95, trend: '+250%' },
      { keyword: 'Samsung Galaxy из Европы', volume: 15000, competition: 'средняя', cpc: 78, trend: '+180%' },
      { keyword: 'игровые консоли из-за рубежа', volume: 12000, competition: 'высокая', cpc: 88, trend: '+320%' },
      { keyword: 'электросамокаты из Китая', volume: 9000, competition: 'средняя', cpc: 45, trend: '+150%' }
    ]
  };

  // Keyword suggestion engine
  const generateSuggestions = (baseTerm) => {
    const prefixes = [
      'купить', 'заказать', 'доставка', 'покупка', 'выкуп', 'сервис', 'услуги'
    ];
    
    const suffixes = [
      'из-за границы', 'из-за рубежа', 'из США', 'из Европы', 'из Китая', 
      'с доставкой', 'недорого', 'быстро', 'надежно', 'официально'
    ];
    
    const cities = [
      'в Москву', 'в СПб', 'в Екатеринбург', 'в Новосибирск', 'в Казань'
    ];
    
    let suggestions = [];
    
    // Generate prefix combinations
    prefixes.forEach(prefix => {
      suggestions.push(`${prefix} ${baseTerm}`);
      suffixes.forEach(suffix => {
        suggestions.push(`${prefix} ${baseTerm} ${suffix}`);
        cities.forEach(city => {
          suggestions.push(`${prefix} ${baseTerm} ${suffix} ${city}`);
        });
      });
    });
    
    return suggestions.slice(0, 20); // Limit to top 20 suggestions
  };

  // Get current season keywords
  const getCurrentSeasonKeywords = () => {
    const month = new Date().getMonth() + 1;
    let season = '';
    
    if (month >= 12 || month <= 2) season = 'зима';
    else if (month >= 3 && month <= 5) season = 'весна';
    else if (month >= 6 && month <= 8) season = 'лето';
    else season = 'осень';
    
    return KEYWORD_DATABASE.seasonal.filter(k => k.season === season);
  };

  // Competition level colors
  const getCompetitionColor = (competition) => {
    switch (competition) {
      case 'низкая': return 'bg-green-100 text-green-800';
      case 'средняя': return 'bg-yellow-100 text-yellow-800';
      case 'высокая': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Handle keyword research
  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const newSuggestions = generateSuggestions(searchTerm);
    setSuggestions(newSuggestions);
    setLoading(false);
  };

  useEffect(() => {
    // Load initial keyword data
    const allKeywords = [
      ...KEYWORD_DATABASE.highVolume,
      ...KEYWORD_DATABASE.mediumVolume,
      ...KEYWORD_DATABASE.trending,
      ...getCurrentSeasonKeywords()
    ].sort((a, b) => b.volume - a.volume);
    
    setKeywords(allKeywords);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          SEO Исследование Ключевых Слов
        </h2>
        <p className="text-gray-600 max-w-3xl mx-auto">
          Анализ и оптимизация ключевых слов для международного шопинга в России
        </p>
      </div>

      {/* Keyword Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="h-5 w-5 mr-2" />
            Генератор Ключевых Слов
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4">
            <Input
              placeholder="Введите базовое слово (например: телефон, одежда, косметика)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={loading}>
              {loading ? 'Поиск...' : 'Найти'}
            </Button>
          </div>
          
          {suggestions.length > 0 && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Предложения:</h4>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <Badge key={index} variant="outline" className="cursor-pointer hover:bg-blue-50">
                    {suggestion}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trending Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
            Трендовые Ключевые Слова
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {KEYWORD_DATABASE.trending.map((keyword, index) => (
              <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-gray-900">{keyword.keyword}</h4>
                  <Badge className="bg-green-100 text-green-800">
                    {keyword.trend}
                  </Badge>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Объем поиска: {keyword.volume.toLocaleString()}/мес</div>
                  <div>CPC: {keyword.cpc} ₽</div>
                  <Badge className={getCompetitionColor(keyword.competition)}>
                    {keyword.competition} конкуренция
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* High Volume Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
            Высокочастотные Запросы
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b">
                  <th className="pb-2">Ключевое слово</th>
                  <th className="pb-2">Объем</th>
                  <th className="pb-2">Конкуренция</th>
                  <th className="pb-2">CPC</th>
                </tr>
              </thead>
              <tbody>
                {keywords.slice(0, 10).map((keyword, index) => (
                  <tr key={index} className="border-b">
                    <td className="py-2 font-medium">{keyword.keyword}</td>
                    <td className="py-2">{keyword.volume.toLocaleString()}</td>
                    <td className="py-2">
                      <Badge className={getCompetitionColor(keyword.competition)}>
                        {keyword.competition}
                      </Badge>
                    </td>
                    <td className="py-2">{keyword.cpc} ₽</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Long Tail Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="h-5 w-5 mr-2 text-purple-600" />
            Длинные Хвосты (Long Tail)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {KEYWORD_DATABASE.longTail.map((keyword, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">{keyword.keyword}</div>
                  <div className="text-sm text-gray-600">
                    {keyword.volume.toLocaleString()} поисков/мес • {keyword.cpc} ₽ CPC
                  </div>
                </div>
                <Badge className={getCompetitionColor(keyword.competition)}>
                  {keyword.competition}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Seasonal Keywords */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Globe className="h-5 w-5 mr-2 text-orange-600" />
            Сезонные Ключевые Слова
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {KEYWORD_DATABASE.seasonal.map((keyword, index) => (
              <div key={index} className="text-center p-4 border rounded-lg">
                <div className="font-medium mb-2">{keyword.keyword}</div>
                <div className="text-sm text-gray-600 mb-2">
                  {keyword.volume.toLocaleString()} поисков
                </div>
                <Badge variant="outline">{keyword.season}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* SEO Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Zap className="h-5 w-5 mr-2 text-yellow-600" />
            Рекомендации по SEO
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">Приоритетные действия:</h4>
              <ul className="text-blue-800 space-y-1 text-sm">
                <li>• Оптимизируйте страницы под высокочастотные запросы</li>
                <li>• Создайте отдельные лендинги для трендовых товаров</li>
                <li>• Используйте длинные хвосты в блоге и FAQ</li>
                <li>• Учитывайте сезонность в контент-планах</li>
              </ul>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-2">Контентная стратегия:</h4>
              <ul className="text-green-800 space-y-1 text-sm">
                <li>• Создавайте гайды по покупкам в конкретных странах</li>
                <li>• Пишите обзоры популярных товаров</li>
                <li>• Добавляйте калькуляторы стоимости доставки</li>
                <li>• Ведите блог о трендах международного шопинга</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};