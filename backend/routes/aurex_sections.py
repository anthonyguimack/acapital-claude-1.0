"""Aurex sections — generic CRUD for the 7 new one-page template sections.

Storage model
─────────────
  `aurex_section_configs`: one doc per section (title, subtitle, CTA, …)
  `aurex_section_items`:   N rows per section (cards / steps / plans / members / logos)
     {
       id: uuid,
       section: 'aurex_audience' | 'aurex_process' | 'aurex_pricing' |
                'aurex_team'     | 'aurex_partners' | 'aurex_clients',
       order: int,
       ...section-specific fields...
     }

The `aurex_events` section is **config-only** — events themselves live in the
existing `calendar_events` collection managed by AUX Calendar in My Account.
This endpoint only stores display preferences (max to show, CTA text, etc.).
"""
from datetime import datetime, timezone
import os
import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from routes.membership import require_admin

router = APIRouter()
client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

VALID_SECTIONS = {
    "aurex_audience", "aurex_process", "aurex_pricing",
    "aurex_team", "aurex_partners", "aurex_clients", "aurex_events", "aurex_video",
    # Config-only "section header" entries that let the admin edit title/
    # subtitle/CTA for legacy sections rendered by the Aurex mono variants.
    "aurex_services_cfg", "aurex_testimonials_cfg", "aurex_news_cfg",
    "aurex_blog_cfg", "aurex_locations_cfg",
}
ITEM_SECTIONS = VALID_SECTIONS - {
    "aurex_events", "aurex_video",
    "aurex_services_cfg", "aurex_testimonials_cfg", "aurex_news_cfg",
    "aurex_blog_cfg", "aurex_locations_cfg",
}


def _check(section: str):
    if section not in VALID_SECTIONS:
        raise HTTPException(status_code=404, detail=f"Unknown Aurex section: {section}")


# ── Section-level config (title, subtitle, CTA, etc.) ───────────────────

@router.get("/admin/aurex/{section}/config")
async def get_config(section: str, user=Depends(require_admin)):
    _check(section)
    doc = await db.aurex_section_configs.find_one({"section": section}, {"_id": 0})
    return doc or {"section": section}


@router.put("/admin/aurex/{section}/config")
async def save_config(section: str, body: dict, request: Request, user=Depends(require_admin)):
    _check(section)
    body["section"] = section
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.aurex_section_configs.update_one({"section": section}, {"$set": body}, upsert=True)
    return await db.aurex_section_configs.find_one({"section": section}, {"_id": 0})


# ── Items (cards / steps / plans / members / logos) ─────────────────────

@router.get("/admin/aurex/{section}/items")
async def list_items(section: str, user=Depends(require_admin)):
    if section not in ITEM_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Section {section} has no items")
    return await db.aurex_section_items.find({"section": section}, {"_id": 0}).sort("order", 1).to_list(500)


@router.post("/admin/aurex/{section}/items")
async def create_item(section: str, body: dict, user=Depends(require_admin)):
    if section not in ITEM_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Section {section} has no items")
    last = await db.aurex_section_items.find({"section": section}).sort("order", -1).limit(1).to_list(1)
    next_order = (last[0].get("order", 0) + 1) if last else 0
    body.update({
        "id": str(uuid.uuid4()),
        "section": section,
        "order": body.get("order", next_order),
        "visible": body.get("visible", True),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.aurex_section_items.insert_one(dict(body))
    body.pop("_id", None)
    return body


@router.put("/admin/aurex/{section}/items/{item_id}")
async def update_item(section: str, item_id: str, body: dict, user=Depends(require_admin)):
    if section not in ITEM_SECTIONS:
        raise HTTPException(status_code=400, detail="Section has no items")
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    body.pop("_id", None)
    body.pop("id", None)
    body.pop("section", None)
    r = await db.aurex_section_items.update_one({"id": item_id, "section": section}, {"$set": body})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return await db.aurex_section_items.find_one({"id": item_id}, {"_id": 0})


@router.delete("/admin/aurex/{section}/items/{item_id}")
async def delete_item(section: str, item_id: str, user=Depends(require_admin)):
    if section not in ITEM_SECTIONS:
        raise HTTPException(status_code=400, detail="Section has no items")
    r = await db.aurex_section_items.delete_one({"id": item_id, "section": section})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"deleted": True}


@router.put("/admin/aurex/{section}/reorder")
async def reorder_items(section: str, body: dict, user=Depends(require_admin)):
    """body = { order: [item_id_1, item_id_2, ...] }"""
    if section not in ITEM_SECTIONS:
        raise HTTPException(status_code=400, detail="Section has no items")
    order = body.get("order") or []
    for idx, item_id in enumerate(order):
        await db.aurex_section_items.update_one({"id": item_id, "section": section}, {"$set": {"order": idx}})
    return {"order": order}


# ── Public endpoint consumed by the Aurex frontend ───────────────────────

@router.get("/public/aurex/{section}")
async def public_section(section: str):
    _check(section)
    config = await db.aurex_section_configs.find_one({"section": section}, {"_id": 0}) or {}
    out = {"config": config}
    if section in ITEM_SECTIONS:
        out["items"] = await db.aurex_section_items.find(
            {"section": section, "visible": {"$ne": False}},
            {"_id": 0},
        ).sort("order", 1).to_list(500)
    elif section == "aurex_events":
        # Pull upcoming events from calendar_events, apply max_items + upcoming_only toggle
        max_items = int(config.get("max_items") or 5)
        only_upcoming = bool(config.get("only_upcoming", True))
        query = {}
        if only_upcoming:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            query["date"] = {"$gte": today}
        events = await db.calendar_events.find(query, {"_id": 0}).sort("date", 1).limit(max_items).to_list(max_items)
        out["items"] = events
    return out
