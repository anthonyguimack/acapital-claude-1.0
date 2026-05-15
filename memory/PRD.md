# Consultant CMS - Product Requirements Document

## Original Problem Statement
Multi-page consultant website with CMS admin panel, Stripe payments, Theme Engine, Visual Page Builder, Maps management, and Landing Page.

## Tech Stack
- **Frontend**: React, TailwindCSS, Shadcn/UI, @dnd-kit, Framer Motion, react-leaflet, react-leaflet-cluster, React-Quill
- **Backend**: FastAPI, Motor (Async MongoDB), Pydantic, APIRouter
- **Database**: MongoDB | **Auth**: JWT + Google OAuth | **Payments**: Stripe


## Latest Update (Feb 5, 2026)
**Personal Brand Pro template + Reading List + QR/captcha refinements**
- Removed captcha (and its backend hook) from `/membership-enrollment` per operator preference — funnel kept only the 5/min/IP rate limit. Welcome / contact / register / forgot-password still have captcha.
- **My Account → Invite Code** now auto-regenerates the QR on mount so the displayed `register?sponsor=…` URL always reflects the current CMS Site URL (no stale cluster URLs from before the operator set Site URL).
- **CMS → Members → Generate QR** + **My Account → Invite Code → Generate QR** both go through `get_site_url()` → CMS Settings wins over Origin/`base_url`. Verified end-to-end with a non-trivial Site URL.
- New theme **Personal Brand Pro** (id `personalbrand`) added to Settings → Themes selector and Page Builder "Editing" dropdown. Shares the entire Aurex One-page section library (Hero, About, Services, News, Blog, Reading List, Audience, Process, Video, Pricing, Team, Testimonials, Events, Partners, Clients, Map, Contact) with a warm cream/terracotta default palette (overridable from Settings → Colors → Website). Each theme keeps its own `section_configs` and `section_orders` scope so layouts don't collide.
- Helper `isAurexFamily(themeId)` introduced in `lib/themeColors.js` so `theme === 'aurex' || theme === 'personalbrand'` is centralised. `Navbar`, `HeroSection`, `HomePage`, `SectionOrderManager` all routed through it.
- Reading List section confirmed wired into the Aurex section map and now appears by default in the Page Builder for both Aurex One-page and Personal Brand Pro scopes.

## Latest Update (Feb 4, 2026 — evening)
**reCAPTCHA + rate-limit + UX/email polish**
- New CMS section **Settings → Captcha**: enable toggle, site key, secret key, version v2 (with Google admin link). Keys persisted in `captcha_settings` Mongo collection. Public endpoint `/api/public/captcha-config` exposes only `enabled` + `site_key` (never the secret).
- Backend `utils/captcha.py` — Google siteverify integration, fail-closed when enabled-but-not-configured, no-op when disabled.
- `utils/rate_limit.py` adds `public_form_guard()` combining 5 req/min/IP throttle + captcha verification. Applied to **every** public POST: `/api/contact`, `/api/member/register`, `/api/public/enrollment/submit`, `/api/public/landing-subscribe`, `/api/public/landing-contact`. Login also throttled at 5/min/IP (no captcha).
- New `<CaptchaWidget>` React component pulls config dynamically, renders or hides itself, exposes a `reset()` ref for failed-submit retry. Wired into Aurex contact form, all 3 HomePage themes (modern/classic/default), Landing Page contact + waitlist, Member Register, Membership Enrollment, Forgot Password.
- **Forgot/Reset password pages** restyled to use the My Account theme variables (`--ma-page-bg`, `--ma-button-bg`, `--ma-button-text`, `--ma-accent`, `--ma-input-bg`, `--ma-text-primary/secondary/muted`) so colours track the operator's CMS choices.
- **Email rendering fixes**:
  - i18n `brand_name` dicts (e.g. `{"en": "Aurex Network"}`) now flatten correctly via `resolve_i18n()` — no more `'dict' object has no attribute 'replace'` on SMTP test.
  - `{{platform_name}}` always resolves from CMS Settings → General first (sample defaults lose).
  - `{{site_url}}` auto-injected from CMS Settings → General; sample `https://example.com/...` URLs in template registries are rewritten to use the configured Site URL so previews + test sends point at the real domain.

## Latest Update (Feb 4, 2026 — afternoon)
**Email Management refinements**
- New 6th template **SMTP Test Email** (key `smtp_test`) — variables: `{{recipient_email}}`, `{{platform_name}}`, `{{sent_at}}`. The legacy `POST /api/admin/smtp/test-email` endpoint now renders through this template + the configured branding so the operator sees exactly what customers will see.
- Templates tab layout: Live Preview moved into the middle column directly below the editor (no more right-column scrolling). Right column now sticky-positioned and contains only the Available Variables panel.
- General Design: added **Font family** dropdown — Inter, Sora, Playfair, Space Grotesk, DM Sans — same options as Section → Page Builder → Font. Choice is stored on `email_branding` (defaults to Inter), embedded as a Google Fonts `@import` in every email head, and applied to body text, headings (`h1-h6`) and the branded button. Email-client fallback stack remains (e.g. `'Sora', Arial, sans-serif`).

## Latest Update (Feb 4, 2026)
**Email Management + admin idempotency + reset rate-limit**
- New CMS section **Settings → Email Management** with two tabs:
  - **Templates** — list/edit subject + rich-text body for the 5 transactional emails (`password_reset`, `welcome_register`, `welcome_enrollment`, `invite_code`, `contact_form_admin`). Per-template variables panel, live preview iframe, "Send test" button, reset-to-default, enable/disable toggle.
  - **General Design** — branding wrapper (logo, primary color, button color, button text color, footer text with `{{platform_name}}` support, optional social links). Wrapper auto-applied around every sent email; live sample preview.
- Backend: `models/email_templates.py` (registry), `utils/email_render.py` (render + branding wrapper), `routes/email_templates.py` (CRUD + preview + test-send). Templates idempotent-seeded on startup.
- All 5 email send-sites refactored to call `render_and_send(key, settings, to, name, variables)` so the operator's edits actually take effect without changing *when* emails fire.
- Reset-link spam protection: `POST /api/auth/forgot-password` now rate-limited to 3 requests / 15 min per IP (in-memory sliding window, honours `X-Forwarded-For`). Verified end-to-end: requests 1-3 → 200, 4-5 → 429.
- **Admin duplicate bug fixed**: `seed_data` now uses `role: "admin"` lookup instead of email lookup, so changing `ADMIN_EMAIL` in `.env` no longer creates a second admin. Existing duplicates are auto-collapsed on startup (kept the one matching env, deleted the rest, logged warning). Belt-and-brace guard added to the insert path.

## Latest Update (Feb 3, 2026)
**Forgot Password flow — COMPLETED**
- Routes registered in `App.js`: `/my-account/forgot-password` and `/my-account/reset-password`
- Frontend pages: `MemberForgotPassword.js` (email entry → neutral success message), `MemberResetPassword.js` (verifies token on mount, dual-confirm new password, single-use redemption)
- Backend endpoints (already present): `POST /api/auth/forgot-password`, `GET /api/auth/reset-password/verify`, `POST /api/auth/reset-password`
- Tokens are 30-min expiry, single-use, stored in `password_resets` collection
- Email delivery wired through `send_email_smtp` (auto-fires when CMS Settings → SMTP host is configured); reset URL uses `Settings → site_url` falling back to request Origin
- Verified end-to-end via curl: request → fetch token from DB → verify → reset → re-verify (returns `used`) → login with new password ✓
- Frontend smoke-tested: both pages render, invalid token shows "Link not valid" panel

## What's Been Implemented

### Core (Phase 1-2)
Full public website, admin CMS, Visual Page Builder (16 content blocks), Theme Engine, Dynamic Pages, SMTP config, External Blog API, Backup/Restore, Gallery, Portfolio, Maps (3 types + clustering), Reading List, Blog Categories CRUD

### Landing Page Module (Apr 9, 2026)
**5-Section Layout:**
1. **Header/Nav** — Fixed, logo left + 4 nav links right, mobile hamburger
2. **Hero** — 2-column: Left (title, countdown, subtitle, description, multi-buttons), Right (video/photo embed). Background overlay toggle.
3. **Get in Touch** — 2-column: Left (image), Right (form: Name/Email/Subject/Message). Saves to `landing_contacts`.
4. **Waiting List** — White bg, centered form (Name/Last Name/Email). Saves to `landing_subscribers`.
5. **Footer** — 2-column: Left (logo+desc), Right (social icons), Copyright center.

**Hero Carousel (Apr 9, 2026):**
- Multi-slide carousel with auto-advance (configurable delay per slide, default 9.4s)
- Prev/Next arrow navigation (glassmorphism buttons)
- Dot indicators with active state highlighting

### Map Improvements (Apr 8, 2026)
MapBlock crash fix, Maps "Open in new tab" fix, Global Maps Language (11 languages), Interactive Map Picker, Tile provider integration

### Membership Enrollment Module (Apr 10, 2026)
**4-Step Wizard at `/membership-enrollment`:**
1. **Step 1 — Invitation CODE**: Invite code validation + email/name/password
2. **Step 2 — Clarity Statement and Interview**: 37 fields (personal, financial, ratings, geo cascading selects)
3. **Step 3 — Application Enrollment**: 3 legal agreements + digital signature
4. **Step 4 — Confirm & Submit**: CMS-managed title + description + Submit button

**Features:**
- Dynamic form fields stored in `enrollment_fields` collection (49 seeded defaults)
- Admin CMS: Full CRUD for fields, grouped by step, with drag-and-drop sorting
- 20 field types: text, email, password, number, currency, date, datetime, select, radio, checkbox, textarea, richtext, rating, rating_table, legal_checkbox, signature_text, signature_date, country, state, city
- Step 4 Content CMS: Dedicated tab with Title + Rich Text Description
- CMS-configurable colors (`--me-*` CSS variables)
- On submit: creates member with Level 1, auto-login, redirect to /my-account

### UI & CMS Refinements (Apr 11, 2026)
- Enrollment form buttons (Save/Continue/Submit) right-aligned
- Step 4 Content management via CMS tab (Title + Description)
- Fixed Step 4 text duplication (removed legacy richtext field rendering)
- Send Invitation modal colors now use CMS `--ma-*` CSS variables

### QR Code System (Apr 11, 2026)
- CMS Members Manager: "Create QR Code" (Yes/No) permission in Membership tab
- My Account Invite Code: Business QR section (conditional on permission)
- QR encodes `/my-account/register?sponsor={membership_number}`
- Download, View Full, Regenerate actions

### Documentation (Apr 11, 2026)
- Admin Documentation page (`/admin/documentation`) with 4 downloadable documents:
  1. Use Case & Flow Diagram (SVG-based, all actors + registration paths)
  2. Technical Documentation (architecture, DB, APIs, auth, CSS vars)
  3. Operator Manual (CMS step-by-step guide)
  4. User Guide (My Account member manual)
- All docs have "Save as PDF" browser print functionality

### Geo Data (Apr 10, 2026)
- 249 countries, 5046 states/subdivisions, 32,423 cities
- CMS admin geo management at /admin/geo

## Key Files
- `/app/frontend/src/pages/MembershipEnrollment.js` — 4-step enrollment wizard
- `/app/frontend/src/pages/admin/EnrollmentFieldsManager.js` — CMS form fields + Step 4 content
- `/app/frontend/src/pages/admin/MembersManager.js` — Members with QR permission
- `/app/frontend/src/pages/myaccount/InviteCode.js` — Invite codes + Business QR
- `/app/frontend/src/pages/admin/DocumentationManager.js` — Docs page
- `/app/backend/routes/enrollment.py` — Enrollment + content APIs
- `/app/backend/routes/membership.py` — Members, QR, invite codes
- `/app/backend/routes/docs.py` — Documentation HTML endpoints

### Dashboard & Analytics Improvements (Apr 13, 2026)
- Dashboard: Added "Members" card (first in grid) showing total member count with Users icon, linking to /admin/members
- Analytics: Fixed "Users" label to "Members", now counts from `db.members` (was incorrectly using `db.users`)
- Analytics: Added "Registered Members" monthly bar chart showing new registrations per month
- Analytics: Added "Logged-In Members" monthly bar chart tracking member logins
- Member login now records `last_login` timestamp for analytics tracking
- Step 4 enrollment: Fixed text overflow by removing `prose` class and adding `overflow-wrap: break-word`

### My Account Quick Links (Apr 13, 2026)
- Quick Links bar in My Account top header (right-aligned, same row as logo)
- Links separated by dividers, external links show ↗ icon, active link highlighted
- Breadcrumb remains visible below the quick links bar
- CMS admin page `/admin/quick-links` with full CRUD, drag-and-drop reorder, toggle active/inactive, new tab toggle
- Backend: `myaccount_links` collection with CRUD + reorder endpoints

### Members Manager & Analytics Fixes (Apr 13, 2026)
- Added "Register" column to Members Manager table showing member registration date
- Fixed Logged-In Members chart: now tracks each login event in `member_logins` collection (was only tracking `last_login` overwrite)
- Analytics counts unique member_ids per month via MongoDB aggregation

### Calendar System (Apr 14, 2026)
- Backend: Full Global Events CRUD, member registration with capacity/waitlist, auto-promotion on cancel
- Backend: Notifications system with unread count, Mentoring slots CRUD, booking with waitlist
- CMS: Global Events Manager at `/admin/calendar/global` with event table, registration viewer, CSV export
- CMS: Mentorship Schedule Manager at `/admin/calendar/mentorship` with slot table, mentor selector, bookings viewer
- My Account: Events Calendar (`/my-account/global-calendar`) — Month grid + List view with event cards
- My Account: Mentorship Calendar (`/my-account/mentorship-calendar`) — Mentor slot management with color-coded calendar
- My Account: Mentor Calendar View (`/my-account/mentor-calendar`) — Member booking with confirmation dialog
- My Account: My Reservations (`/my-account/my-bookings`) — Booking history with cancel
- Notification Bell in header with unread badge, dropdown, mark-all-read, 30s auto-refresh

### Event File Attachments (Apr 15, 2026)
- New `/api/upload-file` endpoint: accepts PDF, PPT, DOC, XLS, CSV, TXT, ZIP, images (max 25MB)
- Events store `attachments[]` array with url, name, size, content_type per file
- CMS: File upload section in event editor (add multiple files, remove individual files)
- CMS: Files column in events table showing attachment count
- My Account: Event cards show downloadable file links with paperclip icon

### Calendar Major Overhaul (Apr 16, 2026)
- Clone Event: Duplicate events with "(Copy)" suffix and inactive status for admin
- CSV Export: Fixed auth-token download using blob response
- Event fields: Split into Address, Map URL, Virtual Link (3 separate fields)
- Past events: Gray on calendar, no action buttons, Virtual Link removed
- Active events: Green on calendar
- Cancelled events: Hidden from member calendar, all registrants notified
- Waitlist: Changed from auto-promote to notify-all-and-remove (members self-register)
- Event Detail page: `/my-account/event/:eventId` with full description, attachments, links
- "Read more" link on event cards
- Renamed "Events Calendar" → "{AUX Prefix} Calendar"
- Mentorship slots: virtual_link, attachments, time dropdowns, One-on-One defaults max=1
- Mentor slot card: Shows participants list (booked + waitlisted)
- Past slots: Gray, view-only (no edit/delete)
- Cancelled slots: Hidden from member calendars, notifications sent
- Mentor Calendar (member view): Month + List views
- My Reservations: Status logic (Upcoming/Completed/Cancelled), Virtual Link column
- CMS Mentorship Schedule: Calendar view alongside list view, time dropdowns

### Calendar Refinements (Apr 16, 2026)
- Member file upload endpoint `/api/member/upload-file` (PDF, PPT, DOC, etc. up to 25MB)
- Title field for mentorship slots (CMS + My Calendar)
- Mentor Calendar moved into Mentorship Profile page (sidebar item removed)
- CMS Global Events + Mentorship Schedule: Calendar views alongside list
- CSV export includes event title and date
- Waitlist: members kept in DB (not deleted) when spots open — notified to self-register
- Cancellation notifications use "mentor" for slots, "administrator" for events
- Virtual link only visible to booked members
- Event detail page rich text rendering fixed (no horizontal scrollbar)
- AUX Calendar enabled in sidebar

### Calendar Fixes — Iteration 56 (Apr 17, 2026)
- Time picker: CMS Mentorship Schedule + My Calendar changed from `<select>` to `<input type="time">` matching Global Events format
- CMS calendar colors: Gray for past/cancelled, Green for upcoming (both Global Events + Mentorship Schedule)
- CMS Mentorship Schedule calendar: Shows slot title (not just mentor name)
- Waitlist-to-booked upgrade: Members on waitlist can now "Book this slot" when spots open (status upgraded from waitlist to booked/registered)
- Event detail: Breadcrumb shows "AUX Calendar", sidebar highlights AUX Calendar item
- Same fix applied to event registration (waitlist → registered upgrade)

### UI Polish — Iteration 57 (Apr 17, 2026)
- Native `<input type="date">` / `<input type="time">` icons now visible on dark My Account & member login/register pages (filter-inverted, hover brightens, cursor pointer)
- Color-scheme set to dark for member inputs so Firefox picker arrow follows text color
- Global rule enforces `--ma-input-border` on every `input`/`select`/`textarea` inside `[data-testid="myaccount-layout"]` — no more drift from hard-coded `border-white/10` on pages like Membership Profile → General Info → Edit
- Mentor Slot `description` field upgraded from `<textarea>` to `RichTextEditor` (ReactQuill) in both CMS (`MentorshipScheduleManager`) and My Account (`MentorshipCalendar`) — new `.ma-quill-dark` class themes the editor for dark backgrounds
- Slot detail display renders rich HTML via `dangerouslySetInnerHTML` + `rich-text-content`; calendar card previews use `stripHtml` helper to avoid tag bleed-through

### Refactor + Mentor Slot Templates — Iteration 58 (Apr 17, 2026)
- Split `/app/backend/routes/calendar.py` (620 lines) into three focused modules:
  - `calendar_helpers.py` — shared notification helpers (`notify_waitlist_spot_open`, `notify_cancellation`)
  - `calendar_events.py` — global events admin CRUD, member registration, notifications
  - `mentor_slots.py` — admin/mentor slot CRUD, bookings, waitlist, mentor-calendar, slot templates
  - `server.py` updated to mount both new routers; old `calendar.py` deleted
- Extracted shared `<CalendarGrid>` component at `/app/frontend/src/components/CalendarGrid.js` — renders month navigation + 7-column day grid. `GlobalCalendar.js` and `MentorCalendarView.js` both now use it (60+ lines of duplicated grid logic removed from each)
- **Feature: Mentor Slot Templates**
  - New collection `mentor_slot_templates` with fields: `name`, `title`, `session_type`, `max_students`, `default_duration_minutes`, `description` (rich HTML), `virtual_link`
  - Admin endpoints: GET/POST/PUT/DELETE `/api/admin/mentor-slot-templates`
  - Member endpoint: GET `/api/member/mentor-slot-templates` (returns `[]` when `mentor_slot_templates_enabled` setting is off — server-side gated)
  - New CMS page `/app/frontend/src/pages/admin/MentorSlotTemplatesManager.js` at route `/admin/calendar/mentor-slot-templates` with full CRUD + RichTextEditor
  - New sidebar item **Calendar → Mentor Slot Templates** in `AdminLayout.js`
  - New **Settings → General → Mentor Slot Templates** toggle (`mentor_slot_templates_enabled` on/off switch)
  - **Apply Template dropdown** added to slot editor in both `MentorshipScheduleManager.js` (admin, gated by `templatesEnabled`) and `MentorshipCalendar.js` (member, server gates via empty list). Selecting a template pre-fills title, session_type, max_students, description (rich HTML), virtual_link, and auto-computes end_time from start_time + default_duration_minutes

### Weekly Recurrence Engine — Iteration 59 (Apr 17, 2026)
- Backend: `POST /api/admin/mentorship/slots` and `POST /api/member/mentorship/slots` now accept an optional `recurrence: { enabled, days_of_week, weeks }` payload. A new `_expand_recurrence(base_date, days_of_week, weeks)` helper in `mentor_slots.py` anchors on the Sunday-on-or-before the start date, iterates week-by-week, deduplicates, and caps at 104 slots (2 years). JS `Date.getDay()` convention (0=Sun..6=Sat). Returns `{created: [...], count: N}` when multiple slots are produced; single-slot response unchanged.
- Frontend: new shared `<SlotRecurrencePicker>` at `/app/frontend/src/components/SlotRecurrencePicker.js` with checkbox + 7 day chips + weeks input + live date-range preview. Adapts to dark (member) vs light (admin) themes. Integrated into both `MentorshipCalendar.js` and `MentorshipScheduleManager.js` beneath the Virtual Link field; shows only when creating (not editing) a slot.
- Toast upgraded: multi-slot creation shows `"Created N slots"`.
- Verified via curl: 4 weeks × [Mon, Wed] starting 2026-04-20 produced 8 correct dates (2026-04-20, 04-22, 04-27, 04-29, 05-04, 05-06, 05-11, 05-13).

### Blocked Dates (holiday skip-list) — Iteration 60 (Apr 17, 2026)
- New `blocked_dates` collection: `{ id, date, reason, created_at }`
- Admin endpoints in `mentor_slots.py`: GET/POST/PUT/DELETE `/api/admin/blocked-dates`. Public read at `/api/public/blocked-dates` so the recurrence picker can preview skipped dates without auth.
- `_expand_recurrence` extended with optional `excluded_dates: set` — filters out blocked dates during expansion.
- Both slot-creation endpoints now:
  - auto-load the blocked set and skip those dates during recurrence (e.g. 4 weeks × [Mon, Wed] with 2026-04-27 blocked → 7 slots instead of 8)
  - reject single-slot creation on a blocked date with HTTP 400 ("2026-04-27 is a blocked date…")
- New CMS page `/app/frontend/src/pages/admin/BlockedDatesManager.js` at route `/admin/calendar/blocked-dates` with date + reason fields.
- New sidebar item **Calendar → Blocked Dates** in `AdminLayout.js`.
- `<SlotRecurrencePicker>` now fetches blocked dates, filters the preview, and adds a second preview line: `"Skipping 1 blocked date: 2026-05-25 (Memorial Day)"`.
- Existing slots on a newly-blocked date are **not** auto-cancelled (per design) — mentors still explicitly cancel those via the existing status-change flow that already triggers member notifications.

### iCal Subscription Feeds — Iteration 61 (Apr 17, 2026)
- New `/app/backend/routes/ical.py` module — RFC 5545 VCALENDAR generator using floating local time (no TZID) so each member's calendar app renders in local TZ.
- Per-member opaque token stored as `ical_token` on the `members` document (auto-generated via `secrets.token_urlsafe(24)` on first visit).
- Endpoints:
  - `GET /api/ical/{token}.ics` — public, serves `text/calendar`; looks up member by token. 404s on invalid tokens.
  - `GET /api/member/ical/info` — authenticated, returns `{ token, path }` (idempotent, generates token if missing).
  - `POST /api/member/ical/regenerate` — authenticated, rotates the token and invalidates the old URL immediately.
- Feed contents: booked mentorship slots (status in booked/completed) + registered global events. Excludes waitlist, cancelled slots, and cancelled events. Rich-HTML descriptions are stripped before escaping. UIDs are stable (`slot-{id}@consultant` / `event-{id}@consultant`) for proper update behavior in client calendar apps.
- Frontend:
  - New reusable `/app/frontend/src/components/CalendarSyncCard.js` — renders URL + copy button + three CTAs (Google Calendar "add by URL" deeplink, Apple Calendar `webcal://`, copy webcal://), expandable manual setup instructions for Google / Apple / Outlook, and a two-step "Regenerate URL" confirmation. Supports inline render or modal via `asModal` prop.
  - New page `/app/frontend/src/pages/myaccount/CalendarSync.js` at route `/my-account/calendar-sync` — dedicated landing with intro copy + card.
  - New sidebar item **Calendar Sync** (Rss icon) in `MyAccountLayout.js` — always visible (not gated by level perms, matching the other calendar items).
  - Inline collapsible card at the top of **My Reservations** page (`MyBookings.js`) — one-click reveal with compact copy.
  - Small **Subscribe** button on **Global / AUX Calendar** page (`GlobalCalendar.js`) that opens the modal variant.
- Curl verified: `.ics` output is valid RFC 5545 (VCALENDAR/VEVENT wrapper, PRODID, VERSION, METHOD, DTSTART/DTEND floating, proper CRLF line-endings). Invalid token returns 404. Regenerate rotates and old URL stops working.

### Paid Mentor Slots (Stripe) — Iteration 62 (Apr 17, 2026)
- New `mentorship_slots.price_cents` (int, default 0) + `currency` (default "usd"); free slots keep working.
- New global **Settings → General → Paid Mentor Slots** toggle `mentor_slots_paid_enabled`. Takes effect immediately — no redeployment.
- Backend (`routes/mentor_slots.py`):
  - `POST /member/mentorship/book/{slot_id}` returns HTTP 402 when toggle=ON and slot has price > 0 (directs to checkout).
  - New `POST /member/mentorship/checkout/{slot_id}` — creates Stripe Checkout via `emergentintegrations`, soft-holds the seat with `pending_payment` booking, inserts `payment_transactions` record. Success URL → `/my-account/mentorship/checkout-success?session_id={CHECKOUT_SESSION_ID}`.
  - New `GET /member/mentorship/checkout/status/{session_id}` — polled by success page; on `paid` flips booking to `booked` (idempotent), notifies mentor + member.
  - Rejects with 400 when: toggle=OFF, slot has no price, already booked/pending, or slot is full.
- Frontend:
  - Admin Settings toggle (clear copy: "Enabled — Stripe active on booking flow" / "Disabled — bookings remain free").
  - Price (USD) input in both slot editors, only rendered when toggle is ON. Dollars input → cents storage.
  - `MentorCalendarView.js`: price badge on SlotCard, "Pay $X & Book" button, dialog shows price line + adaptive CTA. Paid flow redirects to Stripe; free and waitlist flows unchanged.
  - New `MentorshipCheckoutSuccess.js` polls status with 10×2s with loading/paid/failed/timeout/error states.
- Testing (iteration_57): 17/17 backend PASS, CMS + slot editor UI verified, 0 regressions. Toggle left OFF after tests.

### Mentor Earnings Dashboard — Iteration 63 (Apr 17, 2026)
- New `GET /api/member/mentor/earnings` — returns aggregated stats for the authenticated mentor:
  - `total_revenue_cents`, `this_month_revenue_cents`, `pending_revenue_cents` (paid sessions with future dates)
  - `sessions_delivered`, `sessions_pending`, `sessions_total`
  - `monthly_breakdown` — last 12 months filled with zeros where no revenue
  - `transactions` — up to 50 most recent paid bookings with slot/member/amount/status (delivered | upcoming)
- Endpoint is mentor-scoped (`mentor_id` = current member), counts only bookings with `payment_status == 'paid'`. Returns zeros safely when no paid sessions exist.
- Frontend page `/app/frontend/src/pages/myaccount/MentorEarnings.js` at route `/my-account/earnings`:
  - 4 stat cards (Lifetime / This Month / Pending Payout / Delivered) with clean gold/amber accent
  - Monthly bar chart using existing `recharts` dep — respects `--ma-accent` CSS var
  - Transaction table with Delivered/Upcoming status pills
  - Gentle notice when paid toggle is currently OFF: "Paid slots are currently disabled by the administrator — no new charges will occur, but past paid sessions are shown below."
- New sidebar item **Earnings** (BarChart3 icon) in `MyAccountLayout.js`, gated by `mentorOnly: true` (matches existing My Calendar mentor-only pattern).
- Verified via curl + screenshot: seeded 3 paid bookings (2 past delivered, 1 future upcoming) → dashboard correctly showed $225 lifetime, $175 this month, $100 pending, 2/3 delivered, plus monthly chart with Mar $75 / Apr $175 bars and 3-row transaction table.

### Session Bundles — Iteration 64 (Apr 17, 2026)
- New `routes/bundles.py`; new collections `session_bundles` + `credit_packs`.
- **Two scopes**: admin-global bundles (`mentor_id: null`, redeemable against any paid slot) and per-mentor bundles (redeemable only on that mentor's slots). Eligibility priority at redemption: mentor-specific pack → global pack.
- Endpoints:
  - Admin CRUD: `GET/POST/PUT/DELETE /api/admin/bundles`
  - Mentor CRUD: `GET/POST/PUT/DELETE /api/member/mentor/bundles`
  - Member browse: `GET /api/member/bundles` (active only, enriched with mentor name)
  - Purchase: `POST /api/member/bundles/checkout/{id}` → Stripe Checkout; poll `GET /api/member/bundles/checkout/status/{session_id}` materializes a `credit_pack` with `remaining = session_count` on `paid`.
  - `GET /api/member/credits` — all packs owned by the member
- **Booking integration** (in `routes/mentor_slots.py`):
  - `POST /member/mentorship/book/{slot_id}` accepts `{use_credit: true}` — redeems one credit atomically, decrements pack `remaining`, marks booking `payment_status: credit`.
  - Cancellation restores the credit (atomic `$inc: {remaining: 1}` when `credit_pack_id` is set).
- Frontend:
  - Reusable `BundleEditorDialog` (admin-light + mentor-dark themes) used by both CMS and Earnings pages.
  - New CMS page `/admin/calendar/bundles` (AdminBundlesManager). Sidebar item **Calendar → Session Bundles**.
  - New member page `/my-account/bundles` (BundlesBrowse) — cards show bundle name, price, sessions, discount callout (`$600 value — save $200`), rich description, mentor badge for mentor-owned bundles, owned credits panel at top.
  - New `BundleCheckoutSuccess.js` at `/my-account/bundles/checkout-success` — polling + credit-count celebration card.
  - Mentor Earnings page adds a **My Bundles** table with add/edit/delete (uses the shared dialog with dark theme).
  - Booking dialog (`MentorCalendarView.js`) shows a new **Use 1 credit from "<Bundle>"** checkbox when the member has an eligible pack, updates CTA to **Book with Credit**.
- Verified via curl: admin + mentor bundle CRUD, member browse, book-with-credit decrements 5→4, cancel restores 4→5, 402 still fires when trying to book without credit. Seeded 2 demo bundles → browse page renders correctly with savings copy. All seed data cleaned.

### Iteration 58 — Multi-batch (Apr 20, 2026)
**New Admin Settings (Settings → General):**
- `paid_bundles_enabled` (Switch): Independent gate for session bundle Stripe checkout. Falls back to `mentor_slots_paid_enabled` for backwards compatibility when unset.
- `my_account_color_scheme` (Radio `dark`|`light`): Authoritative override for `--ma-color-scheme`. Admin picks the scheme that matches their configured My Account bg — used for all native form control chrome (date/time pickers, selects, scrollbars). When unset, falls back to luminance auto-detection from `ma.card_bg`.

**Session Bundles upgrade:**
- New fields on bundle model: `summary` (short text for card) + `banner_url` (cover image).
- `BundleEditorDialog` now has Banner URL + Summary + Rich Description inputs.
- Member `/my-account/bundles` shows banner image at top of each card, summary text, and "Read more" link → new `/my-account/bundles/:id` details page (sidebar stays active via existing `pathname.startsWith`).
- New `BundleDetail.js` page with hero banner, 3 KPI cards (Price / Sessions / Savings), rich-text About section, and Buy CTA that redirects to Stripe.
- New backend endpoint `GET /api/member/bundles/{id}` for public details.

**Bug fixes:**
- **Document upload (.docx) failing**: `/member/upload-file` now falls back to file-extension whitelist when MIME is `application/octet-stream` (some browsers/proxies strip MIME for Office docs).
- **Template selection not retained**: Converted `<select>` in MentorshipCalendar slot dialog to a controlled input driven by `appliedTemplateId` state; value resets only when "New Slot" is clicked.
- **MentorshipProfile rich text HTML tags visible**: Card description now uses `stripHtml()`; Confirm Booking / Waitlist modal uses `dangerouslySetInnerHTML`. 
- **Paid slot booking broken (402 error)**: `MentorshipProfile.confirmBook` now detects paid mode + redirects to `/member/mentorship/checkout/:id` for Stripe URL instead of free-book endpoint. Price badge + amount now shown on cards and in dialog CTA.

**Testing**: iteration_58 testing agent → 16/16 backend tests pass, all frontend UI verified. Report: `/app/test_reports/iteration_58.json`.

### Iteration 59 — Coupons + Multi-batch (Apr 20, 2026)

**NEW FEATURE — Discount Coupons** (`routes/coupons.py`):
- Admin CRUD at `/admin/calendar/coupons` with fields:
  - `code` (uppercase, unique), `discount_type` (percent|flat), `discount_value`
  - `applies_to` (slots|bundles|both), `usage_mode` (total|per_member), `usage_limit` (0 = unlimited), `expires_at`, `active`
- Member `POST /api/member/coupons/validate` returns `{valid, discount_cents, original_cents, final_cents}` with full error gating (inactive/expired/wrong-context/limit-exceeded)
- Integrated into both paid flows: `/member/mentorship/checkout/{id}` + `/member/bundles/checkout/{id}` accept `coupon_code` in body; Stripe charges the discounted amount; redemption is recorded in `coupon_redemptions` collection on payment success (idempotent)
- If a coupon drops slot price to $0, slot is booked directly (bypass Stripe)
- Confirm Booking modal on `MentorshipProfile` has Ticket-iconed coupon input with Apply button, real-time validation, error messaging, and collapsible price breakdown (Original / Discount / Total)

**Bundle UX upgrades**:
- `BundleEditorDialog`: Banner image now accepts either URL paste OR upload button (uses `adminAPI.uploadImage`) with thumbnail preview; Summary converted from plain `<Input>` to `RichTextEditor`
- `BundlesBrowse` card renders summary via `dangerouslySetInnerHTML`
- `BundleDetail` page gets `max-w-full overflow-x-hidden` root + CSS `.rich-text-content { overflow-wrap: anywhere; word-break: break-word }` to kill horizontal scroll

**Bug fixes**:
- **HTML entities as text** (`&nbsp;` visible): `stripHtml()` in `MentorshipProfile.js` + `MentorCalendarView.js` rewritten to use a DOM decoder (`div.innerHTML → textContent`) so entities decode properly
- **Admin New Event dialog dark bg on native selects/date** fields: replaced unscoped `[role="dialog"][data-state="open"]` rule with `body:has([data-testid="admin-layout"]) [role="dialog"]...` so admin-portaled dialogs inherit the admin `--ad-color-scheme` (light), while my-account dialogs continue to use `--ma-color-scheme`
- **AUX Calendar monthly view not rendering**: `GlobalCalendar.MonthView` was missing `year` and `month` props; signature updated + callsite now passes `{ year, month, monthLabel, onPrev/Next }`
- **My Reservations**: added "Billing" column with color-coded badges (Paid $amount / Credit / Free) — backend enriches `/member/my-bookings` with `billing_type`, `price_cents`, `currency`

**Testing**: iteration_59 testing agent → 17/17 backend tests pass, all frontend UI verified. Report: `/app/test_reports/iteration_59.json`.

### Iteration 60 — Coupon Analytics (Apr 20, 2026)
- New backend endpoint `GET /api/admin/coupons/analytics` aggregates the `coupon_redemptions` collection into: totals (redemptions / discounts given / revenue driven / active coupons), per-coupon performance (redemptions, discount_cents, revenue_cents, avg discount, slots-vs-bundles breakdown, last_used), top 5 redeemers (member name, count, lifetime discount).
- `AdminCouponsManager` is now tabbed: **Coupons** (CRUD, unchanged) / **Analytics** (new).
- Analytics tab renders: 4 KPI cards → Performance by Coupon table (sorted by revenue) → Top Redeemers leaderboard with rank chips.

### Iteration 62 — Mid-word breaks root cause (Apr 20, 2026)
[truncated — see above]

### Iteration 63 — Aurex One-page Theme (Phase 1 of 4, Apr 22, 2026)

**Foundation — infrastructure for new theme + 7 new sections**

Backend (`routes/admin_tools.py` + `routes/public.py`):
- Added `DEFAULT_SECTION_ORDER` (legacy) + `AUREX_DEFAULT_ORDER` (15-section list including `aurex_audience`, `aurex_process`, `aurex_pricing`, `aurex_team`, `aurex_events`, `aurex_partners`, `aurex_clients`).
- `/admin/section-order` now accepts a `?theme=` query → stored in `settings.section_orders.<theme>` (per-theme ordering as user requested).
- New `/admin/section-config` endpoints (GET/PUT) → stores `{ bg_color, font_family }` per section under `settings.section_configs.<theme>.<section_key>`.
- `/api/public/sections` returns `active_theme`, theme-specific `section_order`, and `section_configs`.

Frontend:
- `lib/themeColors.js`: added `AUREX_PALETTE` (7 official swatches), `AUREX_FONTS` (Sora / Inter / Playfair Display / Space Grotesk / DM Sans), `aurexContrastFor(hex)` luminance-based contrast helper. Added Aurex as 4th THEMES entry.
- `public/index.html` loads the 5 theme fonts via Google Fonts.
- `SettingsManager` themes tab now shows a 4-col grid with a custom Aurex preview (monochromatic mock: white header → gray hero → white cards → dark process → black footer).
- **`SectionOrderManager` rebuilt**: preserves existing drag-drop (dnd-kit) + adds a **theme scope selector** ("legacy" vs Aurex), and for Aurex mode each card shows:
  - A live preview chip (bg + font)
  - 7-swatch background picker with live ring-highlight on selection
  - Font dropdown (theme default or 1 of 5) with each option rendered in its own font
  - Enable/disable toggle
- Automatic text contrast flips via `aurexContrastFor()` — admin never picks text color manually.

**Verified**: Backend curl tests return correct per-theme data. Frontend admin UI renders all 15 section cards with 105 swatches + 15 font selectors at `/admin/section-order`.

**Phase 1 = DONE.** Phase 2 (new section CRUD), Phase 3 (frontend rendering), Phase 4 (polish) remain for subsequent sessions.

### Iteration 65 — Aurex Phase 3: Frontend Rendering (Apr 22, 2026)

**Public site now renders all 7 Aurex sections when active_theme = 'aurex'.**

Frontend (`HomePage.js`):
- Added `sectionMap` entries for `aurex_audience / aurex_process / aurex_pricing / aurex_team / aurex_events / aurex_partners / aurex_clients`, each wired to its React component in `components/AurexSections.js`.
- `aurexSection(key, Comp)` helper pulls per-section config from `settings.section_configs.aurex[key]` (bg_color + font_family → looked up in `AUREX_FONTS`), merged with page data from `useAurexSections()` which fetches `/api/public/aurex/<section>` for all 7 in parallel.
- Respects per-theme ordering: reads `settings.section_orders.<active_theme>` first, falls back to legacy `section_order`, finally to hardcoded Aurex defaults.
- Contrast (text color) auto-derived via `aurexContrastFor(bg)` luminance calc — admin never picks text color manually.

`components/AurexSections.js`:
- Fixed `ringColor` (invalid CSS prop) → switched to `boxShadow: 0 0 0 4px <bg>` for process-timeline node rings.
- Added `truncate` on Events section title + meta line so long zoom URLs in `event.location` no longer overflow into the View button.

**Seed data** (one-time admin curl): 3 audience cards, 4 process steps, 3 pricing plans (one featured), 3 team members, 6 partner logos, 6 client logos + config titles/subtitles. Aurex theme activated with per-section bg/font map applied.

**Verified via Playwright screenshot** (1440×900):
- ✅ Audience (#FFFFFF / Inter): 3 icon cards + CTA
- ✅ Process (#1F2937 / Sora): dark bg, alternating vertical timeline with 4 numbered nodes
- ✅ Pricing (#F4F6F8 / Inter): 3 plans, "Signature" featured & scaled up
- ✅ Team (#FFFFFF / Playfair): 3 photos with hover overlays, name+role below
- ✅ Events (#F9FAFB / Inter): date-stacked list pulled from `calendar_events`
- ✅ Partners (#111827 / Space Grotesk): dark strip, autoscrolling logos, grayscale hover
- ✅ Clients (#F4F6F8 / DM Sans): light gallery style

**Phase 3 = DONE.**

### Iteration 66 — Aurex Phase 4: Monochrome Adaptation + Scroll Reveal (Apr 22, 2026)

**All 9 existing homepage sections now render in the Aurex monochrome aesthetic when `active_theme === 'aurex'` + scroll-reveal animations added throughout.**

New code in `components/AurexSections.js`:
- `<Reveal>` component — IntersectionObserver-driven wrapper (opacity + 24px translateY → 0 on enter). `delay` prop enables staggered children. Honors `prefers-reduced-motion`.
- 10 new exported mono variants: `AurexAboutMono`, `AurexServicesMono`, `AurexNewsMono`, `AurexBlogMono`, `AurexReadingMono`, `AurexMapMono`, `AurexPortfolioMono`, `AurexGalleryMono`, `AurexTestimonialsMono`, `AurexContactMono`. Each follows the same design language:
  - White / gray-50 / dark surfaces only (no brand teal accents)
  - 1px `#E5E7EB` borders in place of heavy shadows
  - Uppercase `text-[11px] tracking-[0.3em] text-gray-500` eyebrows
  - Inter-family headings (global h1–h4 Playfair rule neutered via scoped `.aurex-section` CSS override)
  - Grayscale filter on news/blog/portfolio/gallery/testimonial imagery (removes on hover)
  - Dark #111827 contact form with white fields, pill CTA
- Scroll-reveal also retrofitted into the 7 existing Phase-3 Aurex sections (section headers + staggered item cards with `delay={idx * 80…120}`).
- Shared `aurex-section` class on every Aurex-era section scopes the `font-family: inherit` override so per-section font pickers actually take effect.

`HomePage.js`:
- `sectionMap` now swaps between legacy and Aurex variants via `isAurex ? <AurexXxxMono .../> : <XxxSection .../>` for all 9 shared keys — no changes to the legacy 3 themes.

**Verified via Playwright** (1440×900, 10 scroll positions covering the full 10.1k-px page): About/Services/News/Blog/Pricing/Contact all render in the new monochrome style; about-title computed font = `Inter, sans-serif` (was Playfair before the CSS scope fix); contact bg = `rgb(17,24,39)`; services bg = `rgb(249,250,251)`.

**Phase 4 = DONE.** Full 4-phase Aurex One-page theme now shippable end-to-end.

### Iteration 73 — Section Configs + Unified Button Shape + Carousel Polish (Apr 22, 2026)

**CMS — 5 new "Section Configuration" entries in the Aurex Sections manager:**
- Added `aurex_services_cfg`, `aurex_testimonials_cfg`, `aurex_news_cfg`, `aurex_blog_cfg`, `aurex_locations_cfg` to `VALID_SECTIONS` (backend) and to `AUREX_SECTIONS` schema map (frontend). Each defines config-only fields: `eyebrow`, `title`, `subtitle`, and — where appropriate — `cta_text`/`cta_url`/`cta_new_tab`. No `itemFields` — item data continues to come from the existing dedicated managers (Services / Testimonials / News / Blog / Maps). Admin now sees a dedicated card for each of these in Aurex Sections Manager alongside the full-fledged sections.
- `useAurexSections` hook pulls all 5 configs in parallel. `HomePage.js` routes each Aurex mono variant its matching override via `aurexMono(key).cmsConfig`. Mono variants accept a new `cmsConfig` prop and fall back to hardcoded copy when CMS hasn't been edited.

**Unified button shape (frontend):**
- New shared `<MonoButton>` helper in `components/AurexSections.js`. Rectangular `rounded-sm`, 1.5px currentColor border, auto-contrast via `monoStyle()`, arrow icon on CTAs. Adopted across About, Services, News, Blog, Testimonials. Services "See All Services" was `rounded-full px-10 py-3` → now `rounded-sm px-7 py-2.5`. Legacy pill stylings removed to match the "About: Read About Us" button.
- Playwright measured `about-cta-btn`, `services-view-all`, `news-view-all` all at `border-radius: 0px` (confirms `rounded-sm` with no Tailwind pill style overrides).

**Services section — per-service link:**
- Each service card is now a clickable `<Reveal as="a">`. `href` resolves to `s.external_url` when present (honors `s.open_in_new_tab` → `target="_blank" rel="noopener noreferrer"`), else falls back to internal `/service/:id`. Title gets hover-underline to signal interactivity.

**Testimonials carousel — added photo + role per card:**
- Card render order now matches admin feedback: quote → avatar → name → role/company. Avatar is a 80×80 round crop bordered `2px` with the contrast-matching border color. Missing avatar falls back to a circular initial placeholder. `title`/`role` from `t.role` + `t.company` joined with `·`.

**Rich-text rendering fix:**
- Added full typography styles under `.rich-text-content` in `/app/frontend/src/index.css`: `<p>` margins, `<h1-h4>` weights+sizes, `<ul>` disc, `<ol>` decimal, `<blockquote>` with left border, `<a>` underline, `<code>` inline background. Tailwind's preflight had been stripping these defaults. About "description" and any Aurex item `type: 'rich'` field now render with proper paragraph spacing, lists, and headings.

**Page Builder — auto-append new Aurex sections:**
- `SectionOrderManager` now merges any known Aurex keys (including `aurex_video` and the 5 new cfg keys are already in AUREX_SECTIONS) into the displayed order if they're missing from the saved `section_orders.aurex`. Admin no longer needs to re-save after we add new Aurex section types.

**Verified via curl + Playwright**:
- Seeded all 5 config-only endpoints with admin overrides; public endpoints return them correctly.
- Homepage probe returned `services_title: "¿Qué obtienes dentro de Aurex?"` (CMS override), `services_view_all: "See All Services"`, `testimonials_title: "Testimonials"`, `news_title: "From our desk"`, all three CTA buttons at `border-radius: 0px`.
- Testimonials cards show avatar fallback + name + role.



Shipped in one push after detailed user feedback (Spanish/English mix). All 11 items:

**CMS**

1. **Hero 3-button CMS preview** — `HeroSlidePreview` inside `HeroSlideForm` now renders up to 3 pill-shaped preview chips in a flex-wrap row at the `button_x/y` coordinate. First is filled primary, rest are outlined; `hasContent` also checks `button_2_text` / `button_3_text`. Preview refreshes live as admin types in the new fields. Layer-positioning stays with a single `button_x/y` anchor (matches how the public site renders them).

2. **New Aurex section: `aurex_video`** — polymorphic backend added the key to `VALID_SECTIONS` (and excluded from `ITEM_SECTIONS` since video is config-only). Schema `aurex_video` defines config fields `title, subtitle, video_url, poster_url, autoplay, aspect_ratio`. Added to the admin Page Builder's `sectionLabels`, default Aurex order, and the `useAurexSections` fetch hook.

3. **About Us Manager** — added `Call-to-action Button` section with three fields: `button_text`, `button_url` (accepts `/path`, `#anchor`, or external URL), and `button_open_in_new_tab` checkbox. No DB migration needed (schema-less).

4. **Aurex item icons = searchable dropdown** — new `IconPicker` component inside `AurexSectionsManager`. Curated list (`lib/aurexIconList.js`, ~80 lucide names) shown in a 6-col grid with live search. Selected icon previewed on the trigger button. Replaces the free-text input for the `icon` field in any section whose schema declares `type: 'icon'`.

5. **Aurex item descriptions = rich text** — added `type: 'rich'` to `aurex_audience` and `aurex_process` item schemas. `FieldInput` renders them with the existing `RichTextEditor` (TipTap). Frontend renders via `dangerouslySetInnerHTML` inside `.rich-text-content` so formatting (bold / italic / lists / links) carries through.

6. **Our Team dynamic social icons** — replaced the 3 fixed fields (`linkedin_url`, `twitter_url`, `other_url`) with a new `type: 'social_links'` which reads `settings.social_links` (the list already configured at Settings → Social Links) and renders one URL input per enabled network with its icon prefix. Items store them as `{ [network_id]: url }` so adding/removing platforms in Settings just works — the frontend auto-renders only the filled ones.

7. **Page Builder default scope = active theme** — `SectionOrderManager` now bootstraps from `settings.active_theme` on mount (was hardcoded to `'default'`). Added a warning banner when the edited scope differs from the active theme. Admin can still switch scopes via the select but doesn't have to every time.

**Website (frontend)**

8. **Hero 3 buttons on public** — extracted `HeroButtonsRow` helper inside `HeroSection.js` and replaced the 3 button-render sites (legacy-layout, positioned desktop, mobile stacked). Primary button = filled white pill with arrow; secondary / tertiary = outlined transparent pills. Respects each button's `window_open` target individually.

9. **Section Video component** — `AurexVideo` in `components/AurexSections.js`. `buildEmbedUrl()` detects YouTube (`youtube.com`, `youtu.be`, `shorts/`) and Vimeo patterns and converts to proper embed URLs with optional autoplay+mute+loop; direct `.mp4`/`.webm`/`.ogg` URLs render as `<video>` with poster/controls; unsupported URLs show a graceful fallback. Respects admin's `aspect_ratio` choice (16:9 / 4:3 / 1:1 / 21:9) via CSS `aspectRatio`. Resilience: HomePage now appends any known Aurex keys missing from the saved `section_orders.aurex` (fixes pre-existing orders not containing the new `aurex_video`).

10. **About button** — rendered below the signature block as an outlined pill with arrow. Auto-contrast border+text via the shared `monoStyle` helper so it works on any bg color the admin picks.

11. **Services redesign** (per `section_services.png`) — image-top cards in a 3×2 grid: `4/3` cover image with subtle grayscale → color on hover, Playfair-serif title centered, short description centered, single "See All Services" outlined CTA below the grid. Dropped the bordered-card + inline checkout button pattern (checkout still accessible via /service/:id).

12. **Testimonials carousel** (per `section_testimonials.png`) — `AurexTestimonialsMono` rewritten. Responsive `perView` (3 desktop / 2 tablet / 1 mobile). Arrows positioned `-left-8 / -right-8` with circular bg. Page dots stretch when active (`w-6` vs `w-2`). Italic quotes centered, round avatar (grayscale), Playfair name, uppercase-tracked role. All `data-testid` hooks exposed (`testimonials-prev`, `testimonials-next`, `testimonials-dot-{i}`, `testimonial-card-{id}`).

13. **Our Team hover fix** — name + role always sit **outside** the `aspect-square` photo container (separate `pt-4 text-center` div below). Overlay (bio + social icons) is strictly absolute-positioned inside the photo via `.absolute.inset-x-0.bottom-0.bg-gradient-to-t.opacity-0.group-hover:opacity-100`. No more overlap with name/role.

**Verified end-to-end via Playwright on /**:
- `hero_buttons: ["More Information 2", "Membership Lounge", "Notify Me!"]` (all 3 rendered + variant B bucket in effect)
- `about_btn_text: "Learn About Aurex"`
- `services_cards: 3` + `services_view_all: true`
- `video_section: true` + `video_iframe_src: "https://www.youtube.com/embed/dQw4w9WgXcQ"`
- `testimonials_prev / next / dots: 2`
- Team photos render with name/role below, overlay opacity-0 by default (probed)
- Lint clean across 7 frontend files + Python route.



**User feedback (both parts resolved):**
1. *"Changing the colors of each section only affects new sections, not old ones."*
2. *"Enter any other color for each section's colors, as in Settings → Colors."*

**Bug #1 — Legacy Aurex mono variants were ignoring `section_configs.aurex[key]`.**

The 10 `AurexXxxMono` components (About/Services/News/Blog/Reading/Map/Portfolio/Gallery/Testimonials/Contact) had their backgrounds hardcoded as Tailwind classes (`bg-white`, `bg-[#F9FAFB]`, `bg-[#111827]`). They now accept `bg` and `font` props and use them via a shared helper:

```js
function monoStyle(bg, font, fallbackBg) {
  const effectiveBg = bg || fallbackBg;
  const isDark = aurexContrastFor(effectiveBg) === 'light';
  return { style: {backgroundColor, color, fontFamily}, textClass, mutedClass,
           eyebrowClass, borderColor, isDark };
}
```

Each mono variant now wraps its JSX in `<section style={m.style}>` and uses `m.eyebrowClass`, `m.mutedClass`, `m.borderColor`, `m.isDark` for all text/border tokens — so any admin-picked background (light OR dark) automatically gets readable text and subtle borders via luminance math (`aurexContrastFor`). Fallbacks preserve the old look when CMS hasn't set anything.

`HomePage.js` now passes `{ bg, font }` to each mono variant via a tiny `aurexMono(key)` helper that reads `settings.section_configs.aurex[key]` and resolves `font_family` through `AUREX_FONTS` (same mechanism the new Aurex sections already use).

**Feature #2 — Custom hex color input.**

`SectionOrderManager`'s per-section color row now shows, after the 7 preset swatches, a combined custom-color chip:
- `<input type="color">` — native OS color wheel (click the chip to open)
- `<input type="text">` — free-text hex entry (`#RRGGBB` with 3 or 6 hex digits accepted on blur)
Controlled by the same `bg_color` key — changes are saved/loaded identically. Presets remain untouched (single click, `ring-2 ring-[#0D9488]` highlight for active).

**Verified end-to-end via curl + Playwright:**
- Set custom colors (`#0F172A` for About, `#FEF3C7` for Services, `#4C1D95` for News, `#DCFCE7` for Testimonials, `#F9A8D4` for Contact). Public DOM probe returns exactly those `rgb(…)` backgrounds and auto-switched text colors (white on dark, dark on light). Then reset to neutral defaults.
- Admin Page Builder (Aurex scope): 15 sections × 7 swatches = 105 swatches present; 15 color pickers + 15 hex inputs present and pre-populated from CMS state.



**User feedback: "The header and hero should be the same as the modern theme, giving it a modern touch."**

Resolved by treating `active_theme === 'aurex'` as a modern-theme variant for those two components only (all 16 other Aurex section components untouched).

- `components/layout/Navbar.js` — router branch now reads `if (theme === 'modern' || theme === 'aurex') return <ModernNavbar />`. Aurex now inherits the transparent-to-solid-on-scroll header with blur, logo-on-1/logo-on-2 swap, uppercase tracked nav links, pill-shaped teal Login button, mobile hamburger.
- `components/HeroSection.js` — introduced `isModernLike = theme === 'modern' || theme === 'aurex'` covering both the `min-h-[800px]` height and the dark `linear-gradient(135deg, rgba(15,23,42,0.85), rgba(30,41,59,0.7))` overlay.
- `pages/HomePage.js` — removed the `isAurex ? <AurexHeroMono/> : <HeroSection/>` swap; `AurexHeroMono` is no longer imported or mounted on the home page (the component stays in the file for future use / rollback). All hero CMS data (countdown, multi-CTA, A/B testing) remain functional via `HeroSection` or can be added there later if needed.

**Verified via Playwright**: probe confirms `position: fixed` navbar with `rgba(0,0,0,0)` background (transparent) at scrollY=0, 800px hero height. Screenshots show the Playfair "AurexNetwork" headline + teal accent "Team Work" eyebrow over the dark photo overlay + the modern solid-white navbar after scrolling.

**Future note for Phase 5 (optional):** If you want the 3-CTA row, parallax bg, and A/B testing to live on the modern hero as well, those features would need to be ported from `AurexHeroMono` into `HeroSection`. Currently they're inactive (modern hero only uses `button_text` / `button_url`). A/B tracking continues to work for any other component that opts in.

### Iteration 69 — Hero CTA A/B Testing System (Apr 22, 2026)

**End-to-end A/B testing for hero CTA copy**, asked as the "potential improvement" after Iteration 68. Consultants/membership businesses can now ship two headline variants for the same CTA and see which actually converts.

Backend (`routes/hero_ab.py` — NEW, mounted on `api_router`):
- `POST /api/public/hero-cta-event` — fire-and-forget tracking endpoint. Body `{ slide_id, button_index (0-2), variant ('A'|'B'), event_type ('impression'|'click'), visitor_id }`. Inserts to `hero_cta_events` collection. Strict validation on `event_type` and `variant`.
- `GET /api/admin/hero-ab/analytics` (admin-only via `require_admin` dep). Runs a single Mongo `$group` pipeline over `hero_cta_events`, then joins against the ab-enabled slides to emit structured rows:
  `{ slide_id, slide_title, button_index, button_label, variant_a: {text, impressions, clicks, rate}, variant_b: {...}, uplift_pct }`. Overall `totals.impressions/clicks/rate` included.
- Slides flagged with `ab_testing_enabled: true` and matching `button{_N}_text_variant_b` drive what's reported. Buttons missing either variant are excluded.

Schema extension (no migration — Mongo is schema-less):
- Hero slide doc now carries `ab_testing_enabled`, `button_text_variant_b`, `button_2_text_variant_b`, `button_3_text_variant_b`.

Frontend:
- **`AurexHeroMono`** (`components/AurexSections.js`):
  - Deterministic 50/50 bucket per browser: `getVariantFor(slideId)` returns 'A'/'B', persisted in `localStorage.aurex_ab_<slide_id>` so a returning visitor sees the same variant.
  - Anonymous visitor id persisted in `localStorage.aurex_visitor_id` (allows future cohort analysis without PII).
  - New `pickText(base, variantB)` helper swaps CTA text per variant (falls back to base if variant B is blank).
  - `useEffect` fires one `impression` event per ab-tracked button when the slide becomes active. Runs before the early `return null` guard so React hook rules are respected.
  - CTA `onClick` handler fires a `click` event (only for buttons with both variants defined). Uses `fetch({ keepalive: true })` so the beacon survives page-nav clicks.
- **CMS — `HeroSlideForm`**:
  - New "A/B Testing" section with a checkbox toggle + explanatory copy.
  - When enabled, each of the 3 button rows expands to show a Variant B text input in a soft amber callout. "Only buttons with both A and B text set participate in the test."
- **Admin — `HeroAbAnalytics`** (NEW): `/admin/hero-ab` (also added to sidebar right after "Hero"):
  - 3 summary stat cards (impressions, clicks, overall CTR).
  - Per-button comparison cards: side-by-side A vs B panels, trophy icon + green border for the winner, emerald/rose uplift badge at top right, CTR in large numerals.
  - Empty state with setup instructions.
  - Refresh button + axios wired through `lib/api` (interceptor injects `auth_token` so admin session is honored).

**Verified end-to-end:**
- Seeded 480 events across 3 buttons (imp+clk mix). Backend analytics returns: Button 1 A=8% / B=12% (+50% uplift), Button 2 A=6.25% / B=5% (-20%), Button 3 A=16.67% / B=8.33% (-50%). Totals: 480 imp, 44 clk, 9.17% overall CTR. Admin dashboard renders all 3 rows with correct winner highlighting.
- Public hero on /: Playwright landed on variant B bucket and correctly rendered "Join Aurex Now" / "Enter Members Area" / "Get Early Access" instead of the A copy.



**`AurexHeroMono` rebuilt** to match the user-supplied "AurexNetwork" mockup.

Frontend (`components/AurexSections.js`):
- **Full-color** background photo (removed the previous `grayscale(100%)` filter). Soft left-to-right white gradient overlay `linear-gradient(90deg, rgba(255,255,255,.85) 0%, rgba(255,255,255,.55) 45%, rgba(255,255,255,.05) 85%)` keeps headline legible while letting the photo breathe.
- **Parallax**: background image wrapped in a `translate3d(0, scrollY * 0.25, 0) scale(1.08)` transform driven by a `scroll` listener. Capped at 120px travel. Uses `will-change: transform` for smooth 60fps. Honors `prefers-reduced-motion` indirectly through minimal transform math.
- **Massive typography**: `text-5xl sm:text-6xl md:text-7xl lg:text-8xl` (96px at lg+) gray-900 title with `leading-[0.95] tracking-tight`.
- **Multi-CTA row**: new `ctas` array collapses `button_text/url` + `button_2_text/url` + `button_3_text/url` into an inline flex row. First button is filled primary (white → inverts to black on hover, arrow icon). Remaining buttons are outlined. Up to 3 CTAs supported.
- **Layout**: shifted from center to `items-end` bottom-left content placement per mockup; content wrapped in `max-w-3xl` for the same measure as the reference.
- **CountdownMono** gained a `light` prop (dark numerals + gray subtitle) for light-bg heroes.
- **Slide indicators**: kept minimal horizontal strokes; now dark (`bg-gray-900`) instead of white for contrast on light bg.

CMS (`pages/admin/HeroSlideForm.js`):
- Hero Slide editor now has **3 rows of CTA fields** (text + URL + window target). Row 1 preserves the existing `button_text/url/window_open` fields — existing slides continue to work. Rows 2 and 3 use the new `button_2_*` / `button_3_*` keys. Legacy themes still only consume button 1, Aurex uses all 3.
- Inline copy added: *"Up to 3 CTA buttons — the Aurex theme renders them as an inline pill row. Classic themes only use Button 1."*

**Curl + Playwright verified:**
- Updated seed slide via PUT `/admin/hero-slides/{id}` with title=AurexNetwork, 3 CTAs, extended `date_end`.
- Public hero renders: 96px title, 3 CTAs (More Information / Membership Lounge / Notify Me!), full-color photo, parallax pan confirmed on 400px scroll, bg `rgb(255,255,255)` with gradient overlay.



**Hero adapted to Aurex** (`AurexHeroMono` in `components/AurexSections.js`):
- Pitch-black `#0A0A0A` canvas, background image rendered in `grayscale(100%) brightness(.4)` with a black-gradient overlay on top.
- Massive Inter typography — `text-4xl sm:text-5xl md:text-6xl lg:text-7xl` title with `leading-[1.05] tracking-tight`. Newline-separated lines get italic/light styling on subsequent lines for editorial rhythm.
- Uppercase `tracking-[0.3em]` eyebrow subtitle, quiet `text-white/60` description, pill-shaped white-on-ink CTA.
- Optional side photo rendered in `grayscale(100%)` as a second column (auto-detected from `slide.photo`); falls back to single-column typography-forward layout when no media.
- `CountdownMono` — minimal 4-unit Days/Hours/Min/Sec counter, tabular-nums, no boxes. Renders when the slide has `countdown_to`.
- Slide indicators reimagined as thin horizontal strokes (active = wider/brighter). Staggered Reveal entrance (subtitle → title → countdown → description → CTA, 100-300ms delays).
- Wired into `HomePage.js`: `hero: isAurex ? <AurexHeroMono/> : <HeroSection/>`. Legacy themes untouched.

**Duplicate-item button** (`pages/admin/AurexSectionsManager.js`):
- Added `Copy` icon button between Toggle-visible and Edit in every item row (all 6 itemized Aurex sections: audience/process/pricing/team/partners/clients).
- `handleDuplicate(item)` strips server-managed fields (`id`, `order`, `section`, `_id`, `created_at`, `updated_at`), appends " (Copy)" to `name` or `title` (whichever the section uses), and POSTs to the existing `/admin/aurex/{section}/items` — which auto-assigns a fresh uuid and next `order`.
- Curl verified end-to-end: 3 audience items → duplicate → 4 items; new row appears with `order=3`, id=new uuid, title="Founders & Operators (Copy)". Cleanup also verified.

### Iteration 64 — Aurex Phase 2: CMS CRUD for 7 sections (Apr 22, 2026)

Backend (`routes/aurex_sections.py` — NEW):
- **Polymorphic CRUD**: single generic route handles all 7 sections via path param `/api/admin/aurex/{section}/...`
- Storage: `aurex_section_configs` (one doc per section) + `aurex_section_items` (N rows per section with `section` discriminator + `order` + `visible`)
- 9 endpoints: GET/PUT config, GET/POST/PUT/DELETE items, PUT reorder, + public GET
- **Special case `aurex_events`**: config-only; public endpoint pulls from `calendar_events` respecting `max_items` + `only_upcoming` config flags — so events sync automatically from AUX Calendar with zero duplication.

Frontend:
- `lib/aurexSchemas.js` — NEW: schema-driven field definitions for all 7 sections (text/textarea/url/number/bool/image/icon/select). Drives polymorphic admin UI.
- `pages/admin/AurexSectionsManager.js` — NEW: tabbed admin page with 7 tabs (icons: Users/Workflow/DollarSign/UserCircle/Calendar/Building2/Award), each driven by its schema. Handles: section config save, item CRUD with dialog, inline visibility toggle, auto-incrementing order, image upload via `adminAPI.uploadImage`.
- Sidebar "Aurex Sections" entry, route `/admin/aurex-sections`.

**Testing**: iteration 60 testing_agent → 27/27 backend tests pass; all frontend UI (7 tabs, config forms, items CRUD) verified.

**Still remaining** (Phases 3-4): frontend rendering of the 7 sections on the public website + visual adaptation of existing 9 sections + scroll animations + responsive polish.
- All formatted with tailwind colors (rose for discounts given, emerald for revenue driven) + lucide icons (Ticket, TrendingUp, Crown, Package).

## Credentials
Admin: admin@consultant.com / Admin123!
Mentor (Carlos): carlos@example.com / Mentor123!

### Iteration 79 — Testimonials DnD + Section-level Login Required + Global word-break (Apr 24, 2026)

**Verified iteration_66: all 9 features pass.**

**1) TestimonialsManager drag-and-drop** (`/pages/admin/TestimonialsManager.js`):
- Rewritten with `DndContext` + `SortableContext` matching the Services/PageBuilder pattern.
- `TestimonialRow` component extracted with `useSortable` for clean re-renders.
- Removed up/down arrow buttons. `GripVertical` handle on left; drag-end persists new `order` field to each row via `PUT /api/admin/testimonials/{id}`.
- Kept the eye-icon visibility toggle.

**2) Section-level Login Required (padlock)** (`/pages/admin/SectionOrderManager.js`, `/pages/HomePage.js`):
- Added `Lock`/`LockOpen` padlock icon next to each section in the Aurex Sections admin UI.
- Toggle writes `settings.sections[key].login_required` (independent from `enabled`).
- HomePage skips rendering sections when `login_required === true && !userLoggedIn`.
- User detection uses a robust fallback: `user.id || user.member_id || user.username || user.email` because the auth store returns different keys depending on how the session was established (admin-password flow vs member flow vs /auth/me).
- **Semantics**:
  - Eye OFF → hidden from everyone (hard hide, regardless of auth).
  - Padlock ON + Eye ON → shown only to logged-in members.
  - Padlock OFF + Eye ON → public (no login required).

**3) Global word-break CSS** (`/index.css`):
- Added a global rule targeting `p, h1-h6, li, blockquote, span` inside `main`, `section`, `footer`:
  ```css
  word-break: normal;
  overflow-wrap: break-word;
  hyphens: none;
  ```
- Fixes mid-word splits and unwanted auto-hyphens on narrow viewports.
- Kept `.rich-text-content` block-level rule for compatibility.

### Deferred
- **"Notify Me!" form** — still awaiting user clarification on placement / fields.

## Pending/Backlog
- (P2) SEO pre-render for bilingual indexing
- (P2) S3/Cloud Image Storage migration
- (P2) Production SMTP Configuration
- (P2) Stripe Connect full marketplace
- (P2) Add coupon input to `MentorCalendarView` Confirm Booking dialog

### Iteration 78 — Services/Testimonials hide+reorder, Partners/Clients standardization, rich-text CMS upgrades (Apr 23, 2026)

**Verified iteration_65: all 16 features pass.**

**CMS upgrades:**
- **ServicesManager** rewritten with DndContext + SortableContext — drag-and-drop reordering persists via `PUT /api/admin/services/{id}` with `order` field. Eye-icon toggle flips `visible` without opening the editor. Editor dialog has a "Visible on website" switch.
- **TestimonialsManager** — added quick-toggle eye icon in each row + "Visible on site" switch in the editor. Hidden testimonials skip the public carousel.
- **Partners & Clients (aurexSchemas.js)** — standardized to identical config fields: `eyebrow`, `title`, `subtitle`, `cta_text`, `cta_url`, `cta_new_tab`, `autoscroll`, `scroll_speed`. Frontend renders both with matching `SectionHeader` (both at 48px), optional CTA button, and unified auto-scroll + speed.
- **ContactSettingsManager** — `description` is now a `RichTextEditor` wrapped in `LocalizedField`.
- **SettingsManager General tab** — added `footer_newsletter_text` and `footer_newsletter_placeholder` with `LocalizedField` tabs.
- **AboutManager** — `description` is now a `RichTextEditor`.

**Frontend:**
- **AurexContactMono + HomePage ContactSection** (modern+classic+default) render description via `dangerouslySetInnerHTML` + `rich-text-content` class. No more `<p>` tag leaking HTML as text.
- **AboutSection** (HomePage, all 3 themes) — description renders as HTML with proper rich-text styling. Wraps label/title/signature with `tt()` too.
- **AurexNewsMono** — renders `tt(p.summary)` as HTML when present; falls back to stripped-plain-text (with `&nbsp;` cleaned) when empty.
- **AurexTestimonialsMono** — filters by `t.visible !== false && itemHasLocale(t.content, lang)`.
- **AurexPartners + AurexClients** — unified `SectionHeader` + optional CTA + consistent logo row behavior.
- **Anchor IDs** added to all Aurex sections: `aurex-audience`, `aurex-process`, `aurex-pricing`, `aurex-team`, `aurex-events`, `aurex-partners`, `aurex-clients`, `aurex-video`.
- **Footer** reads `tt(settings.footer_newsletter_text)` + `tt(settings.footer_newsletter_placeholder)`.
- **Back-to-top button** — new `/components/BackToTop.js`. Appears at scrollY > 300px, smooth-scrolls to top. Uses `--color-primary` from theme.

**Backend:**
- `/public/services` and `/public/testimonials` filter by `visible !== false` and sort by `order`.

### Deferred items (awaiting user clarification)
1. **"Notify Me! form"** — user description too short; need to know where it's expected to appear.
2. **Page Builder section-level "Login Required"** — larger refactor; deferred to next iteration.

## Pending/Backlog
- (P2) SEO pre-render: nightly job emitting hydrated `/index.html` with meta tags + above-the-fold content (important for bilingual SEO).
- (P2) S3/Cloud Image Storage migration
- (P2) Production SMTP Configuration
- (P2) Stripe Connect full marketplace (automatic payouts replacing manual logging)
- (P2) Add coupon input to `MentorCalendarView` Confirm Booking dialog (currently only MentorshipProfile has it)
- (P1 follow-up) Page Builder section-level Login Required flag

### Iteration 77 — Blog summary rich-text + Contact + Settings i18n (Apr 23, 2026)

**Verified iteration_64: 15/15 backend + frontend pass. Testing agent fixed a critical bug in HomePage.js ContactSection.**

**Blog summary (rich text + HTML rendering):**
- `BlogManager.js` — `summary` field switched from `textarea` → `RichTextEditor` wrapped in `LocalizedField`. Admin can now format the teaser.
- `NewsPage.js` — renders post summary as HTML via `dangerouslySetInnerHTML` with `line-clamp-3` + `rich-text-content` styling. Uses `tt()` on title/summary. Filters posts by `itemHasLocale(p.title, lang)`.
- `NewsDetailPage.js` — summary now renders as italic intro block above main content; `tt()` applied to title/summary/content.

**Contact Section CMS localized (`ContactSettingsManager.js`):**
- 7 fields wrapped with `<LocalizedField>`: `title`, `subtitle`, `description`, `name_placeholder`, `email_placeholder`, `message_placeholder`, `submit_text`.
- `HomePage.js` `ContactSection` now imports and uses `useT()` — fixed a crash that occurred when switching to ES with localized contact settings (testing agent caught this and applied the fix).

**Settings → General CMS localized (`SettingsManager.js`):**
- Added `LocalizedField` to 6 general-tab fields: `brand_name`, `tagline`, `meta_title`, `meta_description`, `footer_description`, `footer_copyright`.

**Public consumers updated:**
- `components/layout/Footer.js` — `tt()` for `brand_name`, `footer_description`, `footer_copyright`.
- `components/layout/Navbar.js` — all 3 variants (Default, Modern/Aurex, Classic) use `tt()` on `brand_name`/`tagline`.
- `App.js` `document.title` — reads localized tagline/brand_name via direct `i18nT()` helper (no hook dependency).

**Backend** — no changes; existing endpoints accept and persist raw dicts.

## Pending/Backlog
- (P2) SEO pre-render: nightly job emitting hydrated `/index.html` with meta tags + above-the-fold content (important for bilingual SEO).
- (P2) S3/Cloud Image Storage migration
- (P2) Production SMTP Configuration
- (P2) Stripe Connect full marketplace (automatic payouts replacing manual logging)
- (P2) Add coupon input to `MentorCalendarView` Confirm Booking dialog (currently only MentorshipProfile has it)

### Iteration 76 — Locale-scoped items + 5 managers with LocalizedField (Apr 23, 2026)

**Per-item locale scoping.** Items (cards, testimonials, posts, etc.) now auto-hide when their primary field has no content in the current locale. Verified via iteration_63: 28/28 backend + frontend manual tests pass.

**New helper (`lib/i18n.js`):**
- `itemHasLocale(value, lang)` → `true` if value is a non-empty plain string (legacy, visible everywhere) OR value is a dict with `value[lang]` non-empty.

**Frontend filtering (`AurexSections.js`) — 14 sections:**
- **Aurex sections**: `AurexAudience` (filter `i.title`), `AurexProcess` (`i.title`), `AurexPricing` (`i.name`), `AurexTeam` (`i.name`, `max_visible` still respected), `AurexEvents` (`e.title`, view-all hidden when empty), `AurexPartners` (`i.name`), `AurexClients` (`i.name`).
- **Mono variants**: `AurexServicesMono` (`s.title`), `AurexNewsMono` (`p.title`), `AurexBlogMono` (`p.title`, external posts), `AurexReadingMono` (`b.title` + wrap `b.title`/`b.author` with `tt()`), `AurexTestimonialsMono` (`t.content`, page index resets on lang change), `AurexPortfolioMono` (`i.title`), `AurexGalleryMono` (`i.title`).
- `AurexAboutMono` now hides the whole section when `data.title` has no translation for the current locale (strict mode). Conditional render for every field.

**CMS managers — LocalizedField wiring for 5 managers:**
- `TestimonialsManager.js` — `name`, `title` (role), `content` get EN/ES tabs. List view uses `adminText()` for name/title/content to prevent React crashes when fields are dicts.
- `AboutManager.js` — `label`, `title`, `description`, `signature_name`, `signature_title`, `button_text` all wrapped with `LocalizedField`.
- `ServicesManager.js` — `title`, `short_description`, `full_content` localized. Table uses `adminText(item.title)`.
- `BlogManager.js` — `title`, `summary`, `content` localized. Table title via `adminText()`.
- `BooksManager.js` (Reading List) — `title`, `author`, `description`, `synopsis`, `who_is_it_for`, `about_author` localized. Table cells use `adminText()`.

**Backend**: no changes — existing endpoints store raw dicts and round-trip transparently.

**Verified behavior:**
- Admin creates item with only ES content → hidden in EN mode, visible in ES mode.
- Admin creates item with both EN and ES → shows correct locale per switcher.
- Legacy plain-string items (pre-i18n content) remain visible in every locale.
- Section-level content (titles, subtitles, CTAs) strict per previous iteration — no cross-locale fallback.

## Pending/Backlog
- (P2) SEO pre-render: nightly job emitting hydrated `/index.html` with meta tags + above-the-fold content (important for bilingual SEO).
- (P2) S3/Cloud Image Storage migration
- (P2) Production SMTP Configuration
- (P2) Stripe Connect full marketplace (automatic payouts replacing manual logging)
- (P2) Add coupon input to `MentorCalendarView` Confirm Booking dialog (currently only MentorshipProfile has it)

**User feedback resolved — 8 fixes in one push.** All verified via iteration_62 testing agent: 31/31 backend tests + frontend verification.

**Strict i18n mode (`lib/i18n.js`):**
- `t(value, lang)` no longer falls back to `defaultLang` or other locales or `_legacy` keys. If the current locale is empty, returns `''`. Plain legacy strings still work (returned as-is).
- `setLocaleValue()` no longer stashes `_legacy` fallbacks — fresh strings are discarded on first edit so old data can't leak into other locales.
- Added `adminText(v)` helper — returns first non-empty locale for admin-only list previews (so CMS rows stay readable regardless of which locale is active).
- Added `hasAnyTranslation(v)` helper for conditional rendering.

**FR React crash fix (`AurexSectionsManager.js`):**
- Item rows were rendering `{item.description}` and `{item.badge}` directly — crashed with "Objects are not valid as a React child" when the field was a dict like `{fr: "…"}`. Now wrapped with `adminText()`.
- `schema.itemPreview(item)` functions in `aurexSchemas.js` refactored to call `adminText()` on every dict-capable field (`i.title`, `i.name`, `i.role`).
- Duplicate handler handles both plain-string and localized `{en, es, …}` dicts when appending " (Copy)".

**"Open in new window" standardization (`aurexSchemas.js`):**
- Added `cta_new_tab` to `aurex_audience` config + `aurex_pricing` items.
- Added `view_all_new_tab` to `aurex_team` + `aurex_events` configs.
- Partners/Clients already had `link_target` select. All Aurex sections now uniformly support the new-tab flag.

**Unified rectangular buttons (`AurexSections.js`):**
- Audience CTA, Team view-all, Events View + View-all, Pricing CTA (in-plan), Contact Submit all switched from `rounded-full` → `rounded-sm` with 1.5px border matching About's `MonoButton`. Verified border-radius = 0px in DOM.

**Removed hardcoded default fallbacks (`AurexSections.js`):**
- Every mono variant header (Services / News / Blog / Map / Testimonials / Contact) now uses conditional render: `{tt(cmsConfig.title) && <h2>{tt(cmsConfig.title)}</h2>}`. No more "Our Services" / "Testimonials" / "Blog" / "From our desk" / "Presence" / "Let's work together" leaking through when the admin has an empty translation in the current locale.
- CTAs hide entirely when `tt(cmsConfig.cta_text)` is empty.
- Video section no longer shows `_legacy` pollution — strict tt() + PUT wipe cleared stale DB data.

**Testimonials photo + role (`AurexTestimonialsMono`):**
- Backend field name was `image` (not `avatar`) — frontend now reads `t.image || t.avatar` as fallback.
- Role field was `t.title` (not `t.role`) in the TestimonialsManager — frontend now prefers `tt(t.title) || tt(t.role)` and renders under the name in uppercase tracking.

**Services card conditional linking (`AurexServicesMono`):**
- Previously fell back to internal `/service/{id}` when `external_url` was unset — now renders as a plain non-clickable `<Reveal>` when no external URL is set. When external URL is present, renders as `<a>` honoring `open_in_new_tab`. Hover underline only applies on linked cards.

**Hero CTA filter fix (`AurexHeroMono`):**
- CTAs array filter changed from `c.text` (truthy check includes objects) to `tt(c.text)` (content check) so buttons without a translation for the active locale are hidden entirely.

## Pending/Backlog
- (P2) SEO pre-render: nightly job emitting hydrated `/index.html` with meta tags + above-the-fold content (important for bilingual SEO).
- (P2) S3/Cloud Image Storage migration
- (P2) Production SMTP Configuration
- (P2) Stripe Connect full marketplace (automatic payouts replacing manual logging)
- (P2) Add coupon input to `MentorCalendarView` Confirm Booking dialog (currently only MentorshipProfile has it)


## Typography — Mid-word Break Fix (Feb 24, 2026)
**Root cause:** RichTextEditor (Quill) saved rich text with `&nbsp;` between every word (e.g. `Aurex&nbsp;is&nbsp;a&nbsp;private...`). The browser treats `&nbsp;` as part of a single word, forcing mid-character or hyphen-point splits when the paragraph had to wrap.

**Fix:**
- `/app/frontend/src/components/AurexSections.js` — imported `normalizeRichText` and wrapped every `dangerouslySetInnerHTML` payload (About description, Process steps, Audience items, Portfolio summaries, Contact description, Hero title+description).
- `/app/frontend/src/pages/HomePage.js` — applied the existing `cleanHtml()` helper at the source of `descriptionHtml` and `csDescription` so all three theme variants (modern/classic/default) inherit the sanitised HTML.
- `/app/frontend/src/components/HeroSection.js` — wrapped `tt(slide.title/subtitle/description)` in `normalizeRichText(...)`.
- Global CSS guard rails in `/app/frontend/src/index.css` preserved: `word-break: normal; overflow-wrap: break-word; hyphens: none;` across `.rich-text-content` and `:where([class*="aurex"])` scopes.

**Verification:** Runtime scan reports 0 of 11 rich-text nodes on the homepage contain `&nbsp;` / U+00A0. Screenshot confirms natural word-boundary wrapping.

## Landing Page Typography + Legacy Theme Crash Fix (Feb 24, 2026)
**Bug 1 — `html.replace is not a function`:** When the landing page was disabled and the active theme switched to `default` / `modern` / `classic`, `HomePage.js` crashed because `cleanHtml()` assumed its input was always a string, but Services cards pass raw field values that can be LocalizedField objects (`{ en: '…' }`) once the CMS saves a translation. The object propagated into `cleanHtml` → `.replace` → TypeError.

**Bug 2 — Mid-word break + hyphen break on Landing Page:** Same `&nbsp;` root cause as the Aurex fix, plus Landing Page had a `nbHyphens()` helper that only guarded hyphenated words without addressing the non-breaking-space problem.

**Fix:**
- `/app/frontend/src/pages/HomePage.js`:
  - Made `cleanHtml()` defensive — accepts any input, coerces to String, now also strips the partial entity `&nbsp` (no semicolon) that can survive slice-truncation of external feeds.
  - Added `const tt = useT();` inside every legacy-theme section and wrapped every text render (`title`, `category`, `description`, `name`, `role`, `content`, etc.) so LocalizedField values resolve to the active locale instead of crashing or rendering `[object Object]`.
  - Sections updated: `ServicesSection`, `NewsSection`, `ReadingListSection`, `PortfolioSection`, `TestimonialsSection` (all three theme variants each), `MapSection` popup.
- `/app/frontend/src/pages/LandingPage.js`:
  - Imported `normalizeRichText` and folded it into `nbHyphens()` so landing page now (a) strips `&nbsp;` / U+00A0 before (b) upgrading hyphens to U+2011. `nbHyphens` is now defensive (accepts strings, LocalizedField objects, null).
- `/app/frontend/src/index.css`:
  - Rewrote the policy comment block to make the base typography rules explicitly permanent across ALL themes (Aurex + default/modern/classic) AND the Landing Page, documenting the CSS layer + companion JS layer (`normalizeRichText`, `nbHyphens`) as the canonical word-wrapping contract for all current and future components.

**Verification:**
- Rendered `/` with `active_theme=modern,classic,default` and `landing_page_enabled=false` — all three render without crash (`PAGE-ERRORS: []`, `HAS-CRASH: false`).
- Rendered `/` with `active_theme=aurex` + `landing_page_enabled=true` — landing page renders cleanly with compound words intact and 0 `&nbsp;` nodes detected.
- ESLint clean on all modified files.


## CMS Roles & Permissions System (Feb 24, 2026)
Granular role-based access control for the entire CMS.

**Backend**
- `/app/backend/models/cms_sections.py` — canonical registry of 42 CMS sections with group/URL-prefix mappings, plus `SYSTEM_ROLES` seed (Administrator = full_access, Member = no CMS).
- `/app/backend/models/database.py` — `require_admin` rewritten to be permission-aware (resolves section from request URL via `get_section_for_path`, admin short-circuits to allow-all). Added strict `require_super_admin` (guards role-management itself) and `get_user_permissions(user)` helper.
- `/app/backend/routes/roles.py` — full CRUD: `GET/POST/PUT/DELETE /api/admin/cms-roles`, `GET /api/admin/cms-sections`, `PUT /api/admin/members/{id}/cms-roles`. System roles cannot be deleted (HTTP 400). Admin-only sections (e.g. `roles_permissions`) are filtered out of the assignable matrix and cannot be granted via permission list.
- `/app/backend/routes/auth.py` — `/auth/me` now returns `cms_roles: [role_id,...]` and sorted `effective_permissions: [section_key,...]` so the frontend can filter the sidebar without a second round-trip.
- `/app/backend/server.py` — `seed_system_roles()` runs on startup; idempotent and back-fills `cms_roles` on every legacy member record.

**Frontend**
- `/app/frontend/src/pages/admin/RolesManager.js` — full editor at `/admin/roles`: role list, create/update/delete, checkbox matrix grouped by CMS Section Registry groups, group-level "Select All" with indeterminate state, global Select-All/Clear-All, Full-access toggle, Save/Cancel.
- `/app/frontend/src/pages/admin/Forbidden.js` — `<CmsSectionGuard section="...">` wrapper renders a 403 panel INSIDE `AdminLayout` so the sidebar stays visible (operators can navigate to permitted sections).
- `/app/frontend/src/pages/admin/AdminLayout.js` — each sidebar item now carries a `section` key; items (and their group dividers) are filtered by `user.effective_permissions`. Header role badge reads "Admin" or "Operator" based on `role`.
- `/app/frontend/src/pages/admin/MembersManager.js` — new "CMS Roles" column with role chips + inline edit dialog (checkbox list of all roles, saves via `PUT /api/admin/members/{id}/cms-roles`).
- `/app/frontend/src/App.js` — `ADMIN_ROUTES` config drives both the landing-enabled and landing-disabled route blocks through a single `renderAdminRoutes()` helper; every entry is wrapped in `<CmsSectionGuard>` or `<AdminOnlyRoute>`. `ProtectedRoute` now admits any user with at least one CMS permission (was `role === 'admin'` only).
- `/app/frontend/src/pages/admin/AdminLoginPage.js` — allows operators through when they have any `effective_permissions`.
- `/app/frontend/src/lib/auth.js` — login re-fetches `/auth/me` after the token is stored so `user` always carries `effective_permissions` and `cms_roles`.

**Verified by testing_agent_v3_fork (iteration_67.json)** — 100% pass on 13 backend API tests + 17 frontend scenarios. Zero critical or minor issues. Confirmed: admin sees all 42 sections, operator (carlos) sees only 3 sections (Dashboard/Analytics/Blog), 403 pages render with sidebar intact, system roles cannot be deleted, admin-only routes reject operators regardless of their permissions.


## Roles & Permissions — Follow-up (Feb 24, 2026)
Five fixes layered on top of the baseline R&P system.

**1. Operator uploads (Gallery Albums + every other section)**
- Root cause: `/api/upload` and `/api/upload-file` used the URL-based `require_admin` which had no section mapping for upload paths → fell through to "Admin access required".
- Fix: new `require_any_cms_access` dependency in `database.py` admits any user with at least one section permission. Both upload endpoints in `admin_tools.py` switched over.

**2. Member-role revocation = instant My Account lockout**
- Backend gates: `/api/auth/login` (default + `login_type='cms'`), `/api/member/login`, and `get_current_member` reject 403 "My Account access has been revoked" when `cms_roles` doesn't include `role_member`. Admins bypass.
- New `login_type='cms'` lets operators (with non-Member roles) keep using `/admin/login` even after role_member is removed.
- Frontend `MemberRoute` redirects to `/my-account/login` if user lacks the role; navbar `hasMyAccount` flag hides the link instantly.

**3. CMS Welcome page (operators without Dashboard permission)**
- New `/app/frontend/src/pages/admin/CmsWelcome.js` renders `settings.cms_welcome` rich text (sanitised through `normalizeRichText`) so operators land on a meaningful greeting instead of a 403.
- Settings → General now has a `LocalizedField`-wrapped `RichTextEditor` for `cms_welcome` (data-testid='settings-cms-welcome').
- `/admin` index route is now `<AdminIndexRouter />` which serves Dashboard or CmsWelcome based on the `dashboard` permission.

**4. Website navbar gating (all 3 theme variants)**
- `useNavData` hook returns `hasCmsAccess` (admin OR ≥1 effective_permission) and `hasMyAccount` (admin OR has `role_member`).
- Aurex / Modern / Classic navbars all reuse these flags. Mobile menus too.
- Result: bare members see only My Account; operators see Admin + (My Account if member); admins see both.

**5. Members table + editor cleanup**
- "Member Type" column renamed to "Mentor" with YES (emerald badge) / "-" values driven by `item.is_mentor`.
- Admin/Member dropdown removed from the Members editor's Personal tab — every new member defaults to `role: 'member'` + `cms_roles: ['role_member']`. Promotion to admin is now done by assigning the Administrator CMS role via the new "CMS Roles" column inline editor.
- Idempotent back-fill on startup defaults `is_mentor: false` on legacy member records.

**Verified by testing_agent_v3_fork (iteration_68.json)** — 14/15 backend (93%, the one "minor" was the legacy `is_mentor` missing field which has now been back-filled), 100% frontend. Manual screenshot regression: operator without Dashboard sees CmsWelcome with only assigned sections in sidebar; navbar correctly toggles Admin / My Account based on roles; Members table renders the new column; revoking role_member redirects to login.


## Global DataTable + Enrollment UX (Feb 26, 2026)
Two large feature batches.

### 1. Reusable DataTable hook for every CMS table
- `/app/frontend/src/components/admin/useDataTable.js` — single drop-in hook + render helpers (`DataTableToolbar`, `DataTablePagination`, `SortableTh`).  Provides real-time search (custom `searchFields` or `searchAccessor`), multi-column sort with locale-aware string + numeric + ISO-date comparisons, page-size selector (10/25/50/100, persisted via `storageKey`), and prev/next + numbered pagination with ellipsis windowing.  Adopting it is ~10 lines per table; future tables inherit the behaviour automatically by importing the hook.
- **16 managers converted in this turn**: Members, Contacts, Blog, Books, Pages, Portfolio, Purchases, Services, Users, MemberTypes, Hero, AdminCoupons (Coupons tab), AdminBundles, Maps (both Locations and Maps tabs), LandingContacts, LandingSubscribers.
- **Stable testIds for QA**: `<id>-search-input`, `<id>-page-size`, `<id>-count`, `th-<field>`, `<id>-pagination`, `<id>-page-{first,prev,next,last,N}`.
- Special case — `ServicesManager` keeps its drag-drop reordering: drag is only active when search is empty AND sort is by `order` (or unset), preventing ambiguous reorder when a user-applied sort/filter is in effect.

### 2. Enrollment bulk visibility + auto-skip empty steps
- **CMS** — `EnrollmentFieldsManager` step header now shows `X/Y visible` count plus a contextual `Show All` / `Hide All` button (data-testid `step-{N}-bulk-toggle`).  Optimistic UI + parallel `Promise.all` of the toggle endpoint; rollback + `load()` if any call fails.  When all fields in a step are hidden, an amber `SKIPPED ON PUBLIC FLOW` badge surfaces next to the step name so admins immediately see the consequence on the public flow.
- **Public flow** — `MembershipEnrollment.js` derives `activeSteps` from `fields` (any step with at least one visible field, plus step 4 which always renders for the submit screen).  Stepper renumbers 1…N, progress bar advances `1/N` per step, nav buttons swap to "Submit" only when on the last *active* step, validation filters by `f.visible !== false` so hidden fields are never required, and a guard `useEffect` automatically advances the user past a step that became empty mid-session.

**Verified by testing_agent_v3_fork (iteration_69.json)** — 100% frontend pass, zero issues, zero action items.  Manual screenshot confirmed: hiding steps 2 + 3 turns the public stepper into "Step 1 of 2" with `Invitation CODE → Confirm & Submit` only and a 50%-per-step progress bar.



## Calendar DataTable Migration + Auth/Enrollment Crash Fix (Feb 27, 2026)
Completes the global DataTable rollout to the remaining 4 calendar-related CMS managers and verifies the React `{en}` object-rendering crash on public Auth + Enrollment pages.

### 1. DataTable applied to all 4 Calendar managers
- **GlobalEventsManager** (`/admin/calendar/global`) — wired (previous fork only added the import). Search by title/type/location, sortable Title/Type/Date/Time/Capacity/Registered/Status, paginated. Calendar grid view untouched.
- **MentorshipScheduleManager** (`/admin/calendar/mentorship`) — search by mentor/title/type, sortable Mentor/Title/Date/Time/Type/Max/Booked/Waitlist/Status, paginated.
- **MentorSlotTemplatesManager** (`/admin/calendar/mentor-slot-templates`) — search by name/title/type, sortable Name/Title/Type/Max/Duration, paginated.
- **BlockedDatesManager** (`/admin/calendar/blocked-dates`) — search by date/reason, sortable Date/Reason, paginated.
- TestId prefixes: `events`, `mslots`, `tpl`, `blocked` (e.g. `events-search-input`, `mslots-pagination`, `th-mentor_name`).
- Row numbering uses `(dt.page - 1) * dt.pageSize + i + 1` so it stays correct across pages.

### 2. Verified `{en}` React-child crash fix
- `MemberLogin.js` wraps `settings.brand_name` in `tt()`.
- `MembershipEnrollment.js` wraps field placeholders + brand name in `tt()`.
- `/my-account/login` and `/membership-enrollment` confirmed crash-free; brand renders as plain string.

**Verified by testing_agent_v3_fork (iteration_70.json)** — 7/7 frontend scenarios pass, 100%, zero action items. Regression-spot-checked Members + Portfolio DataTables still healthy. Note: public enrollment route is `/membership-enrollment` (not `/enroll`).

### Backlog (P2)
- SEO pre-render nightly job to emit hydrated `/index.html` with meta + above-the-fold content.
- Real S3/Cloud image storage migration (currently local container).
- Production SMTP configuration.

## CMS UX Polish + My Account Navigation CMS (Feb 27, 2026)
Four operator-requested improvements, all shipped together.

### 1. Sidebar reorder — Security between Membership and System
Security (Roles & Permissions) divider + link moved from the very bottom of the sidebar to sit between the Membership group and the System group. No permission semantics changed — still admin-only.

### 2. Admin login button honours CMS colours
`AdminLoginPage.js` Sign-In button was hardcoded gold `#c9a84c`. Now uses `var(--ad-button-bg, #0D9488)` + `var(--ad-button-text, #ffffff)` so it respects CMS → Settings → Colors → Admin → Button Background like every other admin surface.

### 3. Member Levels — 5 new My Account Section permissions
`SIDEBAR_SECTIONS` in `MemberLevelsManager.js` gained: **AUX Calendar** (`global-calendar`), **Earnings** (`earnings`), **Session Bundles** (`bundles`), **My Reservations** (`my-bookings`), **Calendar Sync** (`calendar-sync`). Previously the public `MyAccountLayout.js` hardcoded these 5 ids into a bypass list (always visible regardless of level). That bypass is gone — level permissions now gate them like every other nav entry. `mentorship-calendar` remains visible for mentors only (not level-gated).

### 4. NEW — "My Account Navigation" CMS page (drag + toggle)
`/admin/myaccount-nav` — mirrors the Page Builder pattern but for My Account sidebar items. 13 rows (the full nav catalog), drag to reorder, per-row eye-switch to hide globally, single "Save order" button.

**Backend (`routes/membership.py`):**
- Lazy-seeded `myaccount_nav` collection (13 items from `MYACCOUNT_NAV_CATALOG`; backfills any future built-ins on next GET).
- `GET /public/myaccount-nav` — ordered list for `MyAccountLayout.js`.
- `GET /admin/myaccount-nav` — admin list.
- `PUT /admin/myaccount-nav/{id}` — toggle `visible` (and optionally rename `label`).
- `PUT /admin/myaccount-nav-reorder` — persist drag order.

**Registry:** new `myaccount_nav` key under `group: myaccount` in `cms_sections.py` so Roles & Permissions can grant/deny access per CMS operator.

**Public apply:** `MyAccountLayout.js` fetches the nav on mount and (a) hides any row with `visible:false`, (b) renders items in the CMS-saved order, (c) still filters the result by the member's level permissions + mentor-only flags.

**Verified by testing_agent_v3_fork (iteration_71.json)** — 10/10 pass (100% backend pytest + 100% frontend). pytest file at `/app/backend/tests/test_myaccount_nav.py`. Sidebar ordering verified programmatically (Membership Settings idx=36, Roles & Permissions idx=38, Contacts idx=40). Admin login button bg verified as `rgb(115,175,95)` (CSS var, not hardcoded gold).

### Backlog (P2)
- SEO pre-render nightly job to emit hydrated `/index.html` with meta + above-the-fold content.
- Real S3/Cloud image storage migration.
- Production SMTP configuration.



## Inline rename for My Account Navigation (Feb 27, 2026 — same day follow-up)
Per user request, added click-to-rename on top of the existing drag-reorder + visibility toggle.

- **CMS UI** (`MyAccountNavManager.js`) — clicking a row label flips it into an input (auto-focus, 64-char max). Enter commits, Escape cancels, blur commits. Optimistic update + toast on success; rolls back to the previous label on failure. A tiny pencil icon hints editability when the row is idle.
- **Backend** already accepted `{label}` on `PUT /admin/myaccount-nav/{id}` — verified empty/whitespace labels are rejected (`400 No editable fields supplied`).
- **Public apply** (`MyAccountLayout.js`) — when a CMS label override is present it takes precedence over both the hardcoded `ALL_NAV_ITEMS.label` and the dynamic AUX-prefix substitution (`global-calendar`). Breadcrumb also honours the rename.
- Self-tested: API rename `global-calendar → Events Hub` → public endpoint returns `Events Hub`; UI click-to-rename + reload persists; reset back to defaults cleanly.

## My Account Nav — permission sync + URL gate + page titles (Feb 27, 2026 — same day follow-up)
Four operator-reported issues fixed together.

1. **Member Levels permissions reflect CMS renames** — `MemberLevelsManager.js` fetches `/admin/myaccount-nav` on mount and merges live labels onto the hardcoded catalog. Renaming "Portfolios" → "Investments" in CMS immediately updates both the permission checkbox text AND the chips on each existing level card.
2. **"My Calendar" (`mentorship-calendar`) is now a first-class permission** — added to `SIDEBAR_SECTIONS`; also removed the hardcoded bypass in `MyAccountLayout.js` so it is now properly level-gated (still mentor-only via the existing `mentorOnly` flag + member-type permission).
3. **Hidden sections are unreachable via URL** — `isRouteAllowed` in `MyAccountLayout.js` now also denies access when `navOrderState.items[id].visible === false`, so typing `/my-account/my-community` after hiding it in CMS redirects the member to their first allowed page. Also enforces the mentor-only flag at the route level (direct `/my-account/earnings` to a non-mentor → redirect).
4. **Page titles honour CMS rename** — `MyAccountLayout.js` exposes `{ sectionLabel, navItems }` via `useOutletContext`. `PortfolioList.js` now renders a single `<h1>` (`data-testid='portfolio-list-title'`) using `sectionLabel('portfolios', 'Portfolio List')` instead of the confusing "My Account / Portfolio List" dual-title. `MyCommunity.js` gets the same treatment (`data-testid='my-community-title'`).

**Verified by testing_agent_v3_fork (iteration_72.json)** — 6/6 frontend tests PASS (100%), zero issues. Confirmed: (a) live label propagates to Member Levels dialog; (b) `perm-mentorship-calendar` present; (c) member redirected away from hidden URL; (d) both page titles read from CMS; (e) no regressions on prior iterations.


## Full CMS-driven titles across My Account (Feb 27, 2026 — same day follow-up)
Extended the `useOutletContext().sectionLabel(id, fallback)` pattern from 2 pages to **all 11 remaining My Account pages**. Now every sidebar AND every page h1 is editable from `/admin/myaccount-nav`.

**Pages updated** (all gained a `*-title` data-testid + dynamic label):
- `MembershipProfile.js`, `MentorshipProfile.js` (both empty + populated paths), `MySponsor.js`, `MyEbank.js`, `InviteCode.js`
- `GlobalCalendar.js` (smart fallback: `${aux_prefix} Calendar` only when admin hasn't manually renamed; otherwise the CMS label wins)
- `MentorshipCalendar.js`, `MentorEarnings.js`, `BundlesBrowse.js`, `MyBookings.js`, `CalendarSync.js`

**Smarter `sectionLabel` helper** (`MyAccountLayout.js`): now respects the `dynamicLabel: true` flag — `${aux_prefix} Calendar` substitution applies only when the stored label still equals the seeded default; any custom rename takes precedence.

**Verified by testing_agent_v3_fork (iteration_73.json)** — 14/14 frontend tests PASS (100%). Includes two end-to-end rename roundtrips: `portfolios → Investments` and `my-community → My Team`, both verified on the public member view as carlos@example.com and restored to defaults. Mentor-only pages verified via source grep. All iteration_72 regression tests still green.


## Mentor column fix + DB reset + Testing Manual (Feb 27, 2026 — same day follow-up)

### 1. Mentor column derivation
`/api/admin/members` now derives `is_mentor` from the linked `member_types[member_type_id].is_mentor` flag at response-build time. The legacy boolean stored on the member doc was drifting (set once, never refreshed when the type changed). Now: column = YES iff the assigned member type itself has `is_mentor: true`.

### 2. CMS-renamed labels propagate to detail pages
- `BundleDetail.js` "Back to Session Bundles" → uses `sectionLabel('bundles', 'Session Bundles')`. data-testid: `back-to-bundles`.
- `EventDetail.js` "Back to Calendar" → uses `sectionLabel('global-calendar', '${aux_prefix} Calendar')`. data-testid: `back-to-calendar`.
- `MyAccountLayout.js` event-detail breadcrumb now also reads the CMS rename (was hardcoded to AUX prefix).

### 3. Big DB reset + 10-member exhaustive test matrix
Hard-deleted every member except admin, AUX-1, AUX-2, AUX-3 (per user choice 4a). Recreated:
- **4 CMS roles**: CMS Manager (everything except Backup + Roles), Content Editor (Landing+Aurex+Portfolio+SEO), Support (Members+Contacts+Purchases), Mentor Coordinator (Calendar group only).
- **4 member levels**: Free, Standard, Premium, Mentor.
- **10 sample members** AUX-101..AUX-110, password `123456789` for all. Sponsor chain: 1→AUX-1, 2→AUX-2, 3→AUX-3, 4-10→samplemember1. Each combination of role × level × type covered (full matrix in `/app/memory/test_credentials.md`).

Idempotent reseed: `cd /app/backend && python3 scripts/seed_test_scenario.py`.

### 4. Documentation → Testing Manual (NEW block)
- Added `/api/docs/testing-manual` route (no auth, like the other doc endpoints) that auto-renders the live test-account matrix, role/level reference, mentor logic explanation, sponsor tree and 10 suggested test scenarios. Always accurate — pulled from the database at request time.
- DocumentationManager now shows a 5th card pointing to it (data-testid `doc-link-testing-manual`).
- Operator Manual extended with new sections **9. Roles & Permissions** + **10. My Account Navigation** describing the 4 seeded operator roles and the rename/reorder workflow.

**Verified by testing_agent_v3_fork (iteration_74.json)** — 10/10 tests PASS, 100% backend (17/17) + frontend, zero issues. CMS labels mutated during testing have been restored to defaults.


## Sort + Community fields + Bell colors (Feb 27, 2026 — same day follow-up)

1. **Natural-numeric sort across all DataTables** — `useDataTable.compareValues` now uses `localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })`. Effect: AUX column on the Members table now sorts AUX-1, AUX-2, AUX-3, AUX-10, AUX-101 instead of the old alphabetic AUX-1, AUX-101, AUX-2... This benefits every other table that has alphanumeric values too.
2. **Sortable Sponsor column** — `MembersManager` Sponsor `<th>` → `<SortableTh field="sponsor_membership_number">`. Numeric sort, nulls go to the end.
3. **Testing Manual 500 fix** — `/api/docs/testing-manual` previously crashed when a UI-created member had username `samplemember11@gmail.com` (the int-extraction call exploded). Now uses a regex to extract the trailing integer; non-numeric usernames sort to the end without crashing.
4. **My Community modal — 7 new profile fields** — `/member/my-community` response now includes phone, gender, date_of_birth, country, state, city, zip_code on each tree node. Modal renders a 2-col grid with `data-testid='community-modal-<field>'` for each; empty values show a dash. Date-of-birth formatted MM/DD/YYYY.
5. **Notification bell — configurable, prominent colors** — added 4 new MYACCOUNT_COLORS keys (`bell_icon`, `bell_hover_bg`, `bell_badge_bg`, `bell_badge_text`); bell now defaults to gold (was grey) with a red badge ringed by the header bg so it pops. All four are editable from CMS → Settings → Colors.

**Verified by testing_agent_v3_fork (iteration_75.json)** — 6/6 PASS, 100% backend (15/15 pytest) + 100% frontend, zero issues. Regression tests for iterations 70-74 still green.


## Member info modal + Community photo (Feb 27, 2026 — same day follow-up)

### 1. CMS Members table — Info icon + modal
- New per-row Info button (`data-testid='view-info-<member_id>'`) sitting before Edit/Delete.
- Opens dialog `member-info-dialog` with two sections:
  - **Profile facts grid** (`member-info-profile`): 14 labels — Phone, Gender, Date of Birth, Country, State, City, ZIP Code, Address, Member Type, Member Level, Mentor, Sponsor, Status, Registered. Avatar image when present, first-letter fallback otherwise.
  - **Enrollment Q&A** (`member-info-enrollment`): step-tagged question/answer rows pulled from `enrollment_applications.form_data` joined with the live `enrollment_fields` catalog. Richtext blocks stripped; legal_checkbox rendered as "Accepted" / "Not accepted"; legacy keys appended at end.
- Empty-state message (`member-info-no-enrollment`) for members created via CMS / seeded / migrated (no public enrollment record).
- New endpoint `GET /api/admin/members/{member_id}/enrollment` (admin-only).

### 2. My Community modal — real photo
`MyCommunity.js` avatar circle now renders `<img data-testid="community-modal-photo">` when `selected.avatar` is truthy (with `onError` fallback that hides the image), else falls back to the existing first-letter span. Circle gained an avatar-border ring matching the CMS-configurable `--ma-avatar-border` color.

**Verified by testing_agent_v3_fork (iteration_76.json)** — 8/8 PASS, 100% backend (11/11 + 15/15 regression) + 100% frontend, zero issues.


## Admin-create defaults + Enrollment modal hardening (Feb 27, 2026 — same day follow-up)

1. **Admin-created members default to lowest level + Member role** — `POST /api/admin/members` now resolves `level_id` (when missing or empty) to the lowest-order member level (currently `level_free`). Combined with the always-set `cms_roles: ["role_member"]`, an admin-created account now inherits the same baseline restrictions as someone who registered via `/membership-enrollment` (only "Membership Profile" visible until upgraded). Explicit `level_id` in the request body is still honoured.
2. **Friendlier "no enrollment" message** in the Member Info modal — old wording implied something was wrong; new wording explains the case clearly: *"This member was created directly from the CMS, so there are no enrollment-form answers to display. The basic profile data shown above was entered manually."*
3. **React-safe enrollment Q&A serialisation** — backend `_flatten()` helper coerces every saved form value (dict, list, bool, int, etc.) to a string before sending to the modal. Multi-checkbox / dynamic-topics fields like `{Terminology: true, Tools: true, "Capital Markets": false, ...}` now render as comma-joined truthy keys (`"Terminology, Tools, Products, Debt & Credit"`), bools as `Yes`/`No`, ints stringified, lists comma-joined. Frontend `MembersManager.js` keeps a belt-and-braces defensive fallback so any future legacy payload still can't crash the modal.

**Verified by testing_agent_v3_fork (iteration_77.json)** — 7/7 PASS, 100% backend (10/10 pytest) + 100% frontend, zero issues. Iteration 75-76 regressions still green.


## Rating-grid serialisation (Feb 27, 2026 — same day follow-up)
The previous `_flatten()` rule kept only truthy keys, which dropped numeric values for the **"Rate your knowledge (1-5)"** field. Updated the dict branch to detect shape:
- All values bool → join only truthy keys (e.g. `"Terminology, Products"`).
- Otherwise (ratings, scores, mixed) → render `"key: value"` pairs (e.g. `"Terminology: 4, Tools: 3, Capital Markets: 5, ..."`), skipping empty/null entries.
- Self-tested via direct DB seeding all three dict shapes (rating, boolean, mixed). Endpoint output verified.


## Stripe-from-CMS + Site URL + AWS-prep cleanup (Feb 27, 2026 — same day follow-up)

### 1. CMS-driven Stripe configuration
- New `Stripe` tab in **Settings** with: secret-key input (show/hide toggle, masked preview after save), Replace + Clear buttons, status badge (✓ Configured · TEST/LIVE / ⚠ Not configured), and a read-only **Webhook URL** code block with copy button.
- New backend module `/app/backend/utils/runtime_config.py`: `get_stripe_api_key()` and `get_site_url()` look up CMS settings first, fall back to env. All 7 Stripe endpoints (`payments.py`, `bundles.py`, `mentor_slots.py`) now use the helper. Missing key → friendly `503` with operator-actionable message instead of a 500 crash.
- New endpoint `GET /api/admin/stripe-status` returns `{configured, mode, webhook_url, site_url}` for the live UI badge.
- Saved key never leaks: `/admin/settings` masks it (`sk_test_•••ABCD`), `/public/settings` strips `stripe_api_key`, `stripe_publishable_key`, `stripe_webhook_secret`.

### 2. Editable Site URL (CMS-driven)
- New first field in **Settings → General** (`data-testid='settings-site-url'`).
- Server-side normalize: bare domain → `https://`, trailing slash stripped, whitespace trimmed. `mydomain.com` / `http://mydomain.com/` / `https://x.com//` all canonicalize cleanly.
- Used by `webhook_url`, password-reset templates, QR/invite links — single source of truth, no restart required.

### 3. AWS deploy hardening
- Removed Emergent platform scripts (`emergent-main.js`, `debug-monitor.js`) and PostHog analytics block from `/app/frontend/public/index.html`. Two fewer external dependencies, plus removes a hardcoded analytics API key.
- No other references to `assets.emergent.sh` or `posthog.com` exist in the repo.

**Verified by testing_agent_v3_fork (iteration_78.json)** — 10/10 PASS (100% backend 26/26 pytest + 100% frontend, zero issues, zero regressions). Confirmed: keys never leak, normalization works on all edge cases, all 7 Stripe endpoints honor the new config hierarchy, no Emergent/PostHog references in index.html.


## Stripe "Test connection" button (Feb 27, 2026 — same day follow-up)
Adds preflight key validation to the Settings → Stripe tab.

- New endpoint `POST /api/admin/stripe-test` — accepts optional `{api_key}` (so operators can validate a key BEFORE saving). Falls back to the currently saved CMS/env key if body empty. Pings `GET https://api.stripe.com/v1/account` via httpx and returns:
  - `{ok: true, mode, account_id, business_name, country, default_currency, email}` on 200
  - `{ok: false, code: 'bad_format' | 'invalid' | 'no_key' | 'network' | 'http_<n>', message}` otherwise
- New "Test connection" button below the key input (`data-testid='stripe-test-btn'`); result panel `stripe-test-result` shows ✅ business profile (account ID + email + country/currency) or ❌ Stripe's own error message.
- Self-tested all 4 paths: bad format / invalid key / empty body fallback / non-admin 403. No new deps; uses `httpx` which was already pinned.


## AWS Installation Guide (CMS doc + INSTALL.md) — Feb 27, 2026 same day follow-up
- New `/app/INSTALL.md` (~600 lines, 19 KB) covering all 14 requested sections: requirements, stack versions, Ubuntu prep, dependencies, project config, DB import, frontend build, FastAPI systemd service, Nginx (with/without domain), AWS ports table, Let's Encrypt, Stripe setup, verification checklist, troubleshooting (8 common errors). Plain English, no jargon, copy-pasteable commands.
- New CMS doc route `/api/docs/aws-install` — renders INSTALL.md as styled HTML inside the existing docs system using `markdown-it-py` (already in requirements). Includes "Save as PDF", "Download .md" and "Back to Docs" toolbar buttons.
- New `/api/docs/aws-install/markdown` route serves the raw `.md` for download.
- DocumentationManager — 6th card "AWS Installation Guide" with `Server` icon (amber).
- Bundled the live DB dump at `/app/backend/scripts/seed_dump/test_database/` (12 MB) — `mongorestore --db consultant_cms --drop seed_dump/test_database/` rebuilds the production state on the new server.
- Self-tested: HTTP 200 on both routes; INSTALL.md picked up live (any future edit auto-applies on next request, no restart).

