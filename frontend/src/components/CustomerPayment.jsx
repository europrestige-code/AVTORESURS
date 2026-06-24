import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  CreditCard, Smartphone, QrCode, Plus, Trash2, Star, 
  History, CheckCircle, AlertCircle, Clock, Phone
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CustomerPayment = () => {
  const { user } = useAuth();
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [availableMethods, setAvailableMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddMethod, setShowAddMethod] = useState(false);
  const [addMethodData, setAddMethodData] = useState({
    type: 'tbank_qr',
    display_name: '',
    card_holder_name: '',
    phone_number: '',
    bank_name: ''
  });
  const [processingPayment, setProcessingPayment] = useState(false);

  useEffect(() => {
    if (user) {
      loadPaymentData();
    }
  }, [user]);

  const loadPaymentData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const [methodsResponse, historyResponse, availableResponse] = await Promise.all([
        axios.get(`${API}/customer/payment/methods`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/customer/payment/history?limit=10`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/customer/payment/methods/available`)
      ]);

      setPaymentMethods(methodsResponse.data);
      setPaymentHistory(historyResponse.data);
      setAvailableMethods(availableResponse.data.methods);
    } catch (error) {
      console.error('Error loading payment data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMethodIcon = (type) => {
    const iconMap = {
      'tbank_qr': QrCode,
      'sber_qr': QrCode,
      'mir_card': CreditCard,
      'phone_payment': Phone,
      'sbp': Smartphone
    };
    return iconMap[type] || CreditCard;
  };

  const getMethodColor = (type) => {
    const colorMap = {
      'tbank_qr': 'text-blue-600',
      'sber_qr': 'text-green-600',
      'mir_card': 'text-purple-600',
      'phone_payment': 'text-orange-600',
      'sbp': 'text-indigo-600'
    };
    return colorMap[type] || 'text-gray-600';
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      'pending': 'В обработке',
      'completed': 'Завершен',
      'failed': 'Ошибка',
      'cancelled': 'Отменен'
    };
    return texts[status] || status;
  };

  const handleAddMethod = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Auto-generate display name if not provided
      if (!addMethodData.display_name) {
        const methodType = availableMethods.find(m => m.type === addMethodData.type);
        addMethodData.display_name = methodType?.name || 'Новый способ оплаты';
      }
      
      await axios.post(`${API}/customer/payment/methods`, addMethodData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setShowAddMethod(false);
      setAddMethodData({
        type: 'tbank_qr',
        display_name: '',
        card_holder_name: '',
        phone_number: '',
        bank_name: ''
      });
      
      await loadPaymentData();
    } catch (error) {
      console.error('Error adding payment method:', error);
      alert('Ошибка добавления способа оплаты');
    }
  };

  const handleRemoveMethod = async (methodId) => {
    if (!confirm('Удалить этот способ оплаты?')) return;
    
    try {
      const token = localStorage.getItem('access_token');
      
      await axios.delete(`${API}/customer/payment/methods/${methodId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      await loadPaymentData();
    } catch (error) {
      console.error('Error removing payment method:', error);
      alert('Ошибка удаления способа оплаты');
    }
  };

  const handleSetDefault = async (methodId) => {
    try {
      const token = localStorage.getItem('access_token');
      
      await axios.put(`${API}/customer/payment/methods/default`, 
        { method_id: methodId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      await loadPaymentData();
    } catch (error) {
      console.error('Error setting default method:', error);
      alert('Ошибка установки способа оплаты по умолчанию');
    }
  };

  if (loading) {
    return (
      <div className="mobile-container py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загружаем способы оплаты...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-container py-6 space-y-6">
      {/* Payment Methods Section */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-responsive-base">Способы оплаты</CardTitle>
            <Dialog open={showAddMethod} onOpenChange={setShowAddMethod}>
              <DialogTrigger asChild>
                <Button size="sm" className="mobile-btn">
                  <Plus className="h-4 w-4 mr-1" />
                  <span className="hidden sm:inline">Добавить</span>
                  <span className="sm:hidden">+</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="mobile-modal max-w-md">
                <DialogHeader>
                  <DialogTitle className="text-responsive-base">Добавить способ оплаты</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div>
                    <Label htmlFor="method-type">Тип оплаты</Label>
                    <Select value={addMethodData.type} onValueChange={(value) => 
                      setAddMethodData({...addMethodData, type: value})
                    }>
                      <SelectTrigger className="mobile-input">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {availableMethods.map((method) => (
                          <SelectItem key={method.type} value={method.type}>
                            {method.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="display-name">Название</Label>
                    <Input
                      id="display-name"
                      placeholder="Мой способ оплаты"
                      value={addMethodData.display_name}
                      onChange={(e) => setAddMethodData({...addMethodData, display_name: e.target.value})}
                      className="mobile-input"
                    />
                  </div>
                  
                  {(addMethodData.type === 'phone_payment' || addMethodData.type === 'sbp') && (
                    <div>
                      <Label htmlFor="phone">Номер телефона</Label>
                      <Input
                        id="phone"
                        placeholder="+7 999 123 45 67"
                        value={addMethodData.phone_number}
                        onChange={(e) => setAddMethodData({...addMethodData, phone_number: e.target.value})}
                        className="mobile-input"
                      />
                    </div>
                  )}
                  
                  {addMethodData.type === 'mir_card' && (
                    <div>
                      <Label htmlFor="card-holder">Имя держателя карты</Label>
                      <Input
                        id="card-holder"
                        placeholder="IVAN PETROV"
                        value={addMethodData.card_holder_name}
                        onChange={(e) => setAddMethodData({...addMethodData, card_holder_name: e.target.value})}
                        className="mobile-input"
                      />
                    </div>
                  )}
                  
                  {(addMethodData.type === 'tbank_qr' || addMethodData.type === 'sber_qr') && (
                    <div>
                      <Label htmlFor="bank">Банк</Label>
                      <Input
                        id="bank"
                        placeholder="Т-Банк"
                        value={addMethodData.bank_name}
                        onChange={(e) => setAddMethodData({...addMethodData, bank_name: e.target.value})}
                        className="mobile-input"
                      />
                    </div>
                  )}
                  
                  <div className="flex space-x-2 pt-4">
                    <Button onClick={handleAddMethod} className="mobile-btn flex-1">
                      Добавить
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => setShowAddMethod(false)}
                      className="mobile-btn flex-1"
                    >
                      Отмена
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {paymentMethods.length === 0 ? (
            <div className="text-center py-8">
              <CreditCard className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">У вас пока нет сохраненных способов оплаты</p>
              <Button onClick={() => setShowAddMethod(true)} className="mobile-btn">
                <Plus className="h-4 w-4 mr-2" />
                Добавить способ оплаты
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {paymentMethods.map((method) => {
                const IconComponent = getMethodIcon(method.type);
                return (
                  <div key={method.id} className="mobile-card border rounded-lg relative">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <IconComponent className={`h-6 w-6 ${getMethodColor(method.type)}`} />
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium text-gray-900 text-sm sm:text-base">
                              {method.display_name}
                            </h4>
                            {method.is_default && (
                              <Badge className="bg-blue-100 text-blue-800 text-xs">
                                <Star className="h-3 w-3 mr-1" />
                                По умолчанию
                              </Badge>
                            )}
                          </div>
                          {method.card_mask && (
                            <p className="text-xs text-gray-500">**** {method.card_mask}</p>
                          )}
                          {method.phone_number && (
                            <p className="text-xs text-gray-500">{method.phone_number}</p>
                          )}
                          {method.bank_name && (
                            <p className="text-xs text-gray-500">{method.bank_name}</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex space-x-1">
                        {!method.is_default && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleSetDefault(method.id)}
                            className="p-2"
                            title="Установить по умолчанию"
                          >
                            <Star className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleRemoveMethod(method.id)}
                          className="p-2 text-red-600 hover:text-red-700"
                          title="Удалить"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment History Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-responsive-base flex items-center">
            <History className="h-5 w-5 mr-2" />
            История платежей
          </CardTitle>
        </CardHeader>
        <CardContent>
          {paymentHistory.length === 0 ? (
            <div className="text-center py-8">
              <History className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">История платежей пуста</p>
            </div>
          ) : (
            <div className="space-y-3">
              {paymentHistory.map((payment) => (
                <div key={payment.id} className="mobile-card border rounded-lg">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className={getStatusColor(payment.status)}>
                          {getStatusText(payment.status)}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {new Date(payment.created_at).toLocaleDateString('ru-RU')}
                        </span>
                      </div>
                      
                      <div className="text-sm">
                        <p className="font-medium text-gray-900">
                          {payment.amount.toLocaleString('ru-RU')} ₽
                        </p>
                        {payment.description && (
                          <p className="text-gray-600 text-xs mt-1">{payment.description}</p>
                        )}
                        {payment.transaction_id && (
                          <p className="text-gray-500 text-xs mt-1">
                            ID: {payment.transaction_id}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment Information */}
      <Card>
        <CardContent className="mobile-card">
          <div className="text-center">
            <h3 className="text-responsive-base font-semibold text-gray-900 mb-3">
              Безопасность платежей
            </h3>
            <div className="responsive-grid gap-4">
              <div className="text-center">
                <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <h4 className="font-medium text-gray-900 text-sm mb-1">Защищенные переводы</h4>
                <p className="text-gray-600 text-xs">
                  Официальные банковские каналы
                </p>
              </div>
              <div className="text-center">
                <Clock className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <h4 className="font-medium text-gray-900 text-sm mb-1">Мгновенная оплата</h4>
                <p className="text-gray-600 text-xs">
                  СБП и переводы за секунды
                </p>
              </div>
              <div className="text-center">
                <AlertCircle className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                <h4 className="font-medium text-gray-900 text-sm mb-1">24/7 поддержка</h4>
                <p className="text-gray-600 text-xs">
                  Помощь в любое время
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};