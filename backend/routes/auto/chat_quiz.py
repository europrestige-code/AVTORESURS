"""AI chat (Татьяна) + АИ-подборщик quiz endpoints."""
from __future__ import annotations

from datetime import datetime as _dt
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from ._deps import get_db, get_optional_user

router = APIRouter()


@router.post("/chat")
async def chat(
    payload: Dict[str, Any] = Body(...),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db),
):
    """Russian AI assistant trained on the АвтоРесурс business model.

    Body: {message: str, history?: [{role,content}], session_id?: str}.
    Anonymous use is allowed; logged-in users have their conversation
    history persisted to auto_chat_messages for follow-up by support.
    """
    from services.auto_chat_service import get_chat_service
    msg = (payload.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "Пустое сообщение.")
    history = payload.get("history") or []
    session_id = payload.get("session_id")
    svc = get_chat_service()
    result = await svc.reply(history, msg, session_id=session_id)
    if user:
        sid = result.get("session_id") or session_id
        await db.auto_chat_messages.insert_many([
            {"session_id": sid, "user_id": user["id"], "role": "user",
             "content": msg, "created_at": _dt.utcnow()},
            {"session_id": sid, "user_id": user["id"], "role": "assistant",
             "content": result.get("content", ""), "created_at": _dt.utcnow()},
        ])
    return result


@router.get("/quiz/meta")
async def quiz_meta():
    """Static taxonomy used by the quiz wizard in the chat widget."""
    from services.auto_quiz_service import get_quiz_meta
    return get_quiz_meta()


@router.post("/quiz/submit")
async def quiz_submit(
    payload: Dict[str, Any] = Body(...),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db),
):
    """Accept a completed quiz, store it as a lead, and return matches."""
    from services.auto_fx_service import get_fx_rate
    from services.auto_quiz_service import AutoQuizService
    fx = await get_fx_rate()
    fx_rate = float(fx.get("nzd_to_rub_display") or fx.get("nzd_to_rub_spot") or 57.68)
    svc = AutoQuizService(db)
    try:
        result = await svc.submit(
            payload,
            fx_rate=fx_rate,
            user_id=user.get("id") if user else None,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return result
