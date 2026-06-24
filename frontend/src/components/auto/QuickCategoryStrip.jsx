import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";
import {
  Car,           // Cars / Auctions
  Wrench,        // Damaged
  Recycle,       // End of Life / Donor
  CreditCard,    // Buy Now
  CalendarDays,  // Auctions calendar
  Bike,          // Motorbikes
  Anchor,        // Boats / Marine
  Truck,         // Trucks & machinery
  Bus,           // Buses & motorhomes
  Cog,           // Parts
} from "lucide-react";

/**
 * Horizontal strip of category quick-filters at the top of every /auto page.
 * Each tile has a real SVG icon + a live count fetched from /catalog-summary.
 * Items marked `soon: true` render greyed-out with a "скоро" pill.
 */
const ITEMS = [
  { key: "auctions",  label: "Аукционы",       to: "/auto/auctions-list",  Icon: Car,         countKey: "auctions" },
  { key: "buynow",    label: "Купить сейчас",  to: "/auto/buynow",         Icon: CreditCard,  countKey: "buynow" },
  { key: "damaged",   label: "Повреждённые",   to: "/auto/damaged",        Icon: Wrench,      countKey: "damaged" },
  { key: "eol",       label: "End of Life",    to: "/auto/end-of-life",    Icon: Recycle,     countKey: "eol" },
  { key: "calendar",  label: "Календарь",      to: "/auto/auctions",       Icon: CalendarDays },
  { key: "moto",      label: "Мотоциклы",      Icon: Bike,                 soon: true },
  { key: "boats",     label: "Лодки и катера", Icon: Anchor,               soon: true },
  { key: "trucks",    label: "Грузовики",      Icon: Truck,                soon: true },
  { key: "buses",     label: "Автодома",       Icon: Bus,                  soon: true },
  { key: "parts",     label: "Запчасти",       to: "/auto/parts",          Icon: Cog,         soon: true },
];

export default function QuickCategoryStrip() {
  const navigate = useNavigate();
  const [counts, setCounts] = useState({});

  useEffect(() => {
    autoApi.get("/catalog-summary").then((r) => {
      const s = r.data || {};
      const byListing = Object.fromEntries((s.listing_types || []).map((x) => [x.value, x.count]));
      // Compute approx category counts from the summary
      setCounts({
        auctions: byListing["auction"] || 0,
        buynow: byListing["fixed_price"] || 0,
        // damaged + eol counts come from a separate aggregation if available
        damaged: s.damaged_count,
        eol: s.eol_count,
      });
    }).catch(() => {});
  }, []);

  return (
    <nav className="qcs" data-testid="quick-category-strip" aria-label="Категории">
      <div className="qcs__inner">
        {ITEMS.map((it) => {
          const Icon = it.Icon;
          const count = counts[it.countKey];
          const onClick = () => {
            if (it.soon) return;
            if (it.to) navigate(it.to);
          };
          const Cmp = it.soon ? "button" : NavLink;
          const cmpProps = it.soon
            ? { type: "button", onClick, disabled: true }
            : { to: it.to, className: ({ isActive }) => `qcs__item ${isActive ? "qcs__item--active" : ""}` };
          return (
            <Cmp
              key={it.key}
              {...cmpProps}
              className={typeof cmpProps.className === "function" ? cmpProps.className : `qcs__item ${it.soon ? "qcs__item--soon" : ""}`}
              data-testid={`qcs-${it.key}`}
            >
              <span className="qcs__icon" aria-hidden>
                <Icon size={22} strokeWidth={1.7} />
              </span>
              <span className="qcs__label">{it.label}</span>
              {typeof count === "number" && count > 0 && (
                <span className="qcs__count" data-testid={`qcs-count-${it.key}`}>{count}</span>
              )}
              {it.soon && <span className="qcs__badge">скоро</span>}
            </Cmp>
          );
        })}
      </div>
    </nav>
  );
}
