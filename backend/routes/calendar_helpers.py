"""Shared notification helpers for calendar_events and mentor_slots routes."""
from models.database import db
from datetime import datetime, timezone
import uuid


async def notify_waitlist_spot_open(collection, item_id, item_id_field, title, link="/my-account/global-calendar"):
    """Notify ALL waitlisted members that a spot opened (they keep their waitlist status and can book)."""
    waitlisted = await collection.find({item_id_field: item_id, "status": "waitlist"}, {"_id": 0}).to_list(500)
    for w in waitlisted:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "member_id": w["member_id"],
            "type": "spot_available",
            "title": "Spot Available!",
            "message": f"A spot opened up for \"{title}\". Visit the calendar to register before it fills up!",
            "link": link,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


async def notify_cancellation(collection, item_id, item_id_field, title, cancel_type="event"):
    """Notify all registered + waitlisted members that event/slot was cancelled."""
    regs = await collection.find({item_id_field: item_id}, {"_id": 0}).to_list(1000)
    for r in regs:
        cancelled_by = "the mentor" if cancel_type == "slot" else "the administrator"
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "member_id": r["member_id"],
            "type": f"{cancel_type}_cancelled_by_admin",
            "title": f"{cancel_type.capitalize()} Cancelled",
            "message": f"\"{title}\" has been cancelled by {cancelled_by}.",
            "link": "/my-account/global-calendar" if cancel_type == "event" else "/my-account/my-bookings",
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
