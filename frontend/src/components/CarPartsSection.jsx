import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Car, Search, Camera, FileText, Wrench, 
  CheckCircle, AlertCircle, Zap, Database,
  Settings, Shield, TrendingUp
} from 'lucide-react';

const carBrands = [
  'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Toyota', 'Honda',
  'Ford', 'Chevrolet', 'Nissan', 'Hyundai', 'Kia', 'Mazda',
  'Subaru', 'Mitsubishi', 'Peugeot', 'Renault', 'Volvo', 'Skoda'
];

const oemManufacturers = [
  { name: 'BOSCH', description: 'Электроника, тормоза, зажигание', logo: '🔧' },
  { name: 'Continental', description: 'Шины, тормоза, электроника', logo: '⚙️' },
  { name: 'Mahle', description: 'Фильтры, поршни, термостаты', logo: '🔩' },
  { name: 'Febi', description: 'Подвеска, трансмиссия', logo: '🏗️' },
  { name: 'Sachs', description: 'Амортизаторы, сцепление', logo: '🔨' },
  { name: 'Valeo', description: 'Освещение, климат, электрика', logo: '💡' },
  { name: 'Mann+Hummel', description: 'Фильтрация воздуха и масла', logo: '🌪️' },
  { name: 'ZF', description: 'Трансмиссия, рулевое управление', logo: '⚡' }
];

export const CarPartsSection = () => {
  const [activeTab, setActiveTab] = useState('vin');
  const [searchData, setSearchData] = useState({
    vin: '',
    partNumber: '',
    year: '',
    make: '',
    model: '',
    variant: ''
  });
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);

  const handleInputChange = (field, value) => {
    setSearchData(prev => ({ ...prev, [field]: value }));
  };

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

  const performSearch = async (searchType) => {
    setIsSearching(true);
    
    // Simulate AI-powered search
    setTimeout(() => {
      const mockResults = [
        {
          id: '1',
          partName: searchType === 'vin' ? 'Тормозные колодки передние' : 
                   searchType === 'part' ? 'Оригинальная деталь BMW' : 'Воздушный фильтр',
          originalBrand: 'BMW',
          oemManufacturer: 'BOSCH',
          partNumber: '34116858910',
          compatibility: ['BMW 3-Series (F30)', 'BMW 4-Series (F32)'],
          price: '€45-78',
          priceRub: '4,500-7,800 ₽',
          availability: 'В наличии',
          images: ['https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=200&h=200&fit=crop'],
          description: 'Оригинальные тормозные колодки BOSCH, устанавливаемые на заводе BMW',
          specifications: {
            thickness: '17.5mm',
            length: '156.3mm',
            width: '74.0mm',
            material: 'Ceramic'
          }
        },
        {
          id: '2',
          partName: 'Масляный фильтр',
          originalBrand: 'BMW',
          oemManufacturer: 'Mann+Hummel',
          partNumber: '11427566327',
          compatibility: ['BMW 3-Series (F30)', 'BMW X3 (F25)', 'BMW X4 (F26)'],
          price: '€12-25',
          priceRub: '1,200-2,500 ₽',
          availability: 'В наличии',
          images: ['https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=200&h=200&fit=crop'],
          description: 'Оригинальный масляный фильтр Mann+Hummel для двигателей BMW',
          specifications: {
            height: '93mm',
            diameter: '65mm',
            thread: 'M20x1.5',
            material: 'Synthetic'
          }
        },
        {
          id: '3',
          partName: 'Амортизатор передний',
          originalBrand: 'BMW',
          oemManufacturer: 'Sachs',
          partNumber: '31316785965',
          compatibility: ['BMW 3-Series (F30)', 'BMW 4-Series (F32)'],
          price: '€89-156',
          priceRub: '8,900-15,600 ₽',
          availability: 'Под заказ',
          images: ['https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=200&h=200&fit=crop'],
          description: 'Оригинальный амортизатор Sachs с газовым наполнением',
          specifications: {
            length: '565mm',
            diameter: '55mm',
            type: 'Gas-filled',
            mounting: 'Top mount'
          }
        }
      ];
      
      setSearchResults(mockResults);
      setIsSearching(false);
    }, 3000);
  };

  return (
    <div className="py-16 bg-gradient-to-br from-blue-50 to-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            🚗 Автозапчасти с ИИ-определением OEM
          </h2>
          <p className="text-xl text-gray-600 max-w-4xl mx-auto">
            Поиск автозапчастей по VIN, номеру детали или характеристикам автомобиля. 
            ИИ определяет настоящего производителя (OEM) и находит лучшие цены по всему миру.
          </p>
        </div>

        {/* Search Tabs */}
        <div className="max-w-4xl mx-auto mb-12">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="vin" className="flex items-center">
                <FileText className="h-4 w-4 mr-2" />
                VIN номер
              </TabsTrigger>
              <TabsTrigger value="part" className="flex items-center">
                <Settings className="h-4 w-4 mr-2" />
                Номер детали
              </TabsTrigger>
              <TabsTrigger value="car" className="flex items-center">
                <Car className="h-4 w-4 mr-2" />
                Марка/Модель
              </TabsTrigger>
            </TabsList>

            <TabsContent value="vin" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Database className="h-5 w-5 mr-2 text-blue-500" />
                    Поиск по VIN номеру
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="vin">VIN номер автомобиля</Label>
                      <Input
                        id="vin"
                        placeholder="Например: WBAJA5C50HWA12345"
                        value={searchData.vin}
                        onChange={(e) => handleInputChange('vin', e.target.value)}
                        className="text-lg"
                      />
                      <p className="text-sm text-gray-500 mt-1">
                        17-значный код, обычно находится на лобовом стекле или в документах
                      </p>
                    </div>
                    <Button 
                      onClick={() => performSearch('vin')}
                      disabled={isSearching || !searchData.vin}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {isSearching ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Zap className="h-4 w-4 mr-2" />
                      )}
                      Найти все совместимые детали
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="part" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Wrench className="h-5 w-5 mr-2 text-green-500" />
                    Поиск по номеру детали
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="partNumber">Номер детали</Label>
                      <Input
                        id="partNumber"
                        placeholder="Например: 11427566327, 0450906457"
                        value={searchData.partNumber}
                        onChange={(e) => handleInputChange('partNumber', e.target.value)}
                      />
                    </div>
                    
                    {/* Image Upload */}
                    <div>
                      <Label>Фото детали (опционально)</Label>
                      <div className="mt-2">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageUpload}
                          className="hidden"
                          id="part-image"
                        />
                        <label
                          htmlFor="part-image"
                          className="flex items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-gray-400"
                        >
                          {uploadedImage ? (
                            <img 
                              src={uploadedImage} 
                              alt="Uploaded part" 
                              className="h-full object-cover rounded"
                            />
                          ) : (
                            <div className="text-center">
                              <Camera className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                              <span className="text-gray-500">Загрузить фото детали</span>
                            </div>
                          )}
                        </label>
                      </div>
                    </div>
                    
                    <Button 
                      onClick={() => performSearch('part')}
                      disabled={isSearching || !searchData.partNumber}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      {isSearching ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      ) : (
                        <Search className="h-4 w-4 mr-2" />
                      )}
                      Определить OEM производителя
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="car" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Car className="h-5 w-5 mr-2 text-purple-500" />
                    Поиск по марке и модели
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="year">Год выпуска</Label>
                      <Input
                        id="year"
                        placeholder="2020"
                        value={searchData.year}
                        onChange={(e) => handleInputChange('year', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="make">Марка</Label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={searchData.make}
                        onChange={(e) => handleInputChange('make', e.target.value)}
                      >
                        <option value="">Выберите марку</option>
                        {carBrands.map(brand => (
                          <option key={brand} value={brand}>{brand}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="model">Модель</Label>
                      <Input
                        id="model"
                        placeholder="3 Series"
                        value={searchData.model}
                        onChange={(e) => handleInputChange('model', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="variant">Вариант/Двигатель</Label>
                      <Input
                        id="variant"
                        placeholder="320i, 2.0L Turbo"
                        value={searchData.variant}
                        onChange={(e) => handleInputChange('variant', e.target.value)}
                      />
                    </div>
                  </div>
                  <Button 
                    onClick={() => performSearch('car')}
                    disabled={isSearching || !searchData.make || !searchData.model}
                    className="w-full mt-6 bg-purple-600 hover:bg-purple-700"
                  >
                    {isSearching ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    ) : (
                      <Database className="h-4 w-4 mr-2" />
                    )}
                    Найти подходящие детали
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* OEM Manufacturers Section */}
        <div className="mb-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Ведущие OEM производители
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {oemManufacturers.map((manufacturer, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  <div className="text-3xl mb-2">{manufacturer.logo}</div>
                  <h4 className="font-bold text-gray-900">{manufacturer.name}</h4>
                  <p className="text-sm text-gray-600">{manufacturer.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mb-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              Результаты поиска ({searchResults.length})
            </h3>
            <div className="space-y-6">
              {searchResults.map((result) => (
                <Card key={result.id} className="overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex flex-col lg:flex-row lg:space-x-6">
                      {/* Image */}
                      <div className="lg:w-48 mb-4 lg:mb-0">
                        <img 
                          src={result.images[0]} 
                          alt={result.partName}
                          className="w-full h-48 object-cover rounded-lg"
                        />
                      </div>
                      
                      {/* Details */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <div className="flex items-center space-x-2 mb-2">
                              <Badge className="bg-blue-100 text-blue-800">{result.originalBrand}</Badge>
                              <Badge className="bg-green-100 text-green-800">OEM: {result.oemManufacturer}</Badge>
                              <Badge variant={result.availability === 'В наличии' ? 'default' : 'secondary'}>
                                {result.availability}
                              </Badge>
                            </div>
                            <h4 className="text-xl font-bold text-gray-900 mb-1">{result.partName}</h4>
                            <p className="text-gray-600 mb-2">Номер детали: {result.partNumber}</p>
                            <p className="text-sm text-gray-600">{result.description}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-green-600">{result.priceRub}</div>
                            <div className="text-sm text-gray-500">{result.price}</div>
                          </div>
                        </div>
                        
                        {/* Compatibility */}
                        <div className="mb-4">
                          <h5 className="font-semibold text-gray-900 mb-2">Совместимость:</h5>
                          <div className="flex flex-wrap gap-2">
                            {result.compatibility.map((model, index) => (
                              <Badge key={index} variant="outline">{model}</Badge>
                            ))}
                          </div>
                        </div>
                        
                        {/* Specifications */}
                        <div className="mb-4">
                          <h5 className="font-semibold text-gray-900 mb-2">Характеристики:</h5>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                            {Object.entries(result.specifications).map(([key, value]) => (
                              <div key={key} className="bg-gray-50 p-2 rounded">
                                <div className="font-medium text-gray-700 capitalize">{key}</div>
                                <div className="text-gray-600">{value}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        {/* Actions */}
                        <div className="flex space-x-4">
                          <Button className="flex-1">
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Заказать деталь
                          </Button>
                          <Button variant="outline">
                            <TrendingUp className="h-4 w-4 mr-2" />
                            Сравнить цены
                          </Button>
                          <Button variant="outline">
                            <Shield className="h-4 w-4 mr-2" />
                            Гарантия
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
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl p-8">
          <div className="text-center mb-8">
            <h3 className="text-3xl font-bold mb-4">Почему выбирают наш сервис?</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <Database className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-xl font-bold mb-2">Полная база данных</h4>
              <p>Доступ к мировым базам автозапчастей и OEM производителей</p>
            </div>
            <div className="text-center">
              <Zap className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-xl font-bold mb-2">ИИ-определение</h4>
              <p>Точное определение оригинального производителя и аналогов</p>
            </div>
            <div className="text-center">
              <Shield className="h-12 w-12 mx-auto mb-4" />
              <h4 className="text-xl font-bold mb-2">100% гарантия</h4>
              <p>Гарантия подлинности и совместимости всех деталей</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};