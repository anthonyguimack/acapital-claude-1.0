"""Payouts Ledger — manual settlement tracking for mentor earnings.

Flow:
  • Gross earnings  = sum of price_cents from paid bookings (payment_status='paid')
  • Platform fee    = gross × platform_fee_percent (from settings, default 15)
  • Net owed        = gross - fee
  • Total paid out  = sum of payout_records.amount_cents (status='paid')
  • Balance         = net owed - total paid

Credit-redeemed bookings count toward gross because the platform already collected
payment upfront at bundle purchase time — the mentor still earned the session.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from models.database import db, require_admin
from datetime import datetime, timezone
import uuid

router = APIRouter()


async def _fee_percent() -> float:
    s = await db.settings.find_one({}, {"_id": 0}) or {}
    try:
        return float(s.get("platform_fee_percent", 15))
    except (TypeError, ValueError):
        return 15.0


async def _mentor_ledger(mentor_id: str, fee_percent: float) -> dict:
    """Aggregate gross/fee/net for a single mentor + total paid + balance."""
    bookings = await db.mentorship_bookings.find(
        {
            "mentor_id": mentor_id,
            "status": "booked",
            "payment_status": {"$in": ["paid", "credit"]},
        },
        {"_id": 0, "price_cents": 1},
    ).to_list(5000)
    gross = sum(int(b.get("price_cents") or 0) for b in bookings)
    fee = int(round(gross * (fee_percent / 100.0)))
    net = max(0, gross - fee)
    paid_rows = await db.payout_records.find(
        {"mentor_id": mentor_id, "status": "paid"},
        {"_id": 0, "amount_cents": 1},
    ).to_list(1000)
    paid = sum(int(r.get("amount_cents") or 0) for r in paid_rows)
    return {
        "mentor_id": mentor_id,
        "gross_cents": gross,
        "fee_cents": fee,
        "net_cents": net,
        "paid_cents": paid,
        "balance_cents": max(0, net - paid),
        "session_count": len(bookings),
    }


# ── Admin: overview + create payout records ──

@router.get("/admin/payouts")
async def admin_list_payouts(user: dict = Depends(require_admin)):
    """Return per-mentor ledger (only mentors with any earnings or payouts) + fee_percent."""
    fee_percent = await _fee_percent()
    # Gather every mentor who has either a paid booking or a payout record
    mentor_ids = set()
    async for b in db.mentorship_bookings.find(
        {"status": "booked", "payment_status": {"$in": ["paid", "credit"]}},
        {"_id": 0, "mentor_id": 1},
    ):
        if b.get("mentor_id"):
            mentor_ids.add(b["mentor_id"])
    async for r in db.payout_records.find({}, {"_id": 0, "mentor_id": 1}):
        if r.get("mentor_id"):
            mentor_ids.add(r["mentor_id"])
    ledger = []
    for mid in mentor_ids:
        row = await _mentor_ledger(mid, fee_percent)
        mentor = await db.members.find_one({"member_id": mid}, {"_id": 0, "password_hash": 0})
        if mentor:
            row["mentor_name"] = f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip()
            row["membership_id"] = mentor.get("membership_id", "")
            row["email"] = mentor.get("email", "")
        ledger.append(row)
    ledger.sort(key=lambda x: x["balance_cents"], reverse=True)
    records = await db.payout_records.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    for rec in records:
        m = await db.members.find_one({"member_id": rec.get("mentor_id")}, {"_id": 0, "password_hash": 0})
        if m:
            rec["mentor_name"] = f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
    return {"fee_percent": fee_percent, "ledger": ledger, "records": records}


@router.post("/admin/payouts")
async def admin_create_payout(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    mentor_id = body.get("mentor_id")
    amount_cents = int(body.get("amount_cents") or 0)
    if not mentor_id or amount_cents <= 0:
        raise HTTPException(status_code=400, detail="mentor_id and positive amount_cents required")
    fee_percent = await _fee_percent()
    row = await _mentor_ledger(mentor_id, fee_percent)
    if amount_cents > row["balance_cents"]:
        raise HTTPException(status_code=400, detail=f"Amount exceeds current balance (${row['balance_cents']/100:.2f}).")
    doc = {
        "id": str(uuid.uuid4()),
        "mentor_id": mentor_id,
        "amount_cents": amount_cents,
        "currency": (body.get("currency") or "usd").lower(),
        "method": body.get("method", "manual"),
        "reference": body.get("reference", ""),
        "note": body.get("note", ""),
        "status": "paid",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email", "admin"),
    }
    await db.payout_records.insert_one(doc)
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": mentor_id,
        "type": "payout_sent",
        "title": "Payout Sent",
        "message": f"A payout of ${amount_cents/100:.2f} has been recorded to your account.",
        "link": "/my-account/earnings",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return await db.payout_records.find_one({"id": doc["id"]}, {"_id": 0})


@router.delete("/admin/payouts/{record_id}")
async def admin_void_payout(record_id: str, user: dict = Depends(require_admin)):
    await db.payout_records.delete_one({"id": record_id})
    return {"success": True}


# ── Mentor: personal payout history ──

@router.get("/member/mentor/payouts")
async def mentor_payouts(request: Request):
    """Return current balance + personal payout history for the authenticated mentor."""
    from routes.membership import get_current_member
    member = await get_current_member(request)
    fee_percent = await _fee_percent()
    ledger = await _mentor_ledger(member["member_id"], fee_percent)
    records = await db.payout_records.find(
        {"mentor_id": member["member_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return {"fee_percent": fee_percent, "ledger": ledger, "records": records}
