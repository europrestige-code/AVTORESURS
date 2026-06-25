"""Admin 2FA (TOTP) endpoints — setup, verify, disable, exchange-code-for-token,
status. All require a logged-in admin (basic JWT). The MFA-token gate sits
inside `require_admin` so EVERY other admin endpoint is automatically
protected once 2FA is enabled.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException

from ._deps import get_db, require_user

router = APIRouter()


def _ensure_admin(user: Dict[str, Any]) -> None:
    if user.get("role") != "admin":
        raise HTTPException(403, "Требуются права администратора.")


@router.get("/admin/2fa/status")
async def admin_2fa_status(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    _ensure_admin(user)
    from services.auto_admin_2fa import Admin2FAService
    return await Admin2FAService(db).status(user["id"])


@router.post("/admin/2fa/setup")
async def admin_2fa_setup(
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    """Generate a new TOTP secret + provisioning URI + QR data-URL. The
    secret is stored as 'pending' until the admin verifies the first code."""
    _ensure_admin(user)
    from services.auto_admin_2fa import Admin2FAService
    return await Admin2FAService(db).start_setup(user["id"], user.get("email") or user["id"])


@router.post("/admin/2fa/verify-setup")
async def admin_2fa_verify_setup(
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    """Verify the first 6-digit code from the authenticator app and flip
    `auto_totp_enabled=True`. After this call all admin endpoints will
    require X-Admin-MFA-Token."""
    _ensure_admin(user)
    code = (payload.get("code") or "").strip()
    from services.auto_admin_2fa import Admin2FAService, issue_mfa_token
    ok = await Admin2FAService(db).verify_and_enable(user["id"], code)
    if not ok:
        raise HTTPException(400, "Неверный код. Попробуйте новый код из приложения.")
    # Issue the first MFA token so the admin doesn't get kicked out of the panel.
    return {"ok": True, "mfa_token": issue_mfa_token(user["id"])}


@router.post("/admin/2fa/login")
async def admin_2fa_login(
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    """Exchange a fresh OTP for a short-lived (1h) MFA token."""
    _ensure_admin(user)
    code = (payload.get("code") or "").strip()
    from services.auto_admin_2fa import Admin2FAService
    token = await Admin2FAService(db).exchange_code_for_token(user["id"], code)
    if not token:
        raise HTTPException(401, "Неверный код. Попробуйте ещё раз.")
    return {"mfa_token": token, "expires_in": 3600}


@router.post("/admin/2fa/disable")
async def admin_2fa_disable(
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_user),
    db=Depends(get_db),
):
    _ensure_admin(user)
    code = (payload.get("code") or "").strip()
    from services.auto_admin_2fa import Admin2FAService
    ok = await Admin2FAService(db).disable(user["id"], code)
    if not ok:
        raise HTTPException(400, "Неверный код или 2FA не была включена.")
    return {"ok": True}
