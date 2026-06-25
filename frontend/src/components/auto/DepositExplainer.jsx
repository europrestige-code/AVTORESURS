import React from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, RefreshCw, TrendingUp } from "lucide-react";

/* Deposit explainer — explains *why* the NZ$1,000 deposit is required
 * and *how* it's protected. Goes on the homepage, the vehicle detail page
 * (in the no-deposit state) and the dashboard.
 */
export default function DepositExplainer({ compact = false }) {
  if (compact) {
    return (
      <div
        className="rounded-xl border border-blue-500/20 bg-blue-500/[0.05] p-3 text-[12px] leading-snug text-gray-300"
        data-testid="deposit-explainer-compact"
      >
        <b className="text-white">Депозит NZ$1,000</b> — возвратный или зачётный.
        Засчитывается в покупку или остаётся на балансе для будущих ставок.
      </div>
    );
  }

  return (
    <section
      className="mx-auto my-10 max-w-7xl rounded-2xl border border-white/10 bg-[var(--ar-card)] p-6"
      data-testid="deposit-explainer"
    >
      <div className="grid items-start gap-6 md:grid-cols-[1.2fr_1fr]">
        <div>
          <h3 className="text-2xl font-bold text-white">Как работает депозит NZ$1,000?</h3>
          <p className="mt-3 text-sm leading-relaxed text-gray-300">
            Депозит подтверждает серьёзность ваших намерений и открывает доступ к подаче ставок на
            аукционах. <b className="text-white">Это не покупка</b> — это гарантия для аукционных площадок.
          </p>

          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Card
              icon={<ShieldCheck size={20} className="text-[var(--ar-success)]" />}
              title="Безопасно"
              text="Платёж через Stripe (PCI DSS). Карта или банковский перевод."
            />
            <Card
              icon={<RefreshCw size={20} className="text-blue-400" />}
              title="Возвратный"
              text="Если не выиграли — вернём в течение 3 рабочих дней."
            />
            <Card
              icon={<TrendingUp size={20} className="text-[#FFB84D]" />}
              title="Зачётный"
              text="При выигрыше — засчитывается в стоимость авто."
            />
          </div>
        </div>

        <div className="rounded-xl border border-blue-500/20 bg-blue-500/[0.06] p-5">
          <div className="text-sm text-gray-300">До депозита можно:</div>
          <ul className="mt-2 space-y-1.5 text-sm text-white">
            <li>✓ Сохранять авто в избранное</li>
            <li>✓ Запросить расчёт под ключ</li>
            <li>✓ Предложить свою цену (не ставка)</li>
            <li>✓ Получать ответы Татьяны 24/7</li>
          </ul>
          <div className="mt-4 border-t border-white/10 pt-4 text-sm text-gray-300">
            После депозита открывается:
          </div>
          <ul className="mt-2 space-y-1.5 text-sm text-white">
            <li>★ Официальные ставки на NZ-аукционах</li>
            <li>★ Прокси-биддинг (автоматическая защита)</li>
            <li>★ Приоритетная связь с менеджером</li>
          </ul>
          <Link
            to="/auto/dashboard"
            className="mt-5 inline-flex w-full items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
            data-testid="deposit-explainer-cta"
          >
            Внести депозит NZ$1,000
          </Link>
        </div>
      </div>
    </section>
  );
}

function Card({ icon, title, text }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2">{icon}</div>
      <div className="font-bold text-white">{title}</div>
      <div className="mt-1 text-[12px] leading-snug text-gray-400">{text}</div>
    </div>
  );
}
