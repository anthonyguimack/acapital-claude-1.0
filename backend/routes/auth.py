from fastapi import APIRouter, HTTPException, Request, Response, Depends
from models.database import db, verify_password, create_jwt_token, hash_password, generate_reset_token, get_current_user, get_user_permissions, send_email_smtp, logger
from datetime import datetime, timezone, timedelta
import uuid
import httpx

router = APIRouter()

@router.post("/auth/login")
async def login(request: Request, response: Response):
    body = await request.json()
    # Brute-force throttle: 5 login attempts per minute per IP. Login itself
    # doesn't get a captcha (it would frustrate every page load); the rate
    # limit is enough to neutralise password-spray attacks.
    from utils.rate_limit import enforce_rate_limit
    await enforce_rate_limit(request, key="login", max_requests=5, window_seconds=60)
    identifier = body.get("email", "").strip().lower()
    password = body.get("password", "")
    login_type = body.get("login_type", "any")
    member = await db.members.find_one(
        {"$or": [{"email": identifier}, {"username": identifier}]},
        {"_id": 0}
    )
    if not member or not verify_password(password, member.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if login_type == "admin" and member.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    # CMS login (operator or admin) — must have at least one CMS permission.
    if login_type == "cms":
        if member.get("role") != "admin":
            mroles = member.get("cms_roles") or []
            cms_role_ids = [r for r in mroles if r != "role_member"]
            if not cms_role_ids:
                raise HTTPException(status_code=403, detail="No CMS access assigned to this account")
    # My Account / public login gate — non-admins must hold role_member.
    # Both `/admin/login` (login_type="cms") and bootstrap admin path skip this.
    elif login_type != "admin" and member.get("role") != "admin":
        mroles = member.get("cms_roles") or []
        if "role_member" not in mroles:
            raise HTTPException(status_code=403, detail="My Account access has been revoked")
    token = create_jwt_token(member["member_id"], member["email"], member.get("role", "member"))
    response.set_cookie("session_token", token, path="/", httponly=True, secure=True, samesite="none", max_age=7*24*3600)
    return {"token": token, "user": {k: v for k, v in member.items() if k != "password_hash"}}

@router.get("/auth/me")
async def auth_me(request: Request):
    user = await get_current_user(request)
    result = {k: v for k, v in user.items() if k != "password_hash"}
    # Roles & Permissions: effective CMS access for the current session
    result["cms_roles"] = user.get("cms_roles") or (["role_admin"] if user.get("role") == "admin" else ["role_member"])
    result["effective_permissions"] = sorted(await get_user_permissions(user))
    # If member has a member_type_id, attach the type's permissions and allowed_pages
    mt_id = user.get("member_type_id")
    if mt_id:
        mt = await db.member_types.find_one({"id": mt_id}, {"_id": 0})
        if mt:
            result["_member_type"] = {
                "name": mt.get("name", ""),
                "allowed_pages": mt.get("allowed_pages", []),
                "permissions": {k: mt.get(k, False) for k in (
                    "corporate", "is_mentor", "portfolio_development", "application_reviewer",
                    "opportunities_development", "opportunities_reviewer", "project_development",
                    "project_reviewer", "project_management", "content_operator",
                )}
            }
    return result

@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}

@router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id})
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        data = resp.json()
    email = data.get("email", "").strip().lower()
    name = data.get("name", "")
    picture = data.get("picture", "")
    session_token = data.get("session_token", "")
    existing = await db.members.find_one({"email": email}, {"_id": 0})
    if existing:
        member_id = existing["member_id"]
        await db.members.update_one({"email": email}, {"$set": {
            "first_name": name.split()[0] if name else existing.get("first_name", ""),
            "last_name": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else existing.get("last_name", ""),
            "avatar": picture or existing.get("avatar", ""),
            "google_account": email,
        }})
    else:
        from routes.membership import get_next_membership_number, get_aux_prefix
        membership_number = await get_next_membership_number()
        prefix = await get_aux_prefix()
        membership_id = f"{prefix}-{membership_number}"
        member_id = f"member_{uuid.uuid4().hex[:12]}"
        await db.members.insert_one({
            "member_id": member_id,
            "membership_number": membership_number,
            "membership_id": membership_id,
            "username": email.split("@")[0] + str(membership_number),
            "email": email,
            "password_hash": "",
            "first_name": name.split()[0] if name else "",
            "last_name": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else "",
            "gender": "",
            "phone": "",
            "date_of_birth": "",
            "address": "", "country": "", "state": "", "zip_code": "",
            "google_account": email,
            "avatar": picture or "",
            "summary": "", "biography": "",
            "social_links": [],
            "sponsor_id": None, "sponsor_membership_number": None,
            "mentor_id": None, "mentor_membership_number": None,
            "is_mentor": False,
            "portfolio_development": False,
            "role": "member",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    await db.user_sessions.insert_one({
        "user_id": member_id, "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    response.set_cookie("session_token", session_token, path="/", httponly=True, secure=True, samesite="none", max_age=7*24*3600)
    member = await db.members.find_one({"member_id": member_id}, {"_id": 0})
    return {k: v for k, v in member.items() if k != "password_hash"}

@router.post("/auth/forgot-password")
async def forgot_password(request: Request):
    body = await request.json()
    # Hardening: keep the existing 3/15min throttle (stricter than the
    # default 5/min because reset-link spam is high-impact) AND require
    # captcha when enabled.
    from utils.rate_limit import enforce_rate_limit
    from utils.captcha import require_captcha
    await enforce_rate_limit(request, key="forgot_password", max_requests=3, window_seconds=15 * 60)
    await require_captcha(request, body)
    email = body.get("email", "").strip().lower()
    member = await db.members.find_one({"email": email, "role": {"$ne": "admin"}}, {"_id": 0})
    if not member:
        return {"message": "If the email exists, a reset link has been sent."}
    token = generate_reset_token()
    await db.password_resets.insert_one({
        "email": email, "token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
        "used": False, "created_at": datetime.now(timezone.utc).isoformat()
    })
    settings = await db.settings.find_one({}, {"_id": 0})
    if settings and settings.get("smtp_host"):
        try:
            # Reset URLs MUST point at the canonical Site URL. Falling back
            # to the request Origin would put the Emergent preview host in
            # the reset link, which (a) confuses users and (b) breaks the
            # moment the preview URL rotates.  If Site URL isn't set we
            # still record the token (the operator can recover via the DB
            # or by configuring Settings and clicking "forgot" again) but
            # we skip the email send.
            from utils.runtime_config import get_site_url
            base = await get_site_url("")
            if not base:
                logger.warning("Skipping reset-password email: Site URL not configured in CMS → Settings → General.")
                return {"message": "If the email exists, a reset link has been sent."}
            reset_url = f"{base}/my-account/reset-password?token={token}"
            from utils.email_render import render_and_send
            await render_and_send(
                "password_reset", settings, email, member.get("first_name", ""),
                variables={
                    "name": member.get("first_name", "") or email.split("@")[0],
                    "link": reset_url,
                    "expiry_minutes": "30",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to send reset email: {e}")
    return {"message": "If the email exists, a reset link has been sent."}

@router.post("/auth/reset-password")
async def reset_password(request: Request):
    body = await request.json()
    token = body.get("token", "")
    new_password = body.get("password", "")
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password required")
    reset = await db.password_resets.find_one({"token": token, "used": False}, {"_id": 0})
    if not reset:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    expires_at = datetime.fromisoformat(reset["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")
    await db.members.update_one({"email": reset["email"]}, {"$set": {"password_hash": hash_password(new_password)}})
    await db.password_resets.update_one({"token": token}, {"$set": {"used": True}})
    return {"message": "Password reset successfully"}


@router.get("/auth/reset-password/verify")
async def reset_password_verify(token: str):
    """Quick token validation so the reset page can show a friendly
    'expired or already used' message instead of letting the user type a
    new password and only fail on submit."""
    if not token:
        return {"valid": False, "reason": "missing"}
    reset = await db.password_resets.find_one({"token": token}, {"_id": 0})
    if not reset:
        return {"valid": False, "reason": "not_found"}
    if reset.get("used"):
        return {"valid": False, "reason": "used"}
    expires_at = datetime.fromisoformat(reset["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return {"valid": False, "reason": "expired"}
    return {"valid": True, "email": reset.get("email", "")}

@router.post("/auth/change-password")
async def change_password(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    current = body.get("current_password", "")
    new = body.get("new_password", "")
    full_member = await db.members.find_one({"member_id": user["member_id"]}, {"_id": 0})
    if not verify_password(current, full_member.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password incorrect")
    await db.members.update_one({"member_id": user["member_id"]}, {"$set": {"password_hash": hash_password(new)}})
    return {"message": "Password changed successfully"}
