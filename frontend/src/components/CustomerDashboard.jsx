import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Badge } from './ui/badge';  
import { Input } from './ui/input';
import { Label } from './ui/label';
import { 
  Package, Clock, CheckCircle, CreditCard, User, Phone, Mail,
  MapPin, Calendar, TrendingUp, ShoppingBag, Eye, Edit
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { CustomerPayment } from './CustomerPayment';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CustomerDashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({});

  const handleLogout = async () => {
    await logout();
  };

  useEffect(() => {
    if (user) {
      loadDashboardData();
      setProfileData({
        first_name: user.customer_info?.first_name || '',
        last_name: user.customer_info?.last_name || '',
        phone: user.phone || '',
        address: user.customer_info?.address || '',
        city: user.customer_info?.city || ''
      });
    }
  }, [user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const [dashboardResponse, ordersResponse] = await Promise.all([
        axios.get(`${API}/customer/dashboard`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/customer/orders`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setStats(dashboardResponse.data.statistics);
      setOrders(ordersResponse.data.orders);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Set default empty data
      setStats({
        total_orders: 0,
        total_spent: 0,
        avg_order_value: 0
      });
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'paid': 'bg-blue-100 text-blue-800',
      'processing': 'bg-purple-100 text-purple-800',
      'shipping': 'bg-orange-100 text-orange-800',
      'delivered': 'bg-green-100 text-green-800',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status) => {
    const texts = {
      'pending': 'Ожидает оплаты',
      'paid': 'Оплачен',
      'processing': 'В обработке',
      'purchasing': 'Покупаем товар',
      'shipping': 'Доставляется',
      'delivered': 'Доставлен',
      'cancelled': 'Отменён'
    };
    return texts[status] || status;
  };

  const updateProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      await axios.put(`${API}/customer/profile`, profileData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setEditingProfile(false);
      alert('Профиль успешно обновлён!');
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Ошибка обновления профиля');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загружаем ваши данные...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <User className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Личный кабинет</h1>
                <p className="text-sm text-gray-500">
                  {user.customer_info?.first_name} {user.customer_info?.last_name}
                </p>
              </div>
            </div>
            <Button onClick={handleLogout} variant="outline">
              Выход
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="mobile-tabs grid w-full grid-cols-4">
            <TabsTrigger value="dashboard" className="mobile-btn text-xs sm:text-sm">Обзор</TabsTrigger>
            <TabsTrigger value="orders" className="mobile-btn text-xs sm:text-sm">Заказы</TabsTrigger>
            <TabsTrigger value="payment" className="mobile-btn text-xs sm:text-sm">Оплата</TabsTrigger>
            <TabsTrigger value="profile" className="mobile-btn text-xs sm:text-sm">Профиль</TabsTrigger>
          </TabsList>

          {/* Dashboard Overview */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="mobile-dashboard-grid">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <ShoppingBag className="h-8 w-8 text-blue-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Всего заказов</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_orders || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <CreditCard className="h-8 w-8 text-green-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Потрачено</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(stats.total_spent || 0).toLocaleString('ru-RU')} ₽
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <TrendingUp className="h-8 w-8 text-purple-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Средний заказ</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(stats.avg_order_value || 0).toLocaleString('ru-RU')} ₽
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center">
                    <Calendar className="h-8 w-8 text-orange-600" />
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Клиент с</p>
                      <p className="text-lg font-bold text-gray-900">
                        {new Date(user.created_at).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Orders */}
            <Card>
              <CardHeader>
                <CardTitle>Последние заказы</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {orders.slice(0, 5).map((order) => (
                    <div key={order.order_id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <Package className="h-8 w-8 text-gray-400" />
                        <div>
                          <p className="font-medium text-gray-900">{order.product_name}</p>
                          <p className="text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={getStatusColor(order.status)}>
                          {getStatusText(order.status)}
                        </Badge>
                        <p className="text-sm font-medium text-gray-900 mt-1">
                          {order.amount.toLocaleString('ru-RU')} ₽
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                {orders.length > 5 && (
                  <div className="mt-4 text-center">
                    <Button 
                      variant="outline" 
                      onClick={() => setActiveTab('orders')}
                    >
                      Показать все заказы
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Все заказы</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {orders.map((order) => (
                    <div key={order.order_id} className="border rounded-lg p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {order.product_name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Заказ #{order.order_id}
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(order.created_at).toLocaleDateString('ru-RU', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric'
                            })}
                          </p>
                        </div>
                        <div className="text-right">
                          <Badge className={getStatusColor(order.status)}>
                            {getStatusText(order.status)}
                          </Badge>
                          <p className="text-xl font-bold text-gray-900 mt-2">
                            {order.amount.toLocaleString('ru-RU')} ₽
                          </p>
                        </div>
                      </div>

                      {order.store_name && (
                        <div className="mb-4">
                          <p className="text-sm text-gray-600">
                            <strong>Магазин:</strong> {order.store_name}
                          </p>
                        </div>
                      )}

                      {order.tracking_number && (
                        <div className="mb-4">
                          <p className="text-sm text-gray-600">
                            <strong>Трек-номер:</strong> {order.tracking_number}
                          </p>
                        </div>
                      )}

                      <div className="flex justify-between items-center">
                        <div className="flex space-x-2">
                          <Button size="sm" variant="outline">
                            <Eye className="h-4 w-4 mr-2" />
                            Подробности
                          </Button>
                        </div>
                        
                        {order.payment_status === 'pending' && (
                          <Button size="sm">
                            Оплатить
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Payment Tab */}
          <TabsContent value="payment">
            <CustomerPayment />
          </TabsContent>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Личные данные
                  <Button
                    variant={editingProfile ? "default" : "outline"}
                    size="sm"
                    onClick={() => editingProfile ? updateProfile() : setEditingProfile(true)}
                  >
                    {editingProfile ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Сохранить
                      </>
                    ) : (
                      <>
                        <Edit className="h-4 w-4 mr-2" />
                        Редактировать
                      </>
                    )}
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mobile-profile-grid">
                  <div>
                    <Label htmlFor="first_name">Имя</Label>
                    <Input
                      id="first_name"
                      value={profileData.first_name}
                      onChange={(e) => setProfileData({...profileData, first_name: e.target.value})}
                      disabled={!editingProfile}
                      className="mobile-input"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="last_name">Фамилия</Label>
                    <Input
                      id="last_name"
                      value={profileData.last_name}
                      onChange={(e) => setProfileData({...profileData, last_name: e.target.value})}
                      disabled={!editingProfile}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="phone">Телефон</Label>
                    <Input
                      id="phone"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                      disabled={!editingProfile}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      value={user.email}
                      disabled={true}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="city">Город</Label>
                    <Input
                      id="city"
                      value={profileData.city}
                      onChange={(e) => setProfileData({...profileData, city: e.target.value})}
                      disabled={!editingProfile}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="address">Адрес</Label>
                    <Input
                      id="address"
                      value={profileData.address}
                      onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                      disabled={!editingProfile}
                    />
                  </div>
                </div>

                {editingProfile && (
                  <div className="mt-6 flex space-x-4">
                    <Button onClick={updateProfile}>
                      Сохранить изменения
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => setEditingProfile(false)}
                    >
                      Отмена
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Support Information */}
            <Card>
              <CardHeader>
                <CardTitle>Поддержка клиентов</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <Phone className="h-5 w-5 text-blue-600 mr-3" />
                    <div>
                      <p className="font-medium">ИИ поддержка (24/7)</p>
                      <p className="text-sm text-gray-600">+7 (495) 123-45-67</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <Mail className="h-5 w-5 text-blue-600 mr-3" />
                    <div>
                      <p className="font-medium">Email поддержка</p>
                      <p className="text-sm text-gray-600">support@buyanywhere.ru</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    <Clock className="h-5 w-5 text-blue-600 mr-3" />
                    <div>
                      <p className="font-medium">Рабочие часы</p>
                      <p className="text-sm text-gray-600">24/7 автоматическая поддержка</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};