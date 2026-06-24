import React, { useEffect, useState } from "react";
import { MessageCircle, Phone } from "lucide-react";
import autoApi from "../../services/autoApi";

export default function ContactsBar({ variant = "header" }) {
  const [c, setC] = useState(null);
  useEffect(() => { autoApi.get("/contacts").then((r) => setC(r.data)).catch(() => {}); }, []);
  if (!c) return null;
  const Wa = (
    <a
      href={`https://wa.me/${c.whatsapp_raw.replace(/[^0-9]/g, "")}`}
      target="_blank"
      rel="noopener noreferrer"
      className="contacts-link contacts-link--wa"
      data-testid="contacts-whatsapp"
      title="WhatsApp"
    >
      <MessageCircle size={14} strokeWidth={2} />
      <span>WhatsApp {c.whatsapp}</span>
    </a>
  );
  const Nz = (
    <a href={`tel:${c.phone_nz_raw}`} className="contacts-link" data-testid="contacts-phone-nz" title="Звонок NZ">
      <Phone size={14} strokeWidth={2} />
      <span>NZ {c.phone_nz}</span>
    </a>
  );
  const Ru = (
    <a href={`tel:${c.phone_ru_raw}`} className="contacts-link contacts-link--ru" data-testid="contacts-phone-ru" title="Звонок RUS">
      <Phone size={14} strokeWidth={2} />
      <span>RUS {c.phone_ru}</span>
    </a>
  );
  return (
    <div className={`contacts-bar contacts-bar--${variant}`} data-testid="contacts-bar">
      {Wa}
      {Nz}
      {Ru}
    </div>
  );
}
