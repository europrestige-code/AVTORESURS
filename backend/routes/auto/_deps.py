"""Shared dependencies for the AutoResource (АвтоРесурс) sub-routers.

Lives in a tiny module so that every sub-router file imports the same DI
helpers without re-running them or causing circular imports with
`auto_routes.py`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.auth_service import AuthService
from services.auto_ai_service import AutoAIService
from services.auto_import_service import AutoImportService
from services.auto_service import AutoService

security = HTTPBearer(auto_error=False)
auth_service = AuthService()


async def get_db():
    from server import db
    return db


async def get_auto_service(db=Depends(get_db)) -> AutoService:
    return AutoService(db)


async def get_engagement_service(db=Depends(get_db)):
    from services.auto_engagement_service import AutoEngagementService
    return AutoEngagementService(db)


_ai_service = AutoAIService()


def get_ai_service() -> AutoAIService:
    return _ai_service


def get_import_service() -> AutoImportService:
    return AutoImportService(_ai_service)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    try:
        payload = auth_service.verify_token(credentials.credentials)
    except HTTPException:
        return None
    user = await db.users.find_one({"id": payload.get("user_id")})
    if not user:
        return None
    user.pop("_id", None)
    return user


async def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(401, "Требуется авторизация.")
    payload = auth_service.verify_token(credentials.credentials)
    user = await db.users.find_one({"id": payload.get("user_id")})
    if not user:
        raise HTTPException(401, "Пользователь не найден.")
    user.pop("_id", None)
    return user


async def require_admin(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
    x_admin_mfa_token: Optional[str] = Header(default=None, alias="X-Admin-MFA-Token"),
) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(403, "Требуются права администратора.")
    # If the admin enabled 2FA, all admin requests must carry a valid
    # X-Admin-MFA-Token issued by /auto/admin/2fa/login.
    if user.get("auto_totp_enabled"):
        from services.auto_admin_2fa import verify_mfa_token
        payload = verify_mfa_token(x_admin_mfa_token) if x_admin_mfa_token else None
        if not payload or payload.get("uid") != user["id"]:
            raise HTTPException(401, "Требуется код двухфакторной аутентификации.")
    return user
