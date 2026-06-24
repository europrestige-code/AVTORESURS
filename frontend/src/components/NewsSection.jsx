import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Play, ExternalLink, Clock, Eye, TrendingUp, Globe, Zap, ShoppingBag, Rocket, Tag, Loader2 } from 'lucide-react';

export const NewsSection = () => {
  const [selectedCategory, setSelectedCategory] = useState('technology');
  const [newsFeed, setNewsFeed] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Category configuration with Russian names
  const newsCategories = {
    technology: { name: 'Технологии', icon: Zap, color: 'blue' },
    electronics: { name: 'Электроника', icon: Globe, color: 'purple' },
    product_launches: { name: 'Новые продукты', icon: Rocket, color: 'green' },
    shopping: { name: 'Шоппинг', icon: ShoppingBag, color: 'pink' },
    sales: { name: 'Скидки', icon: Tag, color: 'orange' }
  };

  useEffect(() => {
    loadNewsFeed();
  }, []);

  const loadNewsFeed = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/news/feed?language=ru&limit_per_category=4`);
      
      if (response.ok) {
        const data = await response.json();
        setNewsFeed(data.data || {});
        setError(null);
      } else {
        throw new Error('Failed to load news');
      }
    } catch (error) {
      console.error('Error loading news:', error);
      setError('Ошибка загрузки новостей');
      // Fallback to mock data if API fails
      setNewsFeed(getMockNewsData());
    } finally {
      setLoading(false);
    }
  };

  const getMockNewsData = () => ({
    technology: [
      {
        id: 1,
        title: "Революционные технологии ИИ в 2025 году",
        title_ru: "Революционные технологии ИИ в 2025 году",
        description: "Обзор последних достижений в области искусственного интеллекта и машинного обучения",
        description_ru: "Обзор последних достижений в области искусственного интеллекта и машинного обучения",
        source_name: "Tech News",
        published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        image_url: "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=250&fit=crop",
        url: "#",
        tags: ["ИИ", "технологии"],
        views: "2.1M"
      },
      {
        id: 2,
        title: "Будущее квантовых компьютеров",
        title_ru: "Будущее квантовых компьютеров",
        description: "Прорывы в квантовых вычислениях открывают новые возможности",
        description_ru: "Прорывы в квантовых вычислениях открывают новые возможности",
        source_name: "Quantum Tech",
        published_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        image_url: "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=400&h=250&fit=crop",
        url: "#",
        tags: ["квантовые технологии"],
        views: "1.3M"
      }
    ],
    electronics: [
      {
        id: 3,
        title: "iPhone 17 - Первые подробности",
        title_ru: "iPhone 17 - Первые подробности",
        description: "Утечки характеристик нового флагмана Apple с революционными возможностями",
        description_ru: "Утечки характеристик нового флагмана Apple с революционными возможностями",
        source_name: "Apple News",
        published_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        image_url: "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400&h=250&fit=crop",
        url: "#",
        tags: ["Apple", "iPhone"],
        views: "3.2M"
      }
    ],
    shopping: [
      {
        id: 4,
        title: "Тренды интернет-шоппинга 2025",
        title_ru: "Тренды интернет-шоппинга 2025",
        description: "Как изменится онлайн-торговля в ближайшем будущем",
        description_ru: "Как изменится онлайн-торговля в ближайшем будущем",
        source_name: "E-commerce Today",
        published_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        image_url: "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=250&fit=crop",
        url: "#",
        tags: ["e-commerce", "шоппинг"],
        views: "850K"
      }
    ]
  });

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Только что';
    if (diffInHours < 24) return `${diffInHours} ч. назад`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} д. назад`;
  };

  const truncateText = (text, maxLength = 120) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const NewsCard = ({ article }) => (
    <Card className="hover:shadow-lg transition-all duration-300 overflow-hidden group cursor-pointer">
      <div className="relative">
        <img 
          src={article.image_url || article.imageUrl || "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=250&fit=crop"} 
          alt={article.title_ru || article.title}
          className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => {
            e.target.src = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=250&fit=crop";
          }}
        />
        {article.isVideo && (
          <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
            <Play className="h-12 w-12 text-white" />
          </div>
        )}
        {article.trending && (
          <Badge className="absolute top-2 left-2 bg-red-500 hover:bg-red-600">
            <TrendingUp className="h-3 w-3 mr-1" />
            Trending
          </Badge>
        )}
      </div>
      
      <CardContent className="p-4">
        <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
          <span>{article.source_name || article.source}</span>
          <div className="flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            {formatDate(article.published_at || article.publishedAt)}
          </div>
        </div>
        
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
          {article.title_ru || article.title}
        </h3>
        
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
          {truncateText(article.description_ru || article.description)}
        </p>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center text-sm text-gray-500">
            <Eye className="h-4 w-4 mr-1" />
            {article.views || '1K'}
          </div>
          
          <Button 
            variant="ghost" 
            size="sm" 
            className="p-1 h-auto"
            onClick={() => window.open(article.url, '_blank')}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
        
        {article.tags && article.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {article.tags.slice(0, 3).map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const activeArticles = newsFeed[selectedCategory] || [];

  return (
    <section className="mobile-spacing bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
            <h2 className="text-3xl font-bold text-gray-900">
              Международные новости
            </h2>
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Следите за последними новостями технологий, продуктов и трендов международного шоппинга
          </p>
        </div>

        <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 lg:grid-cols-5 mb-8">
            {Object.entries(newsCategories).slice(0, 3).map(([key, category]) => (
              <TabsTrigger key={key} value={key} className="text-xs lg:text-sm">
                {category.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mr-3" />
              <span className="text-gray-600">Загрузка новостей...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadNewsFeed} variant="outline">
                Попробовать снова
              </Button>
            </div>
          ) : (
            Object.entries(newsCategories).slice(0, 3).map(([key, category]) => (
              <TabsContent key={key} value={key}>
                {(newsFeed[key] || []).length > 0 ? (
                  <div className="mobile-news-grid">
                    {(newsFeed[key] || []).map((article, index) => (
                      <NewsCard key={article.id || index} article={article} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Globe className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Новости не найдены
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Новости в категории "{category.name}" пока недоступны
                    </p>
                    <Button onClick={loadNewsFeed} variant="outline">
                      Обновить
                    </Button>
                  </div>
                )}
              </TabsContent>
            ))
          )}
        </Tabs>

        <div className="text-center mt-12">
          <Button 
            onClick={() => window.open('/news', '_blank')}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Все новости
            <ExternalLink className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>
    </section>
  );
};