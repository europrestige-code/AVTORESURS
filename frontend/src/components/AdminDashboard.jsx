import React, { useState, useEffect } from 'react';
import { 
  CreditCard, Users, ShoppingCart, TrendingUp, 
  Settings, Shield, Activity, AlertCircle,
  DollarSign, Package, Clock, CheckCircle, Phone, UserCheck, Search, Image
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import AdminPaymentConfig from './AdminPaymentConfig';
import AdminTelephony from './AdminTelephony';
import AdminCRM from './AdminCRM';
import { SEODashboard } from './SEO/SEODashboard';
import { LogoUpload } from './LogoUpload';
import { CRMBulkUpload } from './CRMBulkUpload';
import api from '../services/api';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalRevenue: 0,
    activeUsers: 0,
    paymentMethods: 0,
    todayOrders: 0,
    pendingOrders: 0
  });
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // In a real implementation, these would be separate API calls
      // For now, we'll use mock data
      setStats({
        totalOrders: 1247,
        totalRevenue: 2840000,
        activeUsers: 89,
        paymentMethods: 3,
        todayOrders: 12,
        pendingOrders: 5
      });

      setRecentOrders([
        {
          id: 'ORD-20250913-001',
          customer: 'Иван Петров',
          amount: 15000,
          status: 'pending',
          created: '2025-09-13T10:30:00Z',
          product: 'iPhone 15 Pro'
        },
        {
          id: 'ORD-20250913-002', 
          customer: 'Мария Смирнова',
          amount: 85000,
          status: 'completed',
          created: '2025-09-13T09:15:00Z',
          product: 'MacBook Pro M3'
        },
        {
          id: 'ORD-20250913-003',
          customer: 'Алексей Волков',
          amount: 25000,
          status: 'processing',
          created: '2025-09-13T08:45:00Z',
          product: 'Samsung Galaxy S24'
        }
      ]);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const getStatusBadge = (status) => {
    const variants = {
      pending: { variant: "outline", text: "Ожидает", icon: Clock },
      processing: { variant: "default", text: "Обрабатывается", icon: Activity },
      completed: { variant: "secondary", text: "Завершен", icon: CheckCircle },
      cancelled: { variant: "destructive", text: "Отменен", icon: AlertCircle }
    };
    
    const config = variants[status] || variants.pending;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {config.text}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загружаем панель управления...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Панель администратора</h1>
          <p className="text-gray-600 mt-2">Управление BuyAnywhere</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="mobile-admin-tabs overflow-x-auto">
            <TabsTrigger value="overview" className="mobile-admin-tab">
              <TrendingUp className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Обзор</span>
              <span className="sm:hidden text-xs">Обзор</span>
            </TabsTrigger>
            <TabsTrigger value="payments" className="mobile-admin-tab">
              <CreditCard className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Платежи</span>
              <span className="sm:hidden text-xs">Платежи</span>
            </TabsTrigger>
            <TabsTrigger value="telephony" className="mobile-admin-tab">
              <Phone className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Телефония</span>
              <span className="sm:hidden text-xs">Тел.</span>
            </TabsTrigger>
            <TabsTrigger value="crm" className="mobile-admin-tab">
              <UserCheck className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">CRM</span>
              <span className="sm:hidden text-xs">CRM</span>
            </TabsTrigger>
            <TabsTrigger value="seo" className="mobile-admin-tab">
              <Search className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">SEO</span>
              <span className="sm:hidden text-xs">SEO</span>
            </TabsTrigger>
            <TabsTrigger value="logo" className="mobile-admin-tab">
              <Image className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Логотип</span>
              <span className="sm:hidden text-xs">Лого</span>
            </TabsTrigger>
            <TabsTrigger value="orders" className="mobile-admin-tab">
              <Package className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Заказы</span>
              <span className="sm:hidden text-xs">Заказы</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="mobile-admin-tab">
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Настройки</span>
              <span className="sm:hidden text-xs">Настр.</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Всего заказов</CardTitle>
                  <Package className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.totalOrders}</div>
                  <p className="text-xs text-muted-foreground">
                    +12% от прошлого месяца
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Общий доход</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrency(stats.totalRevenue)}</div>
                  <p className="text-xs text-muted-foreground">
                    +8% от прошлого месяца
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Активные пользователи</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.activeUsers}</div>
                  <p className="text-xs text-muted-foreground">
                    +5 новых за неделю
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Заказы сегодня</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.todayOrders}</div>
                  <p className="text-xs text-muted-foreground">
                    {stats.pendingOrders} ожидают обработки
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Orders */}
            <Card>
              <CardHeader>
                <CardTitle>Последние заказы</CardTitle>
                <CardDescription>
                  Недавние заказы и их статусы
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentOrders.map((order) => (
                    <div key={order.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div>
                            <p className="font-medium">{order.id}</p>
                            <p className="text-sm text-gray-600">{order.customer}</p>
                          </div>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">{order.product}</p>
                      </div>
                      
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(order.amount)}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(order.created).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                      
                      <div className="ml-4">
                        {getStatusBadge(order.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="payments">
            <AdminPaymentConfig />
          </TabsContent>

          <TabsContent value="telephony" className="space-y-6">
            <AdminTelephony />
          </TabsContent>

          <TabsContent value="crm" className="space-y-6">
            <AdminCRM />
          </TabsContent>

          <TabsContent value="seo" className="space-y-6">
            <SEODashboard />
          </TabsContent>

          <TabsContent value="logo" className="space-y-6">
            <LogoUpload />
          </TabsContent>

          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Управление заказами</CardTitle>
                <CardDescription>
                  Просмотр и управление всеми заказами
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <ShoppingCart className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Управление заказами
                  </h3>
                  <p className="text-gray-600">
                    Функционал управления заказами будет добавлен в следующей версии
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Настройки системы</CardTitle>
                <CardDescription>
                  Общие настройки приложения
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Настройки системы
                  </h3>
                  <p className="text-gray-600">
                    Дополнительные настройки будут добавлены в следующей версии
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdminDashboard;