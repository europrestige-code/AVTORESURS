"""AutoResource (АвтоРесурс) router package.

Splits the formerly 1900-line `auto_routes.py` into themed sub-routers.
Importers should keep using `from routes.auto_routes import router` — that
module simply re-exports the aggregated router built here.
"""
from fastapi import APIRouter

from . import chat_quiz, engagement, admin_crm

router = APIRouter(prefix="/api/auto", tags=["Auto"])
router.include_router(chat_quiz.router)
router.include_router(engagement.router)
router.include_router(admin_crm.router)

__all__ = ["router"]
