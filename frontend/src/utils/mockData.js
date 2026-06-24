export const mockData = {
  getPriceCalculation: (input) => {
    // Mock price calculation based on input
    const mockProducts = [
      {
        name: 'iPhone 15 Pro 256GB',
        originalPriceUSD: 1199,
        bestStore: 'Apple Store USA',
        shipping: 2500,
        customs: 15000,
      },
      {
        name: 'Netflix Premium подписка',
        originalPriceUSD: 15.49,
        bestStore: 'Netflix.com',
        shipping: 0,
        customs: 0,
      },
      {
        name: 'Adobe Creative Suite',
        originalPriceUSD: 52.99,
        bestStore: 'Adobe.com',
        shipping: 0,
        customs: 0,
      },
      {
        name: 'Louis Vuitton сумка',
        originalPriceUSD: 2500,
        bestStore: 'LV официальный сайт',
        shipping: 3500,
        customs: 45000,
      }
    ];

    // Select random product or create based on input
    const selectedProduct = mockProducts[Math.floor(Math.random() * mockProducts.length)];
    
    // Mock currency rate (USD to RUB) - Google rate minus 3 points
    const usdToRub = 97; // Example rate
    
    const originalPrice = Math.round(selectedProduct.originalPriceUSD * usdToRub);
    const commission = Math.max(Math.round(originalPrice * 0.18), 1500);
    const insurance = Math.round((originalPrice + commission) * 0.05);
    const totalPrice = originalPrice + commission + selectedProduct.shipping + selectedProduct.customs + insurance;

    return {
      productName: selectedProduct.name,
      bestStore: selectedProduct.bestStore,
      originalPrice: originalPrice.toLocaleString('ru-RU'),
      commission: commission.toLocaleString('ru-RU'),
      shipping: selectedProduct.shipping.toLocaleString('ru-RU'),
      customs: selectedProduct.customs.toLocaleString('ru-RU'),
      insurance: insurance.toLocaleString('ru-RU'),
      totalPrice: totalPrice.toLocaleString('ru-RU'),
    };
  },

  getPaymentMethods: () => [
    {
      name: 'Сбербанк',
      description: 'Перевод на карту или счёт',
      fee: '0%',
      time: 'Мгновенно'
    },
    {
      name: 'Т-Банк',
      description: 'Перевод на карту',
      fee: '0%',
      time: 'Мгновенно'
    },
    {
      name: 'ВТБ',
      description: 'Перевод на счёт',
      fee: '0%',
      time: '1-2 минуты'
    },
    {
      name: 'По номеру телефона',
      description: 'СБП - быстрые платежи',
      fee: '0%',
      time: 'Мгновенно'
    }
  ],

  getGuarantees: () => [
    'Возврат средств, если товар не доставлен',
    'Страховка на все товары до 5% от стоимости',
    'Полное сопровождение заказа до получения',
    'Уведомления на каждом этапе доставки',
    'Помощь с таможенным оформлением'
  ],

  getPopularLinks: (category) => {
    const links = {
      subscriptions: [
        {
          name: 'Netflix',
          description: 'Фильмы и сериалы',
          url: 'netflix.com',
          price: 'от 1500 ₽/мес'
        },
        {
          name: 'Spotify Premium',
          description: 'Музыка без рекламы',
          url: 'spotify.com',
          price: 'от 1200 ₽/мес'
        },
        {
          name: 'Adobe Creative Cloud',
          description: 'Photoshop, Illustrator, Premiere',
          url: 'adobe.com',
          price: 'от 5200 ₽/мес'
        },
        {
          name: 'Disney+',
          description: 'Marvel, Star Wars, Disney',
          url: 'disneyplus.com',
          price: 'от 800 ₽/мес'
        },
        {
          name: 'YouTube Premium',
          description: 'Без рекламы + YouTube Music',
          url: 'youtube.com/premium',
          price: 'от 1400 ₽/мес'
        },
        {
          name: 'Dropbox Plus',
          description: 'Облачное хранилище 2TB',
          url: 'dropbox.com',
          price: 'от 1000 ₽/мес'
        }
      ],
      courses: [
        {
          name: 'Coursera Plus',
          description: 'Курсы от топ университетов',
          url: 'coursera.org',
          price: 'от 4500 ₽/мес'
        },
        {
          name: 'MasterClass',
          description: 'Уроки от мировых экспертов',
          url: 'masterclass.com',
          price: 'от 15000 ₽/год'
        },
        {
          name: 'Udemy Business',
          description: 'Профессиональные навыки',
          url: 'udemy.com',
          price: 'от 3000 ₽/курс'
        },
        {
          name: 'Skillshare Premium',
          description: 'Креативные навыки',
          url: 'skillshare.com',
          price: 'от 1200 ₽/мес'
        },
        {
          name: 'LinkedIn Learning',
          description: 'Бизнес и технологии',
          url: 'linkedin.com/learning',
          price: 'от 2500 ₽/мес'
        },
        {
          name: 'Pluralsight',
          description: 'IT и разработка',
          url: 'pluralsight.com',
          price: 'от 2800 ₽/мес'
        }
      ],
      brands: [
        {
          name: 'Louis Vuitton',
          description: 'Сумки, аксессуары, одежда',
          url: 'louisvuitton.com',
          price: 'от 50000 ₽'
        },
        {
          name: 'Gucci',
          description: 'Luxury fashion и аксессуары',
          url: 'gucci.com',
          price: 'от 30000 ₽'
        },
        {
          name: 'Zara',
          description: 'Модная одежда',
          url: 'zara.com',
          price: 'от 2000 ₽'
        },
        {
          name: 'H&M',
          description: 'Доступная мода',
          url: 'hm.com',
          price: 'от 800 ₽'
        },
        {
          name: 'Nike',
          description: 'Спортивная одежда и обувь',
          url: 'nike.com',
          price: 'от 5000 ₽'
        },
        {
          name: 'Adidas',
          description: 'Спорт и lifestyle',
          url: 'adidas.com',
          price: 'от 4000 ₽'
        }
      ],
      travel: [
        {
          name: 'Booking.com',
          description: 'Бронирование отелей',
          url: 'booking.com',
          price: 'по тарифам отеля'
        },
        {
          name: 'Airbnb',
          description: 'Аренда жилья',
          url: 'airbnb.com',
          price: 'по тарифам хозяина'
        },
        {
          name: 'Expedia',
          description: 'Авиабилеты и отели',
          url: 'expedia.com',
          price: 'по тарифам авиакомпаний'
        },
        {
          name: 'Hotels.com',
          description: 'Отели по всему миру',
          url: 'hotels.com',
          price: 'по тарифам отелей'
        },
        {
          name: 'Kayak',
          description: 'Поиск дешёвых билетов',
          url: 'kayak.com',
          price: 'сравнение цен'
        },
        {
          name: 'Skyscanner',
          description: 'Авиабилеты',
          url: 'skyscanner.com',
          price: 'поиск лучших цен'
        }
      ],
      electronics: [
        {
          name: 'Apple Store',
          description: 'iPhone, MacBook, iPad',
          url: 'apple.com',
          price: 'от 50000 ₽'
        },
        {
          name: 'Best Buy',
          description: 'Электроника и гаджеты',
          url: 'bestbuy.com',
          price: 'от 5000 ₽'
        },
        {
          name: 'Amazon',
          description: 'Всё для дома и техника',
          url: 'amazon.com',
          price: 'от 1000 ₽'
        },
        {
          name: 'Newegg',
          description: 'Компьютеры и комплектующие',
          url: 'newegg.com',
          price: 'от 3000 ₽'
        },
        {
          name: 'B&H Photo',
          description: 'Фото/видео техника',
          url: 'bhphotovideo.com',
          price: 'от 10000 ₽'
        },
        {
          name: 'Samsung',
          description: 'Смартфоны и техника',
          url: 'samsung.com',
          price: 'от 15000 ₽'
        }
      ],
      digital: [
        {
          name: 'Steam',
          description: 'PC игры',
          url: 'store.steampowered.com',
          price: 'от 500 ₽'
        },
        {
          name: 'Epic Games Store',
          description: 'Бесплатные игры каждую неделю',
          url: 'epicgames.com',
          price: 'от 1000 ₽'
        },
        {
          name: 'App Store',
          description: 'iOS приложения',
          url: 'apps.apple.com',
          price: 'от 100 ₽'
        },
        {
          name: 'Google Play',
          description: 'Android приложения',
          url: 'play.google.com',
          price: 'от 100 ₽'
        },
        {
          name: 'Microsoft Store',
          description: 'Xbox игры и приложения',
          url: 'microsoft.com/store',
          price: 'от 800 ₽'
        },
        {
          name: 'PlayStation Store',
          description: 'PlayStation игры',
          url: 'store.playstation.com',
          price: 'от 1500 ₽'
        }
      ]
    };

    return links[category] || [];
  }
};