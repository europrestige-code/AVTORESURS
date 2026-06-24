import React, { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import autoApi from "../../services/autoApi";
import {
  CalendarDays,
  Bike,
  Anchor,
  Truck,
  Bus,
  Cog,
} from "lucide-react";

/**
 * Horizontal strip of category quick-filters at the top of every /auto page.
 *
 * The four "live" categories (Аукционы, Купить сейчас, Повреждённые,
 * Списанные авто) use a real photo background so the strip looks like a
 * premium SaaS instead of a row of generic icons. The remaining tiles
 * (Календарь + future verticals) keep the lucide icon look.
 */
const ITEMS = [
  {
    key: "auctions",
    label: "Аукционы",
    to: "/auto/auctions-list",
    countKey: "auctions",
    photo:
      "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=600&auto=format&fit=crop",
  },
  {
    key: "buynow",
    label: "Купить сейчас",
    to: "/auto/buynow",
    countKey: "buynow",
    photo:
      "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?q=80&w=600&auto=format&fit=crop",
  },
  {
    key: "damaged",
    label: "Повреждённые",
    to: "/auto/damaged",
    countKey: "damaged",
    photo:
      "https://images.pexels.com/photos/3608542/pexels-photo-3608542.jpeg?cs=srgb&w=600", // damaged late-model car
  },
  {
    key: "eol",
    label: "Списанные авто",
    to: "/auto/end-of-life",
    countKey: "eol",
    photo:
      "https://images.pexels.com/photos/210019/pexels-photo-210019.jpeg?cs=srgb&w=600", // abandoned/scrap car
  },
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
      setCounts({
        auctions: byListing["auction"] || 0,
        buynow: byListing["fixed_price"] || 0,
        damaged: s.damaged_count,
        eol: s.eol_count,
      });
    }).catch(() => {});
  }, []);

  return (
    <nav className="qcs" data-testid="quick-category-strip" aria-label="Категории">
      <div className="qcs__inner">
        {ITEMS.map((it) => {
          const count = counts[it.countKey];
          const onClick = () => { if (!it.soon && it.to) navigate(it.to); };
          const hasPhoto = !!it.photo;

          if (it.soon || !hasPhoto) {
            const Icon = it.Icon;
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
                  {Icon && <Icon size={22} strokeWidth={1.7} />}
                </span>
                <span className="qcs__label">{it.label}</span>
                {typeof count === "number" && count > 0 && (
                  <span className="qcs__count" data-testid={`qcs-count-${it.key}`}>{count}</span>
                )}
                {it.soon && <span className="qcs__badge">скоро</span>}
              </Cmp>
            );
          }

          // Photo-backed tile
          return (
            <NavLink
              key={it.key}
              to={it.to}
              className={({ isActive }) => `qcs__photo ${isActive ? "qcs__photo--active" : ""}`}
              data-testid={`qcs-${it.key}`}
            >
              <img src={it.photo} alt={it.label} loading="lazy" />
              <span className="qcs__photo__shade" />
              <span className="qcs__photo__body">
                <span className="qcs__photo__label">{it.label}</span>
                {it.sub && <span className="qcs__photo__sub">{it.sub}</span>}
              </span>
              {typeof count === "number" && count > 0 && (
                <span className="qcs__photo__count" data-testid={`qcs-count-${it.key}`}>{count}</span>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
