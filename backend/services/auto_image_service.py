"""
АвтоРесурс — image branding service.

Goal: keep clean attribution to source auctions (Turners, Manheim, Pickles)
while presenting all photos inside an AvtoResurs branded frame so the
catalogue looks coherent to clients.

This service DOES NOT remove third-party watermarks from source photos.
That would be legally risky and is explicitly forbidden by the project PRD.

Instead, it:
  1. downloads the source image,
  2. resizes it to a sensible max-edge,
  3. composites an "АвтоРесурс" header strip + a "Источник: …" footer
     attribution onto the image,
  4. writes the result to /app/backend/uploads/branded/<vehicle_id>-<i>.jpg
     and returns a relative URL that the catalog can serve.

Branded images become part of vehicle.local_images and the catalog will
prefer local_images over source_images when both are present.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
from typing import List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "branded")
MAX_EDGE = 1280
HEADER_H = 56
FOOTER_H = 44
BRAND_BLUE = (0, 102, 255)
BLACK = (11, 11, 11)
WHITE = (255, 255, 255)
MUTED = (160, 160, 160)


def _font(size: int) -> ImageFont.ImageFont:
    """Try to use a real TTF; fall back to PIL default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _font_regular(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _fit(image: Image.Image, max_edge: int) -> Image.Image:
    w, h = image.size
    long_edge = max(w, h)
    if long_edge <= max_edge:
        return image
    ratio = max_edge / float(long_edge)
    return image.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)


def brand_image(
    src_bytes: bytes,
    source_label: str = "",
    vehicle_title: Optional[str] = None,
) -> bytes:
    """Compose a branded JPEG. Returns binary content."""
    src = Image.open(io.BytesIO(src_bytes)).convert("RGB")
    src = _fit(src, MAX_EDGE)
    sw, sh = src.size
    canvas = Image.new("RGB", (sw, sh + HEADER_H + FOOTER_H), BLACK)
    # Header band
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, sw, HEADER_H], fill=BLACK)
    # Logo monogram + wordmark
    monogram_font = _font(32)
    wordmark_font = _font(22)
    tagline_font = _font_regular(11)
    # AR monogram in blue square
    pad = 12
    box = HEADER_H - pad * 2
    draw.rounded_rectangle([pad, pad, pad + box, pad + box], radius=8, fill=BRAND_BLUE)
    # measure 'АР' to center it inside the box
    txt = "АР"
    try:
        bb = draw.textbbox((0, 0), txt, font=monogram_font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((pad + (box - tw) / 2, pad + (box - th) / 2 - 2), txt, fill=WHITE, font=monogram_font)
    except Exception:
        draw.text((pad + 6, pad + 4), txt, fill=WHITE, font=monogram_font)
    # Wordmark text "АВТОРЕСУРС"
    wm_x = pad + box + 12
    draw.text((wm_x, 12), "АВТО", fill=WHITE, font=wordmark_font)
    # Compute width of "АВТО" for offset
    try:
        bb = draw.textbbox((0, 0), "АВТО", font=wordmark_font)
        wm_off = bb[2] - bb[0] + 2
    except Exception:
        wm_off = 56
    draw.text((wm_x + wm_off, 12), "РЕСУРС", fill=BRAND_BLUE, font=wordmark_font)
    # Tagline
    draw.text((wm_x, 38), "АВТОМОБИЛИ СО ВСЕГО МИРА", fill=MUTED, font=tagline_font)

    # Vehicle title (right of header)
    if vehicle_title:
        try:
            tf = _font_regular(13)
            t = vehicle_title[:60]
            bb = draw.textbbox((0, 0), t, font=tf)
            tw = bb[2] - bb[0]
            draw.text((sw - tw - 14, 22), t, fill=MUTED, font=tf)
        except Exception:
            pass

    # Image
    canvas.paste(src, (0, HEADER_H))

    # Footer band
    draw.rectangle([0, HEADER_H + sh, sw, HEADER_H + sh + FOOTER_H], fill=BLACK)
    ff = _font_regular(13)
    label = "Покупка через АвтоРесурс. " + (f"Источник: {source_label}" if source_label else "Источник: партнёрский аукцион")
    draw.text((14, HEADER_H + sh + 14), label, fill=MUTED, font=ff)
    site = "avtoresurs · buyanywhere.ru/auto"
    try:
        bb = draw.textbbox((0, 0), site, font=ff)
        tw = bb[2] - bb[0]
        draw.text((sw - tw - 14, HEADER_H + sh + 14), site, fill=BRAND_BLUE, font=ff)
    except Exception:
        pass

    out = io.BytesIO()
    canvas.save(out, "JPEG", quality=82, optimize=True)
    return out.getvalue()


async def _download(url: str) -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True,
                                     headers={"User-Agent": "AvtoResursBot/1.0"}) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.content
    except Exception as e:
        logger.warning(f"Download failed for {url}: {e}")
        return None


async def brand_vehicle_images(
    image_urls: List[str],
    vehicle_id: str,
    source_label: str = "",
    vehicle_title: Optional[str] = None,
) -> List[str]:
    """Download each URL, brand it, save locally. Returns list of relative paths."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    out: List[str] = []
    for i, url in enumerate(image_urls):
        data = await _download(url)
        if not data:
            continue
        try:
            branded = await asyncio.to_thread(
                brand_image, data, source_label, vehicle_title
            )
        except Exception as e:
            logger.warning(f"Branding failed for vehicle={vehicle_id} url={url}: {e}")
            continue
        fname = f"{vehicle_id}-{i}.jpg"
        fpath = os.path.join(UPLOAD_DIR, fname)
        with open(fpath, "wb") as f:
            f.write(branded)
        out.append(f"/uploads/branded/{fname}")
    return out
