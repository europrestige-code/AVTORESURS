import React, { useState } from 'react';
import { Shield, User, Lock, LogIn } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { useToast } from '../hooks/use-toast';
import api from '../services/api';

const AdminLogin = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/api/admin/auth/login', credentials);
      
      // Store admin token
      localStorage.setItem('admin_token', response.data.access_token);
      
      // Update API default headers
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      toast({
        title: "Вход выполнен",
        description: `Добро пожаловать, ${response.data.user.name}!`
      });
      
      onLogin(response.data.user);
      
    } catch (error) {
      toast({
        title: "Ошибка входа",
        description: error.response?.data?.detail || "Неверные данные для входа",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    setCredentials({
      email: 'admin@buyanywhere.com',
      password: 'admin123'
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Shield className="mx-auto h-12 w-12 text-blue-600" />
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Админ панель
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Панель управления BuyAnywhere
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Вход в систему</CardTitle>
            <CardDescription>
              Введите данные администратора для входа
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    value={credentials.email}
                    onChange={(e) => setCredentials({
                      ...credentials,
                      email: e.target.value
                    })}
                    placeholder="admin@buyanywhere.com"
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="password">Пароль</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    type="password"
                    value={credentials.password}
                    onChange={(e) => setCredentials({
                      ...credentials,
                      password: e.target.value
                    })}
                    placeholder="Введите пароль"
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Входим...
                  </>
                ) : (
                  <>
                    <LogIn className="w-4 h-4 mr-2" />
                    Войти
                  </>
                )}
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">или</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                onClick={handleDemoLogin}
                className="w-full"
              >
                Демо вход
              </Button>
            </form>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Демо доступы:</h4>
              <div className="text-sm text-blue-800 space-y-1">
                <p><strong>Admin:</strong> admin@buyanywhere.com</p>
                <p><strong>Demo:</strong> demo@buyanywhere.com</p>
                <p className="text-blue-600">Любой пароль для демо</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminLogin;