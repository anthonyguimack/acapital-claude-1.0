"""Global Events — admin CRUD + member registration + notifications."""
from fastapi import APIRouter, HTTPException, Request, Depends
from models.database import db, require_admin
from routes.calendar_helpers import notify_waitlist_spot_open, notify_cancellation
from datetime import datetime, timezone
import uuid

router = APIRouter()


# ── Admin: Global Events CRUD ──

@router.get("/admin/calendar/events")
async def admin_list_events(user: dict = Depends(require_admin)):
    events = await db.calendar_events.find({}, {"_id": 0}).sort("date", -1).to_list(500)
    for e in events:
        e["registered_count"] = await db.event_registrations.count_documents({"event_id": e["id"], "status": "registered"})
        e["waitlist_count"] = await db.event_registrations.count_documents({"event_id": e["id"], "status": "waitlist"})
    return events


@router.post("/admin/calendar/events")
async def admin_create_event(request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    body["id"] = str(uuid.uuid4())
    body.setdefault("status", "active")
    body.setdefault("max_capacity", 50)
    body.setdefault("image", "")
    body.setdefault("location", "")
    body.setdefault("map_url", "")
    body.setdefault("virtual_link", "")
    body.setdefault("description", "")
    body.setdefault("attachments", [])
    body.setdefault("member_uploads", [])
    body["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.calendar_events.insert_one(body)
    result = await db.calendar_events.find_one({"id": body["id"]}, {"_id": 0})
    result["registered_count"] = 0
    result["waitlist_count"] = 0
    return result


@router.get("/admin/calendar/events/{event_id}")
async def admin_get_event(event_id: str, user: dict = Depends(require_admin)):
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event["registered_count"] = await db.event_registrations.count_documents({"event_id": event_id, "status": "registered"})
    return event


@router.put("/admin/calendar/events/{event_id}")
async def admin_update_event(event_id: str, request: Request, user: dict = Depends(require_admin)):
    body = await request.json()
    old_event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    body.pop("id", None)
    body.pop("_id", None)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    if old_event and old_event.get("status") != "cancelled" and body.get("status") == "cancelled":
        await notify_cancellation(db.event_registrations, event_id, "event_id", old_event.get("title", ""), "event")
    result = await db.calendar_events.update_one({"id": event_id}, {"$set": body})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    event["registered_count"] = await db.event_registrations.count_documents({"event_id": event_id, "status": "registered"})
    return event


@router.delete("/admin/calendar/events/{event_id}")
async def admin_delete_event(event_id: str, user: dict = Depends(require_admin)):
    await db.calendar_events.delete_one({"id": event_id})
    await db.event_registrations.delete_many({"event_id": event_id})
    return {"success": True}


@router.post("/admin/calendar/events/{event_id}/clone")
async def admin_clone_event(event_id: str, user: dict = Depends(require_admin)):
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    clone = {k: v for k, v in event.items()}
    clone["id"] = str(uuid.uuid4())
    clone["title"] = f"{event.get('title', '')} (Copy)"
    clone["status"] = "inactive"
    clone["created_at"] = datetime.now(timezone.utc).isoformat()
    clone.pop("updated_at", None)
    clone.pop("member_uploads", None)
    await db.calendar_events.insert_one(clone)
    result = await db.calendar_events.find_one({"id": clone["id"]}, {"_id": 0})
    result["registered_count"] = 0
    result["waitlist_count"] = 0
    return result


@router.get("/admin/calendar/events/{event_id}/registrations")
async def admin_event_registrations(event_id: str, user: dict = Depends(require_admin)):
    regs = await db.event_registrations.find({"event_id": event_id}, {"_id": 0}).sort("registered_at", 1).to_list(1000)
    for r in regs:
        member = await db.members.find_one({"member_id": r["member_id"]}, {"_id": 0, "password_hash": 0})
        if member:
            r["membership_id"] = member.get("membership_id", "")
            r["name"] = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
            r["email"] = member.get("email", "")
    return regs


@router.get("/admin/calendar/events/{event_id}/registrations/csv")
async def admin_event_registrations_csv(event_id: str, user: dict = Depends(require_admin)):
    from fastapi.responses import StreamingResponse
    import io
    import csv
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    event_title = event.get("title", "Event") if event else "Event"
    event_date = event.get("date", "") if event else ""
    regs = await db.event_registrations.find({"event_id": event_id}, {"_id": 0}).sort("registered_at", 1).to_list(1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f"Event: {event_title}", f"Date: {event_date}"])
    writer.writerow(["#", "Membership ID", "Name", "Email", "Registered At", "Status"])
    for i, r in enumerate(regs, 1):
        member = await db.members.find_one({"member_id": r["member_id"]}, {"_id": 0, "password_hash": 0})
        name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip() if member else ""
        writer.writerow([i, member.get("membership_id", "") if member else "", name, member.get("email", "") if member else "", r.get("registered_at", ""), r.get("status", "")])
    output.seek(0)
    safe_title = event_title.replace(" ", "_").replace("/", "-")[:50]
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={safe_title}_{event_date}_registrations.csv"})


# ── Member: Event Access ──

@router.get("/member/calendar/events")
async def member_list_events(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    events = await db.calendar_events.find({"status": {"$in": ["active"]}}, {"_id": 0}).sort("date", 1).to_list(500)
    member_id = member["member_id"]
    for e in events:
        e["registered_count"] = await db.event_registrations.count_documents({"event_id": e["id"], "status": "registered"})
        e["waitlist_count"] = await db.event_registrations.count_documents({"event_id": e["id"], "status": "waitlist"})
        my_reg = await db.event_registrations.find_one({"event_id": e["id"], "member_id": member_id}, {"_id": 0})
        e["my_status"] = my_reg["status"] if my_reg else None
    return events


@router.get("/member/calendar/events/{event_id}")
async def member_get_event(event_id: str, request: Request):
    """Get single event detail for the detail page."""
    from routes.membership import get_current_member
    member = await get_current_member(request)
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event["registered_count"] = await db.event_registrations.count_documents({"event_id": event_id, "status": "registered"})
    event["waitlist_count"] = await db.event_registrations.count_documents({"event_id": event_id, "status": "waitlist"})
    my_reg = await db.event_registrations.find_one({"event_id": event_id, "member_id": member["member_id"]}, {"_id": 0})
    event["my_status"] = my_reg["status"] if my_reg else None
    return event


@router.post("/member/calendar/events/{event_id}/register")
async def member_register_event(event_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.get("status") != "active":
        raise HTTPException(status_code=400, detail="Event is not active")
    existing = await db.event_registrations.find_one({"event_id": event_id, "member_id": member["member_id"]})
    if existing and existing.get("status") == "registered":
        raise HTTPException(status_code=400, detail="Already registered for this event")
    registered_count = await db.event_registrations.count_documents({"event_id": event_id, "status": "registered"})
    max_cap = event.get("max_capacity", 50)
    if existing and existing.get("status") == "waitlist" and registered_count < max_cap:
        await db.event_registrations.update_one({"event_id": event_id, "member_id": member["member_id"]}, {"$set": {"status": "registered", "registered_at": datetime.now(timezone.utc).isoformat()}})
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "member_id": member["member_id"], "type": "event_registration",
            "title": "Registration Confirmed", "message": f"You are now registered for \"{event.get('title', '')}\".",
            "link": "/my-account/global-calendar", "read": False, "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"success": True, "status": "registered"}
    if existing:
        raise HTTPException(status_code=400, detail="Already on the waiting list")
    status = "registered" if registered_count < max_cap else "waitlist"
    reg = {
        "id": str(uuid.uuid4()),
        "event_id": event_id,
        "member_id": member["member_id"],
        "status": status,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.event_registrations.insert_one(reg)
    msg = f"You have been {'registered for' if status == 'registered' else 'added to the waiting list for'} \"{event.get('title', '')}\"."
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": member["member_id"],
        "type": "event_registration",
        "title": "Event Registration" if status == "registered" else "Waiting List",
        "message": msg,
        "link": "/my-account/global-calendar",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"success": True, "status": status}


@router.post("/member/calendar/events/{event_id}/cancel")
async def member_cancel_event(event_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    reg = await db.event_registrations.find_one({"event_id": event_id, "member_id": member["member_id"]})
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    was_registered = reg.get("status") == "registered"
    await db.event_registrations.delete_one({"event_id": event_id, "member_id": member["member_id"]})
    if was_registered:
        event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
        await notify_waitlist_spot_open(db.event_registrations, event_id, "event_id", event.get("title", ""), "/my-account/global-calendar")
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": member["member_id"],
        "type": "event_cancellation",
        "title": "Registration Cancelled",
        "message": f"Your registration for \"{event.get('title', '')}\" has been cancelled.",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"success": True}


@router.post("/member/calendar/events/{event_id}/upload")
async def member_upload_event_file(event_id: str, request: Request):
    """Members can upload files to events they are registered for."""
    from routes.membership import get_current_member
    member = await get_current_member(request)
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    body = await request.json()
    upload = {
        "id": str(uuid.uuid4()),
        "member_id": member["member_id"],
        "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
        "membership_id": member.get("membership_id", ""),
        "url": body.get("url", ""),
        "name": body.get("name", ""),
        "size": body.get("size", 0),
        "content_type": body.get("content_type", ""),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.calendar_events.update_one({"id": event_id}, {"$push": {"member_uploads": upload}})
    return {"success": True}


# ── Notifications ──

@router.get("/member/notifications")
async def member_notifications(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    notifs = await db.notifications.find({"member_id": member["member_id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return notifs


@router.get("/member/notifications/unread-count")
async def member_unread_count(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    count = await db.notifications.count_documents({"member_id": member["member_id"], "read": False})
    return {"count": count}


@router.put("/member/notifications/{notif_id}/read")
async def member_mark_read(notif_id: str, request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    await db.notifications.update_one({"id": notif_id, "member_id": member["member_id"]}, {"$set": {"read": True}})
    return {"success": True}


@router.put("/member/notifications/read-all")
async def member_mark_all_read(request: Request):
    from routes.membership import get_current_member
    member = await get_current_member(request)
    await db.notifications.update_many({"member_id": member["member_id"], "read": False}, {"$set": {"read": True}})
    return {"success": True}
