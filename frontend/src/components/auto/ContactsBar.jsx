import React from "react";
import { Phone, MessageCircle, Send, Mail, MapPin, Clock } from "lucide-react";

const PHONE_NZ = "+64 210 809 4550";
const PHONE_RU = "+7 913 512 1934";
const EMAIL = "europrestige@gmail.com";
const WHATSAPP_URL = "https://wa.me/6421425233";
const WHATSAPP_LABEL = "WhatsApp +64 21 425 233";
const TELEGRAM_URL = "https://t.me/avtoresurs";

/**
 * ContactsBar — sliding contact strip that always sits at the top of the
 * site. Two variants:
 *   • header  → animated marquee track (CSS keyframes) on a solid dark
 *               background — never transparent, never overlapping the logo.
 *   • footer  → static block grid for the footer.
 */
export default function ContactsBar({ variant = "header" }) {
  if (variant === "footer") {
    return (
      <div className="grid gap-3 text-sm text-gray-300 sm:grid-cols-2" data-testid="contacts-footer">
        <Item icon={Phone} label="NZ" value={PHONE_NZ} href={`tel:${PHONE_NZ.replace(/\s/g, "")}`} />
        <Item icon={Phone} label="RU" value={PHONE_RU} href={`tel:${PHONE_RU.replace(/\s/g, "")}`} />
        <Item icon={Mail} value={EMAIL} href={`mailto:${EMAIL}`} />
        <Item icon={MessageCircle} value={WHATSAPP_LABEL} href={WHATSAPP_URL} accent="#25D366" />
        <Item icon={Send} value="Telegram" href={TELEGRAM_URL} accent="#229ED9" />
        <Item icon={MapPin} value="Auckland, New Zealand" />
        <Item icon={Clock} value="Пн–Пт 9:00–18:00 NZDT" />
      </div>
    );
  }

  // header — repeating marquee track so the bar visibly slides
  const items = [
    { icon: Phone,          text: PHONE_NZ,          href: `tel:${PHONE_NZ.replace(/\s/g, "")}` },
    { icon: MessageCircle,  text: WHATSAPP_LABEL,    href: WHATSAPP_URL,                       accent: "#25D366" },
    { icon: Send,           text: "Telegram",        href: TELEGRAM_URL,                       accent: "#229ED9" },
    { icon: Mail,           text: EMAIL,             href: `mailto:${EMAIL}` },
    { icon: MapPin,         text: "Auckland, NZ" },
    { icon: Clock,          text: "Пн–Пт 9–18 NZDT" },
  ];
  // Render twice in the same track so the slide loop is seamless.
  return (
    <div className="ar-contacts-marquee" data-testid="contacts-header">
      <div className="ar-contacts-marquee__track" aria-hidden={false}>
        {[0, 1].map((dup) => (
          <div key={dup} className="ar-contacts-marquee__chunk">
            {items.map((it, i) => (
              <Inline key={`${dup}-${i}`} {...it} />
            ))}
          </div>
        ))}
      </div>
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
  return href ? (
    <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noreferrer">{inner}</a>
  ) : inner;
}

function Item({ icon: Icon, label, value, href, accent }) {
  const text = label ? `${label}: ${value}` : value;
  const inner = (
    <div className="flex items-center gap-2">
      <Icon size={14} style={accent ? { color: accent } : { color: "var(--ar-blue-hover)" }} />
      <span>{text}</span>
    </div>
  );
  return href ? (
    <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="transition hover:text-white">{inner}</a>
  ) : inner;
}
