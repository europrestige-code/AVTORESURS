import React from 'react';
import { Card, CardContent } from './ui/card';
import { CheckCircle, Shield, Truck, Bell, HeadphonesIcon } from 'lucide-react';
import { mockData } from '../utils/mockData';

export const Guarantees = () => {
  const guarantees = mockData.getGuarantees();
  
  const guaranteeIcons = [Shield, CheckCircle, Truck, Bell, HeadphonesIcon];

  return (
    <section className="py-16 bg-gradient-to-br from-green-50 to-emerald-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full mb-6">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Гарантированный сервис
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Мы несём полную ответственность за каждый заказ. 
            Ваши деньги под защитой на всех этапах покупки.
          </p>
          
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 max-w-3xl mx-auto">
            <p className="text-sm text-orange-800">
              <strong>Политика возвратов:</strong> Возвраты и обмены — по правилам продавца; мы помогаем оформить как услугу. Расходы на возврат несёт клиент, если иное не предусмотрено политикой продавца.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {guarantees.map((guarantee, index) => {
            const IconComponent = guaranteeIcons[index] || CheckCircle;
            return (
              <Card key={index} className="border-green-200 hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 mr-4">
                      <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                        <IconComponent className="h-5 w-5 text-green-600" />
                      </div>
                    </div>
                    <p className="text-gray-700 font-medium">{guarantee}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-lg border border-green-200">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Процесс работы с гарантиями
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold">1</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Оформление</h4>
                <p className="text-gray-600 text-sm">Делаете заказ и оплачиваете</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold">2</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Покупка</h4>
                <p className="text-gray-600 text-sm">Мы покупаем товар за рубежом</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold">3</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Доставка</h4>
                <p className="text-gray-600 text-sm">Отправляем и отслеживаем</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Получение</h4>
                <p className="text-gray-600 text-sm">Вы получаете товар</p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mt-8">
          <div className="inline-flex items-center px-6 py-3 bg-green-600 text-white font-semibold rounded-lg">
            <Shield className="h-5 w-5 mr-2" />
            100% возврат средств при неисполнении
          </div>
        </div>
      </div>
    </section>
  );
};