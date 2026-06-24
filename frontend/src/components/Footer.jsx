import React from 'react';
import { Button } from './ui/button';
import { Phone, Mail, Clock, MapPin } from 'lucide-react';
import NewBuyAnywhereLogo from './NewBuyAnywhereLogo';

export const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <div className="mb-4">
              <NewBuyAnywhereLogo size="small" variant="dark" />
            </div>
            <p className="text-gray-300 text-sm mb-4">
              Покупаем для вас всё недоступное в России. 
              Гарантированно, быстро, по лучшим ценам.
            </p>
            <Button variant="outline" size="sm" className="border-blue-400 text-blue-400 hover:bg-blue-400 hover:text-white">
              Начать покупку
            </Button>
          </div>

          {/* Services */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Услуги</h4>
            <ul className="space-y-2 text-gray-300">
              <li><a href="#" className="hover:text-blue-400 transition-colors">Подписки на сервисы</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Онлайн курсы</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Товары брендов</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Билеты и отели</a></li>
              <li><a href="#" className="hover:text-blue-400 transition-colors">Электроника</a></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Контакты</h4>
            <div className="space-y-3 text-gray-300">
              <div className="flex items-center">
                <Phone className="h-4 w-4 mr-3 text-blue-400" />
                <span>+7 913 553 33 69</span>
              </div>
              <div className="flex items-center">
                <Mail className="h-4 w-4 mr-3 text-blue-400" />
                <span>info@buyanywhere.ru</span>
              </div>
              <div className="flex items-center">
                <Clock className="h-4 w-4 mr-3 text-blue-400" />
                <span>24/7 поддержка</span>
              </div>
              <div className="flex items-center">
                <MapPin className="h-4 w-4 mr-3 text-blue-400" />
                <span>Доставка по всей России</span>
              </div>
            </div>
          </div>

          {/* Payment Methods */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Способы оплаты</h4>
            <div className="space-y-2 text-gray-300 text-sm">
              <p>• Сбербанк</p>
              <p>• Т-Банк</p>
              <p>• ВТБ</p>
              <p>• СБП (по номеру телефона)</p>
              <p>• Переводы на карту</p>
            </div>
            <div className="mt-4 p-3 bg-green-900 rounded-lg">
              <p className="text-green-300 text-sm font-medium">
                Комиссия 0% за все переводы
              </p>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-400 text-sm">
              <p>&copy; 2024 BuyAnywhere. Все права защищены.</p>
            </div>
            <div className="flex flex-wrap gap-4 sm:gap-6 text-gray-400 text-sm mt-4 md:mt-0">
              <a href="/privacy-policy-professional.html" className="hover:text-blue-400 transition-colors" target="_blank">Политика конфиденциальности</a>
              <a href="/user-agreement-professional.html" className="hover:text-blue-400 transition-colors" target="_blank">Пользовательское соглашение</a>
              <a href="#guarantees" className="hover:text-blue-400 transition-colors">Гарантии</a>
              <a href="#faq" className="hover:text-blue-400 transition-colors">FAQ</a>
            </div>
          </div>
        </div>

        <div className="text-center mt-6 pt-6 border-t border-gray-700">
          <p className="text-gray-400 text-sm">
            🛡️ Гарантированный сервис • 🚀 Быстрая доставка • 💰 Оплата в рублях
          </p>
        </div>
      </div>
    </footer>
  );
};