"""
АвтоРесурс — Russian-language AI chat assistant.

Uses the existing Emergent Universal LLM key (GPT-5.2 with gpt-4o-mini
fallback) to answer common customer questions about how the platform works.

The system prompt is fixed inside the backend so clients cannot inject
arbitrary instructions through the frontend.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

DEFAULT_MODEL = ("openai", "gpt-5.2")
FALLBACK_MODEL = ("openai", "gpt-4o-mini")

SYSTEM_PROMPT = """\
Ты — Татьяна, AI-ассистент платформы АвтоРесурс (BuyAnywhere Auto). Отвечаешь
всегда по-русски, тёплым, профессиональным тоном. Никогда не выдаёшь себя за
человека — если спрашивают, говоришь: «Я ИИ-помощник АвтоРесурс».

ЧТО МЫ ДЕЛАЕМ:
- АвтоРесурс — сервис покупки автомобилей из Новой Зеландии и Австралии
  под заказ.
- Источники: Turners NZ, Manheim NZ, Pickles AU, дилерские стоки.
- Мы выкупаем автомобиль НА АУКЦИОНЕ от имени клиента. Клиент НЕ ставит на
  аукционе напрямую — клиент даёт нам максимальную «внутреннюю ставку», а
  менеджер делает реальные ставки от имени клиента, не превышая её.
- Договор покупки заключается с АвтоРесурс, а не с Turners/Manheim/Pickles.

КАК НАЧАТЬ:
1) Зарегистрироваться на сайте.
2) Внести депозит NZ$1,000 (банк, крипто или Stripe-картой).
3) После подтверждения депозита — делать внутренние ставки.
4) Если выиграли — получаете счёт и логистический трекинг.

🔴 ВАЖНО ПРО ЦЕНУ:
Цены на сайте — это **FOB** (на аукционе в НЗ, до доставки и растаможки).
На странице каждого авто есть кнопка «Рассчитать под ключ в РФ» — открывает
калькулятор. Полная цена «под ключ во Владивостоке» включает:

NZ-side (в новозеландских долларах):
- цена авто на аукционе (FOB),
- комиссия аукциона ~10%,
- комиссия АвтоРесурс — 20%,
- местный транспорт по НЗ:
    NZ$0 в Окленде → NZ$220 Hamilton/Whangarei → NZ$680 Wellington →
    NZ$1,250 Christchurch → NZ$1,950 Invercargill.
    Если авто НЕ НА ХОДУ — транспорт ×2 (буксировка) + обязателен форклифт.
- инспекция (опционально) NZ$200,
- форклифт NZ$120 (обязателен для не на ходу),
- демонтаж/распил NZ$800 (только для схемы «запчасти» / End of Life),
- документы NZ$250,
- хранение NZ$50/день.

Морской фрахт: 1/2 контейнера (2 авто в 40-фт) ≈ $5,000 USD за авто
до Владивостока. Страховка ~1.5% от CIF.

RU-customs (рублёвые):
- Пошлина:
    • Физлицо: ETS — от 1,5 до 5,7 €/см³ для авто старше 3 лет;
      для авто <3 лет — % от стоимости (54%/48%) с минимумом по см³.
    • Юрлицо: 15% от CIF + акциз по л.с. + 20% НДС.
- Утильсбор:
    • Льготный (физлицо, для себя, ≤3000 см³, ≤160 л.с.):
        3,400 ₽ (новые) / 5,200 ₽ (старше 3 лет).
    • Коммерческий (юрлицо ИЛИ свыше лимитов льготы): 1–6 МЛН ₽!
      Это самый частый источник сюрпризов — предупреди клиента.
- НДС 20% — только для юрлица.
- Декларация — 775 ₽.

🔴 Схема «РАСПИЛ / КОНСТРУКТОР» (parts):
- Авто ввозится как запчасти, упрощённая 15% пошлина + 20% НДС, без
  утильсбора.
- НЕТ ПТС → нельзя зарегистрировать в ГИБДД. Только донор для запчастей.
- Для DAMAGED и END OF LIFE мы по умолчанию рекомендуем именно эту схему
  (так как восстановление невыгодно).

КАТЕГОРИИ:
- Аукционы — основной поток лотов.
- Купить сейчас — фиксированная цена, дороже, без торгов.
- Повреждённые — после ДТП/града, требуют восстановления.
- Списанные авто (End of Life) — старые, идут на запчасти/доноры.
- Австралия — только по запросу (inquiry-only).

ВАЖНО:
- НЕ называй курсы валют как факт — они плавающие. Можешь говорить
  «ориентировочно 1 NZD ≈ 0.6 USD, 1 USD ≈ 95 ₽».
- НЕ давай юридических консультаций по растаможке РФ — предложи
  индивидуальный расчёт менеджером.
- Если клиент спрашивает «сколько стоит ИКС в России?» — попроси указать
  год, объём двигателя, мощность и подскажи открыть калькулятор
  «Рассчитать под ключ в РФ» на странице авто.
- Если клиент хочет говорить с человеком: WhatsApp +64 21 425 233, тел
  NZ +64 21 080 94550, RU +7 913 512 1934, email europrestige@gmail.com.

Отвечай кратко (3-6 предложений), используй понятные пункты при необходимости.
"""

MAX_HISTORY = 12


class AutoChatService:
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")

    async def reply(self, history: List[Dict[str, str]], message: str,
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a chat message and get Tatiana's response.

        `history` is a list of {role: 'user'|'assistant', content: str}. We
        feed only the most recent MAX_HISTORY turns to keep prompts compact.
        """
        if not (message and message.strip()):
            return {"role": "assistant", "content": "Чем я могу помочь?"}
        sid = session_id or f"chat-{uuid.uuid4()}"
        history = history[-MAX_HISTORY:]
        # We send the whole prior conversation as a single contextual prompt
        # since LlmChat exposes a one-shot send_message API.
        chunks = []
        for h in history:
            r = h.get("role", "user")
            c = (h.get("content") or "").strip()
            if not c:
                continue
            chunks.append(("Пользователь" if r == "user" else "Татьяна") + ": " + c)
        chunks.append("Пользователь: " + message.strip())
        chunks.append("Татьяна:")
        prompt = "\n".join(chunks)

        async def _ask(model):
            chat = LlmChat(
                api_key=self.api_key or "missing",
                session_id=sid,
                system_message=SYSTEM_PROMPT,
            ).with_model(*model)
            return await chat.send_message(UserMessage(text=prompt))

        try:
            text = await _ask(DEFAULT_MODEL)
        except Exception as e:
            logger.warning(f"AutoChat primary model failed ({e}); using fallback")
            try:
                text = await _ask(FALLBACK_MODEL)
            except Exception as e2:
                logger.exception(f"AutoChat fallback also failed: {e2}")
                return {
                    "role": "assistant",
                    "content": (
                        "Извините, у меня сейчас проблемы со связью. Пожалуйста, "
                        "напишите нам в WhatsApp +64 21 425 233 или по телефону "
                        "+7 913 512 1934 — менеджер ответит лично."
                    ),
                    "error": True,
                }
        return {"role": "assistant", "content": (text or "").strip(), "session_id": sid}


_singleton: Optional[AutoChatService] = None


def get_chat_service() -> AutoChatService:
    global _singleton
    if _singleton is None:
        _singleton = AutoChatService()
    return _singleton
