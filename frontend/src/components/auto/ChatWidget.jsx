import React, { useEffect, useRef, useState } from "react";
import { MessageCircle, X, Send, Bot, Sparkles } from "lucide-react";
import autoApi from "../../services/autoApi";
import QuizFlow from "./QuizFlow";

const STORAGE_KEY = "avtoresurs_chat_history";

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveHistory(history) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-20)));
  } catch { /* localStorage unavailable */ }
}

const GREETING = {
  role: "assistant",
  content: "Здравствуйте! Я Татьяна — ИИ-ассистент АвтоРесурс. Помогу разобраться с покупкой авто из НЗ или Австралии. Что вас интересует?",
};

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("chat"); // "chat" | "quiz"
  const [history, setHistory] = useState(() => {
    const h = loadHistory();
    return h.length ? h : [GREETING];
  });
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const scrollerRef = useRef(null);

  useEffect(() => { saveHistory(history); }, [history]);

  useEffect(() => {
    if (open && mode === "chat" && scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight;
    }
  }, [open, mode, history.length, busy]);

  const send = async (e) => {
    e?.preventDefault?.();
    const text = input.trim();
    if (!text || busy) return;
    const next = [...history, { role: "user", content: text }];
    setHistory(next);
    setInput("");
    setBusy(true);
    try {
      const r = await autoApi.post("/chat", {
        message: text,
        history: next.slice(-12),
        session_id: sessionId,
      });
      if (r.data.session_id) setSessionId(r.data.session_id);
      setHistory((cur) => [...cur, { role: "assistant", content: r.data.content || "(пустой ответ)" }]);
    } catch (err) {
      setHistory((cur) => [
        ...cur,
        {
          role: "assistant",
          content:
            "Не получилось связаться с сервером. Напишите нам в WhatsApp +64 21 425 233 или RUS +7 913 512 1934.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const clear = () => {
    setHistory([GREETING]);
    setSessionId(null);
    saveHistory([GREETING]);
  };

  const QUICK_QUESTIONS = [
    "Сколько стоит депозит?",
    "Как считается итоговая цена?",
    "Можно ли купить авто на запчасти?",
    "Доставка в Россию — сколько по времени?",
  ];

  const startQuiz = () => setMode("quiz");
  const closeQuiz = () => {
    setMode("chat");
    // Drop a friendly assistant message acknowledging the quiz completion
    setHistory((cur) => [
      ...cur,
      {
        role: "assistant",
        content:
          "Готово! Я записала ваши предпочтения. Менеджер свяжется в течение часа. Если хотите, могу ответить на дополнительные вопросы прямо сейчас.",
      },
    ]);
  };

  return (
    <>
      {!open && (
        <button
          type="button"
          className="chat-fab"
          onClick={() => setOpen(true)}
          data-testid="chat-fab"
          aria-label="Открыть чат"
        >
          <MessageCircle size={26} strokeWidth={2} />
          <span className="chat-fab__label">Спросить Татьяну</span>
        </button>
      )}
      {open && (
        <div className="chat-panel" data-testid="chat-panel" role="dialog" aria-label="Чат с Татьяной">
          <header className="chat-panel__head">
            <div className="chat-panel__title">
              <span className="chat-panel__avatar"><Bot size={18} /></span>
              <div>
                <div style={{ fontWeight: 700 }}>Татьяна · АвтоРесурс</div>
                <div className="auto-muted" style={{ fontSize: 11 }}>Отвечает по-русски, обычно за пару секунд</div>
              </div>
            </div>
            <button type="button" className="chat-panel__close" onClick={() => setOpen(false)} aria-label="Закрыть" data-testid="chat-close">
              <X size={18} />
            </button>
          </header>

          {mode === "quiz" ? (
            <div className="chat-panel__body chat-panel__body--quiz">
              <QuizFlow onClose={closeQuiz} />
            </div>
          ) : (
            <>
              <div className="chat-panel__body" ref={scrollerRef}>
                {history.map((m, i) => (
                  <div key={i} className={`chat-msg chat-msg--${m.role}`} data-testid={`chat-msg-${i}`}>
                    {m.content}
                  </div>
                ))}
                {busy && (
                  <div className="chat-msg chat-msg--assistant chat-msg--typing" data-testid="chat-typing">
                    Татьяна печатает<span className="chat-dots"><span/><span/><span/></span>
                  </div>
                )}
              </div>

              <div className="chat-panel__quick chat-panel__quick--top" data-testid="chat-quiz-cta-row">
                <button
                  type="button"
                  className="auto-btn auto-btn--primary chat-quick chat-quick--quiz"
                  onClick={startQuiz}
                  data-testid="chat-quiz-cta"
                >
                  <Sparkles size={14} style={{ marginRight: 6, verticalAlign: "text-bottom" }} />
                  Подобрать авто за 60 секунд
                </button>
              </div>

              {history.length <= 1 && (
                <div className="chat-panel__quick">
                  {QUICK_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      type="button"
                      className="auto-badge auto-badge-primary chat-quick"
                      onClick={() => { setInput(q); }}
                      data-testid={`chat-quick-${i}`}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
              <form className="chat-panel__input" onSubmit={send} data-testid="chat-form">
                <input
                  className="auto-input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Напишите вопрос…"
                  disabled={busy}
                  data-testid="chat-input"
                />
                <button type="submit" className="auto-btn" disabled={busy || !input.trim()} data-testid="chat-send">
                  <Send size={16} />
                </button>
              </form>
              <button type="button" className="chat-panel__clear" onClick={clear} data-testid="chat-clear">
                Очистить
              </button>
            </>
          )}
        </div>
      )}
    </>
  );
}
