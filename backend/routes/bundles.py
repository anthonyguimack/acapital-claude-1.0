"""Session Bundles — prepaid session credit packs.

Two scopes:
  • Admin bundles  (mentor_id is None) → redeemable on any paid slot
  • Mentor bundles (mentor_id set)     → redeemable only on that mentor's paid slots

When a member purchases a bundle, a credit_pack document is created with
`remaining = session_count`. Each time the member books a paid slot and
elects to redeem, `remaining -= 1` on an eligible pack (global preferred
last; mentor-specific first). On booking cancellation the credit is restored.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from models.database import db, require_admin
from utils.runtime_config import get_stripe_api_key
from datetime import datetime, timezone
import os
import uuid

router = APIRouter()


def _clean_bundle_body(body: dict) -> dict:
    return {
        "name": (body.get("name") or "").strip(),
        "summary": body.get("summary") or "",
        "description": body.get("description") or "",
        "banner_url": (body.get("banner_url") or "").strip(),
        "session_count": max(1, int(body.get("session_count") or 1)),
        "price_cents": max(0, int(body.get("price_cents") or 0)),
        "single_session_value_cents": max(0, int(body.get("single_session_value_cents") or 0)),
        "currency": (body.get("currency") or "usd").lower(),
        "active": body.get("active", True),
    }


async def _eligible_credit_pack(member_id: str, mentor_id: str):
    """Return the best credit pack the member can spend on this mentor,
    prioritizing mentor-specific packs before global packs (to exhaust
    narrow credits first). Returns None if nothing available."""
    pack = await db.credit_packs.find_one(
        {"member_id": member_id, "mentor_id": mentor_id, "remaining": {"$gt": 0}},
        {"_id": 0},
        sort=[("purchased_at", 1)],
    )
    if pack:
        return pack
    return await db.credit_packs.find_one(
        {"member_id": member_id, "mentor_id": None, "remaining": {"$gt": 0}},
        {"_id": 0},
        sort=[("purchased_at", 1)],
    )


# ── Admin: global bundle catalog ──

@router.get("/admin/bundles")
async def admin_list_bundles(user: dict = Depends(require_admin)):
    items = await db.session_bundles.find({"mentor_id": None}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return items


@router.post("/admin/bundles")
async def admin_create_bundle(request: Request, user: dict = Depends(require_admin)):
    body = _clean_bundle_body(await request.json())
    if not body["name"]:
        raise HTTPException(status_code=400, detail="Bundle name required")
    doc = {
        "id": str(uuid.uuid4()),
        "mentor_id": None,
        "created_by": "admin",
        **body,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.session_bundles.insert_one(doc)
    return await db.session_bundles.find_one({"id": doc["id"]}, {"_id": 0})


@router.put("/admin/bundles/{bundle_id}")
async def admin_update_bundle(bundle_id: str, request: Request, user: dict = Depends(require_admin)):
    body = _clean_bundle_body(await request.json())
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    r = await db.session_bundles.update_one({"id": bundle_id, "mentor_id": None}, {"$set": body})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return await db.session_bundles.find_one({"id": bundle_id}, {"_id": 0})


@router.delete("/admin/bundles/{bundle_id}")
async def admin_delete_bundle(bundle_id: str, user: dict = Depends(require_admin)):
    await db.session_bundles.delete_one({"id": bundle_id, "mentor_id": None})
    return {"success": True}


# ── Mentor: personal bundles ──

@router.get("/member/mentor/bundles")
async def mentor_list_bundles(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    items = await db.session_bundles.find({"mentor_id": member["member_id"]}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return items


@router.post("/member/mentor/bundles")
async def mentor_create_bundle(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    body = _clean_bundle_body(await request.json())
    if not body["name"]:
        raise HTTPException(status_code=400, detail="Bundle name required")
    doc = {
        "id": str(uuid.uuid4()),
        "mentor_id": member["member_id"],
        "created_by": member["member_id"],
        **body,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.session_bundles.insert_one(doc)
    return await db.session_bundles.find_one({"id": doc["id"]}, {"_id": 0})


@router.put("/member/mentor/bundles/{bundle_id}")
async def mentor_update_bundle(bundle_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    body = _clean_bundle_body(await request.json())
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    r = await db.session_bundles.update_one({"id": bundle_id, "mentor_id": member["member_id"]}, {"$set": body})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return await db.session_bundles.find_one({"id": bundle_id}, {"_id": 0})


@router.delete("/member/mentor/bundles/{bundle_id}")
async def mentor_delete_bundle(bundle_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    await db.session_bundles.delete_one({"id": bundle_id, "mentor_id": member["member_id"]})
    return {"success": True}


# ── Member: browse + purchase + my credits ──

@router.get("/member/bundles")
async def member_list_bundles(request: Request):
    """Active bundles visible to the member — admin-global + any mentor bundles."""
    from routes.membership import get_current_member
    await get_current_member(request)
    items = await db.session_bundles.find({"active": True}, {"_id": 0}).sort("created_at", -1).to_list(500)
    # Enrich mentor-owned bundles with mentor name
    for b in items:
        if b.get("mentor_id"):
            m = await db.members.find_one({"member_id": b["mentor_id"]}, {"_id": 0, "password_hash": 0})
            if m:
                b["mentor_name"] = f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
    return items


@router.get("/member/bundles/{bundle_id}")
async def member_get_bundle(bundle_id: str, request: Request):
    """Full bundle record (for the public details page)."""
    from routes.membership import get_current_member
    await get_current_member(request)
    b = await db.session_bundles.find_one({"id": bundle_id, "active": True}, {"_id": 0})
    if not b:
        raise HTTPException(status_code=404, detail="Bundle not found")
    if b.get("mentor_id"):
        m = await db.members.find_one({"member_id": b["mentor_id"]}, {"_id": 0, "password_hash": 0})
        if m:
            b["mentor_name"] = f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
    return b


@router.post("/member/bundles/checkout/{bundle_id}")
async def member_bundle_checkout(bundle_id: str, request: Request):
    """Start a Stripe session to purchase this bundle. On success, a credit_pack
    is created via the status-poll endpoint."""
    import stripe as stripe_lib
    from routes.membership import get_current_member
    member = await get_current_member(request)
    bundle = await db.session_bundles.find_one({"id": bundle_id, "active": True}, {"_id": 0})
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    settings = await db.settings.find_one({}, {"_id": 0}) or {}
    # Paid bundles are gated by their own independent setting. Fallback to
    # mentor_slots_paid_enabled for backwards compatibility if admin hasn't
    # explicitly set paid_bundles_enabled yet.
    bundles_paid = settings.get("paid_bundles_enabled")
    if bundles_paid is None:
        bundles_paid = settings.get("mentor_slots_paid_enabled", False)
    if not bundles_paid:
        raise HTTPException(status_code=400, detail="Paid session bundles are currently disabled")
    if int(bundle.get("price_cents") or 0) <= 0:
        raise HTTPException(status_code=400, detail="This bundle has no price")

    body = await request.json() if int(request.headers.get("content-length") or 0) > 0 else {}
    origin_url = (body.get("origin_url") or "").rstrip("/")
    if not origin_url:
        raise HTTPException(status_code=400, detail="origin_url is required")

    # Optional coupon
    base_cents = int(bundle["price_cents"])
    coupon_code = (body.get("coupon_code") or "").strip().upper()
    coupon_id = None
    discount_cents = 0
    original_cents = base_cents
    final_cents = base_cents
    if coupon_code:
        from routes.coupons import _compute_discount, _is_expired
        coupon = await db.coupons.find_one({"code": coupon_code}, {"_id": 0})
        if not coupon or not coupon.get("active") or _is_expired(coupon):
            raise HTTPException(status_code=400, detail="Coupon is not valid")
        applies = coupon.get("applies_to", "both")
        if applies not in ("both", "bundles"):
            raise HTTPException(status_code=400, detail="Coupon not valid for bundles")
        limit = int(coupon.get("usage_limit") or 0)
        if limit > 0:
            if coupon.get("usage_mode") == "per_member":
                used = await db.coupon_redemptions.count_documents({"coupon_id": coupon["id"], "member_id": member["member_id"]})
                if used >= limit:
                    raise HTTPException(status_code=400, detail="You already used this coupon the max number of times")
            elif int(coupon.get("usage_count") or 0) >= limit:
                raise HTTPException(status_code=400, detail="Coupon usage limit reached")
        discount_cents = _compute_discount(coupon, base_cents)
        final_cents = max(0, base_cents - discount_cents)
        coupon_id = coupon["id"]

    api_key = await get_stripe_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured. Set the API key in CMS → Settings → Stripe.")
    success_url = f"{origin_url}/my-account/bundles/checkout-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/my-account/bundles"
    metadata = {
        "kind": "bundle_purchase",
        "bundle_id": bundle_id,
        "member_id": member["member_id"],
        "coupon_id": coupon_id or "",
        "coupon_code": coupon_code or "",
        "original_cents": str(original_cents),
        "discount_cents": str(discount_cents),
    }
    currency = (bundle.get("currency") or "usd").lower()
    stripe_client = stripe_lib.StripeClient(api_key)
    session = await stripe_client.checkout.sessions.create_async({
        "payment_method_types": ["card"],
        "line_items": [{
            "price_data": {
                "currency": currency,
                "product_data": {"name": bundle.get("name", "Session Bundle")},
                "unit_amount": final_cents,
            },
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata,
    })
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session.id,
        "kind": "bundle_purchase",
        "bundle_id": bundle_id,
        "member_id": member["member_id"],
        "amount": final_cents / 100.0,
        "currency": (bundle.get("currency") or "usd").lower(),
        "status": "initiated",
        "payment_status": "pending",
        "coupon_id": coupon_id,
        "coupon_code": coupon_code or None,
        "original_cents": original_cents,
        "discount_cents": discount_cents,
        "metadata": metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"url": session.url, "session_id": session.id}


@router.get("/member/bundles/checkout/status/{session_id}")
async def member_bundle_checkout_status(session_id: str, request: Request):
    import stripe as stripe_lib
    from routes.membership import get_current_member
    member = await get_current_member(request)
    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx or tx.get("member_id") != member["member_id"] or tx.get("kind") != "bundle_purchase":
        raise HTTPException(status_code=404, detail="Checkout session not found")

    if tx.get("payment_status") == "paid":
        pack = await db.credit_packs.find_one({"purchase_session_id": session_id}, {"_id": 0})
        return {"payment_status": "paid", "credit_pack": pack}

    api_key = await get_stripe_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured.")
    stripe_client = stripe_lib.StripeClient(api_key)
    stripe_session = await stripe_client.checkout.sessions.retrieve_async(session_id)

    update = {"status": stripe_session.status, "payment_status": stripe_session.payment_status}
    if stripe_session.payment_status == "paid":
        update["paid_at"] = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": update})

    credit_pack = None
    if stripe_session.payment_status == "paid":
        existing = await db.credit_packs.find_one({"purchase_session_id": session_id}, {"_id": 0})
        if not existing:
            bundle = await db.session_bundles.find_one({"id": tx["bundle_id"]}, {"_id": 0})
            if bundle:
                pack = {
                    "id": str(uuid.uuid4()),
                    "member_id": member["member_id"],
                    "bundle_id": bundle["id"],
                    "bundle_name": bundle["name"],
                    "mentor_id": bundle.get("mentor_id"),
                    "session_count": int(bundle["session_count"]),
                    "remaining": int(bundle["session_count"]),
                    "single_session_value_cents": int(bundle.get("single_session_value_cents") or 0),
                    "price_cents_paid": int(bundle["price_cents"]),
                    "currency": (bundle.get("currency") or "usd").lower(),
                    "purchase_session_id": session_id,
                    "purchased_at": datetime.now(timezone.utc).isoformat(),
                }
                await db.credit_packs.insert_one(pack)
                credit_pack = pack
                # Record coupon redemption (idempotent: check if already recorded)
                if tx.get("coupon_id"):
                    existing_red = await db.coupon_redemptions.find_one({"reference_id": session_id})
                    if not existing_red:
                        from routes.coupons import record_redemption
                        await record_redemption(
                            tx["coupon_id"], member["member_id"], "bundles",
                            int(tx.get("original_cents") or 0),
                            int(tx.get("discount_cents") or 0),
                            session_id,
                        )
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "member_id": member["member_id"],
                    "type": "bundle_purchased",
                    "title": "Bundle Purchased",
                    "message": f"You now have {pack['remaining']} session credit{'' if pack['remaining']==1 else 's'} from \"{pack['bundle_name']}\".",
                    "link": "/my-account/bundles",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        else:
            credit_pack = existing

    return {
        "payment_status": status.payment_status,
        "status": status.status,
        "credit_pack": credit_pack,
    }


@router.get("/member/credits")
async def member_list_credits(request: Request):
    """All credit packs owned by the member, with mentor display name enriched."""
    from routes.membership import get_current_member
    member = await get_current_member(request)
    packs = await db.credit_packs.find({"member_id": member["member_id"]}, {"_id": 0}).sort("purchased_at", -1).to_list(200)
    for p in packs:
        if p.get("mentor_id"):
            m = await db.members.find_one({"member_id": p["mentor_id"]}, {"_id": 0, "password_hash": 0})
            if m:
                p["mentor_name"] = f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
    return packs
