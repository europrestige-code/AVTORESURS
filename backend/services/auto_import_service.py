"""
BuyAnywhere Auto - vehicle importer (text / URL / CSV).

The importer is intentionally simple: it normalises raw text using the AI
extractor and constructs an AutoVehicle. URL fetching is best-effort; if the
page cannot be retrieved we instruct the admin to paste raw text.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from models.auto import (
    AutoCountry,
    AutoImageRights,
    AutoListingType,
    AutoVehicle,
    AutoVehicleStatus,
)
from services.auto_ai_service import AutoAIService

logger = logging.getLogger(__name__)


def _vehicle_from_extracted(data: Dict[str, Any], default_source: str = "manual") -> AutoVehicle:
    country = (data.get("country") or "NZ").upper()
    if country not in ("NZ", "AU"):
        country = "NZ"
    listing_type = data.get("listing_type") or "auction"
    if listing_type not in ("auction", "fixed_price", "inquiry_only"):
        listing_type = "auction"
    title_original = data.get("title_original") or ""
    return AutoVehicle(
        source=data.get("source") or default_source,
        source_url=data.get("source_url"),
        source_reference=data.get("source_reference"),
        country=AutoCountry(country),
        listing_type=AutoListingType(listing_type),
        title_original=title_original or None,
        title_ru=title_original or "Автомобиль",
        description_original=data.get("description_original"),
        make=data.get("make"),
        model=data.get("model"),
        year=int(data["year"]) if data.get("year") else None,
        mileage_km=int(data["mileage_km"]) if data.get("mileage_km") else None,
        engine=data.get("engine"),
        fuel=data.get("fuel"),
        transmission=data.get("transmission"),
        body_type=data.get("body_type"),
        location=data.get("location"),
        condition=data.get("condition"),
        damage_type=data.get("damage_type"),
        current_price_nzd=float(data["current_price_nzd"]) if data.get("current_price_nzd") else None,
        buy_now_price_nzd=float(data["buy_now_price_nzd"]) if data.get("buy_now_price_nzd") else None,
        images=data.get("images") or [],
        image_rights_status=AutoImageRights.SOURCE_PREVIEW,
        status=AutoVehicleStatus.AVAILABLE,
    )


class AutoImportService:
    def __init__(self, ai: AutoAIService):
        self.ai = ai

    async def import_from_text(self, raw_text: str, default_source: str = "manual") -> Dict[str, Any]:
        extracted = await self.ai.extract_vehicle_from_text(raw_text)
        if "error" in extracted:
            return {"ok": False, "error": extracted["error"], "raw": extracted.get("raw")}
        try:
            vehicle = _vehicle_from_extracted(extracted, default_source=default_source)
        except Exception as e:
            logger.exception("Failed to build vehicle from extraction")
            return {"ok": False, "error": f"Не удалось собрать автомобиль из ответа AI: {e}"}
        return {"ok": True, "vehicle": vehicle.model_dump(), "extracted": extracted}

    async def import_from_url(self, url: str) -> Dict[str, Any]:
        if not url or not url.startswith("http"):
            return {"ok": False, "error": "Неверный URL."}
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "BuyAnywhereAuto/1.0"})
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            logger.warning(f"URL fetch failed for {url}: {e}")
            return {
                "ok": False,
                "error": "Не удалось автоматически прочитать страницу. Вставьте текст объявления вручную.",
            }
        # Reduce HTML to text
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)[:6000]
        # Collect a handful of image URLs as a hint
        imgs: List[str] = []
        for img in soup.find_all("img"):
            src = img.get("src") or ""
            if src.startswith("http") and src not in imgs:
                imgs.append(src)
            if len(imgs) >= 6:
                break
        result = await self.import_from_text(text, default_source=url)
        if result.get("ok"):
            vehicle = result["vehicle"]
            vehicle["source_url"] = url
            if not vehicle.get("images"):
                vehicle["images"] = imgs
        return result

    async def import_from_csv(self, csv_text: str) -> Dict[str, Any]:
        """Parse a CSV with vehicle rows. Returns parsed AutoVehicle dicts (not yet inserted)."""
        if not csv_text.strip():
            return {"ok": False, "error": "Пустой CSV."}
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
        except Exception as e:
            return {"ok": False, "error": f"Ошибка парсинга CSV: {e}"}

        vehicles: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        for i, row in enumerate(rows):
            try:
                # Be permissive about types
                row_clean = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
                if row_clean.get("year"):
                    row_clean["year"] = int(float(row_clean["year"]))
                if row_clean.get("mileage_km"):
                    row_clean["mileage_km"] = int(float(row_clean["mileage_km"]))
                if row_clean.get("current_price_nzd"):
                    row_clean["current_price_nzd"] = float(row_clean["current_price_nzd"])
                if row_clean.get("buy_now_price_nzd"):
                    row_clean["buy_now_price_nzd"] = float(row_clean["buy_now_price_nzd"])
                images = row_clean.get("images")
                if isinstance(images, str) and images:
                    row_clean["images"] = [u.strip() for u in images.split("|") if u.strip()]
                vehicle = _vehicle_from_extracted(row_clean, default_source=row_clean.get("source") or "csv")
                if row_clean.get("title_ru"):
                    vehicle.title_ru = row_clean["title_ru"]
                vehicles.append(vehicle.model_dump())
            except Exception as e:
                errors.append({"row": i + 1, "error": str(e)})
        return {"ok": True, "vehicles": vehicles, "errors": errors}
