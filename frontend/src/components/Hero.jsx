import React from 'react';
import { Button } from './ui/button';
import { Shield, Truck, CreditCard, Zap } from 'lucide-react';

export const Hero = () => {
  return (
    <section className="bg-gradient-to-br from-slate-50 to-blue-50 mobile-spacing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-responsive-xl font-bold text-gray-900 mb-6">
            Покупаем для вас
            <span className="text-blue-600 block">всё и везде</span>
          </h1>
          <p className="text-responsive-base text-gray-600 mb-8 max-w-3xl mx-auto mobile-container">
            Персональный сервис покупок из любых зарубежных интернет-магазинов. 
            Подписки, курсы, товары брендов, билеты — оплачивайте в рублях, получайте гарантии.
          </p>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-8 sm:mb-12 max-w-4xl mx-auto mobile-container">
            <div className="mobile-card flex flex-col items-center bg-white rounded-lg shadow-sm">
              <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-green-600 mb-2" />
              <span className="text-xs sm:text-sm font-medium text-gray-700 text-center">100% Гарантия</span>
            </div>
            <div className="mobile-card flex flex-col items-center bg-white rounded-lg shadow-sm">
              <CreditCard className="h-6 w-6 sm:h-8 sm:w-8 text-blue-600 mb-2" />
              <span className="text-xs sm:text-sm font-medium text-gray-700 text-center">Оплата в рублях</span>
            </div>
            <div className="mobile-card flex flex-col items-center bg-white rounded-lg shadow-sm">
              <Truck className="h-6 w-6 sm:h-8 sm:w-8 text-purple-600 mb-2" />
              <span className="text-xs sm:text-sm font-medium text-gray-700 text-center">Быстрая доставка</span>
            </div>
            <div className="mobile-card flex flex-col items-center bg-white rounded-lg shadow-sm">
              <Zap className="h-6 w-6 sm:h-8 sm:w-8 text-orange-600 mb-2" />
              <span className="text-xs sm:text-sm font-medium text-gray-700 text-center">ИИ поиск цен</span>
            </div>
          </div>
          
          <Button size="lg" className="mobile-btn bg-blue-600 hover:bg-blue-700 text-white w-full sm:w-auto">
            Рассчитать стоимость
          </Button>
        </div>
      </div>
    </section>
  );
};