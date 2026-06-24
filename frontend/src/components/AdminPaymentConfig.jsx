import React, { useState, useEffect } from 'react';
import { 
  Plus, Settings, TestTube, Trash2, Eye, EyeOff, 
  CheckCircle, XCircle, AlertCircle, Save 
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const AdminPaymentConfig = () => {
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [providers, setProviders] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPassword, setShowPassword] = useState({});
  const [testResults, setTestResults] = useState({});
  const { toast } = useToast();

  useEffect(() => {
    loadPaymentMethods();
    loadProviders();
  }, []);

  const loadPaymentMethods = async () => {
    try {
      const response = await api.get('/admin/payment-methods');
      setPaymentMethods(response.data);
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось загрузить платежные методы",
        variant: "destructive"
      });
    }
  };

  const loadProviders = async () => {
    try {
      const response = await api.get('/admin/payment-providers');
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to load providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestMethod = async (method) => {
    try {
      setTestResults({ ...testResults, [method.id]: { testing: true } });
      
      const response = await api.post(`/admin/payment-methods/${method.id}/test`, {
        provider: method.provider,
        amount: 100.0
      });
      
      setTestResults({ 
        ...testResults, 
        [method.id]: { 
          testing: false, 
          result: response.data 
        } 
      });
      
      toast({
        title: response.data.success ? "Тест успешен" : "Тест не пройден",
        description: response.data.message,
        variant: response.data.success ? "default" : "destructive"
      });
      
    } catch (error) {
      setTestResults({ ...testResults, [method.id]: { testing: false, error: true } });
      toast({
        title: "Ошибка теста",
        description: "Не удалось протестировать платежный метод",
        variant: "destructive"
      });
    }
  };

  const handleDeleteMethod = async (methodId) => {
    if (!confirm('Вы уверены, что хотите удалить этот платежный метод?')) {
      return;
    }

    try {
      await api.delete(`/admin/payment-methods/${methodId}`);
      setPaymentMethods(paymentMethods.filter(m => m.id !== methodId));
      
      toast({
        title: "Успешно",
        description: "Платежный метод удален"
      });
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось удалить платежный метод",
        variant: "destructive"
      });
    }
  };

  const togglePasswordVisibility = (fieldKey) => {
    setShowPassword({
      ...showPassword,
      [fieldKey]: !showPassword[fieldKey]
    });
  };

  const getStatusBadge = (status) => {
    const variants = {
      active: { variant: "default", icon: CheckCircle, text: "Активен" },
      inactive: { variant: "secondary", icon: XCircle, text: "Неактивен" },
      testing: { variant: "outline", icon: AlertCircle, text: "Тестируется" }
    };
    
    const config = variants[status] || variants.inactive;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.text}
      </Badge>
    );
  };

  const PaymentMethodCard = ({ method }) => {
    const testResult = testResults[method.id];
    const providerInfo = providers[method.provider];
    
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">{method.name}</CardTitle>
              <CardDescription>{providerInfo?.description}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge(method.status)}
              {method.test_mode && (
                <Badge variant="outline" className="text-orange-600">
                  Тест
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              Создан: {new Date(method.created_at).toLocaleDateString('ru-RU')}
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTestMethod(method)}
                disabled={testResult?.testing}
                className="flex items-center gap-1"
              >
                <TestTube className="w-4 h-4" />
                {testResult?.testing ? 'Тестируем...' : 'Тест'}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedMethod(method)}
                className="flex items-center gap-1"
              >
                <Settings className="w-4 h-4" />
                Настроить
              </Button>
              
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleDeleteMethod(method.id)}
                className="flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Удалить
              </Button>
            </div>
          </div>
          
          {testResult?.result && (
            <div className={`mt-3 p-3 rounded border ${
              testResult.result.success 
                ? 'bg-green-50 border-green-200 text-green-800' 
                : 'bg-red-50 border-red-200 text-red-800'
            }`}>
              <div className="flex items-center gap-2">
                {testResult.result.success ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <XCircle className="w-4 h-4" />
                )}
                <span className="font-medium">{testResult.result.message}</span>
              </div>
              {testResult.result.response_time_ms && (
                <div className="text-sm mt-1">
                  Время отклика: {testResult.result.response_time_ms.toFixed(0)}мс
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загружаем конфигурацию платежей...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Настройка платежей</h1>
          <p className="text-gray-600 mt-2">
            Управление платежными системами и API ключами
          </p>
        </div>
        
        <Button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Добавить метод оплаты
        </Button>
      </div>

      {paymentMethods.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Нет настроенных платежных методов
            </h3>
            <p className="text-gray-600 mb-4">
              Добавьте первый платежный метод для начала приема платежей
            </p>
            <Button onClick={() => setShowCreateForm(true)}>
              Добавить платежный метод
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {paymentMethods.map(method => (
            <PaymentMethodCard key={method.id} method={method} />
          ))}
        </div>
      )}

      {(showCreateForm || selectedMethod) && (
        <PaymentMethodForm
          method={selectedMethod}
          providers={providers}
          onClose={() => {
            setShowCreateForm(false);
            setSelectedMethod(null);
          }}
          onSave={(method) => {
            if (selectedMethod) {
              setPaymentMethods(paymentMethods.map(m => 
                m.id === method.id ? method : m
              ));
            } else {
              setPaymentMethods([...paymentMethods, method]);
            }
            setShowCreateForm(false);
            setSelectedMethod(null);
          }}
        />
      )}
    </div>
  );
};

const PaymentMethodForm = ({ method, providers, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    provider: method?.provider || '',
    name: method?.name || '',
    status: method?.status || 'inactive',
    configuration: method?.configuration || {}
  });
  const [saving, setSaving] = useState(false);
  const [showPassword, setShowPassword] = useState({});
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      let response;
      if (method) {
        response = await api.put(`/admin/payment-methods/${method.id}`, formData);
      } else {
        response = await api.post('/admin/payment-methods', formData);
      }

      toast({
        title: "Успешно",
        description: method ? "Конфигурация обновлена" : "Платежный метод создан"
      });

      onSave(response.data);
    } catch (error) {
      toast({
        title: "Ошибка",
        description: error.response?.data?.detail || "Не удалось сохранить конфигурацию",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const selectedProvider = providers[formData.provider];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">
            {method ? 'Редактировать платежный метод' : 'Новый платежный метод'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Provider Selection */}
            <div>
              <Label htmlFor="provider">Платежная система</Label>
              <Select
                value={formData.provider}
                onValueChange={(value) => {
                  setFormData({
                    ...formData,
                    provider: value,
                    configuration: {}
                  });
                }}
                disabled={!!method}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите платежную систему" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(providers).map(([key, provider]) => (
                    <SelectItem key={key} value={key}>
                      {provider.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Method Name */}
            <div>
              <Label htmlFor="name">Название метода</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Например: UnitPay Основной"
                required
              />
            </div>

            {/* Status */}
            <div>
              <Label htmlFor="status">Статус</Label>
              <Select
                value={formData.status}
                onValueChange={(value) => setFormData({ ...formData, status: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Активен</SelectItem>
                  <SelectItem value="inactive">Неактивен</SelectItem>
                  <SelectItem value="testing">Тестируется</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Provider Configuration */}
            {selectedProvider && (
              <div className="border rounded-lg p-4 bg-gray-50">
                <h3 className="font-medium mb-3">Конфигурация {selectedProvider.name}</h3>
                <div className="grid gap-4">
                  {selectedProvider.fields.map((field) => (
                    <div key={field.name}>
                      <Label htmlFor={field.name}>{field.label}</Label>
                      {field.type === 'boolean' ? (
                        <div className="flex items-center space-x-2 mt-1">
                          <Switch
                            checked={formData.configuration[field.name] ?? field.default}
                            onCheckedChange={(checked) => 
                              setFormData({
                                ...formData,
                                configuration: {
                                  ...formData.configuration,
                                  [field.name]: checked
                                }
                              })
                            }
                          />
                          <span className="text-sm text-gray-600">
                            {formData.configuration[field.name] ? 'Включено' : 'Отключено'}
                          </span>
                        </div>
                      ) : field.type === 'password' ? (
                        <div className="relative">
                          <Input
                            id={field.name}
                            type={showPassword[field.name] ? 'text' : 'password'}
                            value={formData.configuration[field.name] || ''}
                            onChange={(e) => 
                              setFormData({
                                ...formData,
                                configuration: {
                                  ...formData.configuration,
                                  [field.name]: e.target.value
                                }
                              })
                            }
                            required={field.required}
                            placeholder={`Введите ${field.label.toLowerCase()}`}
                            className="pr-10"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="absolute right-0 top-0 h-full px-3"
                            onClick={() => setShowPassword({
                              ...showPassword,
                              [field.name]: !showPassword[field.name]
                            })}
                          >
                            {showPassword[field.name] ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      ) : (
                        <Input
                          id={field.name}
                          type={field.type}
                          value={formData.configuration[field.name] || field.default || ''}
                          onChange={(e) => 
                            setFormData({
                              ...formData,
                              configuration: {
                                ...formData.configuration,
                                [field.name]: field.type === 'number' 
                                  ? parseFloat(e.target.value) || 0
                                  : e.target.value
                              }
                            })
                          }
                          required={field.required}
                          min={field.min}
                          max={field.max}
                          step={field.type === 'number' ? '0.01' : undefined}
                          placeholder={`Введите ${field.label.toLowerCase()}`}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit" disabled={saving || !formData.provider || !formData.name}>
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Сохраняем...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  {method ? 'Обновить' : 'Создать'}
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AdminPaymentConfig;