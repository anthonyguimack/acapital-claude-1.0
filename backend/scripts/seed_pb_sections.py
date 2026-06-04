"""
Seed realistic test data for all Personal Brand Pro sections.
Run with: python3 scripts/seed_pb_sections.py
Requires MONGO_URL and DB_NAME environment variables (same as backend .env).
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.environ.get("DB_NAME", "consultant_cms")

client = AsyncIOMotorClient(MONGO_URL)
db     = client[DB_NAME]

now = datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


async def upsert_config(section: str, data: dict):
    data["section"] = section
    data["updated_at"] = now.isoformat()
    await db.aurex_section_configs.update_one(
        {"section": section}, {"$set": data}, upsert=True
    )
    print(f"  ✓ config  → {section}")


async def seed_items(section: str, items: list):
    await db.aurex_section_items.delete_many({"section": section})
    for i, item in enumerate(items):
        item.setdefault("id", uid())
        item["section"] = section
        item["order"] = i
        item["visible"] = True
        item["created_at"] = now.isoformat()
    if items:
        await db.aurex_section_items.insert_many(items)
    print(f"  ✓ items   → {section} ({len(items)} items)")


# ─────────────────────────────────────────────────────────────────────────────
# Process
# ─────────────────────────────────────────────────────────────────────────────
async def seed_process():
    await upsert_config("aurex_process", {
        "eyebrow": "How it works",
        "title": "Our proven methodology",
        "subtitle": "A structured four-step framework that transforms insights into measurable results.",
    })
    await seed_items("aurex_process", [
        {
            "title": "Discovery & Assessment",
            "step_number": 1,
            "description": "We conduct a deep-dive audit of your current positioning, competitive landscape, and untapped opportunities. Every recommendation is grounded in data, not guesswork.",
        },
        {
            "title": "Strategy Blueprint",
            "step_number": 2,
            "description": "Using discovery insights, we craft a 90-day action plan with clear KPIs, channel priorities, and quick wins that build momentum from day one.",
        },
        {
            "title": "Execution & Launch",
            "step_number": 3,
            "description": "Our team activates the strategy across every chosen channel—content, partnerships, outreach—while you stay focused on your core work.",
        },
        {
            "title": "Optimize & Scale",
            "step_number": 4,
            "description": "We analyse performance weekly, double down on what works, and iteratively refine until your brand reaches consistent, compounding growth.",
        },
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Pricing
# ─────────────────────────────────────────────────────────────────────────────
async def seed_pricing():
    await upsert_config("aurex_pricing", {
        "eyebrow": "Investment",
        "title": "Simple, transparent pricing",
        "subtitle": "Choose the plan that fits your ambition. No hidden fees, no long-term lock-in.",
        "show_toggle": True,
    })
    await seed_items("aurex_pricing", [
        {
            "name": "Starter",
            "badge": "",
            "price": "1,500",
            "price_annual": "1,200",
            "currency": "$",
            "period": "/ month",
            "is_featured": False,
            "features": (
                "Brand audit & positioning report\n"
                "Monthly strategy session (60 min)\n"
                "Content calendar template\n"
                "Email support\n"
                "✗ Done-for-you content\n"
                "✗ Partnership introductions\n"
                "✗ Priority response (< 4 h)"
            ),
            "cta_text": "Get started",
            "cta_url": "#contact",
            "cta_new_tab": False,
        },
        {
            "name": "Growth",
            "badge": "Most popular",
            "price": "3,500",
            "price_annual": "2,800",
            "currency": "$",
            "period": "/ month",
            "is_featured": True,
            "features": (
                "Everything in Starter\n"
                "Bi-weekly strategy sessions\n"
                "Done-for-you content (8 posts)\n"
                "LinkedIn + newsletter management\n"
                "Partnership introductions (2/mo)\n"
                "Priority response (< 4 h)\n"
                "✗ Dedicated account manager"
            ),
            "cta_text": "Start growing",
            "cta_url": "#contact",
            "cta_new_tab": False,
        },
        {
            "name": "Authority",
            "badge": "White-glove",
            "price": "7,500",
            "price_annual": "6,000",
            "currency": "$",
            "period": "/ month",
            "is_featured": False,
            "features": (
                "Everything in Growth\n"
                "Unlimited strategy sessions\n"
                "Done-for-you content (20 posts)\n"
                "Speaker booking assistance\n"
                "Media & press outreach\n"
                "Partnership introductions (5/mo)\n"
                "Dedicated account manager"
            ),
            "cta_text": "Apply now",
            "cta_url": "#contact",
            "cta_new_tab": False,
        },
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Events (config only — events come from Calendar)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_events():
    await upsert_config("aurex_events", {
        "eyebrow": "Mark your calendar",
        "title": "Upcoming events",
        "subtitle": "Live sessions, masterclasses, and networking opportunities — all free for members.",
        "view_text": "Register",
        "view_all_text": "View all events",
        "view_all_url": "/my-account/calendar",
        "max_items": 5,
        "only_upcoming": True,
        "empty_message": "New events coming soon — check back shortly.",
    })
    # Optionally seed a few calendar_events so something shows
    existing = await db.calendar_events.count_documents({})
    if existing == 0:
        base_date = now + timedelta(days=7)
        sample_events = [
            {
                "id": uid(), "title": "Brand Positioning Masterclass",
                "date": (base_date).strftime("%Y-%m-%d"),
                "start_time": "14:00", "end_time": "15:30",
                "location": "Zoom (link sent on registration)",
                "created_at": now.isoformat(),
            },
            {
                "id": uid(), "title": "LinkedIn Authority Workshop",
                "date": (base_date + timedelta(days=10)).strftime("%Y-%m-%d"),
                "start_time": "10:00", "end_time": "11:00",
                "location": "Online",
                "created_at": now.isoformat(),
            },
            {
                "id": uid(), "title": "Members Networking Call",
                "date": (base_date + timedelta(days=20)).strftime("%Y-%m-%d"),
                "start_time": "18:00", "end_time": "19:00",
                "location": "Google Meet",
                "created_at": now.isoformat(),
            },
        ]
        await db.calendar_events.insert_many(sample_events)
        print(f"  ✓ events  → calendar_events (3 sample events)")
    else:
        print(f"  ✓ events  → aurex_events config (calendar already has {existing} events)")


# ─────────────────────────────────────────────────────────────────────────────
# Partners
# ─────────────────────────────────────────────────────────────────────────────
async def seed_partners():
    await upsert_config("aurex_partners", {
        "eyebrow": "Ecosystem",
        "title": "Our strategic partners",
        "subtitle": "We collaborate with industry-leading organisations to amplify every client outcome.",
        "autoscroll": True,
        "scroll_speed": 30,
    })
    await seed_items("aurex_partners", [
        {"name": "Acapital Group",       "logo_url": "", "link_url": ""},
        {"name": "Aurex Network",        "logo_url": "", "link_url": ""},
        {"name": "Elevate Media Co.",    "logo_url": "", "link_url": ""},
        {"name": "Strategos Advisory",   "logo_url": "", "link_url": ""},
        {"name": "Northvault Capital",   "logo_url": "", "link_url": ""},
        {"name": "Meridian Consulting",  "logo_url": "", "link_url": ""},
        {"name": "Apex Digital Studio",  "logo_url": "", "link_url": ""},
        {"name": "Growth Architects",    "logo_url": "", "link_url": ""},
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────────────────────────────────────
async def seed_clients():
    await upsert_config("aurex_clients", {
        "eyebrow": "Trusted by",
        "title": "Clients who transformed their brand",
        "subtitle": "Independent professionals and organisations across 12 industries.",
        "autoscroll": True,
        "scroll_speed": 28,
    })
    await seed_items("aurex_clients", [
        {"name": "Luminary Ventures",     "logo_url": "", "link_url": ""},
        {"name": "Pinnacle RE Group",     "logo_url": "", "link_url": ""},
        {"name": "Solaris Finance",       "logo_url": "", "link_url": ""},
        {"name": "ClearPath Analytics",  "logo_url": "", "link_url": ""},
        {"name": "Ember Creative Lab",    "logo_url": "", "link_url": ""},
        {"name": "Verdant Wealth Mgmt",  "logo_url": "", "link_url": ""},
        {"name": "Nexus Talent Group",   "logo_url": "", "link_url": ""},
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Video
# ─────────────────────────────────────────────────────────────────────────────
async def seed_video():
    await upsert_config("aurex_video", {
        "eyebrow": "See it in action",
        "title": "What we do — in 90 seconds",
        "subtitle": "A quick overview of how we help independent professionals build authority and attract premium clients.",
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "aspect_ratio": "16/9",
        "autoplay": False,
    })
    print("  ✓ config  → aurex_video")


# ─────────────────────────────────────────────────────────────────────────────
# Section configs for News & Blog
# ─────────────────────────────────────────────────────────────────────────────
async def seed_news_blog_cfg():
    await upsert_config("aurex_news_cfg", {
        "eyebrow": "Insights",
        "title": "From the newsroom",
        "subtitle": "Strategy, trends, and expert perspectives — curated for ambitious professionals.",
        "cta_text": "Read all articles",
        "cta_url": "/news",
        "cta_new_tab": False,
    })
    await upsert_config("aurex_blog_cfg", {
        "eyebrow": "From the blog",
        "title": "Thinking out loud",
        "subtitle": "Long-form essays on brand building, influence, and what it takes to lead in your field.",
        "cta_text": "Visit blog",
        "cta_url": "#",
        "cta_new_tab": True,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Audience section (if empty)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_audience():
    existing = await db.aurex_section_items.count_documents({"section": "aurex_audience"})
    if existing > 0:
        print(f"  ✓ skipped → aurex_audience ({existing} items already present)")
        return
    await upsert_config("aurex_audience", {
        "eyebrow": "Who we serve",
        "title": "Built for independent leaders",
        "subtitle": "Whether you're a consultant, investor, or creative — we help you stand out and scale.",
        "cta_text": "See if we're a fit",
        "cta_url": "#contact",
        "cta_new_tab": False,
    })
    await seed_items("aurex_audience", [
        {
            "eyebrow": "Consultants",
            "icon": "briefcase",
            "title": "Independent Consultants",
            "description": "Build the thought-leadership presence that commands premium retainers and shortens your sales cycle.",
        },
        {
            "eyebrow": "Investors",
            "icon": "trending-up",
            "title": "Investment Professionals",
            "description": "Establish credibility, attract deal flow, and position yourself as the go-to voice in your asset class.",
        },
        {
            "eyebrow": "Creators",
            "icon": "pen-tool",
            "title": "Content Creators",
            "description": "Turn your expertise into a scalable media brand that opens doors to sponsorships, courses, and speaking.",
        },
        {
            "eyebrow": "Executives",
            "icon": "users",
            "title": "C-Suite Leaders",
            "description": "Develop a personal brand that extends your company's reach and cements your legacy beyond any single role.",
        },
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Testimonials section config (if missing)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_testimonials_cfg():
    await upsert_config("aurex_testimonials_cfg", {
        "eyebrow": "Real testimonials",
        "title": "What our clients say",
        "subtitle": "Hear directly from the professionals who've transformed their brand with our guidance.",
        "cta_text": "Read more reviews",
        "cta_url": "/testimonials",
        "cta_new_tab": False,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Services config (if missing)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_services_cfg():
    await upsert_config("aurex_services_cfg", {
        "eyebrow": "Our quality services",
        "title": "Everything you need to scale",
        "subtitle": "From brand strategy to content production — we handle the heavy lifting so you can focus on your zone of genius.",
        "cta_text": "Explore all services",
        "cta_url": "#contact",
        "cta_new_tab": False,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Reading List config (if missing)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_reading_cfg():
    await upsert_config("aurex_reading_cfg", {
        "eyebrow": "Curated reading",
        "title": "Books that shaped our thinking",
        "subtitle": "The essential titles every ambitious professional should have on their shelf.",
        "cta_text": "View full reading list",
        "cta_url": "/reading-list",
        "cta_new_tab": False,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio config (if missing)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_portfolio_cfg():
    await upsert_config("aurex_portfolio_cfg", {
        "eyebrow": "Featured work",
        "title": "Client success stories",
        "subtitle": "A selection of brand transformations across consulting, finance, and creative industries.",
        "cta_text": "View all projects",
        "cta_url": "/featured-projects",
        "cta_new_tab": False,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Gallery config (if missing)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_gallery_cfg():
    await upsert_config("aurex_gallery_cfg", {
        "eyebrow": "Moments",
        "title": "Behind the scenes",
        "subtitle": "Workshops, conferences, and the everyday work of building great brands.",
        "cta_text": "See all photos",
        "cta_url": "/gallery",
        "cta_new_tab": False,
    })


# ─────────────────────────────────────────────────────────────────────────────
# News posts (if empty)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_news():
    existing = await db.blog_posts.count_documents({})
    if existing > 0:
        print(f"  ✓ skipped → blog_posts ({existing} posts already present)")
        return
    posts = [
        {
            "id": uid(),
            "title": "How to Build a $1M Personal Brand in 12 Months",
            "slug": "build-1m-personal-brand-12-months",
            "summary": "The exact framework we used to take three clients from zero to industry recognition in under a year.",
            "content": "<p>Building a personal brand that commands premium fees requires three things: clarity, consistency, and credibility. Here's how we approach it...</p>",
            "image": "",
            "published": True,
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": (now - timedelta(days=5)).isoformat(),
        },
        {
            "id": uid(),
            "title": "The LinkedIn Algorithm Decoded: 2026 Edition",
            "slug": "linkedin-algorithm-2026",
            "summary": "What actually moves the needle on LinkedIn today — and how to engineer content that reaches decision-makers.",
            "content": "<p>The algorithm has shifted dramatically in 2026. Here's what our data from 47 client accounts tells us...</p>",
            "image": "",
            "published": True,
            "created_at": (now - timedelta(days=12)).isoformat(),
            "updated_at": (now - timedelta(days=12)).isoformat(),
        },
        {
            "id": uid(),
            "title": "Why Most Consultants Undercharge (And How to Fix It)",
            "slug": "consultants-undercharge-how-to-fix",
            "summary": "Pricing psychology for independent professionals — a practical guide to doubling your rates without losing clients.",
            "content": "<p>The biggest obstacle to higher fees isn't the market — it's positioning. Once you fix this, everything changes...</p>",
            "image": "",
            "published": True,
            "created_at": (now - timedelta(days=20)).isoformat(),
            "updated_at": (now - timedelta(days=20)).isoformat(),
        },
    ]
    await db.blog_posts.insert_many(posts)
    print(f"  ✓ seeded  → blog_posts (3 posts)")


# ─────────────────────────────────────────────────────────────────────────────
# Team config (if missing)
# ─────────────────────────────────────────────────────────────────────────────
async def seed_team_config():
    existing = await db.aurex_section_configs.find_one({"section": "aurex_team"})
    if existing and existing.get("title"):
        print(f"  ✓ skipped → aurex_team config (already has title)")
        return
    await upsert_config("aurex_team", {
        "eyebrow": "The people behind the results",
        "title": "Meet our team",
        "subtitle": "Specialists in brand strategy, content, partnerships, and growth — all working in service of your success.",
        "show_view_all": False,
        "view_all_text": "View full team",
        "view_all_url": "/team",
        "max_visible": 6,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    print("\n🌱  Seeding Personal Brand Pro sections...\n")

    await seed_audience()
    await seed_process()
    await seed_pricing()
    await seed_events()
    await seed_partners()
    await seed_clients()
    await seed_video()
    await seed_news_blog_cfg()
    await seed_news()
    await seed_team_config()
    await seed_testimonials_cfg()
    await seed_services_cfg()
    await seed_reading_cfg()
    await seed_portfolio_cfg()
    await seed_gallery_cfg()

    print("\n✅  Seeding complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
