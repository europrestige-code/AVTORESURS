import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CreditCard, Clock, Shield, Zap } from 'lucide-react';
import { mockData } from '../utils/mockData';

export const PaymentMethods = () => {
  const paymentMethods = mockData.getPaymentMethods();

  return (
    <section className="py-16 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Способы оплаты
          </h2>
          <p className="text-lg text-gray-600">
            Оплачивайте удобным способом в российских рублях
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {paymentMethods.map((method, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader className="text-center">
                <CreditCard className="h-12 w-12 text-blue-600 mx-auto mb-3" />
                <CardTitle className="text-lg">{method.name}</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-gray-600 text-sm mb-3">{method.description}</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Комиссия:</span>
                    <span className="font-semibold text-green-600">{method.fee}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Время:</span>
                    <span className="font-semibold">{method.time}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Безопасность платежей
            </h3>
            <p className="text-gray-600">
              Все платежи защищены российскими банковскими стандартами
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <Shield className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h4 className="font-semibold text-gray-900 mb-2">Защищённые переводы</h4>
              <p className="text-gray-600 text-sm">
                Используем только официальные банковские каналы
              </p>
            </div>
            <div className="text-center">
              <Zap className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h4 className="font-semibold text-gray-900 mb-2">Мгновенная оплата</h4>
              <p className="text-gray-600 text-sm">
                СБП и переводы между картами за секунды
              </p>
            </div>
            <div className="text-center">
              <Clock className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h4 className="font-semibold text-gray-900 mb-2">24/7 поддержка</h4>
              <p className="text-gray-600 text-sm">
                Помогаем с оплатой в любое время
              </p>
            </div>
          </div>
        </div>


      </div>
    </section>
  );
};