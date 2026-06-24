import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { 
  Search, TrendingUp, FileText, BarChart3, Globe, 
  Target, Zap, AlertCircle, CheckCircle, Eye 
} from 'lucide-react';
import { KeywordResearch } from './KeywordResearch';
import { ContentOptimizer } from './ContentOptimizer';

export const SEODashboard = () => {
  const [seoMetrics, setSeoMetrics] = useState({
    organicTraffic: 0,
    keywordRankings: 0,
    contentScore: 0,
    technicalScore: 0
  });

  const [rankingKeywords, setRankingKeywords] = useState([]);
  const [competitorAnalysis, setCompetitorAnalysis] = useState([]);

  useEffect(() => {
    // Simulate loading SEO data
    const loadSEOData = () => {
      setSeoMetrics({
        organicTraffic: 15420,
        keywordRankings: 87,
        contentScore: 78,
        technicalScore: 85
      });

      setRankingKeywords([
        { keyword: 'покупки из-за границы', position: 12, volume: 50000, change: +3 },
        { keyword: 'доставка из-за рубежа', position: 8, volume: 45000, change: +1 },
        { keyword: 'заказ товаров из США', position: 15, volume: 25000, change: -2 },
        { keyword: 'международная доставка', position: 22, volume: 40000, change: +5 },
        { keyword: 'сервис доставки', position: 7, volume: 18000, change: +2 },
        { keyword: 'выкуп товаров', position: 11, volume: 12000, change: 0 },
        { keyword: 'посредник покупок', position: 19, volume: 15000, change: +4 },
        { keyword: 'таможенное оформление', position: 25, volume: 22000, change: -1 }
      ]);

      setCompetitorAnalysis([
        { 
          domain: 'shipito.com', 
          keywords: 1250, 
          traffic: 125000, 
          backlinks: 8500,
          authority: 72
        },
        { 
          domain: 'boxberry.ru', 
          keywords: 980, 
          traffic: 89000, 
          backlinks: 3200,
          authority: 65
        },
        { 
          domain: 'qwintry.com', 
          keywords: 756, 
          traffic: 67000, 
          backlinks: 2100,
          authority: 58
        }
      ]);
    };

    loadSEOData();
  }, []);

  const getPositionColor = (position) => {
    if (position <= 3) return 'text-green-600';
    if (position <= 10) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (change < 0) return <TrendingUp className="h-4 w-4 text-red-600 rotate-180" />;
    return <div className="h-4 w-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          SEO Панель Управления
        </h1>
        <p className="text-gray-600 max-w-3xl mx-auto">
          Комплексная система SEO оптимизации для международного шопинга
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Органический трафик</p>
                <p className="text-2xl font-bold text-gray-900">
                  {seoMetrics.organicTraffic.toLocaleString()}
                </p>
                <p className="text-xs text-green-600">+12% за месяц</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Ключевые слова в ТОП-30</p>
                <p className="text-2xl font-bold text-gray-900">{seoMetrics.keywordRankings}</p>
                <p className="text-xs text-green-600">+8 за неделю</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <Target className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Оценка контента</p>
                <p className="text-2xl font-bold text-gray-900">{seoMetrics.contentScore}/100</p>
                <Progress value={seoMetrics.contentScore} className="mt-2" />
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Техническое SEO</p>
                <p className="text-2xl font-bold text-gray-900">{seoMetrics.technicalScore}/100</p>
                <Progress value={seoMetrics.technicalScore} className="mt-2" />
              </div>
              <div className="h-12 w-12 bg-orange-100 rounded-full flex items-center justify-center">
                <Zap className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Обзор</TabsTrigger>
          <TabsTrigger value="keywords">Ключевые слова</TabsTrigger>
          <TabsTrigger value="content">Контент</TabsTrigger>
          <TabsTrigger value="technical">Техническое SEO</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Current Rankings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="h-5 w-5 mr-2" />
                Текущие позиции в поиске
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="pb-2">Ключевое слово</th>
                      <th className="pb-2">Позиция</th>
                      <th className="pb-2">Объем</th>
                      <th className="pb-2">Изменение</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankingKeywords.map((keyword, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2">{keyword.keyword}</td>
                        <td className={`py-2 font-bold ${getPositionColor(keyword.position)}`}>
                          #{keyword.position}
                        </td>
                        <td className="py-2">{keyword.volume.toLocaleString()}</td>
                        <td className="py-2">
                          <div className="flex items-center space-x-1">
                            {getChangeIcon(keyword.change)}
                            <span className={
                              keyword.change > 0 ? 'text-green-600' : 
                              keyword.change < 0 ? 'text-red-600' : 'text-gray-600'
                            }>
                              {keyword.change > 0 ? '+' : ''}{keyword.change}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Competitor Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Eye className="h-5 w-5 mr-2" />
                Анализ конкурентов
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {competitorAnalysis.map((competitor, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">{competitor.domain}</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Ключевые слова:</span>
                        <span className="font-medium">{competitor.keywords}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Трафик:</span>
                        <span className="font-medium">{competitor.traffic.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Обратные ссылки:</span>
                        <span className="font-medium">{competitor.backlinks.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Авторитет:</span>
                        <Badge className={
                          competitor.authority >= 70 ? 'bg-green-100 text-green-800' :
                          competitor.authority >= 50 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }>
                          {competitor.authority}/100
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-5 w-5 mr-2" />
                Быстрые действия
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <Search className="h-8 w-8 text-blue-600 mb-2" />
                  <h4 className="font-semibold text-blue-900">Анализ ключевых слов</h4>
                  <p className="text-sm text-blue-700 mt-1">Найти новые возможности</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <FileText className="h-8 w-8 text-green-600 mb-2" />
                  <h4 className="font-semibold text-green-900">Оптимизация контента</h4>
                  <p className="text-sm text-green-700 mt-1">Улучшить существующие страницы</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <Globe className="h-8 w-8 text-purple-600 mb-2" />
                  <h4 className="font-semibold text-purple-900">Технический аудит</h4>
                  <p className="text-sm text-purple-700 mt-1">Проверить техническое SEO</p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <BarChart3 className="h-8 w-8 text-orange-600 mb-2" />
                  <h4 className="font-semibold text-orange-900">Отчеты</h4>
                  <p className="text-sm text-orange-700 mt-1">Создать SEO отчет</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Keywords Tab */}
        <TabsContent value="keywords">
          <KeywordResearch />
        </TabsContent>

        {/* Content Tab */}
        <TabsContent value="content">
          <ContentOptimizer />
        </TabsContent>

        {/* Technical SEO Tab */}
        <TabsContent value="technical" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Globe className="h-5 w-5 mr-2" />
                Техническое SEO
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Индексация и сканирование</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Robots.txt</span>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>XML Sitemap</span>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Canonical URLs</span>
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Hreflang</span>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-900">Производительность</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Скорость загрузки</span>
                      <Badge className="bg-green-100 text-green-800">2.1s</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Core Web Vitals</span>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Mobile-friendly</span>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>HTTPS</span>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">Рекомендации:</h4>
                <ul className="text-blue-800 space-y-1 text-sm">
                  <li>• Добавьте canonical URLs для страниц товаров</li>
                  <li>• Оптимизируйте изображения для ускорения загрузки</li>
                  <li>• Настройте сжатие GZIP для статических файлов</li>
                  <li>• Добавьте структурированные данные для лучшего понимания контента</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};