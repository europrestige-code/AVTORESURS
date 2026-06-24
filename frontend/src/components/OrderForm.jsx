import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Upload, Link, Package, Calculator, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const OrderForm = () => {
  const [orderType, setOrderType] = useState('url');
  const [formData, setFormData] = useState({
    url: '',
    productName: '',
    model: '',
    serialNumber: '',
    description: '',
    photo: null
  });
  
  const [calculation, setCalculation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear previous results when user changes input
    if (calculation) {
      setCalculation(null);
      setSuccess(false);
    }
    if (error) {
      setError(null);
    }
  };

  const calculatePrice = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);

      // Validate input based on type
      if (orderType === 'url' && !formData.url) {
        throw new Error('Пожалуйста, введите URL товара');
      }
      if (orderType === 'manual' && !formData.productName) {
        throw new Error('Пожалуйста, введите название товара');
      }
      if (orderType === 'photo' && !formData.photo) {
        throw new Error('Пожалуйста, загрузите фото товара');
      }

      // Prepare request data
      const requestData = {
        input_type: orderType,
      };

      if (orderType === 'url') {
        requestData.url = formData.url;
      } else if (orderType === 'manual') {
        requestData.product_name = formData.productName;
        requestData.model = formData.model;
        requestData.serial_number = formData.serialNumber;
        requestData.description = formData.description;
      } else if (orderType === 'photo') {
        // Convert file to base64
        const fileReader = new FileReader();
        const base64Promise = new Promise((resolve, reject) => {
          fileReader.onload = () => resolve(fileReader.result);
          fileReader.onerror = reject;
          fileReader.readAsDataURL(formData.photo);
        });
        const base64 = await base64Promise;
        requestData.photo_base64 = base64;
      }

      console.log('Sending request to backend:', requestData);

      // Call backend API
      const response = await axios.post(`${API}/calculate-price`, requestData, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout for AI processing
      });

      if (response.data.success) {
        setCalculation({
          productName: response.data.product_name,
          bestStore: response.data.best_store,
          originalPrice: response.data.breakdown.original_price,
          commission: response.data.breakdown.commission,
          shipping: response.data.breakdown.shipping,
          customs: response.data.breakdown.customs,
          insurance: response.data.breakdown.insurance,
          totalPrice: response.data.breakdown.total_price,
          aiConfidence: response.data.ai_confidence,
          calculationId: response.data.calculation_id
        });
        setSuccess(true);
        console.log('Price calculation successful:', response.data);
      } else {
        throw new Error(response.data.message || 'Ошибка расчёта стоимости');
      }

    } catch (err) {
      console.error('Error calculating price:', err);
      
      let errorMessage = 'Произошла ошибка при расчёте стоимости';
      
      if (err.response) {
        // Backend error response
        errorMessage = err.response.data?.detail || errorMessage;
      } else if (err.request) {
        // Network error
        errorMessage = 'Ошибка сети. Проверьте подключение к интернету';
      } else if (err.message) {
        // Custom error
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Пожалуйста, загрузите изображение');
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('Размер файла должен быть меньше 10МБ');
        return;
      }
      
      handleInputChange('photo', file);
    }
  };

  const proceedToOrder = () => {
    // This would open a customer info modal or redirect to order page
    console.log('Proceeding to order with calculation:', calculation);
    alert('Функция оформления заказа будет добавлена в следующем обновлении');
  };

  return (
    <section className="mobile-spacing bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Рассчитать стоимость товара
          </h2>
          
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8 max-w-2xl mx-auto">
            <p className="text-sm text-amber-800">
              <strong>Агентская модель:</strong> Вы самостоятельно выбираете товары, мы покупаем их по вашему поручению. 
              Ответственность за качество и соответствие товара вашим потребностям несёт продавец.
            </p>
          </div>
          <p className="text-lg text-gray-600">
            Выберите удобный способ описания товара
          </p>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calculator className="h-5 w-5 mr-2" />
              Детали заказа
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={orderType} onValueChange={setOrderType}>
              <TabsList className="mobile-order-tabs">
                <TabsTrigger value="url" className="flex items-center justify-center mobile-btn">
                  <Link className="h-4 w-4 mr-1 sm:mr-2" />
                  <span className="text-xs sm:text-sm">Ссылка</span>
                </TabsTrigger>
                <TabsTrigger value="manual" className="flex items-center justify-center mobile-btn">
                  <Package className="h-4 w-4 mr-1 sm:mr-2" />
                  <span className="text-xs sm:text-sm">Модель/Артикул</span>
                </TabsTrigger>
                <TabsTrigger value="photo" className="flex items-center justify-center mobile-btn">
                  <Upload className="h-4 w-4 mr-1 sm:mr-2" />
                  <span className="text-xs sm:text-sm">Фото товара</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="url" className="space-y-4">
                <div>
                  <Label htmlFor="url">Ссылка на товар</Label>
                  <Input
                    id="url"
                    placeholder="https://example.com/product"
                    value={formData.url}
                    onChange={(e) => handleInputChange('url', e.target.value)}
                    disabled={loading}
                    className="mobile-input"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Вставьте ссылку на товар из любого интернет-магазина
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="manual" className="space-y-4">
                <div className="mobile-profile-grid">
                  <div>
                    <Label htmlFor="productName">Название товара *</Label>
                    <Input
                      id="productName"
                      placeholder="iPhone 15 Pro"
                      value={formData.productName}
                      onChange={(e) => handleInputChange('productName', e.target.value)}
                      disabled={loading}
                      className="mobile-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="model">Модель</Label>
                    <Input
                      id="model"
                      placeholder="A2848"
                      value={formData.model}
                      onChange={(e) => handleInputChange('model', e.target.value)}
                      disabled={loading}
                      className="mobile-input"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="serialNumber">Серийный номер / Артикул</Label>
                  <Input
                    id="serialNumber"
                    placeholder="MTQN3LL/A"
                    value={formData.serialNumber}
                    onChange={(e) => handleInputChange('serialNumber', e.target.value)}
                    disabled={loading}
                    className="mobile-input"
                  />
                </div>
                <div>
                  <Label htmlFor="description">Дополнительное описание</Label>
                  <Textarea
                    id="description"
                    placeholder="Цвет, размер, конфигурация..."
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    disabled={loading}
                  />
                </div>
              </TabsContent>

              <TabsContent value="photo" className="space-y-4">
                <div>
                  <Label htmlFor="photo">Загрузить фото товара</Label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="mt-4">
                      <input
                        type="file"
                        id="photo"
                        className="hidden"
                        accept="image/*"
                        onChange={handleFileUpload}
                        disabled={loading}
                      />
                      <Button
                        variant="outline"
                        onClick={() => document.getElementById('photo').click()}
                        disabled={loading}
                      >
                        Выбрать файл
                      </Button>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">
                      PNG, JPG до 10МБ
                    </p>
                    {formData.photo && (
                      <p className="text-sm text-green-600 mt-2">
                        Файл загружен: {formData.photo.name}
                      </p>
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            )}

            <div className="mt-6">
              <Button 
                onClick={calculatePrice} 
                className="mobile-btn w-full bg-blue-600 hover:bg-blue-700"
                disabled={loading || (!formData.url && !formData.productName && !formData.photo)}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Анализируем товар...
                  </>
                ) : (
                  'Рассчитать стоимость'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {calculation && success && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2" />
                Расчёт стоимости
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Товар</p>
                    <p className="font-semibold">{calculation.productName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Лучшая цена найдена</p>
                    <p className="font-semibold">{calculation.bestStore}</p>
                  </div>
                </div>
                
                {calculation.aiConfidence && (
                  <div className="text-sm text-gray-600">
                    Точность анализа ИИ: {Math.round(calculation.aiConfidence * 100)}%
                  </div>
                )}
                
                <div className="border-t pt-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Цена товара:</span>
                      <span>{calculation.originalPrice} ₽</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Комиссия (18%):</span>
                      <span>{calculation.commission} ₽</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Доставка:</span>
                      <span>{calculation.shipping} ₽</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Таможня:</span>
                      <span>{calculation.customs} ₽</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Страховка (5%):</span>
                      <span>{calculation.insurance} ₽</span>
                    </div>
                    <div className="border-t pt-2 flex justify-between font-bold text-lg">
                      <span>Итого к оплате:</span>
                      <span className="text-blue-600">{calculation.totalPrice} ₽</span>
                    </div>
                  </div>
                </div>
                
                <Button 
                  className="mobile-btn w-full bg-green-600 hover:bg-green-700"
                  onClick={proceedToOrder}
                >
                  Оформить заказ
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  );
};