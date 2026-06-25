"""Saved-search models. A saved search captures a snapshot of the catalog
filters and the user's preferred notification channels (email + Telegram).
Each filter is matched against the *new* vehicles imported since the last
run; matching vehicles are pushed through the notifier."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class SavedSearchFilters(BaseModel):
    """All fields are optional — empty filter means «любой»."""
    country: Optional[str] = None
    body_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    price_from_nzd: Optional[float] = None
    price_to_nzd: Optional[float] = None
    price_from_rub: Optional[float] = None
    price_to_rub: Optional[float] = None
    mileage_to_km: Optional[int] = None
    fuel: Optional[str] = None
    damage_only: Optional[bool] = None
    keywords: Optional[str] = None  # free-text matched against title_ru/description


class SavedSearchChannels(BaseModel):
    email: bool = True
    telegram: bool = False


class SavedSearch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    filters: SavedSearchFilters
    channels: SavedSearchChannels = Field(default_factory=SavedSearchChannels)
    email: Optional[str] = None        # snapshot at create-time for the notifier
    telegram_chat_id: Optional[int] = None
    last_run_at: Optional[datetime] = None
    last_match_ids: List[str] = Field(default_factory=list)   # dedupe window
    enabled: bool = True
    notify_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SavedSearchCreate(BaseModel):
    name: str
    filters: SavedSearchFilters
    channels: SavedSearchChannels = Field(default_factory=SavedSearchChannels)
