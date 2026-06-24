import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import autoApi from "../../services/autoApi";
import VehicleCard from "../../components/auto/VehicleCard";

export default function AutoAustralia() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    autoApi
      .get("/vehicles", { params: { country: "AU", limit: 24 } })
      .then((r) => setItems(r.data.items || []))
      .catch(() => setItems([]));
  }, []);

  return (
    <div className="auto-section">
      <div className="auto-card auto-hero" style={{ marginBottom: 18 }}>
        <h1 style={{ fontSize: 28, margin: 0 }}>Автомобили из Австралии — по запросу</h1>
        <p className="auto-muted" style={{ maxWidth: 700, marginTop: 8 }}>
          В австралийском разделе ставки не принимаются. Вы можете запросить цену, предложить свою цену,
          либо мы найдём похожий автомобиль в Новой Зеландии. Депозит не требуется для заявок.
        </p>
        <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
          <Link to="/auto/catalog?country=NZ" className="auto-btn">Перейти к каталогу NZ</Link>
        </div>
      </div>
      <h2 style={{ fontSize: 22 }}>Доступные автомобили (AU)</h2>
      {items.length === 0 ? (
        <div className="auto-card auto-muted" data-testid="au-empty">Сейчас ничего не выставлено.</div>
      ) : (
        <div className="auto-grid" data-testid="au-grid">
          {items.map((v) => <VehicleCard key={v.id} vehicle={v} />)}
        </div>
      )}
    </div>
  );
}
