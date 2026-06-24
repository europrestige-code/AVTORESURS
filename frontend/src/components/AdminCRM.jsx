import React, { useState, useEffect } from 'react';
import { 
  Users, MessageCircle, Ticket, TrendingUp, Star, Mail, 
  Phone, Calendar, Filter, Plus, Search, Edit, Eye,
  BarChart3, PieChart, Activity, Clock, CheckCircle,
  AlertCircle, Zap, Target, Send, Upload
} from 'lucide-react';
import { CRMBulkUpload } from './CRMBulkUpload';

const AdminCRM = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // CRM Data State
  const [dashboard, setDashboard] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [communications, setCommunications] = useState([]);
  const [automationRules, setAutomationRules] = useState([]);

  // Filter State
  const [customerFilter, setCustomerFilter] = useState({
    status: '',
    segment: '',
    search: ''
  });
  const [ticketFilter, setTicketFilter] = useState({
    status: '',
    category: '',
    priority: ''
  });

  // Modal State
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [showCommunicationModal, setShowCommunicationModal] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedTicket, setSelectedTicket] = useState(null);

  useEffect(() => {
    loadCRMData();
  }, []);

  const loadCRMData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('adminToken');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load dashboard data
      const dashboardResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/dashboard`, { headers });
      if (dashboardResponse.ok) {
        const dashboardData = await dashboardResponse.json();
        setDashboard(dashboardData.data);
      }

      // Load customers
      const customersResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/customers?limit=50`, { headers });
      if (customersResponse.ok) {
        const customersData = await customersResponse.json();
        setCustomers(customersData.data);
      }

      // Load tickets
      const ticketsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/tickets?limit=50`, { headers });
      if (ticketsResponse.ok) {
        const ticketsData = await ticketsResponse.json();
        setTickets(ticketsData.data);
      }

    } catch (error) {
      console.error('Error loading CRM data:', error);
      setError('Ошибка загрузки данных CRM');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB'
    }).format(amount);
  };

  const getStatusBadge = (status, type = 'customer') => {
    const statusConfig = {
      customer: {
        active: { color: 'bg-green-100 text-green-800', text: 'Активный' },
        inactive: { color: 'bg-gray-100 text-gray-800', text: 'Неактивный' },
        vip: { color: 'bg-purple-100 text-purple-800', text: 'VIP' },
        lead: { color: 'bg-blue-100 text-blue-800', text: 'Лид' },
        blocked: { color: 'bg-red-100 text-red-800', text: 'Заблокирован' }
      },
      ticket: {
        open: { color: 'bg-yellow-100 text-yellow-800', text: 'Открыта' },
        in_progress: { color: 'bg-blue-100 text-blue-800', text: 'В работе' },
        resolved: { color: 'bg-green-100 text-green-800', text: 'Решена' },
        closed: { color: 'bg-gray-100 text-gray-800', text: 'Закрыта' },
        escalated: { color: 'bg-red-100 text-red-800', text: 'Эскалирована' }
      }
    };

    const config = statusConfig[type][status] || { color: 'bg-gray-100 text-gray-800', text: status };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.text}
      </span>
    );
  };

  const getPriorityIcon = (priority) => {
    const icons = {
      low: <TrendingUp className="h-4 w-4 text-green-500" />,
      medium: <TrendingUp className="h-4 w-4 text-yellow-500" />,
      high: <TrendingUp className="h-4 w-4 text-orange-500" />,
      urgent: <AlertCircle className="h-4 w-4 text-red-500" />
    };
    return icons[priority] || icons.medium;
  };

  const renderDashboard = () => {
    if (!dashboard) return <div>Загрузка...</div>;

    return (
      <div className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Всего клиентов</p>
                <p className="text-2xl font-bold text-blue-600">{dashboard.total_customers}</p>
                <p className="text-xs text-green-600">+{dashboard.new_customers_this_month} в этом месяце</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Активные заявки</p>
                <p className="text-2xl font-bold text-orange-600">{dashboard.open_tickets}</p>
                <p className="text-xs text-gray-600">{dashboard.tickets_this_week} на этой неделе</p>
              </div>
              <Ticket className="h-8 w-8 text-orange-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">VIP клиенты</p>
                <p className="text-2xl font-bold text-purple-600">{dashboard.vip_customers}</p>
                <p className="text-xs text-gray-600">Премиум сегмент</p>
              </div>
              <Star className="h-8 w-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Выручка</p>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(dashboard.revenue_this_month)}</p>
                <p className="text-xs text-gray-600">В этом месяце</p>
              </div>
              <BarChart3 className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>

        {/* Customer Status Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Статусы клиентов</h3>
            <div className="space-y-3">
              {Object.entries(dashboard.customers_by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center">
                    {getStatusBadge(status)}
                    <span className="ml-2 text-sm text-gray-600">{status}</span>
                  </div>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Коммуникации</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Mail className="h-5 w-5 text-blue-600 mr-2" />
                  <span className="text-sm text-gray-600">Email за неделю</span>
                </div>
                <span className="font-medium">{dashboard.emails_sent_this_week}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <MessageCircle className="h-5 w-5 text-green-600 mr-2" />
                  <span className="text-sm text-gray-600">SMS за неделю</span>
                </div>
                <span className="font-medium">{dashboard.sms_sent_this_week}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Zap className="h-5 w-5 text-purple-600 mr-2" />
                  <span className="text-sm text-gray-600">Активные автоматизации</span>
                </div>
                <span className="font-medium">{dashboard.active_automation_rules}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Новые клиенты</h3>
            <div className="space-y-3">
              {dashboard.recent_customers.slice(0, 5).map((customer) => (
                <div key={customer.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium">{customer.full_name}</p>
                    <p className="text-sm text-gray-600">{customer.email}</p>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(customer.status)}
                    <p className="text-xs text-gray-500 mt-1">{formatDate(customer.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Последние заявки</h3>
            <div className="space-y-3">
              {dashboard.recent_tickets.slice(0, 5).map((ticket) => (
                <div key={ticket.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex-1">
                    <div className="flex items-center">
                      {getPriorityIcon(ticket.priority)}
                      <p className="font-medium ml-2">{ticket.ticket_number}</p>
                    </div>
                    <p className="text-sm text-gray-600 truncate">{ticket.subject}</p>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(ticket.status, 'ticket')}
                    <p className="text-xs text-gray-500 mt-1">{formatDate(ticket.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderCustomers = () => (
    <div className="space-y-6">
      {/* Filters and Actions */}
      <div className="bg-white p-4 rounded-lg shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск клиентов..."
                value={customerFilter.search}
                onChange={(e) => setCustomerFilter({...customerFilter, search: e.target.value})}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select
              value={customerFilter.status}
              onChange={(e) => setCustomerFilter({...customerFilter, status: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все статусы</option>
              <option value="active">Активные</option>
              <option value="inactive">Неактивные</option>
              <option value="vip">VIP</option>
              <option value="lead">Лиды</option>
            </select>
            <select
              value={customerFilter.segment}
              onChange={(e) => setCustomerFilter({...customerFilter, segment: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все сегменты</option>
              <option value="high_value">Дорогие клиенты</option>
              <option value="frequent_buyer">Частые покупатели</option>
              <option value="new_customer">Новые клиенты</option>
              <option value="premium_buyer">Премиум покупатели</option>
            </select>
          </div>
          <button
            onClick={() => setShowCustomerModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Добавить клиента
          </button>
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Клиент</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Заказы</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Потрачено</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Последний заказ</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {customers.map((customer) => (
              <tr key={customer.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-medium">
                        {customer.full_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{customer.full_name}</div>
                      <div className="text-sm text-gray-500">{customer.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(customer.status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {customer.total_orders}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatCurrency(customer.total_spent)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(customer.last_order_date)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setSelectedCustomer(customer);
                        setShowCustomerModal(true);
                      }}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => {
                        setSelectedCustomer(customer);
                        setShowCommunicationModal(true);
                      }}
                      className="text-green-600 hover:text-green-900"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderTickets = () => (
    <div className="space-y-6">
      {/* Filters and Actions */}
      <div className="bg-white p-4 rounded-lg shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex flex-col md:flex-row gap-4">
            <select
              value={ticketFilter.status}
              onChange={(e) => setTicketFilter({...ticketFilter, status: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все статусы</option>
              <option value="open">Открытые</option>
              <option value="in_progress">В работе</option>
              <option value="resolved">Решённые</option>
              <option value="closed">Закрытые</option>
            </select>
            <select
              value={ticketFilter.priority}
              onChange={(e) => setTicketFilter({...ticketFilter, priority: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все приоритеты</option>
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
              <option value="urgent">Срочно</option>
            </select>
          </div>
          <button
            onClick={() => setShowTicketModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Создать заявку
          </button>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Заявка</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Клиент</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Категория</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Приоритет</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Создана</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tickets.map((ticket) => (
              <tr key={ticket.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{ticket.ticket_number}</div>
                    <div className="text-sm text-gray-500 truncate max-w-xs">{ticket.subject}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{ticket.customer_name}</div>
                    <div className="text-sm text-gray-500">{ticket.customer_email}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {ticket.category}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getPriorityIcon(ticket.priority)}
                    <span className="ml-2 text-sm text-gray-900 capitalize">{ticket.priority}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(ticket.status, 'ticket')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(ticket.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => {
                      setSelectedTicket(ticket);
                      setShowTicketModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadCRMData}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Повторить
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">CRM Система</h2>
        <p className="text-gray-600">Управление клиентами, заявками и коммуникациями</p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { key: 'dashboard', label: 'Панель управления', icon: BarChart3 },
          { key: 'customers', label: 'Клиенты', icon: Users },
          { key: 'bulk_upload', label: 'Массовая загрузка', icon: Upload },
          { key: 'tickets', label: 'Заявки', icon: Ticket },
          { key: 'communications', label: 'Коммуникации', icon: MessageCircle },
          { key: 'automation', label: 'Автоматизация', icon: Zap }
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === key
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="h-4 w-4 mr-2" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'customers' && renderCustomers()}
      {activeTab === 'bulk_upload' && <CRMBulkUpload />}
      {activeTab === 'tickets' && renderTickets()}
      {activeTab === 'communications' && (
        <div className="text-center py-12">
          <MessageCircle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Коммуникации</h3>
          <p className="text-gray-600">Управление коммуникациями с клиентами</p>
        </div>
      )}
      {activeTab === 'automation' && (
        <div className="text-center py-12">
          <Zap className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Автоматизация</h3>
          <p className="text-gray-600">Правила автоматизации CRM процессов</p>
        </div>
      )}
    </div>
  );
};

export default AdminCRM;