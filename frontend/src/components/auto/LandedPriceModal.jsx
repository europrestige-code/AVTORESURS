import React, { useEffect, useMemo, useState } from "react";
import { X, Calculator, AlertTriangle, Info, Loader2 } from "lucide-react";
import autoApi from "../../services/autoApi";

const RUB = (n) => (n == null ? "—" : `${Math.round(n).toLocaleString("ru-RU")} ₽`);
const NZD = (n) => (n == null ? "—" : `NZ$${Math.round(n).toLocaleString("en-NZ")}`);
const USD = (n) => (n == null ? "—" : `$${Math.round(n).toLocaleString("en-US")}`);

/**
 * LandedPriceModal — popup calculator for "под ключ во Владивостоке".
 *
 * Two modes:
 *   1) vehicleId — fetches /vehicles/{id}/landed-defaults to preset all
 *      fields (branch, condition-driven extras, fob, engine guess).
 *   2) Standalone — pass fobNzd and let the user fill the rest.
 *
 * For DAMAGED listings: non-runner + forklift + inspection are pre-on.
 * For END_OF_LIFE: scheme=parts + non-runner + forklift + dismantling on.
 */
export default function LandedPriceModal({ open, onClose, vehicleId, fallbackFobNzd }) {
  const [defaults, setDefaults] = useState(null);
  const [loadingDefaults, setLoadingDefaults] = useState(false);

  // form state
  const [fob, setFob] = useState(fallbackFobNzd || 15000);
  const [age, setAge] = useState(5);
  const [cc, setCc] = useState(2000);
  const [hp, setHp] = useState(150);
  const [type, setType] = useState("personal");
  const [scheme, setScheme] = useState("whole");
  const [branch, setBranch] = useState("");
  const [nonRunner, setNonRunner] = useState(false);
  const [inspection, setInspection] = useState(false);
  const [forklift, setForklift] = useState(false);
  const [dismantling, setDismantling] = useState(false);
  const [storageDays, setStorageDays] = useState(0);

  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  // Fetch vehicle-driven defaults
  useEffect(() => {
    if (!open) return;
    if (!vehicleId) return;
    let cancelled = false;
    (async () => {
      setLoadingDefaults(true);
      try {
        const r = await autoApi.get(`/vehicles/${vehicleId}/landed-defaults`);
        if (cancelled) return;
        const d = r.data || {};
        setDefaults(d);
        if (d.fob_nzd) setFob(d.fob_nzd);
        if (d.age_years != null) setAge(d.age_years);
        if (d.engine_cc) setCc(d.engine_cc);
        if (d.engine_hp) setHp(d.engine_hp);
        if (d.nz_branch) setBranch(d.nz_branch);
        if (d.scheme) setScheme(d.scheme);
        setNonRunner(!!d.is_non_runner);
        setInspection(!!d.inspection);
        setForklift(!!d.forklift);
        setDismantling(!!d.dismantling);
      } catch (e) {
        // non-fatal — manual entry mode
      } finally {
        if (!cancelled) setLoadingDefaults(false);
      }
    })();
    return () => { cancelled = true; };
  }, [open, vehicleId]);

  // Auto-recalculate on inputs change (debounced)
  useEffect(() => {
    if (!open) return;
    if (!fob || fob <= 0) return;
    const t = setTimeout(async () => {
      setBusy(true);
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
            nz_branch: branch || undefined,
            is_non_runner: nonRunner,
            inspection,
            forklift,
            dismantling,
            storage_days: storageDays,
          },
        });
        setResult(r.data);
      } catch (e) {
        setErr(e?.response?.data?.detail || "Ошибка расчёта");
      } finally {
        setBusy(false);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [open, fob, age, cc, hp, type, scheme, branch, nonRunner, inspection, forklift, dismantling, storageDays]);

  const overLimit = useMemo(
    () => type === "personal" && scheme === "whole" && (cc > 3000 || hp > 160),
    [type, scheme, cc, hp]
  );

  if (!open) return null;

  return (
    <div className="landed-modal__backdrop" data-testid="landed-modal" role="dialog" aria-modal="true">
      <div className="landed-modal__panel">
        <header className="landed-modal__head">
          <div className="flex items-center gap-2">
            <Calculator size={18} className="text-blue-400" />
            <h3 className="text-base font-bold text-white">
              Под ключ во Владивостоке (ориентир)
            </h3>
            <span className="ml-2 rounded-md bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-amber-300">
              ±10–15%
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
            aria-label="Закрыть"
            data-testid="landed-modal-close"
          >
            <X size={20} />
          </button>
        </header>

        <div className="landed-modal__body">
          <p className="text-xs text-gray-400">
            Цены каталога — <b className="text-white">FOB</b> (на аукционе в НЗ).
            Этот калькулятор добавляет премию аукциона, комиссию АвтоРесурс (20%),
            локальный транспорт по бранчу (×2 если не на ходу), форклифт/инспекцию/
            демонтаж при необходимости, контейнер до Владивостока (2 авто × $5 000),
            страховку и растаможку РФ.
          </p>

          {loadingDefaults && (
            <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
              <Loader2 size={14} className="animate-spin" /> Подгружаем данные авто…
            </div>
          )}

          {/* Inputs */}
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <Field label="FOB цена, NZ$">
              <input type="number" min={0} className="auto-input" value={fob}
                     onChange={(e) => setFob(Number(e.target.value))} data-testid="lm-fob" />
            </Field>
            <Field label="Откуда забираем (NZ branch / city)">
              <input className="auto-input" value={branch}
                     placeholder="например, Wellington"
                     onChange={(e) => setBranch(e.target.value)} data-testid="lm-branch" />
            </Field>
            <Field label="Возраст, лет">
              <input type="number" min={0} max={30} className="auto-input" value={age}
                     onChange={(e) => setAge(Number(e.target.value))} data-testid="lm-age" />
            </Field>
            <Field label="Объём двигателя, см³">
              <input type="number" min={0} step={100} className="auto-input" value={cc}
                     onChange={(e) => setCc(Number(e.target.value))} data-testid="lm-cc" />
            </Field>
            <Field label="Мощность, л.с.">
              <input type="number" min={0} className="auto-input" value={hp}
                     onChange={(e) => setHp(Number(e.target.value))} data-testid="lm-hp" />
            </Field>
            <Field label="Хранение, дней">
              <input type="number" min={0} className="auto-input" value={storageDays}
                     onChange={(e) => setStorageDays(Number(e.target.value))} data-testid="lm-storage" />
            </Field>
            <Field label="Кто ввозит">
              <select className="auto-select" value={type}
                      onChange={(e) => setType(e.target.value)} data-testid="lm-importer">
                <option value="personal">Физлицо (для себя)</option>
                <option value="commercial">Юрлицо / ИП</option>
              </select>
            </Field>
            <Field label="Схема">
              <select className="auto-select" value={scheme}
                      onChange={(e) => setScheme(e.target.value)} data-testid="lm-scheme">
                <option value="whole">Цельный авто (с ПТС)</option>
                <option value="parts">Запчасти: распил / конструктор</option>
              </select>
            </Field>
          </div>

          {/* Extras */}
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            <Toggle label="Не на ходу (×2 транспорт + форклифт)" checked={nonRunner}
                    onChange={setNonRunner} testid="lm-nonrunner" />
            <Toggle label="Инспекция (NZ$200)" checked={inspection}
                    onChange={setInspection} testid="lm-inspection" />
            <Toggle label="Форклифт (NZ$120)" checked={forklift || nonRunner}
                    disabled={nonRunner}
                    onChange={setForklift} testid="lm-forklift" />
            <Toggle label="Демонтаж / распил (NZ$800)" checked={dismantling}
                    onChange={setDismantling} testid="lm-dismantling" />
          </div>

          {overLimit && (
            <Warn tone="amber" testid="lm-overlimit">
              <b>Внимание:</b> {cc}&nbsp;см³ / {hp}&nbsp;л.с. превышает лимиты льготы
              утильсбора (≤3000 см³ и ≤160 л.с.) — применится коммерческая ставка,
              это +1–4 млн&nbsp;₽.
            </Warn>
          )}
          {scheme === "parts" && (
            <Warn tone="red" testid="lm-parts-warn">
              «Запчасти» (распил/конструктор) ввозятся <b>без ПТС</b>. Зарегистрировать
              такой автомобиль в ГИБДД нельзя — только донор для другого ТС.
            </Warn>
          )}

          {err && <div className="mt-3 text-sm text-red-400" data-testid="lm-error">{err}</div>}

          {result && (
            <div className="mt-5" data-testid="lm-result">
              {/* NZ block */}
              <Section title="Закупка в Новой Зеландии">
                <Row label="FOB цена аукциона" value={NZD(result.fob_nzd)} muted />
                <Row label="Премия аукциона (~10%)" value={NZD(result.nz_buyers_premium_nzd)} muted />
                <Row label="Комиссия АвтоРесурс (20%)" value={NZD(result.avtoresurs_commission_nzd)} muted />
                <Row label={`Транспорт по НЗ${result.nz_local_transport_non_runner ? " (×2 не на ходу)" : ""}`}
                     value={NZD(result.nz_local_transport_nzd)} muted />
                {result.inspection_fee_nzd > 0 && <Row label="Инспекция" value={NZD(result.inspection_fee_nzd)} muted />}
                {result.forklift_fee_nzd > 0 && <Row label="Форклифт" value={NZD(result.forklift_fee_nzd)} muted />}
                {result.dismantling_fee_nzd > 0 && <Row label="Демонтаж / распил" value={NZD(result.dismantling_fee_nzd)} muted />}
                {result.docs_fee_nzd > 0 && <Row label="Документы НЗ" value={NZD(result.docs_fee_nzd)} muted />}
                {result.storage_fee_nzd > 0 && <Row label={`Хранение (${result.storage_days} дн.)`} value={NZD(result.storage_fee_nzd)} muted />}
                <Divider />
                <Row label="Сумма NZ-расходов" value={NZD(result.nz_extras_total_nzd)} bold />
              </Section>

              {/* Freight + CIF */}
              <Section title="Фрахт и страховка">
                <Row label="Морской фрахт (1/2 контейнера)" value={USD(result.freight_usd)} muted />
                <Row label="Страховка 1.5%" value={USD(result.insurance_usd)} muted />
                <Divider />
                <Row label="CIF в РФ" value={RUB(result.cif_rub)} bold />
              </Section>

              {/* RU customs */}
              <Section title="Таможня и налоги РФ">
                <Row label="Пошлина" value={RUB(result.duty_rub)} />
                {result.excise_rub > 0 && <Row label="Акциз" value={RUB(result.excise_rub)} />}
                {result.vat_rub > 0 && <Row label="НДС 20%" value={RUB(result.vat_rub)} />}
                <Row label="Утильсбор" value={RUB(result.utilsbor_rub)}
                     highlight={result.utilsbor_rub > 100_000} />
                <Row label="Декларация" value={RUB(result.declaration_fee_rub)} muted />
                <Divider />
                <Row label="Итого таможня" value={RUB(result.customs_total_rub)} bold />
              </Section>

              <div className="mt-4 rounded-2xl bg-gradient-to-br from-blue-600/25 to-blue-600/5 p-5 ring-1 ring-blue-500/20">
                <div className="text-[11px] uppercase tracking-wider text-blue-200">
                  Ориентировочно под ключ во Владивостоке
                </div>
                <div className="mt-1 text-3xl font-black text-white" data-testid="lm-total">
                  {RUB(result.landed_total_rub)}
                </div>
                <div className="mt-1 text-sm text-gray-300">
                  ≈ {NZD(result.landed_total_nzd)} · {USD(result.landed_total_usd)}
                </div>
              </div>

              {result.notes?.length > 0 && (
                <ul className="mt-3 space-y-1.5 text-[11px] leading-relaxed text-gray-400">
                  {result.notes.map((n, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-amber-400">•</span><span>{n}</span>
                    </li>
                  ))}
                </ul>
              )}

              <div className="mt-3 text-[11px] leading-relaxed text-gray-500">
                Расчёт ориентировочный. Точные суммы зависят от заявленного VIN,
                HP, объёма, года и курсов ЦБ на дату подачи декларации. Менеджер
                АвтоРесурс подтвердит итог индивидуально.
              </div>
            </div>
          )}
          {busy && !result && <div className="mt-4 text-xs text-gray-400">Считаем…</div>}
        </div>
      </div>
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

function Toggle({ label, checked, onChange, testid, disabled }) {
  return (
    <label className={`flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-sm ${disabled ? "opacity-60" : "cursor-pointer hover:bg-white/[0.06]"}`}>
      <input
        type="checkbox"
        checked={!!checked}
        disabled={disabled}
        onChange={(e) => onChange?.(e.target.checked)}
        data-testid={testid}
      />
      <span>{label}</span>
    </label>
  );
}

function Section({ title, children }) {
  return (
    <div className="mt-4 rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{title}</div>
      {children}
    </div>
  );
}

function Row({ label, value, muted, bold, highlight }) {
  return (
    <div className={`flex items-center justify-between py-1 text-sm ${muted ? "text-gray-400" : "text-gray-100"} ${bold ? "font-bold text-white" : ""} ${highlight ? "text-amber-300" : ""}`}>
      <span>{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

function Divider() { return <div className="my-1 border-t border-white/5" />; }

function Warn({ children, tone = "amber", testid }) {
  const cls = tone === "red"
    ? "border-red-500/40 bg-red-500/10 text-red-200"
    : "border-amber-500/40 bg-amber-500/10 text-amber-200";
  const Icon = tone === "red" ? Info : AlertTriangle;
  return (
    <div className={`mt-3 flex items-start gap-2 rounded-lg border p-3 text-xs ${cls}`} data-testid={testid}>
      <Icon size={16} className="mt-0.5 shrink-0" />
      <div>{children}</div>
    </div>
  );
}
