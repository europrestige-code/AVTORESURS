import React, { useEffect, useMemo, useState } from "react";
import { Calculator, AlertTriangle, Info } from "lucide-react";
import autoApi from "../../services/autoApi";

const RUB = (n) =>
  n == null ? "—" : `${Math.round(n).toLocaleString("ru-RU")} ₽`;
const NZD = (n) =>
  n == null ? "—" : `NZ$${Math.round(n).toLocaleString("ru-RU")}`;
const USD = (n) =>
  n == null ? "—" : `$${Math.round(n).toLocaleString("ru-RU")}`;

/**
 * RuCustomsCalculator — приблизительная стоимость "под ключ" в РФ
 * на основе FOB цены аукциона в НЗ + контейнерная доставка + растаможка.
 *
 * Props:
 *   fobNzd       — стартовая FOB цена (например текущая ставка лота)
 *   defaults     — { age_years, engine_cc, engine_hp }
 *   variant      — 'card' (для VehicleDetail) | 'page' (для отдельной страницы)
 */
export default function RuCustomsCalculator({
  fobNzd = 15000,
  defaults = {},
  variant = "card",
}) {
  const [fob, setFob] = useState(fobNzd);
  const [age, setAge] = useState(defaults.age_years ?? 5);
  const [cc, setCc] = useState(defaults.engine_cc ?? 2000);
  const [hp, setHp] = useState(defaults.engine_hp ?? 150);
  const [type, setType] = useState("personal");
  const [scheme, setScheme] = useState("whole");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { setFob(fobNzd); }, [fobNzd]);

  // Debounced auto-calc on any input change
  useEffect(() => {
    const t = setTimeout(async () => {
      if (!fob || fob <= 0) return;
      setLoading(true);
      setErr(null);
      try {
        const r = await autoApi.get("/ru-customs/calc", {
          params: {
            fob_nzd: fob,
            age_years: age,
            engine_cc: cc,
            engine_hp: hp,
            importer_type: type,
            scheme,
          },
        });
        setData(r.data);
      } catch (e) {
        setErr(e?.response?.data?.detail || "Ошибка расчёта");
      } finally {
        setLoading(false);
      }
    }, 350);
    return () => clearTimeout(t);
  }, [fob, age, cc, hp, type, scheme]);

  const overLimit = useMemo(() =>
    type === "personal" && scheme === "whole" && (cc > 3000 || hp > 160),
    [type, scheme, cc, hp]
  );

  return (
    <div
      className="rounded-2xl border border-white/10 bg-[#0D111A] p-5"
      data-testid="ru-customs-calc"
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 text-lg font-bold text-white">
          <Calculator size={18} className="text-blue-400" />
          Под ключ в РФ (ориентир)
        </h3>
        <span className="rounded-md bg-amber-500/15 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-amber-300">
          ± 10–15%
        </span>
      </div>
      <p className="mt-1 text-xs text-gray-400">
        Цена аукциона — <b className="text-white">FOB</b> (без доставки и
        растаможки). Расчёт ниже добавляет: премию аукциона, локальный
        транспорт в НЗ, контейнер до Владивостока (2 авто × $5 000),
        страховку, пошлину, НДС, акциз и утильсбор по правилам РФ.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field label="FOB цена, NZ$">
          <input
            type="number"
            min={0}
            className="auto-input"
            value={fob}
            onChange={(e) => setFob(Number(e.target.value))}
            data-testid="calc-fob"
          />
        </Field>
        <Field label="Возраст, лет">
          <input
            type="number"
            min={0}
            max={30}
            className="auto-input"
            value={age}
            onChange={(e) => setAge(Number(e.target.value))}
            data-testid="calc-age"
          />
        </Field>
        <Field label="Объём двигателя, см³">
          <input
            type="number"
            min={0}
            step={100}
            className="auto-input"
            value={cc}
            onChange={(e) => setCc(Number(e.target.value))}
            data-testid="calc-cc"
          />
        </Field>
        <Field label="Мощность, л.с.">
          <input
            type="number"
            min={0}
            className="auto-input"
            value={hp}
            onChange={(e) => setHp(Number(e.target.value))}
            data-testid="calc-hp"
          />
        </Field>
        <Field label="Кто ввозит">
          <select
            className="auto-select"
            value={type}
            onChange={(e) => setType(e.target.value)}
            data-testid="calc-importer"
          >
            <option value="personal">Физлицо (для себя)</option>
            <option value="commercial">Юрлицо / ИП</option>
          </select>
        </Field>
        <Field label="Схема">
          <select
            className="auto-select"
            value={scheme}
            onChange={(e) => setScheme(e.target.value)}
            data-testid="calc-scheme"
          >
            <option value="whole">Цельный авто (с ПТС)</option>
            <option value="parts">Запчасти: распил / конструктор</option>
          </select>
        </Field>
      </div>

      {overLimit && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200" data-testid="calc-overlimit">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <div>
            <b>Внимание:</b> двигатель {cc}&nbsp;см³ / {hp}&nbsp;л.с. превышает
            пороги льготы (≤3000&nbsp;см³ и ≤160&nbsp;л.с.). Утильсбор будет
            рассчитан по коммерческой ставке — это +1–4&nbsp;млн&nbsp;₽
            (~$10–40&nbsp;тыс).
          </div>
        </div>
      )}

      {scheme === "parts" && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200" data-testid="calc-parts-warn">
          <Info size={16} className="mt-0.5 shrink-0" />
          <div>
            «Запчасти» (распил/конструктор) ввозятся <b>без ПТС</b>. Зарегистрировать
            такой автомобиль в ГИБДД нельзя — только как донор для другого ТС.
          </div>
        </div>
      )}

      {loading && <div className="mt-4 text-xs text-gray-400">Считаем…</div>}
      {err && <div className="mt-4 text-sm text-red-400" data-testid="calc-error">{err}</div>}

      {data && !err && (
        <div className="mt-5" data-testid="calc-result">
          <Row label="FOB цена (НЗ)" value={NZD(data.fob_nzd)} muted />
          <Row label="Премия аукциона (10%)" value={NZD(data.nz_buyers_premium_nzd)} muted />
          <Row label="Локальный транспорт (НЗ)" value={NZD(data.nz_local_transport_nzd)} muted />
          <Row label="Морской фрахт (1/2 контейнера)" value={USD(data.freight_usd)} muted />
          <Row label="Страховка (1.5%)" value={USD(data.insurance_usd)} muted />
          <Divider />
          <Row label="CIF в РФ" value={RUB(data.cif_rub)} bold />
          <Divider />
          <Row label="Пошлина" value={RUB(data.duty_rub)} />
          {data.excise_rub > 0 && <Row label="Акциз" value={RUB(data.excise_rub)} />}
          {data.vat_rub > 0 && <Row label="НДС 20%" value={RUB(data.vat_rub)} />}
          <Row
            label="Утильсбор"
            value={RUB(data.utilsbor_rub)}
            highlight={data.utilsbor_rub > 100000}
          />
          <Row label="Декларация" value={RUB(data.declaration_fee_rub)} muted />
          <Divider />
          <Row label="Итого таможня" value={RUB(data.customs_total_rub)} bold />
          <Divider />
          <div className="mt-3 rounded-xl bg-gradient-to-br from-blue-600/20 to-blue-600/5 p-4">
            <div className="text-xs text-blue-200">
              ОРИЕНТИРОВОЧНО ПОД КЛЮЧ ВО ВЛАДИВОСТОКЕ
            </div>
            <div className="mt-1 text-3xl font-black text-white" data-testid="calc-total">
              {RUB(data.landed_total_rub)}
            </div>
            <div className="mt-1 text-sm text-gray-300">
              ≈ {NZD(data.landed_total_nzd)} · {USD(data.landed_total_usd)}
            </div>
          </div>

          {data.notes?.length > 0 && (
            <ul className="mt-3 space-y-1.5 text-[11px] leading-relaxed text-gray-400">
              {data.notes.map((n, i) => (
                <li key={i} className="flex gap-1.5">
                  <span className="text-amber-400">•</span>
                  <span>{n}</span>
                </li>
              ))}
            </ul>
          )}

          <div className="mt-3 text-[11px] leading-relaxed text-gray-500">
            Расчёт ориентировочный. Точные суммы зависят от заявленного VIN,
            HP, объёма, года выпуска и курсов ЦБ на дату подачи декларации.
            Менеджер АвтоРесурс подтвердит итог индивидуально.
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block text-xs">
      <span className="mb-1 block uppercase tracking-wider text-gray-500">{label}</span>
      {children}
    </label>
  );
}

function Row({ label, value, muted, bold, highlight }) {
  return (
    <div
      className={`flex items-center justify-between py-1.5 text-sm ${
        muted ? "text-gray-400" : "text-gray-100"
      } ${bold ? "font-bold text-white" : ""} ${highlight ? "text-amber-300" : ""}`}
    >
      <span>{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

function Divider() {
  return <div className="my-1 border-t border-white/5" />;
}
