import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Factory, Zap, Settings, Wrench, Camera, Search,
  FileText, TrendingUp, Shield, CheckCircle, Building,
  Cpu, Database, Globe, Star
} from 'lucide-react';

const businessCategories = [
  {
    id: 'automation',
    name: 'Автоматизация и Робототехника',
    icon: <Cpu className="h-8 w-8" />,
    description: 'Промышленная автоматизация, роботы, ПЛК, датчики',
    color: 'from-blue-500 to-cyan-500',
    brands: [
      { name: 'ABB', specialty: 'Промышленные роботы, приводы', country: '🇸🇪' },
      { name: 'KUKA', specialty: 'Роботизированные системы', country: '🇩🇪' },
      { name: 'Fanuc', specialty: 'ЧПУ, роботы, серводвигатели', country: '🇯🇵' },
      { name: 'Siemens', specialty: 'ПЛК, HMI, SCADA системы', country: '🇩🇪' },
      { name: 'Omron', specialty: 'Датчики, реле, контроллеры', country: '🇯🇵' },
      { name: 'Mitsubishi Electric', specialty: 'ПЛК, серводвигатели', country: '🇯🇵' },
      { name: 'Rockwell Automation', specialty: 'Allen-Bradley ПЛК', country: '🇺🇸' },
      { name: 'B&R Automation', specialty: 'Модульные системы', country: '🇦🇹' }
    ]
  },
  {
    id: 'electrical',
    name: 'Электротехника',
    icon: <Zap className="h-8 w-8" />,
    description: 'Электрооборудование, щиты, кабели, автоматика',
    color: 'from-yellow-500 to-orange-500',
    brands: [
      { name: 'Schneider Electric', specialty: 'Автоматика, УЗО, контакторы', country: '🇫🇷' },
      { name: 'Siemens', specialty: 'Электрооборудование, щиты', country: '🇩🇪' },
      { name: 'ABB', specialty: 'Выключатели, реле, приводы', country: '🇸🇪' },
      { name: 'Phoenix Contact', specialty: 'Клеммы, разъемы, реле', country: '🇩🇪' },
      { name: 'Weidmüller', specialty: 'Соединительная техника', country: '🇩🇪' },
      { name: 'Rittal', specialty: 'Шкафы, климатика', country: '🇩🇪' },
      { name: 'Legrand', specialty: 'Электроустановочные изделия', country: '🇫🇷' },
      { name: 'WAGO', specialty: 'Клеммные блоки', country: '🇩🇪' }
    ]
  },
  {
    id: 'pneumatics',
    name: 'Пневматика',
    icon: <Settings className="h-8 w-8" />,
    description: 'Пневмоцилиндры, клапаны, компрессоры, фитинги',
    color: 'from-green-500 to-teal-500',
    brands: [
      { name: 'Festo', specialty: 'Пневматика, автоматизация', country: '🇩🇪' },
      { name: 'SMC', specialty: 'Пневмокомпоненты', country: '🇯🇵' },
      { name: 'Parker', specialty: 'Гидравлика, пневматика', country: '🇺🇸' },
      { name: 'Norgren', specialty: 'Пневматические системы', country: '🇬🇧' },
      { name: 'Camozzi', specialty: 'Пневмоавтоматика', country: '🇮🇹' },
      { name: 'AVENTICS', specialty: 'Пневматические решения', country: '🇩🇪' },
      { name: 'Metal Work', specialty: 'Пневмокомпоненты', country: '🇮🇹' },
      { name: 'Airtac', specialty: 'Пневматическое оборудование', country: '🇹🇼' }
    ]
  },
  {
    id: 'machinery',
    name: 'Станки и Оборудование',
    icon: <Factory className="h-8 w-8" />,
    description: 'Промышленные станки, оборудование, инструмент',
    color: 'from-purple-500 to-pink-500',
    brands: [
      { name: 'Caterpillar', specialty: 'Тяжелая техника, двигатели', country: '🇺🇸' },
      { name: 'Komatsu', specialty: 'Строительная техника', country: '🇯🇵' },
      { name: 'Liebherr', specialty: 'Краны, экскаваторы', country: '🇩🇪' },
      { name: 'DMG MORI', specialty: 'Станки с ЧПУ', country: '🇩🇪' },
      { name: 'Mazak', specialty: 'Токарные, фрезерные станки', country: '🇯🇵' },
      { name: 'Sandvik', specialty: 'Режущий инструмент', country: '🇸🇪' },
      { name: 'Atlas Copco', specialty: 'Компрессоры, инструмент', country: '🇸🇪' },
      { name: 'Haas', specialty: 'Станки с ЧПУ', country: '🇺🇸' }
    ]
  }
];

export const BusinessSolutionsSection = () => {
  const [activeCategory, setActiveCategory] = useState('automation');
  const [searchQuery, setSearchQuery] = useState('');
  const [modelQuery, setModelQuery] = useState('');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [predictiveSuggestions, setPredictiveSuggestions] = useState([]);

  const currentCategory = businessCategories.find(cat => cat.id === activeCategory);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleModelInput = (value) => {
    setModelQuery(value);
    
    // Simulate predictive suggestions
    if (value.length > 2) {
      const suggestions = [
        `${value} - Серия A`,
        `${value} - Серия B Pro`,
        `${value} - Industrial Grade`,
        `${value} - Compact Version`,
        `${value} - Heavy Duty`
      ];
      setPredictiveSuggestions(suggestions);
    } else {
      setPredictiveSuggestions([]);
    }
  };

  const performSearch = async () => {
    setIsSearching(true);
    
    // Simulate AI-powered equipment search
    setTimeout(() => {
      const mockResults = [
        {
          id: '1',
          name: searchQuery || modelQuery || 'Siemens S7-1200 ПЛК',
          brand: 'Siemens',
          model: 'S7-1200 CPU 1214C',
          category: 'Программируемые логические контроллеры',
          description: 'Компактный ПЛК для автоматизации малых и средних систем',
          specifications: {
            'Цифровые входы': '14',
            'Цифровые выходы': '10',
            'Аналоговые входы': '2',
            'Память программы': '100 КБ',
            'Интерфейсы': 'Ethernet, USB'
          },
          price: '€450-680',
          priceRub: '45,000-68,000 ₽',
          availability: 'В наличии',
          leadTime: '2-3 недели',
          image: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=300&h=200&fit=crop',
          datasheet: 'siemens_s7_1200_datasheet.pdf',
          certifications: ['CE', 'UL', 'CSA']
        },
        {
          id: '2',
          name: 'Schneider Electric Altivar ATV320',
          brand: 'Schneider Electric',
          model: 'ATV320U75N4C',
          category: 'Преобразователи частоты',
          description: 'Компактный частотный преобразователь для управления асинхронными двигателями',
          specifications: {
            'Мощность': '7.5 кВт',
            'Напряжение': '380-480 В',
            'Частота': '0-500 Гц',
            'Защита': 'IP20',
            'Интерфейс': 'Modbus RTU'
          },
          price: '€320-480',
          priceRub: '32,000-48,000 ₽',
          availability: 'Под заказ',
          leadTime: '1-2 недели',
          image: 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=300&h=200&fit=crop',
          datasheet: 'schneider_atv320_manual.pdf',
          certifications: ['CE', 'UL', 'GOST-R']
        },
        {
          id: '3',
          name: 'Festo DSBC Пневмоцилиндр',
          brand: 'Festo',
          model: 'DSBC-63-100-PPVA-N3',
          category: 'Пневматические цилиндры',
          description: 'Стандартный пневмоцилиндр с магнитным поршнем',
          specifications: {
            'Диаметр поршня': '63 мм',
            'Ход': '100 мм',
            'Рабочее давление': '1-10 бар',
            'Температура': '-20°C до +80°C',
            'Крепление': 'Передний фланец'
          },
          price: '€180-250',
          priceRub: '18,000-25,000 ₽',
          availability: 'В наличии',
          leadTime: '1 неделя',
          image: 'https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=300&h=200&fit=crop',
          datasheet: 'festo_dsbc_datasheet.pdf',
          certifications: ['CE', 'ISO 15552']
        }
      ];
      
      setSearchResults(mockResults);
      setIsSearching(false);
    }, 2500);
  };

  return (
    <div className="py-16 bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            🏭 Решения для бизнеса (B2B)
          </h2>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto">
            Поиск промышленного оборудования ведущих мировых брендов с ИИ-распознаванием 
            по фото и предиктивным поиском моделей
          </p>
        </div>

        {/* Category Tabs */}
        <div className="mb-12">
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            {businessCategories.map((category) => (
              <Button
                key={category.id}
                variant={activeCategory === category.id ? "default" : "outline"}
                onClick={() => setActiveCategory(category.id)}
                className={`flex items-center space-x-2 px-6 py-3 ${
                  activeCategory === category.id 
                    ? `bg-gradient-to-r ${category.color} text-white` 
                    : ''
                }`}
              >
                {category.icon}
                <span>{category.name}</span>
              </Button>
            ))}
          </div>

          {/* Current Category Info */}
          <Card className="max-w-4xl mx-auto">
            <CardHeader>
              <CardTitle className={`flex items-center text-2xl bg-gradient-to-r ${currentCategory.color} bg-clip-text text-transparent`}>
                {currentCategory.icon}
                <span className="ml-3">{currentCategory.name}</span>
              </CardTitle>
              <p className="text-gray-600">{currentCategory.description}</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {currentCategory.brands.map((brand, index) => (
                  <div key={index} className="p-3 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-gray-900">{brand.name}</span>
                      <span className="text-lg">{brand.country}</span>
                    </div>
                    <p className="text-xs text-gray-600">{brand.specialty}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search Section */}
        <div className="max-w-4xl mx-auto mb-12">
          <Tabs defaultValue="search" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="search" className="flex items-center">
                <Search className="h-4 w-4 mr-2" />
                Поиск по описанию
              </TabsTrigger>
              <TabsTrigger value="model" className="flex items-center">
                <FileText className="h-4 w-4 mr-2" />
                Модель/Артикул
              </TabsTrigger>
              <TabsTrigger value="photo" className="flex items-center">
                <Camera className="h-4 w-4 mr-2" />
                Фото оборудования
              </TabsTrigger>
            </TabsList>

            <TabsContent value="search" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Поиск оборудования по описанию</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="search">Описание необходимого оборудования</Label>
                      <Input
                        id="search"
                        placeholder="Например: ПЛК Siemens на 24 входа, частотный преобразователь 7.5кВт..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="text-lg"
                      />
                    </div>
                    <Button 
                      onClick={performSearch}
                      disabled={isSearching || !searchQuery}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {isSearching ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Search className="h-4 w-4 mr-2" />
                      )}
                      Найти подходящее оборудование
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="model" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Предиктивный поиск по модели</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="model">Модель или артикул</Label>
                      <Input
                        id="model"
                        placeholder="Начните вводить: S7-1200, ATV320, DSBC..."
                        value={modelQuery}
                        onChange={(e) => handleModelInput(e.target.value)}
                        className="text-lg"
                      />
                      
                      {/* Predictive Suggestions */}
                      {predictiveSuggestions.length > 0 && (
                        <div className="mt-2 border rounded-lg bg-white shadow-lg">
                          {predictiveSuggestions.map((suggestion, index) => (
                            <div
                              key={index}
                              className="px-4 py-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                              onClick={() => {
                                setModelQuery(suggestion);
                                setPredictiveSuggestions([]);
                              }}
                            >
                              {suggestion}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    <Button 
                      onClick={performSearch}
                      disabled={isSearching || !modelQuery}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      {isSearching ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Database className="h-4 w-4 mr-2" />
                      )}
                      Найти точную модель
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="photo" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>ИИ-распознавание по фото</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label>Загрузите фото оборудования</Label>
                      <div className="mt-2">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageUpload}
                          className="hidden"
                          id="equipment-image"
                        />
                        <label
                          htmlFor="equipment-image"
                          className="flex items-center justify-center w-full h-48 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400"
                        >
                          {uploadedImage ? (
                            <img 
                              src={uploadedImage} 
                              alt="Uploaded equipment" 
                              className="h-full object-cover rounded"
                            />
                          ) : (
                            <div className="text-center">
                              <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                              <span className="text-gray-500">Загрузить фото шильдика или оборудования</span>
                              <p className="text-xs text-gray-400 mt-2">
                                Поддерживаются форматы: JPG, PNG, WEBP
                              </p>
                            </div>
                          )}
                        </label>
                      </div>
                    </div>
                    <Button 
                      onClick={performSearch}
                      disabled={isSearching || !uploadedImage}
                      className="w-full bg-purple-600 hover:bg-purple-700"
                    >
                      {isSearching ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Zap className="h-4 w-4 mr-2" />
                      )}
                      Распознать и найти оборудование
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mb-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              Найденное оборудование ({searchResults.length})
            </h3>
            <div className="space-y-6">
              {searchResults.map((result) => (
                <Card key={result.id} className="overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex flex-col lg:flex-row lg:space-x-6">
                      {/* Image */}
                      <div className="lg:w-64 mb-4 lg:mb-0">
                        <img 
                          src={result.image} 
                          alt={result.name}
                          className="w-full h-48 object-cover rounded-lg"
                        />
                      </div>
                      
                      {/* Details */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <div className="flex items-center space-x-2 mb-2">
                              <Badge className="bg-blue-100 text-blue-800">{result.brand}</Badge>
                              <Badge className="bg-green-100 text-green-800">{result.category}</Badge>
                              <Badge variant={result.availability === 'В наличии' ? 'default' : 'secondary'}>
                                {result.availability}
                              </Badge>
                            </div>
                            <h4 className="text-xl font-bold text-gray-900 mb-1">{result.name}</h4>
                            <p className="text-gray-600 mb-2">Модель: {result.model}</p>
                            <p className="text-sm text-gray-600">{result.description}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-green-600">{result.priceRub}</div>
                            <div className="text-sm text-gray-500">{result.price}</div>
                            <div className="text-xs text-gray-400 mt-1">
                              Поставка: {result.leadTime}
                            </div>
                          </div>
                        </div>
                        
                        {/* Specifications */}
                        <div className="mb-4">
                          <h5 className="font-semibold text-gray-900 mb-2">Технические характеристики:</h5>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                            {Object.entries(result.specifications).map(([key, value]) => (
                              <div key={key} className="bg-gray-50 p-2 rounded">
                                <div className="font-medium text-gray-700">{key}</div>
                                <div className="text-gray-600">{value}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        {/* Certifications */}
                        <div className="mb-4">
                          <h5 className="font-semibold text-gray-900 mb-2">Сертификаты:</h5>
                          <div className="flex space-x-2">
                            {result.certifications.map((cert, index) => (
                              <Badge key={index} variant="outline">{cert}</Badge>
                            ))}
                          </div>
                        </div>
                        
                        {/* Actions */}
                        <div className="flex flex-wrap gap-3">
                          <Button className="flex-1 min-w-[160px]">
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Запросить КП
                          </Button>
                          <Button variant="outline">
                            <FileText className="h-4 w-4 mr-2" />
                            Техпаспорт
                          </Button>
                          <Button variant="outline">
                            <TrendingUp className="h-4 w-4 mr-2" />
                            Аналоги
                          </Button>
                          <Button variant="outline">
                            <Building className="h-4 w-4 mr-2" />
                            Поставщики
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Features Section */}
        <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-2xl p-8">
          <div className="text-center mb-8">
            <h3 className="text-3xl font-bold mb-4">Преимущества для B2B клиентов</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <Globe className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-lg font-bold mb-2">Мировые бренды</h4>
              <p className="text-sm text-gray-300">Прямые поставки от ведущих производителей</p>
            </div>
            <div className="text-center">
              <Zap className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-lg font-bold mb-2">ИИ-поиск</h4>
              <p className="text-sm text-gray-300">Умный поиск по фото и описанию</p>
            </div>
            <div className="text-center">
              <Shield className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-lg font-bold mb-2">Гарантии</h4>
              <p className="text-sm text-gray-300">Официальная гарантия и сертификаты</p>
            </div>
            <div className="text-center">
              <Star className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-lg font-bold mb-2">VIP сервис</h4>
              <p className="text-sm text-gray-300">Персональный менеджер и техподдержка</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};