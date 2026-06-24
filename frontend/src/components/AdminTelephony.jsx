import React, { useState, useEffect } from 'react';
import { Phone, Settings, Globe, Users, BarChart3, Plus, TestTube, Check, X, AlertCircle } from 'lucide-react';

const AdminTelephony = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [providers, setProviders] = useState([]);
  const [virtualNumbers, setVirtualNumbers] = useState([]);
  const [calls, setCalls] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Provider configuration state
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [providerTemplates, setProviderTemplates] = useState({});
  const [selectedProviderType, setSelectedProviderType] = useState('');
  const [providerConfig, setProviderConfig] = useState({
    name: '',
    api_credentials: {},
    webhook_url: '',
    enabled: true,
    priority: 1
  });

  // Number purchase state
  const [showNumberModal, setShowNumberModal] = useState(false);
  const [availableNumbers, setAvailableNumbers] = useState([]);
  const [selectedCity, setSelectedCity] = useState('moscow');
  const [selectedNumber, setSelectedNumber] = useState('');
  const [callerName, setCallerName] = useState('BuyAnywhere');

  useEffect(() => {
    loadTelephonyData();
    loadProviderTemplates();
  }, []);

  const loadTelephonyData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('admin_token');
      const headers = { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load dashboard data
      const dashboardResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/dashboard`, { headers });
      if (dashboardResponse.ok) {
        const dashboardData = await dashboardResponse.json();
        setDashboard(dashboardData.data);
      }

      // Load providers
      const providersResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/providers`, { headers });
      if (providersResponse.ok) {
        const providersData = await providersResponse.json();
        setProviders(providersData.data);
      }

      // Load virtual numbers
      const numbersResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/numbers`, { headers });
      if (numbersResponse.ok) {
        const numbersData = await numbersResponse.json();
        setVirtualNumbers(numbersData.data);
      }

      // Load calls
      const callsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/calls?limit=20`, { headers });
      if (callsResponse.ok) {
        const callsData = await callsResponse.json();
        setCalls(callsData.data.calls);
      }

    } catch (error) {
      console.error('Error loading telephony data:', error);
      setError('Ошибка загрузки данных телефонии');
    } finally {
      setLoading(false);
    }
  };

  const loadProviderTemplates = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/providers/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProviderTemplates(data.data);
      }
    } catch (error) {
      console.error('Error loading provider templates:', error);
    }
  };

  const handleCreateProvider = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/providers`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          provider_type: selectedProviderType,
          ...providerConfig
        })
      });

      if (response.ok) {
        const data = await response.json();
        setProviders([...providers, data.data]);
        setShowProviderModal(false);
        resetProviderForm();
        alert('Провайдер успешно создан!');
      } else {
        const error = await response.json();
        alert(`Ошибка: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error creating provider:', error);
      alert('Ошибка при создании провайдера');
    }
  };

  const testProvider = async (providerId) => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/providers/${providerId}/test`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.message);
      } else {
        const error = await response.json();
        alert(`Ошибка тестирования: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error testing provider:', error);
      alert('Ошибка при тестировании провайдера');
    }
  };

  const activateProvider = async (providerId) => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/providers/${providerId}/activate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('Провайдер активирован!');
        loadTelephonyData();
      } else {
        const error = await response.json();
        alert(`Ошибка: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error activating provider:', error);
      alert('Ошибка при активации провайдера');
    }
  };

  const searchNumbers = async (city) => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/numbers/search?city=${city}&limit=20`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableNumbers(data.data);
      }
    } catch (error) {
      console.error('Error searching numbers:', error);
      alert('Ошибка при поиске номеров');
    }
  };

  const purchaseNumber = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/telephony/numbers/purchase`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          number: selectedNumber,
          city: selectedCity,
          caller_name: callerName
        })
      });

      if (response.ok) {
        const data = await response.json();
        setVirtualNumbers([...virtualNumbers, data.data]);
        setShowNumberModal(false);
        alert('Номер успешно приобретён!');
      } else {
        const error = await response.json();
        alert(`Ошибка: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error purchasing number:', error);
      alert('Ошибка при приобретении номера');
    }
  };

  const resetProviderForm = () => {
    setProviderConfig({
      name: '',
      api_credentials: {},
      webhook_url: '',
      enabled: true,
      priority: 1
    });
    setSelectedProviderType('');
  };

  const renderDashboard = () => {
    if (!dashboard) return <div>Загрузка...</div>;

    return (
      <div className="space-y-6">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Активные звонки</p>
                <p className="text-2xl font-bold text-blue-600">{dashboard.active_calls}</p>
              </div>
              <Phone className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Виртуальные номера</p>
                <p className="text-2xl font-bold text-green-600">{dashboard.virtual_numbers}</p>
              </div>
              <Globe className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Активные провайдеры</p>
                <p className="text-2xl font-bold text-purple-600">{dashboard.active_providers}</p>
              </div>
              <Settings className="h-8 w-8 text-purple-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Звонков сегодня</p>
                <p className="text-2xl font-bold text-orange-600">{dashboard.today_stats.total_calls}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-orange-600" />
            </div>
          </div>
        </div>

        {/* Recent Calls */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4">Последние звонки</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">От</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">К</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Время</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Длительность</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dashboard.recent_calls.map((call) => (
                  <tr key={call.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{call.from_number}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{call.to_number}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        call.status === 'completed' ? 'bg-green-100 text-green-800' :
                        call.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {call.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(call.created_at).toLocaleString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {call.duration_seconds ? `${call.duration_seconds}с` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderProviders = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Провайдеры телефонии</h3>
        <button
          onClick={() => setShowProviderModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Добавить провайдера
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {providers.map((provider) => (
          <div key={provider.id} className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="font-semibold text-lg">{provider.name}</h4>
                <p className="text-sm text-gray-600">{provider.provider_type}</p>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                provider.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {provider.enabled ? 'Активен' : 'Отключен'}
              </span>
            </div>

            <div className="space-y-2 mb-4">
              <p className="text-sm text-gray-600">Приоритет: {provider.priority}</p>
              <p className="text-sm text-gray-600">
                Создан: {new Date(provider.created_at).toLocaleDateString('ru-RU')}
              </p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => testProvider(provider.id)}
                className="flex-1 bg-yellow-600 text-white px-3 py-2 rounded hover:bg-yellow-700 flex items-center justify-center gap-1"
              >
                <TestTube className="h-4 w-4" />
                Тест
              </button>
              <button
                onClick={() => activateProvider(provider.id)}
                className="flex-1 bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 flex items-center justify-center gap-1"
              >
                <Check className="h-4 w-4" />
                Активировать
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderNumbers = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Виртуальные номера</h3>
        <button
          onClick={() => setShowNumberModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Приобрести номер
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Номер</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Город</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Провайдер</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Стоимость</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Активирован</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {virtualNumbers.map((number) => (
              <tr key={number.id}>
                <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{number.number}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{number.city}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{number.provider_type}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  ${number.monthly_cost}/мес
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    number.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {number.status === 'active' ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {number.activated_at ? new Date(number.activated_at).toLocaleDateString('ru-RU') : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderProviderModal = () => {
    if (!showProviderModal) return null;

    const selectedTemplate = providerTemplates[selectedProviderType];

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4">Добавить провайдера</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Тип провайдера</label>
              <select
                value={selectedProviderType}
                onChange={(e) => setSelectedProviderType(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="">Выберите провайдера</option>
                {Object.entries(providerTemplates).map(([key, template]) => (
                  <option key={key} value={key}>{template.name}</option>
                ))}
              </select>
              {selectedTemplate && (
                <p className="text-sm text-gray-600 mt-1">{selectedTemplate.description}</p>
              )}
            </div>

            {selectedTemplate && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Название</label>
                  <input
                    type="text"
                    value={providerConfig.name}
                    onChange={(e) => setProviderConfig({...providerConfig, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder={`${selectedTemplate.name} Provider`}
                  />
                </div>

                {selectedTemplate.fields.map((field) => (
                  <div key={field.key}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {field.label}
                      {field.required && <span className="text-red-500">*</span>}
                    </label>
                    <input
                      type={field.type}
                      value={providerConfig.api_credentials[field.key] || ''}
                      onChange={(e) => setProviderConfig({
                        ...providerConfig,
                        api_credentials: {
                          ...providerConfig.api_credentials,
                          [field.key]: e.target.value
                        }
                      })}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      placeholder={field.description}
                    />
                  </div>
                ))}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Webhook URL</label>
                  <input
                    type="text"
                    value={providerConfig.webhook_url}
                    onChange={(e) => setProviderConfig({...providerConfig, webhook_url: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder={`${process.env.REACT_APP_BACKEND_URL}/api/telephony/webhooks/${selectedProviderType}`}
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={providerConfig.enabled}
                    onChange={(e) => setProviderConfig({...providerConfig, enabled: e.target.checked})}
                    className="mr-2"
                  />
                  <label className="text-sm text-gray-700">Включить провайдера</label>
                </div>
              </>
            )}
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleCreateProvider}
              disabled={!selectedProviderType || !providerConfig.name}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
            >
              Создать
            </button>
            <button
              onClick={() => {
                setShowProviderModal(false);
                resetProviderForm();
              }}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderNumberModal = () => {
    if (!showNumberModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
          <h3 className="text-lg font-semibold mb-4">Приобрести виртуальный номер</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Город</label>
              <select
                value={selectedCity}
                onChange={(e) => {
                  setSelectedCity(e.target.value);
                  searchNumbers(e.target.value);
                }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="moscow">Москва</option>
                <option value="krasnoyarsk">Красноярск</option>
                <option value="vladivostok">Владивосток</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Имя абонента</label>
              <input
                type="text"
                value={callerName}
                onChange={(e) => setCallerName(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="BuyAnywhere"
              />
            </div>

            {availableNumbers.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Доступные номера</label>
                <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-lg">
                  {availableNumbers.map((number) => (
                    <label key={number.number} className="flex items-center p-3 hover:bg-gray-50 cursor-pointer">
                      <input
                        type="radio"
                        name="selectedNumber"
                        value={number.number}
                        onChange={(e) => setSelectedNumber(e.target.value)}
                        className="mr-3"
                      />
                      <div className="flex-1">
                        <div className="font-medium">{number.number}</div>
                        <div className="text-sm text-gray-600">${number.monthly_cost}/мес</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => searchNumbers(selectedCity)}
              className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              Найти доступные номера
            </button>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={purchaseNumber}
              disabled={!selectedNumber}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
            >
              Приобрести
            </button>
            <button
              onClick={() => setShowNumberModal(false)}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    );
  };

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
            onClick={loadTelephonyData}
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
        <h2 className="text-2xl font-bold text-gray-800 mb-2">AI IP Телефония</h2>
        <p className="text-gray-600">Управление системой телефонии с ИИ поддержкой</p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { key: 'dashboard', label: 'Панель управления', icon: BarChart3 },
          { key: 'providers', label: 'Провайдеры', icon: Settings },
          { key: 'numbers', label: 'Номера', icon: Phone },
          { key: 'calls', label: 'Звонки', icon: Users }
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
      {activeTab === 'providers' && renderProviders()}
      {activeTab === 'numbers' && renderNumbers()}
      {activeTab === 'calls' && renderNumbers()} {/* Will add calls view later */}

      {/* Modals */}
      {renderProviderModal()}
      {renderNumberModal()}
    </div>
  );
};

export default AdminTelephony;