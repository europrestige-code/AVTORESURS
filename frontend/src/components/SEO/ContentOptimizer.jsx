import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { 
  FileText, CheckCircle, AlertCircle, TrendingUp, 
  Eye, Search, Globe, Target, Zap, BarChart3 
} from 'lucide-react';

export const ContentOptimizer = () => {
  const [content, setContent] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedKeywords, setSelectedKeywords] = useState([]);

  // Russian keyword targets for international shopping
  const TARGET_KEYWORDS = [
    'покупки из-за границы',
    'доставка из-за рубежа',
    'заказ товаров',
    'международная доставка',
    'таможенное оформление',
    'выкуп товаров',
    'сервис доставки',
    'посредник',
    'оригинальные товары',
    'брендовые товары'
  ];

  // Content analysis function
  const analyzeContent = (text) => {
    const words = text.toLowerCase().split(/\s+/).filter(word => word.length > 0);
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const paragraphs = text.split(/\n\s*\n/).filter(p => p.trim().length > 0);

    // Keyword density analysis
    const keywordDensity = {};
    TARGET_KEYWORDS.forEach(keyword => {
      const regex = new RegExp(keyword.toLowerCase(), 'g');
      const matches = (text.toLowerCase().match(regex) || []).length;
      keywordDensity[keyword] = {
        count: matches,
        density: words.length > 0 ? ((matches / words.length) * 100).toFixed(2) : 0
      };
    });

    // Readability analysis (simplified Flesch formula for Russian)
    const avgWordsPerSentence = sentences.length > 0 ? words.length / sentences.length : 0;
    const avgSyllablesPerWord = words.reduce((sum, word) => {
      // Simplified syllable count for Russian
      const syllables = word.match(/[аеёиоуыэюя]/gi);
      return sum + (syllables ? syllables.length : 1);
    }, 0) / words.length;

    const readabilityScore = 206.835 - (1.015 * avgWordsPerSentence) - (84.6 * avgSyllablesPerWord);

    // SEO analysis
    const hasH1 = /<h1[^>]*>.*?<\/h1>/i.test(text) || text.includes('# ');
    const hasH2 = /<h[2-6][^>]*>.*?<\/h[2-6]>/i.test(text) || text.includes('## ');
    const hasMetaDescription = text.includes('description') || text.includes('мета-описание');
    const wordCount = words.length;

    // Title and description extraction
    const titleMatch = text.match(/<title[^>]*>(.*?)<\/title>/i) || text.match(/^#\s(.+)$/m);
    const title = titleMatch ? titleMatch[1] : '';
    
    const descMatch = text.match(/<meta[^>]*name="description"[^>]*content="([^"]*)"[^>]*>/i);
    const description = descMatch ? descMatch[1] : '';

    return {
      basic: {
        wordCount,
        characterCount: text.length,
        paragraphCount: paragraphs.length,
        sentenceCount: sentences.length,
        avgWordsPerSentence: Math.round(avgWordsPerSentence * 10) / 10
      },
      keywords: keywordDensity,
      readability: {
        score: Math.max(0, Math.min(100, Math.round(readabilityScore))),
        level: readabilityScore > 60 ? 'легкий' : readabilityScore > 30 ? 'средний' : 'сложный'
      },
      seo: {
        hasH1,
        hasH2,
        hasMetaDescription,
        titleLength: title.length,
        descriptionLength: description.length,
        keywordInTitle: TARGET_KEYWORDS.some(k => title.toLowerCase().includes(k.toLowerCase())),
        keywordInDescription: TARGET_KEYWORDS.some(k => description.toLowerCase().includes(k.toLowerCase()))
      },
      title,
      description
    };
  };

  // Handle content analysis
  const handleAnalyze = async () => {
    if (!content.trim()) return;
    
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate analysis delay
    
    const result = analyzeContent(content);
    setAnalysis(result);
    setLoading(false);
  };

  // Get score color
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Get optimization suggestions
  const getOptimizationTips = () => {
    if (!analysis) return [];

    const tips = [];

    // Word count
    if (analysis.basic.wordCount < 300) {
      tips.push({
        type: 'warning',
        text: 'Увеличьте объем контента до 300+ слов для лучшего ранжирования'
      });
    }

    // Title optimization
    if (analysis.seo.titleLength === 0) {
      tips.push({
        type: 'error',
        text: 'Добавьте заголовок H1 с ключевыми словами'
      });
    } else if (analysis.seo.titleLength > 60) {
      tips.push({
        type: 'warning',
        text: 'Сократите заголовок до 60 символов для корректного отображения в поиске'
      });
    }

    // Keyword density
    const overOptimized = Object.entries(analysis.keywords).filter(([_, data]) => data.density > 3);
    if (overOptimized.length > 0) {
      tips.push({
        type: 'warning',
        text: `Снизьте плотность ключевых слов: ${overOptimized.map(([k]) => k).join(', ')}`
      });
    }

    const underOptimized = Object.entries(analysis.keywords).filter(([_, data]) => data.count === 0 && selectedKeywords.includes(_));
    if (underOptimized.length > 0) {
      tips.push({
        type: 'info',
        text: `Добавьте ключевые слова: ${underOptimized.map(([k]) => k).join(', ')}`
      });
    }

    // Structure
    if (!analysis.seo.hasH2) {
      tips.push({
        type: 'info',
        text: 'Добавьте подзаголовки H2-H3 для лучшей структуры'
      });
    }

    // Readability
    if (analysis.readability.score < 30) {
      tips.push({
        type: 'warning',
        text: 'Упростите текст: используйте короткие предложения и простые слова'
      });
    }

    return tips;
  };

  // Calculate overall SEO score
  const calculateSEOScore = () => {
    if (!analysis) return 0;

    let score = 0;
    let maxScore = 0;

    // Word count (20 points)
    maxScore += 20;
    if (analysis.basic.wordCount >= 300) score += 20;
    else if (analysis.basic.wordCount >= 150) score += 10;

    // Title optimization (15 points)
    maxScore += 15;
    if (analysis.seo.titleLength > 0 && analysis.seo.titleLength <= 60) score += 15;
    else if (analysis.seo.titleLength > 0) score += 8;

    // Keyword usage (25 points)
    maxScore += 25;
    const keywordScore = Object.values(analysis.keywords).reduce((sum, data) => {
      if (data.count > 0 && data.density <= 3) return sum + 1;
      return sum;
    }, 0);
    score += Math.min(25, keywordScore * 3);

    // Structure (20 points)
    maxScore += 20;
    if (analysis.seo.hasH1) score += 10;
    if (analysis.seo.hasH2) score += 10;

    // Readability (20 points)
    maxScore += 20;
    if (analysis.readability.score >= 60) score += 20;
    else if (analysis.readability.score >= 30) score += 12;
    else score += 5;

    return Math.round((score / maxScore) * 100);
  };

  const seoScore = analysis ? calculateSEOScore() : 0;
  const optimizationTips = analysis ? getOptimizationTips() : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Оптимизатор Контента
        </h2>
        <p className="text-gray-600 max-w-3xl mx-auto">
          Анализ и оптимизация контента для поисковых систем
        </p>
      </div>

      {/* Content Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="h-5 w-5 mr-2" />
            Введите текст для анализа
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Textarea
              placeholder="Вставьте ваш контент сюда..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={10}
              className="min-h-[200px]"
            />
            
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                Символов: {content.length} | Слов: {content.split(/\s+/).filter(w => w.length > 0).length}
              </div>
              <Button onClick={handleAnalyze} disabled={loading || !content.trim()}>
                {loading ? 'Анализируем...' : 'Анализировать'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Keyword Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="h-5 w-5 mr-2" />
            Целевые ключевые слова
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {TARGET_KEYWORDS.map((keyword, index) => (
              <Badge
                key={index}
                variant={selectedKeywords.includes(keyword) ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => {
                  if (selectedKeywords.includes(keyword)) {
                    setSelectedKeywords(selectedKeywords.filter(k => k !== keyword));
                  } else {
                    setSelectedKeywords([...selectedKeywords, keyword]);
                  }
                }}
              >
                {keyword}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {analysis && (
        <>
          {/* SEO Score */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2" />
                  SEO Оценка
                </div>
                <div className={`text-2xl font-bold ${getScoreColor(seoScore)}`}>
                  {seoScore}/100
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Progress value={seoScore} className="mb-4" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {analysis.basic.wordCount}
                  </div>
                  <div className="text-sm text-gray-600">Слов</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {analysis.readability.score}
                  </div>
                  <div className="text-sm text-gray-600">Читаемость</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {Object.values(analysis.keywords).filter(k => k.count > 0).length}
                  </div>
                  <div className="text-sm text-gray-600">Ключевых слов</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Keyword Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Search className="h-5 w-5 mr-2" />
                Анализ ключевых слов
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b">
                      <th className="pb-2">Ключевое слово</th>
                      <th className="pb-2">Количество</th>
                      <th className="pb-2">Плотность</th>
                      <th className="pb-2">Статус</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(analysis.keywords).map(([keyword, data]) => (
                      <tr key={keyword} className="border-b">
                        <td className="py-2 font-medium">{keyword}</td>
                        <td className="py-2">{data.count}</td>
                        <td className="py-2">{data.density}%</td>
                        <td className="py-2">
                          {data.count === 0 ? (
                            <Badge className="bg-gray-100 text-gray-800">Отсутствует</Badge>
                          ) : data.density > 3 ? (
                            <Badge className="bg-red-100 text-red-800">Переспам</Badge>
                          ) : data.density >= 1 ? (
                            <Badge className="bg-green-100 text-green-800">Оптимально</Badge>
                          ) : (
                            <Badge className="bg-yellow-100 text-yellow-800">Мало</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Optimization Tips */}
          {optimizationTips.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2" />
                  Рекомендации по оптимизации
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {optimizationTips.map((tip, index) => (
                    <div
                      key={index}
                      className={`flex items-start space-x-3 p-3 rounded-lg ${
                        tip.type === 'error' 
                          ? 'bg-red-50 border border-red-200' 
                          : tip.type === 'warning'
                          ? 'bg-yellow-50 border border-yellow-200'
                          : 'bg-blue-50 border border-blue-200'
                      }`}
                    >
                      {tip.type === 'error' && <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />}
                      {tip.type === 'warning' && <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />}
                      {tip.type === 'info' && <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5" />}
                      <div className={`flex-1 ${
                        tip.type === 'error' 
                          ? 'text-red-800' 
                          : tip.type === 'warning'
                          ? 'text-yellow-800'
                          : 'text-blue-800'
                      }`}>
                        {tip.text}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Technical SEO */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Globe className="h-5 w-5 mr-2" />
                Техническое SEO
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Заголовок H1</span>
                    {analysis.seo.hasH1 ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Подзаголовки H2-H6</span>
                    {analysis.seo.hasH2 ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Длина заголовка</span>
                    <span className={analysis.seo.titleLength <= 60 ? 'text-green-600' : 'text-red-600'}>
                      {analysis.seo.titleLength} симв.
                    </span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Ключевое слово в заголовке</span>
                    {analysis.seo.keywordInTitle ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Читаемость</span>
                    <Badge className={
                      analysis.readability.score >= 60 
                        ? 'bg-green-100 text-green-800'
                        : analysis.readability.score >= 30
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }>
                      {analysis.readability.level}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Объем контента</span>
                    <span className={analysis.basic.wordCount >= 300 ? 'text-green-600' : 'text-yellow-600'}>
                      {analysis.basic.wordCount >= 300 ? 'Достаточно' : 'Мало'}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};