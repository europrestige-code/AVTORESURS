import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { ChevronDown, ChevronUp, HelpCircle, ArrowLeft, Package, CreditCard, Shield } from 'lucide-react';

export const FAQ = () => {
  const [openQuestion, setOpenQuestion] = useState(null);

  const faqData = [
    {
      category: "Общие вопросы",
      icon: HelpCircle,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      questions: [
        {
          question: "Что представляет собой сервис BuyAnywhere?",
          answer: "BuyAnywhere — это агентский сервис, который помогает российским клиентам покупать товары в зарубежных интернет-магазинах. Мы не являемся продавцом товаров — мы действуем как ваш агент, покупая выбранные вами товары по вашему поручению."
        },
        {
          question: "В чём отличие от других сервисов покупок?",
          answer: "Мы работаем по агентской модели: вы самостоятельно выбираете товары, а мы организуем их покупку и доставку. Это означает, что ответственность за качество и соответствие товара несёт продавец, а не мы."
        },
        {
          question: "Какие товары можно заказать?",
          answer: "Мы можем купить практически любые товары из зарубежных интернет-магазинов: электронику, одежду, товары для дома, автозапчасти, подписки на сервисы. Исключение составляют товары, запрещённые к ввозу в РФ."
        }
      ]
    },
    {
      category: "Возвраты и обмены",
      icon: ArrowLeft,
      color: "text-red-600",
      bgColor: "bg-red-50",
      questions: [
        {
          question: "Можно ли вернуть или обменять товар?",
          answer: "BuyAnywhere действует как агент и не является продавцом товаров. Возвраты и обмены возможны только в рамках политики продавца, у которого был приобретён товар. Каждый магазин имеет свои правила возврата."
        },
        {
          question: "Кто оплачивает расходы на возврат?",
          answer: "BuyAnywhere содействует оформлению возврата/обмена в качестве дополнительной услуги. Расходы на пересылку и комиссии несёт клиент, если иное не предусмотрено политикой продавца."
        },
        {
          question: "Возвращается ли комиссия BuyAnywhere при возврате товара?",
          answer: "В случае возврата товара стоимость комиссии BuyAnywhere не возвращается, так как услуга по исполнению поручения (поиск, покупка, оформление) считается оказанной."
        },
        {
          question: "Что делать, если товар пришёл повреждённым?",
          answer: "Немедленно сообщите нам о повреждении с фотографиями. Мы поможем оформить претензию к продавцу или перевозчику (если товар был застрахован). Компенсация зависит от политики продавца и условий страхования."
        }
      ]
    },
    {
      category: "Оплата и стоимость",
      icon: CreditCard,
      color: "text-green-600",
      bgColor: "bg-green-50",
      questions: [
        {
          question: "Как рассчитывается стоимость услуг?",
          answer: "Итоговая стоимость включает: цену товара у продавца + комиссию BuyAnywhere (18%, минимум 1500 руб.) + международную доставку + таможенные платежи + внутреннюю доставку по РФ + страхование (по желанию)."
        },
        {
          question: "Какие способы оплаты доступны?",
          answer: "Мы принимаем оплату в рублях через: T-Bank QR, Сбер QR, карты МИР, СБП (Система быстрых платежей), оплату с баланса телефона. Все расчёты производятся в российских рублях."
        },
        {
          question: "Можно ли изменить заказ после оплаты?",
          answer: "После оплаты изменения возможны только до момента размещения заказа у продавца. Как только заказ оформлен у продавца, изменения подчиняются политике конкретного магазина."
        },
        {
          question: "Что происходит, если цена товара изменилась?",
          answer: "Возможен пересчёт стоимости при изменении курсов валют или цен до момента оплаты продавцу. Мы уведомляем вас обо всех изменениях и требуем подтверждения."
        }
      ]
    },
    {
      category: "Доставка и гарантии",
      icon: Package,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
      questions: [
        {
          question: "Сколько времени занимает доставка?",
          answer: "Сроки зависят от продавца, страны отправления и таможенного оформления: поиск товара (1-3 дня), покупка (1-7 дней), международная доставка (7-21 день), таможенное оформление (3-10 дней)."
        },
        {
          question: "Как гарантируется подлинность товаров?",
          answer: "Для премиальных брендов (Apple, Samsung и др.) мы покупаем у официальных ритейлеров и проверенных поставщиков, предоставляющих документы, подтверждающие подлинность (инвойсы, серийные номера)."
        },
        {
          question: "Что покрывает страхование?",
          answer: "Страхование (5% от стоимости товара) покрывает риски утери или повреждения при международной перевозке. Страхование не покрывает отказ от товара или несоответствие ожиданиям."
        },
        {
          question: "Действует ли гарантия производителя в России?",
          answer: "Гарантийные обязательства несёт производитель в соответствии с их политикой. Возможность гарантийного обслуживания в РФ зависит от политики производителя и его сервисных центров."
        }
      ]
    },
    {
      category: "Безопасность и данные",
      icon: Shield,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
      questions: [
        {
          question: "Как защищены мои персональные данные?",
          answer: "Мы обрабатываем данные в соответствии с ФЗ-152 «О персональных данных». Данные передаются только для выполнения заказа: продавцам, платёжным системам, перевозчикам, таможенным органам."
        },
        {
          question: "Передаются ли данные за границу?",
          answer: "При заказе у зарубежных продавцов ваши данные могут передаваться за пределы РФ для оформления заказа. Мы требуем от партнёров обеспечения адекватного уровня защиты данных."
        },
        {
          question: "Можно ли отозвать согласие на обработку данных?",
          answer: "Да, вы можете отозвать согласие, обратившись на email privacy@buyanywhere.ru. При отзыве согласия мы прекратим обработку данных, за исключением случаев, когда хранение требуется по закону."
        }
      ]
    }
  ];

  const toggleQuestion = (categoryIndex, questionIndex) => {
    const key = `${categoryIndex}-${questionIndex}`;
    setOpenQuestion(openQuestion === key ? null : key);
  };

  return (
    <section className="mobile-spacing bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-6xl mx-auto mobile-container">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-6">
            <HelpCircle className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-responsive-xl font-bold text-gray-900 mb-4">
            Часто задаваемые вопросы
          </h2>
          <p className="text-responsive-base text-gray-600 max-w-3xl mx-auto">
            Ответы на основные вопросы о работе нашего агентского сервиса покупок из зарубежных магазинов
          </p>
        </div>

        <div className="space-y-8">
          {faqData.map((category, categoryIndex) => {
            const IconComponent = category.icon;
            return (
              <div key={categoryIndex} className="space-y-4">
                {/* Category Header */}
                <div className={`${category.bgColor} rounded-lg p-4 border-l-4 border-${category.color.replace('text-', '')}`}>
                  <div className="flex items-center space-x-3">
                    <IconComponent className={`h-6 w-6 ${category.color}`} />
                    <h3 className="text-responsive-lg font-semibold text-gray-900">
                      {category.category}
                    </h3>
                  </div>
                </div>

                {/* Questions */}
                <div className="space-y-3">
                  {category.questions.map((item, questionIndex) => {
                    const isOpen = openQuestion === `${categoryIndex}-${questionIndex}`;
                    return (
                      <Card key={questionIndex} className="mobile-card hover:shadow-md transition-shadow">
                        <CardContent className="p-0">
                          <button
                            onClick={() => toggleQuestion(categoryIndex, questionIndex)}
                            className="w-full p-4 sm:p-6 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                          >
                            <h4 className="font-medium text-gray-900 text-sm sm:text-base pr-4">
                              {item.question}
                            </h4>
                            {isOpen ? (
                              <ChevronUp className="h-5 w-5 text-gray-500 flex-shrink-0" />
                            ) : (
                              <ChevronDown className="h-5 w-5 text-gray-500 flex-shrink-0" />
                            )}
                          </button>
                          
                          {isOpen && (
                            <div className="px-4 sm:px-6 pb-4 sm:pb-6">
                              <div className="border-t pt-4">
                                <p className="text-gray-700 text-sm sm:text-base leading-relaxed">
                                  {item.answer}
                                </p>
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Contact Section */}
        <div className="mt-12 bg-white rounded-2xl p-6 sm:p-8 shadow-lg border border-gray-200">
          <div className="text-center">
            <h3 className="text-responsive-lg font-bold text-gray-900 mb-4">
              Не нашли ответ на свой вопрос?
            </h3>
            <p className="text-gray-600 mb-6">
              Наша служба поддержки работает 24/7 и готова помочь с любыми вопросами
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <a
                href="tel:+74951234567"
                className="mobile-btn bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                +7 (495) 123-45-67
              </a>
              <a
                href="mailto:support@buyanywhere.ru"
                className="mobile-btn bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                support@buyanywhere.ru
              </a>
              <a
                href="https://t.me/BuyAnywhereSupport"
                target="_blank"
                rel="noopener noreferrer"
                className="mobile-btn bg-cyan-600 hover:bg-cyan-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Telegram
              </a>
            </div>
          </div>
        </div>

        {/* Legal Notice */}
        <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4 sm:p-6">
          <div className="text-center">
            <p className="text-sm text-amber-800">
              <strong>Правовое уведомление:</strong> BuyAnywhere работает по агентской модели. 
              Полные условия услуг и политика обработки данных доступны в{' '}
              <a href="/user-agreement-professional.html" target="_blank" className="underline hover:no-underline">
                Пользовательском соглашении
              </a>
              {' '}и{' '}
              <a href="/privacy-policy-professional.html" target="_blank" className="underline hover:no-underline">
                Политике конфиденциальности
              </a>.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};