"""LinkedIn OAuth (authorization code flow)."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse

from app.services.linkedin_oauth import (
    build_linkedin_authorization_url,
    create_oauth_state,
    exchange_code_for_tokens,
    ensure_fresh_access_token,
    save_tokens,
    validate_oauth_state,
)

router = APIRouter(tags=["auth"])


@router.get("/auth/linkedin")
async def auth_linkedin():
    state = create_oauth_state()
    url = build_linkedin_authorization_url(state)
    return RedirectResponse(url=url)


@router.get("/callback")
async def linkedin_callback(
    code: str | None = Query(default=None),
    state: str = Query(...),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
):
    if error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": error, "error_description": error_description},
        )
    if not validate_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")
    if not code:
        raise HTTPException(status_code=400, detail="Missing `code` from LinkedIn.")

    try:
        tokens = exchange_code_for_tokens(code)
        save_tokens(tokens)
        _ = ensure_fresh_access_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {
        "ok": True,
        "message": "LinkedIn authorization successful. Tokens stored.",
        "member_urn_set": bool(tokens.get("member_urn")),
    }
