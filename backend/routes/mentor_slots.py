"""Mentor Slots — admin + mentor CRUD, member booking, waitlist, and slot templates."""
from fastapi import APIRouter, HTTPException, Request, Depends
from models.database import db, require_admin
from routes.calendar_helpers import notify_waitlist_spot_open, notify_cancellation
from utils.runtime_config import get_stripe_api_key
from datetime import datetime, timezone, date, timedelta
import uuid

router = APIRouter()


def _expand_recurrence(base_date: str, days_of_week: list, weeks: int, excluded_dates: set = None) -> list:
    """Given a start date and a list of JS-style day-of-week indices (0=Sun..6=Sat),
    produce the sorted, deduplicated list of ISO dates across `weeks` consecutive weeks.
    The first week starts at the Sunday on or before `base_date`.
    Any date present in `excluded_dates` (ISO strings) is skipped."""
    if not base_date or not days_of_week or weeks <= 0:
        return []
    try:
        y, m, d = [int(x) for x in base_date.split("-")]
        start = date(y, m, d)
    except (ValueError, AttributeError):
        return []
    # Python weekday(): Mon=0..Sun=6. JS: Sun=0..Sat=6. Convert JS dow → python dow.
    def js_to_py(dow: int) -> int:
        return 6 if dow == 0 else dow - 1
    # Anchor each week at the Sunday on-or-before the start date, so selecting
    # Monday against a Wednesday start yields next Monday, not 5 days in the past.
    sunday_anchor = start - timedelta(days=(start.weekday() + 1) % 7)
    excluded = excluded_dates or set()
    out = set()
    for w in range(weeks):
        for dow in days_of_week:
            py_dow = js_to_py(int(dow))
            offset = (py_dow + 1) % 7  # days after Sunday
            dt = sunday_anchor + timedelta(weeks=w, days=offset)
            if dt >= start and dt.isoformat() not in excluded:
                out.add(dt.isoformat())
    return sorted(out)


async def _load_blocked_dates_set() -> set:
    """Return a set of ISO date strings marked as blocked by the admin."""
    rows = await db.blocked_dates.find({}, {"_id": 0, "date": 1}).to_list(500)
    return {r["date"] for r in rows if r.get("date")}


async def _materialize_slot(base_body: dict, override_date: str) -> dict:
    """Insert a single slot document; return the enriched record."""
    doc = {**base_body, "id": str(uuid.uuid4()), "date": override_date, "created_at": datetime.now(timezone.utc).isoformat()}
    doc.pop("recurrence", None)
    await db.mentorship_slots.insert_one(doc)
    result = await db.mentorship_slots.find_one({"id": doc["id"]}, {"_id": 0})
    result["booked_count"] = 0
    result["waitlist_count"] = 0
    return result


# ── Admin: Mentorship Schedule ──

@router.get("/admin/mentorship/slots")
async def admin_list_mentorship_slots(user: dict = Depends(require_admin)):
    slots = await db.mentorship_slots.find({}, {"_id": 0}).sort("date", 1).to_list(1000)
    for s in slots:
        s["booked_count"] = await db.mentorship_bookings.count_documents({"slot_id": s["id"], "status": {"$in": ["booked", "completed"]}})
        s["waitlist_count"] = await db.mentorship_bookings.count_documents({"slot_id": s["id"], "status": "waitlist"})
        mentor = await db.members.find_one({"member_id": s.get("mentor_id")}, {"_id": 0, "password_hash": 0})
        s["mentor_name"] = f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip() if mentor else ""
        s["mentor_membership_id"] = mentor.get("membership_id", "") if mentor else ""
    return slots


@router.post("/admin/mentorship/slots")
async def admin_create_mentorship_slot(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    body.setdefault("status", "active")
    body.setdefault("max_students", 1)
    body.setdefault("session_type", "One-on-One")
    body.setdefault("description", "")
    body.setdefault("virtual_link", "")
    body.setdefault("attachments", [])
    body.setdefault("price_cents", 0)
    body.setdefault("currency", "usd")
    if not body.get("mentor_id"):
        raise HTTPException(status_code=400, detail="mentor_id is required")
    if not body.get("date"):
        raise HTTPException(status_code=400, detail="date is required")
    # Recurrence support: produce N cloned slots across selected weekdays/weeks.
    recurrence = body.pop("recurrence", None)
    dates = [body["date"]]
    if recurrence and recurrence.get("enabled"):
        blocked = await _load_blocked_dates_set()
        expanded = _expand_recurrence(body["date"], recurrence.get("days_of_week") or [], int(recurrence.get("weeks") or 1), excluded_dates=blocked)
        if expanded:
            dates = expanded[:104]  # hard cap (2 years)
    elif body["date"]:
        blocked = await _load_blocked_dates_set()
        if body["date"] in blocked:
            raise HTTPException(status_code=400, detail=f"{body['date']} is a blocked date. Remove it from Calendar → Blocked Dates first, or pick another date.")
    created = []
    for d in dates:
        rec = await _materialize_slot(body, d)
        created.append(rec)
    mentor = await db.members.find_one({"member_id": body["mentor_id"]}, {"_id": 0, "password_hash": 0})
    mentor_name = f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip() if mentor else ""
    mentor_mid = mentor.get("membership_id", "") if mentor else ""
    for rec in created:
        rec["mentor_name"] = mentor_name
        rec["mentor_membership_id"] = mentor_mid
    if len(created) == 1:
        return created[0]
    return {"created": created, "count": len(created)}


@router.put("/admin/mentorship/slots/{slot_id}")
async def admin_update_mentorship_slot(slot_id: str, request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    body.pop("id", None)
    body.pop("_id", None)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.mentorship_slots.update_one({"id": slot_id}, {"$set": body})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Slot not found")
    slot = await db.mentorship_slots.find_one({"id": slot_id}, {"_id": 0})
    mentor = await db.members.find_one({"member_id": slot.get("mentor_id")}, {"_id": 0, "password_hash": 0})
    slot["mentor_name"] = f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip() if mentor else ""
    return slot


@router.delete("/admin/mentorship/slots/{slot_id}")
async def admin_delete_mentorship_slot(slot_id: str, user: dict = Depends(require_admin)):
    await db.mentorship_slots.delete_one({"id": slot_id})
    await db.mentorship_bookings.delete_many({"slot_id": slot_id})
    return {"success": True}


@router.get("/admin/mentorship/slots/{slot_id}/bookings")
async def admin_slot_bookings(slot_id: str, user: dict = Depends(require_admin)):
    bookings = await db.mentorship_bookings.find({"slot_id": slot_id}, {"_id": 0}).sort("booked_at", 1).to_list(200)
    for b in bookings:
        member = await db.members.find_one({"member_id": b["member_id"]}, {"_id": 0, "password_hash": 0})
        if member:
            b["membership_id"] = member.get("membership_id", "")
            b["name"] = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
            b["email"] = member.get("email", "")
    return bookings


# ── Admin: Mentor Slot Templates (Feature: quick-fill library) ──

@router.get("/admin/mentor-slot-templates")
async def admin_list_templates(user: dict = Depends(require_admin)):
    items = await db.mentor_slot_templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return items


@router.post("/admin/mentor-slot-templates")
async def admin_create_template(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Template name is required")
    doc = {
        "id": str(uuid.uuid4()),
        "name": body.get("name", ""),
        "title": body.get("title", ""),
        "session_type": body.get("session_type", "One-on-One"),
        "max_students": int(body.get("max_students", 1)),
        "default_duration_minutes": int(body.get("default_duration_minutes", 60)),
        "description": body.get("description", ""),
        "virtual_link": body.get("virtual_link", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.mentor_slot_templates.insert_one(doc)
    return await db.mentor_slot_templates.find_one({"id": doc["id"]}, {"_id": 0})


@router.put("/admin/mentor-slot-templates/{tpl_id}")
async def admin_update_template(tpl_id: str, request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    body.pop("id", None)
    body.pop("_id", None)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "max_students" in body:
        body["max_students"] = int(body["max_students"])
    if "default_duration_minutes" in body:
        body["default_duration_minutes"] = int(body["default_duration_minutes"])
    result = await db.mentor_slot_templates.update_one({"id": tpl_id}, {"$set": body})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return await db.mentor_slot_templates.find_one({"id": tpl_id}, {"_id": 0})


@router.delete("/admin/mentor-slot-templates/{tpl_id}")
async def admin_delete_template(tpl_id: str, user: dict = Depends(require_admin)):
    await db.mentor_slot_templates.delete_one({"id": tpl_id})
    return {"success": True}


# ── Admin: Blocked Dates (skip-list for recurrence engine) ──

@router.get("/admin/blocked-dates")
async def admin_list_blocked_dates(user: dict = Depends(require_admin)):
    items = await db.blocked_dates.find({}, {"_id": 0}).sort("date", 1).to_list(500)
    return items


@router.post("/admin/blocked-dates")
async def admin_create_blocked_date(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    if not body.get("date"):
        raise HTTPException(status_code=400, detail="date is required")
    existing = await db.blocked_dates.find_one({"date": body["date"]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail=f"{body['date']} is already blocked")
    doc = {
        "id": str(uuid.uuid4()),
        "date": body["date"],
        "reason": body.get("reason", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.blocked_dates.insert_one(doc)
    return await db.blocked_dates.find_one({"id": doc["id"]}, {"_id": 0})


@router.put("/admin/blocked-dates/{bd_id}")
async def admin_update_blocked_date(bd_id: str, request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    body.pop("id", None)
    body.pop("_id", None)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.blocked_dates.update_one({"id": bd_id}, {"$set": body})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return await db.blocked_dates.find_one({"id": bd_id}, {"_id": 0})


@router.delete("/admin/blocked-dates/{bd_id}")
async def admin_delete_blocked_date(bd_id: str, user: dict = Depends(require_admin)):
    await db.blocked_dates.delete_one({"id": bd_id})
    return {"success": True}


@router.get("/public/blocked-dates")
async def public_list_blocked_dates():
    """Public read so the recurrence picker can preview skipped dates."""
    items = await db.blocked_dates.find({}, {"_id": 0}).sort("date", 1).to_list(500)
    return items


# ── Member-side: Mentor slot templates (read-only, gated by setting) ──

@router.get("/member/mentor-slot-templates")
async def member_list_templates(request: Request):
    """Return templates only if the feature is enabled in settings."""
    from routes.membership import get_current_member
    await get_current_member(request)  # enforce auth
    settings = await db.settings.find_one({}, {"_id": 0}) or {}
    if not settings.get("mentor_slot_templates_enabled"):
        return []
    items = await db.mentor_slot_templates.find({}, {"_id": 0}).sort("name", 1).to_list(200)
    return items


# ── Mentor (member role): Manage own slots ──

@router.get("/member/mentorship/slots")
async def mentor_list_slots(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    slots = await db.mentorship_slots.find({"mentor_id": member["member_id"]}, {"_id": 0}).sort("date", 1).to_list(500)
    for s in slots:
        s["booked_count"] = await db.mentorship_bookings.count_documents({"slot_id": s["id"], "status": {"$in": ["booked", "completed"]}})
        s["waitlist_count"] = await db.mentorship_bookings.count_documents({"slot_id": s["id"], "status": "waitlist"})
        bookings = await db.mentorship_bookings.find({"slot_id": s["id"]}, {"_id": 0}).sort("booked_at", 1).to_list(50)
        participants = []
        for b in bookings:
            m = await db.members.find_one({"member_id": b["member_id"]}, {"_id": 0, "password_hash": 0})
            if m:
                participants.append({"member_id": b["member_id"], "name": f"{m.get('first_name', '')} {m.get('last_name', '')}".strip(), "membership_id": m.get("membership_id", ""), "status": b["status"]})
        s["participants"] = participants
    return slots


@router.post("/member/mentorship/slots")
async def mentor_create_slot(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    body = await request.json()
    body["mentor_id"] = member["member_id"]
    body.setdefault("status", "active")
    body.setdefault("max_students", 1)
    body.setdefault("session_type", "One-on-One")
    body.setdefault("description", "")
    body.setdefault("virtual_link", "")
    body.setdefault("attachments", [])
    if not body.get("date"):
        raise HTTPException(status_code=400, detail="date is required")
    recurrence = body.pop("recurrence", None)
    dates = [body["date"]]
    if recurrence and recurrence.get("enabled"):
        blocked = await _load_blocked_dates_set()
        expanded = _expand_recurrence(body["date"], recurrence.get("days_of_week") or [], int(recurrence.get("weeks") or 1), excluded_dates=blocked)
        if expanded:
            dates = expanded[:104]
    elif body["date"]:
        blocked = await _load_blocked_dates_set()
        if body["date"] in blocked:
            raise HTTPException(status_code=400, detail=f"{body['date']} is a blocked date. Ask the administrator to remove it, or pick another date.")
    created = []
    for d in dates:
        rec = await _materialize_slot(body, d)
        rec["participants"] = []
        created.append(rec)
    if len(created) == 1:
        return created[0]
    return {"created": created, "count": len(created)}


@router.put("/member/mentorship/slots/{slot_id}")
async def mentor_update_slot(slot_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    body = await request.json()
    old_slot = await db.mentorship_slots.find_one({"id": slot_id, "mentor_id": member["member_id"]}, {"_id": 0})
    body.pop("id", None)
    body.pop("_id", None)
    body.pop("mentor_id", None)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    if old_slot and old_slot.get("status") != "cancelled" and body.get("status") == "cancelled":
        await notify_cancellation(db.mentorship_bookings, slot_id, "slot_id", f"Mentorship on {old_slot.get('date', '')}", "slot")
    result = await db.mentorship_slots.update_one({"id": slot_id, "mentor_id": member["member_id"]}, {"$set": body})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Slot not found")
    updated = await db.mentorship_slots.find_one({"id": slot_id}, {"_id": 0})
    updated["booked_count"] = await db.mentorship_bookings.count_documents({"slot_id": slot_id, "status": {"$in": ["booked", "completed"]}})
    updated["waitlist_count"] = await db.mentorship_bookings.count_documents({"slot_id": slot_id, "status": "waitlist"})
    bookings = await db.mentorship_bookings.find({"slot_id": slot_id}, {"_id": 0}).sort("booked_at", 1).to_list(50)
    participants = []
    for b in bookings:
        m = await db.members.find_one({"member_id": b["member_id"]}, {"_id": 0, "password_hash": 0})
        if m:
            participants.append({"member_id": b["member_id"], "name": f"{m.get('first_name', '')} {m.get('last_name', '')}".strip(), "membership_id": m.get("membership_id", ""), "status": b["status"]})
    updated["participants"] = participants
    return updated


@router.delete("/member/mentorship/slots/{slot_id}")
async def mentor_delete_slot(slot_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    await db.mentorship_slots.delete_one({"id": slot_id, "mentor_id": member["member_id"]})
    await db.mentorship_bookings.delete_many({"slot_id": slot_id})
    return {"success": True}


# ── Member: Mentor calendar view (book / cancel / my bookings) ──

@router.get("/member/mentor-calendar")
async def member_view_mentor_calendar(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    mentor_id = member.get("mentor_id")
    if not mentor_id:
        return {"slots": [], "mentor": None}
    slots = await db.mentorship_slots.find({"mentor_id": mentor_id, "status": "active"}, {"_id": 0}).sort("date", 1).to_list(500)
    for s in slots:
        s["booked_count"] = await db.mentorship_bookings.count_documents({"slot_id": s["id"], "status": {"$in": ["booked", "completed"]}})
        s["waitlist_count"] = await db.mentorship_bookings.count_documents({"slot_id": s["id"], "status": "waitlist"})
        my_booking = await db.mentorship_bookings.find_one({"slot_id": s["id"], "member_id": member["member_id"]}, {"_id": 0})
        s["my_status"] = my_booking["status"] if my_booking else None
        if s["my_status"] != "booked":
            s.pop("virtual_link", None)
    mentor = await db.members.find_one({"member_id": mentor_id}, {"_id": 0, "password_hash": 0})
    return {"slots": slots, "mentor": {"name": f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip(), "membership_id": mentor.get("membership_id", "")} if mentor else None}


@router.post("/member/mentorship/book/{slot_id}")
async def member_book_slot(slot_id: str, request: Request):
    from routes.membership import get_current_member
    from routes.bundles import _eligible_credit_pack
    member = await get_current_member(request)
    slot = await db.mentorship_slots.find_one({"id": slot_id}, {"_id": 0})
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.get("status") != "active":
        raise HTTPException(status_code=400, detail="Slot is not available")

    body = await request.json() if int(request.headers.get("content-length") or 0) > 0 else {}
    use_credit = bool(body.get("use_credit"))

    # Paid-slot gate: when global toggle is ON and the slot has a price,
    # bookings must either redeem a credit pack or go through Stripe via
    # /member/mentorship/checkout/{slot_id}
    settings = await db.settings.find_one({}, {"_id": 0}) or {}
    is_paid_mode = settings.get("mentor_slots_paid_enabled") and int(slot.get("price_cents") or 0) > 0
    redeemed_pack = None
    if is_paid_mode:
        if use_credit:
            redeemed_pack = await _eligible_credit_pack(member["member_id"], slot["mentor_id"])
            if not redeemed_pack:
                raise HTTPException(status_code=400, detail="No eligible session credit available")
        else:
            raise HTTPException(status_code=402, detail="This is a paid slot. Use the checkout flow to book.")

    existing = await db.mentorship_bookings.find_one({"slot_id": slot_id, "member_id": member["member_id"]})
    if existing and existing.get("status") == "booked":
        raise HTTPException(status_code=400, detail="Already booked this slot")
    booked_count = await db.mentorship_bookings.count_documents({"slot_id": slot_id, "status": {"$in": ["booked", "completed"]}})
    max_students = slot.get("max_students", 1)
    if booked_count >= max_students and (not existing or existing.get("status") != "waitlist"):
        if existing:
            raise HTTPException(status_code=400, detail="Already on the waiting list")
        status = "waitlist"
    elif existing and existing.get("status") == "waitlist" and booked_count < max_students:
        await db.mentorship_bookings.update_one({"slot_id": slot_id, "member_id": member["member_id"]}, {"$set": {"status": "booked", "booked_at": datetime.now(timezone.utc).isoformat()}})
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "member_id": slot["mentor_id"],
            "type": "mentorship_booking",
            "title": "Booking Confirmed",
            "message": f"{member.get('first_name', '')} {member.get('last_name', '')} confirmed their booking for {slot.get('session_type', 'session')} on {slot.get('date', '')}.",
            "link": "/my-account/mentorship-calendar",
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "member_id": member["member_id"],
            "type": "mentorship_confirmed",
            "title": "Booking Confirmed",
            "message": f"Your mentorship session on {slot.get('date', '')} has been confirmed.",
            "link": "/my-account/my-bookings",
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"success": True, "status": "booked"}
    else:
        status = "booked" if booked_count < max_students else "waitlist"
    booking = {
        "id": str(uuid.uuid4()),
        "slot_id": slot_id,
        "member_id": member["member_id"],
        "mentor_id": slot["mentor_id"],
        "status": status,
        "booked_at": datetime.now(timezone.utc).isoformat(),
    }
    if redeemed_pack and status == "booked":
        # Decrement one credit from the chosen pack, stamp the booking.
        r = await db.credit_packs.update_one(
            {"id": redeemed_pack["id"], "remaining": {"$gt": 0}},
            {"$inc": {"remaining": -1}},
        )
        if r.modified_count == 0:
            raise HTTPException(status_code=409, detail="Credit was just spent elsewhere — try again")
        booking.update({
            "credit_pack_id": redeemed_pack["id"],
            "bundle_name": redeemed_pack.get("bundle_name"),
            "payment_status": "credit",
            "price_cents": int(slot.get("price_cents") or 0),
            "currency": (slot.get("currency") or "usd"),
        })
    await db.mentorship_bookings.insert_one(booking)
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": slot["mentor_id"],
        "type": "mentorship_booking",
        "title": "New Booking",
        "message": f"{member.get('first_name', '')} {member.get('last_name', '')} booked your {slot.get('session_type', 'session')} on {slot.get('date', '')}.",
        "link": "/my-account/mentorship-calendar",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": member["member_id"],
        "type": "mentorship_confirmed" if status == "booked" else "mentorship_waitlist",
        "title": "Booking Confirmed" if status == "booked" else "Waiting List",
        "message": f"Your mentorship session on {slot.get('date', '')} has been {'confirmed' if status == 'booked' else 'added to the waiting list'}.",
        "link": "/my-account/my-bookings",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"success": True, "status": status}


@router.post("/member/mentorship/cancel/{slot_id}")
async def member_cancel_booking(slot_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    booking = await db.mentorship_bookings.find_one({"slot_id": slot_id, "member_id": member["member_id"]})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    was_booked = booking.get("status") == "booked"
    # Refund credit pack if this booking was redeemed from one.
    credit_pack_id = booking.get("credit_pack_id")
    if credit_pack_id and was_booked:
        await db.credit_packs.update_one({"id": credit_pack_id}, {"$inc": {"remaining": 1}})
    await db.mentorship_bookings.delete_one({"slot_id": slot_id, "member_id": member["member_id"]})
    if was_booked:
        slot = await db.mentorship_slots.find_one({"id": slot_id}, {"_id": 0})
        await notify_waitlist_spot_open(db.mentorship_bookings, slot_id, "slot_id", f"Mentorship on {slot.get('date', '')}", "/my-account/mentor-calendar")
    return {"success": True}


@router.get("/member/my-bookings")
async def member_my_bookings(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    bookings = await db.mentorship_bookings.find({"member_id": member["member_id"]}, {"_id": 0}).sort("booked_at", -1).to_list(200)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for b in bookings:
        slot = await db.mentorship_slots.find_one({"id": b["slot_id"]}, {"_id": 0})
        if slot:
            b["date"] = slot.get("date", "")
            b["start_time"] = slot.get("start_time", "")
            b["end_time"] = slot.get("end_time", "")
            b["session_type"] = slot.get("session_type", "")
            b["virtual_link"] = slot.get("virtual_link", "")
            # Payment / pricing info for "Paid or Free" column
            slot_price = int(slot.get("price_cents") or 0)
            b["price_cents"] = int(b.get("price_cents") or slot_price)
            b["currency"] = b.get("currency") or slot.get("currency") or "usd"
            # Billing type: free | paid | credit
            pay_status = b.get("payment_status") or ""
            if pay_status == "credit":
                b["billing_type"] = "credit"
            elif b["price_cents"] > 0 and pay_status in {"paid", "pending"}:
                b["billing_type"] = "paid"
            elif b["price_cents"] > 0:
                b["billing_type"] = "paid"
            else:
                b["billing_type"] = "free"
            b["payment_status"] = pay_status
            mentor = await db.members.find_one({"member_id": slot["mentor_id"]}, {"_id": 0, "password_hash": 0})
            b["mentor_name"] = f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip() if mentor else ""
            if slot.get("status") == "cancelled":
                b["display_status"] = "cancelled"
            elif b["date"] < today and b["status"] == "booked":
                b["display_status"] = "completed"
            elif b["status"] == "booked":
                b["display_status"] = "upcoming"
            else:
                b["display_status"] = b["status"]
    return bookings



# ── Paid booking via Stripe Checkout ──

@router.post("/member/mentorship/checkout/{slot_id}")
async def member_mentorship_checkout(slot_id: str, request: Request):
    """Start a Stripe Checkout session for a paid mentorship slot.

    Creates a `pending_payment` booking so the seat is soft-held until payment
    clears. On payment success the status-poll endpoint flips it to `booked`.
    """
    import os
    import stripe as stripe_lib
    from routes.membership import get_current_member
    member = await get_current_member(request)
    slot = await db.mentorship_slots.find_one({"id": slot_id}, {"_id": 0})
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.get("status") != "active":
        raise HTTPException(status_code=400, detail="Slot is not available")
    settings = await db.settings.find_one({}, {"_id": 0}) or {}
    if not settings.get("mentor_slots_paid_enabled"):
        raise HTTPException(status_code=400, detail="Paid mentorship is currently disabled")
    price_cents = int(slot.get("price_cents") or 0)
    if price_cents <= 0:
        raise HTTPException(status_code=400, detail="This slot has no price — use the free booking flow")

    # Optional coupon
    body = await request.json() if int(request.headers.get("content-length") or 0) > 0 else {}
    origin_url = (body.get("origin_url") or "").rstrip("/")
    if not origin_url:
        raise HTTPException(status_code=400, detail="origin_url is required")

    coupon_code = (body.get("coupon_code") or "").strip().upper()
    coupon_id = None
    original_cents = price_cents
    discount_cents = 0
    if coupon_code:
        from routes.coupons import _compute_discount, _is_expired
        coupon = await db.coupons.find_one({"code": coupon_code}, {"_id": 0})
        if not coupon or not coupon.get("active") or _is_expired(coupon):
            raise HTTPException(status_code=400, detail="Coupon is not valid")
        applies = coupon.get("applies_to", "both")
        if applies not in ("both", "slots"):
            raise HTTPException(status_code=400, detail="Coupon not valid for mentorship slots")
        limit = int(coupon.get("usage_limit") or 0)
        if limit > 0:
            if coupon.get("usage_mode") == "per_member":
                used = await db.coupon_redemptions.count_documents({"coupon_id": coupon["id"], "member_id": member["member_id"]})
                if used >= limit:
                    raise HTTPException(status_code=400, detail="You already used this coupon the max number of times")
            elif int(coupon.get("usage_count") or 0) >= limit:
                raise HTTPException(status_code=400, detail="Coupon usage limit reached")
        discount_cents = _compute_discount(coupon, price_cents)
        price_cents = max(0, price_cents - discount_cents)
        coupon_id = coupon["id"]

    # Enforce the same seat/waitlist rules as the free path
    existing = await db.mentorship_bookings.find_one({"slot_id": slot_id, "member_id": member["member_id"]})
    if existing and existing.get("status") in ("booked", "pending_payment"):
        raise HTTPException(status_code=400, detail="You already have an active booking or pending payment for this slot")
    booked_count = await db.mentorship_bookings.count_documents({"slot_id": slot_id, "status": {"$in": ["booked", "completed", "pending_payment"]}})
    if booked_count >= int(slot.get("max_students", 1)):
        raise HTTPException(status_code=400, detail="Slot is full. Join the waiting list via the free booking flow.")

    # If the coupon dropped the price to zero, skip Stripe and just confirm the booking
    if price_cents <= 0:
        if existing:
            await db.mentorship_bookings.update_one(
                {"slot_id": slot_id, "member_id": member["member_id"]},
                {"$set": {
                    "status": "booked",
                    "payment_status": "coupon_free",
                    "price_cents": 0,
                    "original_cents": original_cents,
                    "discount_cents": discount_cents,
                    "coupon_code": coupon_code,
                    "coupon_id": coupon_id,
                    "booked_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
        else:
            await db.mentorship_bookings.insert_one({
                "id": str(uuid.uuid4()),
                "slot_id": slot_id,
                "member_id": member["member_id"],
                "mentor_id": slot["mentor_id"],
                "status": "booked",
                "payment_status": "coupon_free",
                "price_cents": 0,
                "original_cents": original_cents,
                "discount_cents": discount_cents,
                "coupon_code": coupon_code,
                "coupon_id": coupon_id,
                "booked_at": datetime.now(timezone.utc).isoformat(),
            })
        if coupon_id:
            from routes.coupons import record_redemption
            await record_redemption(coupon_id, member["member_id"], "slots", original_cents, discount_cents, slot_id)
        return {"url": f"{origin_url}/my-account/my-bookings", "session_id": None, "zero_priced": True}

    api_key = await get_stripe_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured. Set the API key in CMS → Settings → Stripe.")
    success_url = f"{origin_url}/my-account/mentorship/checkout-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/my-account/mentor-calendar"
    metadata = {
        "kind": "mentorship_booking",
        "slot_id": slot_id,
        "member_id": member["member_id"],
        "member_email": member.get("email", ""),
        "coupon_id": coupon_id or "",
        "coupon_code": coupon_code or "",
        "original_cents": str(original_cents),
        "discount_cents": str(discount_cents),
    }
    currency = (slot.get("currency") or "usd").lower()
    stripe_client = stripe_lib.StripeClient(api_key)
    session = await stripe_client.checkout.sessions.create_async({
        "payment_method_types": ["card"],
        "line_items": [{
            "price_data": {
                "currency": currency,
                "product_data": {"name": f"Mentorship session – {slot.get('session_type', 'Session')}"},
                "unit_amount": price_cents,
            },
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": metadata,
    })

    # Upsert a pending booking tied to this session
    if existing:
        await db.mentorship_bookings.update_one(
            {"slot_id": slot_id, "member_id": member["member_id"]},
            {"$set": {
                "status": "pending_payment",
                "payment_session_id": session.id,
                "payment_status": "pending",
                "price_cents": price_cents,
                "original_cents": original_cents,
                "discount_cents": discount_cents,
                "coupon_code": coupon_code,
                "coupon_id": coupon_id,
                "currency": currency,
                "booked_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
    else:
        await db.mentorship_bookings.insert_one({
            "id": str(uuid.uuid4()),
            "slot_id": slot_id,
            "member_id": member["member_id"],
            "mentor_id": slot["mentor_id"],
            "status": "pending_payment",
            "payment_session_id": session.id,
            "payment_status": "pending",
            "price_cents": price_cents,
            "original_cents": original_cents,
            "discount_cents": discount_cents,
            "coupon_code": coupon_code,
            "coupon_id": coupon_id,
            "currency": currency,
            "booked_at": datetime.now(timezone.utc).isoformat(),
        })

    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session.id,
        "kind": "mentorship_booking",
        "slot_id": slot_id,
        "member_id": member["member_id"],
        "amount": price_cents / 100.0,
        "currency": currency,
        "status": "initiated",
        "payment_status": "pending",
        "metadata": metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"url": session.url, "session_id": session.id}


@router.get("/member/mentorship/checkout/status/{session_id}")
async def member_mentorship_checkout_status(session_id: str, request: Request):
    """Poll Stripe for payment status. On `paid`, confirm the booking.

    Safe to call repeatedly — if the booking is already confirmed, this
    short-circuits and returns the cached `paid` state.
    """
    import stripe as stripe_lib
    from routes.membership import get_current_member
    member = await get_current_member(request)

    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx or tx.get("member_id") != member["member_id"]:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    if tx.get("payment_status") == "paid":
        booking = await db.mentorship_bookings.find_one({"payment_session_id": session_id}, {"_id": 0})
        return {"payment_status": "paid", "booking_status": booking.get("status") if booking else "booked"}

    api_key = await get_stripe_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured.")
    stripe_client = stripe_lib.StripeClient(api_key)
    stripe_session = await stripe_client.checkout.sessions.retrieve_async(session_id)

    update = {"status": stripe_session.status, "payment_status": stripe_session.payment_status}
    if stripe_session.payment_status == "paid":
        update["paid_at"] = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": update})

    booking_status = None
    if stripe_session.payment_status == "paid":
        booking = await db.mentorship_bookings.find_one({"payment_session_id": session_id}, {"_id": 0})
        if booking and booking.get("status") == "pending_payment":
            await db.mentorship_bookings.update_one(
                {"payment_session_id": session_id},
                {"$set": {
                    "status": "booked",
                    "payment_status": "paid",
                    "paid_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            # Record coupon redemption if applicable (idempotent — only runs here once per session)
            if booking.get("coupon_id"):
                existing_red = await db.coupon_redemptions.find_one({"reference_id": session_id})
                if not existing_red:
                    from routes.coupons import record_redemption
                    await record_redemption(
                        booking["coupon_id"], member["member_id"], "slots",
                        int(booking.get("original_cents") or booking.get("price_cents") or 0),
                        int(booking.get("discount_cents") or 0),
                        session_id,
                    )
            slot = await db.mentorship_slots.find_one({"id": booking["slot_id"]}, {"_id": 0})
            if slot:
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "member_id": slot["mentor_id"],
                    "type": "mentorship_booking",
                    "title": "New Paid Booking",
                    "message": f"Payment received for your {slot.get('session_type', 'session')} on {slot.get('date', '')}.",
                    "link": "/my-account/mentorship-calendar",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                await db.notifications.insert_one({
                    "id": str(uuid.uuid4()),
                    "member_id": member["member_id"],
                    "type": "mentorship_confirmed",
                    "title": "Booking Confirmed",
                    "message": f"Your paid mentorship session on {slot.get('date', '')} is confirmed.",
                    "link": "/my-account/my-bookings",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            booking_status = "booked"
        elif booking:
            booking_status = booking.get("status")

    return {
        "payment_status": stripe_session.payment_status,
        "status": stripe_session.status,
        "booking_status": booking_status,
        "amount_total": stripe_session.amount_total,
        "currency": stripe_session.currency,
    }


# ── Mentor Earnings Dashboard ──

@router.get("/member/mentor/earnings")
async def mentor_earnings(request: Request):
    """Return aggregate earnings + monthly breakdown + recent transactions
    for the authenticated mentor. Only paid bookings are counted."""
    from routes.membership import get_current_member
    from collections import defaultdict
    member = await get_current_member(request)
    mentor_id = member["member_id"]
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")
    this_month_prefix = today.strftime("%Y-%m")

    # All paid bookings for this mentor
    bookings = await db.mentorship_bookings.find(
        {"mentor_id": mentor_id, "payment_status": "paid"},
        {"_id": 0},
    ).sort("paid_at", -1).to_list(1000)

    total_cents = 0
    this_month_cents = 0
    pending_revenue_cents = 0  # paid but session date is in the future
    sessions_delivered = 0
    sessions_pending = 0
    monthly_map = defaultdict(lambda: {"revenue_cents": 0, "sessions": 0})
    transactions = []

    for b in bookings:
        slot = await db.mentorship_slots.find_one({"id": b["slot_id"]}, {"_id": 0})
        if not slot:
            continue
        cents = int(b.get("price_cents") or slot.get("price_cents") or 0)
        paid_at = b.get("paid_at") or b.get("booked_at") or ""
        month_key = paid_at[:7] if paid_at else today.strftime("%Y-%m")
        total_cents += cents
        monthly_map[month_key]["revenue_cents"] += cents
        monthly_map[month_key]["sessions"] += 1
        if paid_at.startswith(this_month_prefix):
            this_month_cents += cents
        slot_date = slot.get("date", "")
        if slot_date and slot_date < today_str:
            sessions_delivered += 1
        else:
            sessions_pending += 1
            pending_revenue_cents += cents
        if len(transactions) < 50:
            m = await db.members.find_one({"member_id": b["member_id"]}, {"_id": 0, "password_hash": 0})
            transactions.append({
                "booking_id": b.get("id"),
                "slot_id": b["slot_id"],
                "slot_date": slot_date,
                "slot_title": slot.get("title") or slot.get("session_type", "Mentorship"),
                "session_type": slot.get("session_type", ""),
                "member_name": f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() if m else "",
                "membership_id": m.get("membership_id", "") if m else "",
                "amount_cents": cents,
                "currency": (b.get("currency") or "usd"),
                "paid_at": paid_at,
                "status": "delivered" if (slot_date and slot_date < today_str) else "upcoming",
            })

    # Monthly breakdown — last 12 months (fill gaps with zeros)
    monthly = []
    for i in range(11, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        key = f"{y:04d}-{m:02d}"
        data = monthly_map.get(key, {"revenue_cents": 0, "sessions": 0})
        monthly.append({"month": key, "revenue_cents": data["revenue_cents"], "sessions": data["sessions"]})

    return {
        "currency": "usd",
        "total_revenue_cents": total_cents,
        "this_month_revenue_cents": this_month_cents,
        "pending_revenue_cents": pending_revenue_cents,
        "sessions_delivered": sessions_delivered,
        "sessions_pending": sessions_pending,
        "sessions_total": sessions_delivered + sessions_pending,
        "monthly_breakdown": monthly,
        "transactions": transactions,
    }

