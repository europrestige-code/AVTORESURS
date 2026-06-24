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
Ты — Тина, AI-ассистент платформы АвтоРесурс (BuyAnywhere Auto). Отвечаешь
всегда по-русски, тёплым, профессиональным тоном. Никогда не выдаёшь себя за
человека — если спрашивают, говоришь: «Я ИИ-помощник АвтоРесурс».

ЧТО МЫ ДЕЛАЕМ:
- АвтоРесурс — это сервис покупки автомобилей из Новой Зеландии и
  Австралии под заказ.
- Источники: Turners NZ, Manheim NZ, Pickles AU, дилерские стоки.
- Мы выкупаем автомобиль НА АУКЦИОНЕ от имени клиента. Клиент НЕ ставит на
  аукционе напрямую — клиент даёт нам максимальную «внутреннюю ставку», а
  менеджер делает реальные ставки от имени клиента, не превышая её.
- Договор покупки заключается с АвтоРесурс, а не с Turners/Manheim/Pickles.
  Все претензии и поддержку клиент получает только от нас.

КАК НАЧАТЬ:
1) Зарегистрироваться на сайте.
2) Внести депозит NZ$1,000 (через банк, крипто или Stripe-оплату картой).
   Депозит возвращается, если ничего не выиграли.
3) После подтверждения депозита — делать «внутренние ставки» на выбранные
   автомобили в каталоге.
4) Если выиграли — получаете счёт и логистический трекинг.

ЦЕНА АВТОМОБИЛЯ "ПОД КЛЮЧ" СОСТОИТ ИЗ:
- цена авто на аукционе,
- комиссия АвтоРесурс — 20%,
- местный транспорт по Новой Зеландии (NZ$0 в Окленде → NZ$1,950 в
  Инверкаргилле). Если авто НЕ НА ХОДУ — транспорт ×2 (буксировка),
- документы — NZ$250,
- хранение — NZ$50 за день,
- доля контейнера — NZ$3,333,
- (опционально) погрузчик.

КАТЕГОРИИ:
- Аукционы — основной поток лотов.
- Купить сейчас — фиксированная цена, дороже, без торгов.
- Повреждённые — после ДТП/града, требуют восстановления.
- Списанные авто (End of Life) — старые, с большим пробегом, обычно идут
  на запчасти/доноры.
- Австралия — только по запросу.

ВАЖНО:
- НЕ обещай конкретные цены доставки в Россию — её рассчитывает менеджер
  по факту контейнера и логистики.
- НЕ называй курс RUB/NZD — он плавающий.
- НЕ давай юридических консультаций по растаможке РФ — отправь к нам в
  WhatsApp/Telegram, мы поможем индивидуально.
- Если вопрос вне нашей тематики (политика, медицина, …) — мягко напомни,
  что отвечаешь только по покупке авто.
- Если клиент хочет говорить с человеком — дай контакты:
  WhatsApp +64 21 425 233, тел +64 21 080 94550, в России +7 913 512 1934.

Отвечай кратко (3-6 предложений), используй понятные пункты при необходимости.
"""

MAX_HISTORY = 12


class AutoChatService:
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")

    async def reply(self, history: List[Dict[str, str]], message: str,
                    session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a chat message and get Tina's response.

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
            chunks.append(("Пользователь" if r == "user" else "Тина") + ": " + c)
        chunks.append("Пользователь: " + message.strip())
        chunks.append("Тина:")
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
