/**
 * Russian-translation helpers for Turners / Manheim auction titles.
 *
 * The auction calendar pulls raw English titles like:
 *   "BIG THURSDAY - Vehicles Under $10k"
 *   "Central/South Auckland CARS - All makes and models $15k and below"
 *
 * We render BOTH the original (small grey) and a Russian summary so a
 * Russian buyer instantly understands what's on offer.
 */

const RULES = [
  // [pattern, ru replacement, eventType]
  // Event-type keywords
  { re: /tender/i,                  ru: "Тендер" },
  { re: /live\s+auction/i,          ru: "Живой аукцион" },
  { re: /online\s+auction/i,        ru: "Онлайн-аукцион" },
  // Day prefixes
  { re: /\bbig\s+wednesday\b/i,     ru: "Большая среда" },
  { re: /\bbig\s+thursday\b/i,      ru: "Большой четверг" },
  { re: /\bbig\s+tuesday\b/i,       ru: "Большой вторник" },
  { re: /\bbig\s+monday\b/i,        ru: "Большой понедельник" },
  { re: /\blow\s+price\s+tuesday\b/i, ru: "Низкие цены — вторник" },
  // Vehicle classes
  { re: /4WD\s*&?\s*light\s+commercial/i, ru: "Внедорожники и лёгкий коммерческий" },
  { re: /\b4WD\b/i,                 ru: "Внедорожники" },
  { re: /quality\s*&\s*commercial/i, ru: "Премиум и коммерческий" },
  { re: /commercials?\s*&\s*4WDs?/i, ru: "Коммерческие и внедорожники" },
  { re: /\bcars\b\s*,?\s*commercials?\b/i, ru: "Легковые и коммерческие" },
  // All / general
  { re: /all\s+vehicles?\s*[,&]?\s*all\s+prices/i, ru: "Все авто, все цены" },
  { re: /all\s+in\s+thursday\s+auction/i, ru: "Большой четверговый аукцион" },
  { re: /all\s+makes?\s+and\s+models?/i, ru: "Все марки и модели" },
  // Price bands
  { re: /\$?(\d{1,3}(?:[,\s]?\d{3})?)k?\s*&\s*over/i,    (m) => `от $${m[1]}k` },
  { re: /\$?(\d{1,3}(?:[,\s]?\d{3})?)k?\s*&\s*below/i,   (m) => `до $${m[1]}k` },
  { re: /\$?(\d{1,3}(?:[,\s]?\d{3})?)k?\s+and\s+above/i, (m) => `от $${m[1]}k` },
  { re: /\$?(\d{1,3}(?:[,\s]?\d{3})?)k?\s+and\s+below/i, (m) => `до $${m[1]}k` },
  { re: /under\s+\$?(\d{1,3}(?:[,\s]?\d{3})?)k?/i,        (m) => `до $${m[1]}k` },
  // Regions
  { re: /\bhamilton\s*,\s*tauranga\s*&\s*rotorua/i, ru: "Хэмилтон / Тауранга / Роторуа" },
  { re: /central\/south\s+auckland/i, ru: "Окленд (центр/юг)" },
  { re: /north\s+west\s+auckland/i,   ru: "Окленд (северо-запад)" },
  { re: /north\s+shore\s+tender/i,    ru: "Тендер Норт-Шор" },
  { re: /\bwellington\b/i,            ru: "Веллингтон" },
  { re: /\bdunedin\b/i,               ru: "Данидин" },
  { re: /\bporirua\b/i,               ru: "Порируа" },
  { re: /\bnapier\b/i,                ru: "Нейпир" },
  { re: /\bpalmerston\s+north\b/i,    ru: "Палмерстон-Норт" },
  { re: /\bnew\s+plymouth\b/i,        ru: "Нью-Плимут" },
  { re: /\bhornby\b/i,                ru: "Хорнби" },
  { re: /\botahuhu\b/i,               ru: "Отахуху" },
  { re: /\bwhangarei\b/i,             ru: "Вангарей" },
  { re: /\bhamilton\b/i,              ru: "Хэмилтон" },
  // Day names
  { re: /\bwednesday\b/i, ru: "среда" },
  { re: /\bthursday\b/i,  ru: "четверг" },
  { re: /\btuesday\b/i,   ru: "вторник" },
  { re: /\bmonday\b/i,    ru: "понедельник" },
  { re: /\bfriday\b/i,    ru: "пятница" },
  // Lots / categories
  { re: /\bcars\b/i,      ru: "Легковые" },
];

export function detectEventType(title = "") {
  const t = String(title).toLowerCase();
  if (/tender/i.test(t)) return { code: "tender",  ru: "Тендер",       tone: "amber" };
  if (/live/i.test(t))   return { code: "live",    ru: "Живой аукцион", tone: "red" };
  if (/online/i.test(t)) return { code: "online",  ru: "Онлайн",        tone: "blue" };
  if (/sale/i.test(t))   return { code: "sale",    ru: "Продажа",       tone: "gray" };
  return { code: "auction", ru: "Аукцион", tone: "blue" };
}

export function translateAuctionTitle(title = "") {
  let s = String(title);
  // Strip date suffixes like "24/6/2026"
  s = s.replace(/\b\d{1,2}\/\d{1,2}\/\d{4}\b/g, "").trim();
  // Apply rules sequentially
  for (const r of RULES) {
    if (typeof r.ru === "function") {
      s = s.replace(r.re, r.ru);
    } else {
      s = s.replace(r.re, r.ru);
    }
  }
  // Drop residual separators
  s = s.replace(/\s+[-–—]\s+$/g, "").replace(/^\s+[-–—]\s+/g, "").trim();
  // Collapse multiple spaces
  s = s.replace(/\s{2,}/g, " ").trim();
  return s || title;
}

const STATUS_RU = {
  "Not Yet Started": "Не начался",
  "View Live":       "Идёт сейчас",
  "Sold":            "Продан",
  "Closed":          "Завершён",
};

export function translateStatus(status = "") {
  return STATUS_RU[status] || status;
}
