"""iCal (.ics) subscription feeds — personal per-member calendar subscription URLs.

Generates an RFC 5545 VCALENDAR containing the member's booked mentorship slots
and registered global events using floating local time (no TZID) so each
calendar app renders it in the user's local timezone.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from models.database import db
from datetime import datetime, timezone
import uuid
import secrets

router = APIRouter()


def _escape(text: str) -> str:
    """Escape iCal special chars per RFC 5545."""
    if not text:
        return ""
    # Strip HTML tags (descriptions are stored as rich HTML)
    import re
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return (
        text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold lines over 75 octets per RFC 5545."""
    if len(line) <= 75:
        return line
    parts = []
    remaining = line
    while len(remaining) > 75:
        parts.append(remaining[:75])
        remaining = remaining[75:]
    parts.append(remaining)
    return "\r\n ".join(parts)


def _dt_floating(date_str: str, time_str: str) -> str:
    """Produce a floating local DATE-TIME: YYYYMMDDTHHMMSS."""
    try:
        d = date_str.replace("-", "")
        t = (time_str or "00:00").replace(":", "") + "00"
        return f"{d}T{t[:6]}"
    except Exception:
        return "19700101T000000"


def _build_vevent(uid: str, dtstamp: str, date_str: str, start_time: str, end_time: str,
                  summary: str, description: str = "", location: str = "", url: str = "") -> list:
    """Return a list of lines for a single VEVENT component."""
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{_dt_floating(date_str, start_time)}",
        f"DTEND:{_dt_floating(date_str, end_time or start_time)}",
        f"SUMMARY:{_escape(summary)}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")
    if location:
        lines.append(f"LOCATION:{_escape(location)}")
    if url:
        lines.append(f"URL:{_escape(url)}")
    lines.append("END:VEVENT")
    return [_fold(line) for line in lines]


async def _ensure_ical_token(member_id: str) -> str:
    """Generate (if missing) and return the member's opaque iCal subscription token."""
    member = await db.members.find_one({"member_id": member_id}, {"_id": 0, "ical_token": 1})
    if member and member.get("ical_token"):
        return member["ical_token"]
    token = secrets.token_urlsafe(24)
    await db.members.update_one({"member_id": member_id}, {"$set": {"ical_token": token}})
    return token


async def _build_calendar_for_member(member_id: str) -> str:
    """Compose the full VCALENDAR string for this member's booked slots + registered events."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Consultant Platform//Calendar Sync 1.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:My Consultant Schedule",
        "X-WR-CALDESC:Booked mentorship sessions and registered global events",
    ]
    # Mentorship bookings — booked only (exclude waitlist + cancelled)
    bookings = await db.mentorship_bookings.find(
        {"member_id": member_id, "status": {"$in": ["booked", "completed"]}},
        {"_id": 0},
    ).to_list(500)
    for b in bookings:
        slot = await db.mentorship_slots.find_one({"id": b["slot_id"]}, {"_id": 0})
        if not slot or slot.get("status") == "cancelled":
            continue
        mentor = await db.members.find_one({"member_id": slot.get("mentor_id")}, {"_id": 0, "password_hash": 0})
        mentor_name = f"{mentor.get('first_name', '')} {mentor.get('last_name', '')}".strip() if mentor else ""
        summary = slot.get("title") or f"{slot.get('session_type', 'Mentorship')} with {mentor_name}".strip()
        lines.extend(_build_vevent(
            uid=f"slot-{slot['id']}@consultant",
            dtstamp=stamp,
            date_str=slot.get("date", ""),
            start_time=slot.get("start_time", ""),
            end_time=slot.get("end_time", ""),
            summary=summary,
            description=slot.get("description", ""),
            location="",
            url=slot.get("virtual_link", ""),
        ))
    # Global event registrations — registered only (not waitlist)
    regs = await db.event_registrations.find(
        {"member_id": member_id, "status": "registered"},
        {"_id": 0},
    ).to_list(500)
    for r in regs:
        event = await db.calendar_events.find_one({"id": r["event_id"]}, {"_id": 0})
        if not event or event.get("status") == "cancelled":
            continue
        lines.extend(_build_vevent(
            uid=f"event-{event['id']}@consultant",
            dtstamp=stamp,
            date_str=event.get("date", ""),
            start_time=event.get("start_time", ""),
            end_time=event.get("end_time", ""),
            summary=event.get("title", "Event"),
            description=event.get("description", ""),
            location=event.get("location", ""),
            url=event.get("virtual_link") or event.get("map_url", ""),
        ))
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


@router.get("/ical/{token}.ics")
async def get_ical_feed(token: str):
    """Public: serve the VCALENDAR. Authenticated by the opaque token in the URL."""
    member = await db.members.find_one({"ical_token": token}, {"_id": 0, "member_id": 1})
    if not member:
        raise HTTPException(status_code=404, detail="Calendar not found")
    ics = await _build_calendar_for_member(member["member_id"])
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'inline; filename="my-schedule.ics"',
            "Cache-Control": "no-cache, must-revalidate",
        },
    )


@router.get("/member/ical/info")
async def member_ical_info(request: Request):
    """Return the member's subscription URL. Generates the token on first call."""
    from routes.membership import get_current_member
    member = await get_current_member(request)
    token = await _ensure_ical_token(member["member_id"])
    return {"token": token, "path": f"/api/ical/{token}.ics"}


@router.post("/member/ical/regenerate")
async def member_ical_regenerate(request: Request):
    """Rotate the token — old URL stops working immediately."""
    from routes.membership import get_current_member
    member = await get_current_member(request)
    token = secrets.token_urlsafe(24)
    await db.members.update_one({"member_id": member["member_id"]}, {"$set": {"ical_token": token}})
    return {"token": token, "path": f"/api/ical/{token}.ics"}
