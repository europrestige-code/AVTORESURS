import React from "react";
import { Phone, MessageCircle, Send, Mail, MapPin, Clock } from "lucide-react";

const PHONE_NZ = "+64 21 425 233";
const PHONE_RU = "+7 913 512 1934";
const EMAIL = "europrestige@gmail.com";
const WHATSAPP_URL = "https://wa.me/6421425233";
const TELEGRAM_URL = "https://t.me/avtoresurs";

/**
 * ContactsBar — thin top bar with phones, email, messengers, office, hours.
 * Two variants: header (small inline) and footer (block).
 */
export default function ContactsBar({ variant = "header" }) {
  if (variant === "footer") {
    return (
      <div className="grid gap-3 text-sm text-gray-300 sm:grid-cols-2" data-testid="contacts-footer">
        <Item icon={Phone} label="NZ" value={PHONE_NZ} href={`tel:${PHONE_NZ.replace(/\s/g, "")}`} />
        <Item icon={Phone} label="RU" value={PHONE_RU} href={`tel:${PHONE_RU.replace(/\s/g, "")}`} />
        <Item icon={Mail} value={EMAIL} href={`mailto:${EMAIL}`} />
        <Item icon={MessageCircle} value="WhatsApp" href={WHATSAPP_URL} accent="#25D366" />
        <Item icon={Send} value="Telegram" href={TELEGRAM_URL} accent="#229ED9" />
        <Item icon={MapPin} value="Auckland, New Zealand" />
        <Item icon={Clock} value="Пн–Пт 9:00–18:00 NZDT" />
      </div>
    );
  }
  // header — single line, compact, hidden on mobile
  return (
    <div className="hidden flex-wrap items-center justify-end gap-x-5 gap-y-1 text-[11px] text-gray-300 md:flex" data-testid="contacts-header">
      <Inline icon={Phone} text={PHONE_NZ} href={`tel:${PHONE_NZ.replace(/\s/g, "")}`} />
      <Inline icon={MessageCircle} text="WhatsApp" href={WHATSAPP_URL} accent="#25D366" />
      <Inline icon={Send} text="Telegram" href={TELEGRAM_URL} accent="#229ED9" />
      <Inline icon={Mail} text={EMAIL} href={`mailto:${EMAIL}`} />
      <Inline icon={MapPin} text="Auckland, NZ" />
      <Inline icon={Clock} text="Пн–Пт 9–18 NZDT" />
    </div>
  );
}

function Inline({ icon: Icon, text, href, accent }) {
  const inner = (
    <span className="inline-flex items-center gap-1.5 transition hover:text-white">
      <Icon size={12} style={accent ? { color: accent } : undefined} />
      <span>{text}</span>
    </span>
  );
  return href ? <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noreferrer">{inner}</a> : inner;
}

function Item({ icon: Icon, label, value, href, accent }) {
  const text = label ? `${label}: ${value}` : value;
  const inner = (
    <div className="flex items-center gap-2">
      <Icon size={14} style={accent ? { color: accent } : { color: "#3385FF" }} />
      <span>{text}</span>
    </div>
  );
  return href ? (
    <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="transition hover:text-white">{inner}</a>
  ) : inner;
}
