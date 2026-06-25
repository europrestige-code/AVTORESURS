import React, { useEffect, useState } from "react";
import { AlertCircle, Clock, CreditCard, Diamond } from "lucide-react";
import autoApi from "../../services/autoApi";

const CACHE_KEY = "ar_payment_terms_v1";
const CACHE_TTL_MS = 60 * 60 * 1000; // 1h — static disclosure, safe to cache.

function readCachedTerms() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { at, data } = JSON.parse(raw);
    if (!at || Date.now() - at > CACHE_TTL_MS) return null;
    return data;
  } catch { return null; }
}
function writeCachedTerms(data) {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), data })); } catch { /* quota */ }
}

/**
 * Universal payment-terms disclosure block. Renders three tiered rules:
 *   1. Base deposit NZ$1,000 for lots up to NZ$20,000
 *   2. 20% deposit if price > NZ$20,000
 *   3. 30% deposit if price > NZ$40,000
 *   4. Full payment within 24h of winning, otherwise deposit forfeited.
 *
 * Used on vehicle detail, in the bid CTA, and on /auto/fees.
 */
export default function PaymentTermsBanner({ compact = false, vehicleDeposit = null }) {
  const [terms, setTerms] = useState(() => readCachedTerms());

  useEffect(() => {
    if (terms) return; // already cached
    autoApi
      .get("/payment-terms")
      .then((r) => { setTerms(r.data); writeCachedTerms(r.data); })
      .catch(() => {});
  }, [terms]);

  if (!terms) return null;

  const tier1 = Number(terms.tier1_threshold_nzd).toLocaleString("en-NZ");
  const tier2 = Number(terms.tier2_threshold_nzd).toLocaleString("en-NZ");

  return (
    <div
      className={`payment-terms ${compact ? "payment-terms--compact" : ""}`}
      data-testid="payment-terms-banner"
    >
      <div className="payment-terms__row">
        <CreditCard size={18} className="payment-terms__icon" />
        <div>
          <div className="payment-terms__head" data-testid="payment-terms-deposit-base">
            Лоты до NZ${tier1} — депозит NZ${Number(terms.base_deposit_nzd).toLocaleString("en-NZ")}
          </div>
          <div className="payment-terms__sub auto-muted">
            Возвратный взнос для участия в торгах. Возвращаем, если вы не выиграли лот.
          </div>
        </div>
      </div>

      <div className="payment-terms__row">
        <AlertCircle size={18} className="payment-terms__icon" style={{ color: "var(--ar-warning)" }} />
        <div>
          <div className="payment-terms__head" data-testid="payment-terms-tier1">
            Лоты от NZ${tier1} — депозит {terms.tier1_percent}% от цены
          </div>
          <div className="payment-terms__sub auto-muted">
            Перед ставкой на дорогой лот нужно довнести {terms.tier1_percent}% от текущей цены.
            {vehicleDeposit && vehicleDeposit.tier === "tier1" && (
              <span data-testid="payment-terms-this-vehicle-tier1">
                {" "}Для этого лота — NZ${Number(vehicleDeposit.amount_nzd).toLocaleString("en-NZ")}.
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="payment-terms__row">
        <Diamond size={18} className="payment-terms__icon" style={{ color: "var(--ar-blue, #3a86ff)" }} />
        <div>
          <div className="payment-terms__head" data-testid="payment-terms-tier2">
            Премиум-лоты свыше NZ${tier2} — депозит {terms.tier2_percent}%
          </div>
          <div className="payment-terms__sub auto-muted">
            Для премиум-сегмента (Land Cruiser, Hilux SR5, Mercedes и т.п.) — депозит {terms.tier2_percent}% от цены.
            {vehicleDeposit && vehicleDeposit.tier === "tier2" && (
              <span data-testid="payment-terms-this-vehicle-tier2">
                {" "}Для этого лота — NZ${Number(vehicleDeposit.amount_nzd).toLocaleString("en-NZ")}.
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="payment-terms__row">
        <Clock size={18} className="payment-terms__icon" style={{ color: "var(--ar-danger)" }} />
        <div>
          <div className="payment-terms__head" data-testid="payment-terms-window">
            Полная оплата — в течение {terms.full_payment_window_hours} часов после выигрыша
          </div>
          <div className="payment-terms__sub auto-muted">
            При нарушении срока лот возвращается на аукцион, а внесённый депозит удерживается.
          </div>
        </div>
      </div>

      {!compact && (
        <div className="payment-terms__small auto-muted">
          Расчёт в ₽ по курсу на момент оплаты + 3% банковского спреда. Версия условий: {terms.version}.
        </div>
      )}
    </div>
  );
}
