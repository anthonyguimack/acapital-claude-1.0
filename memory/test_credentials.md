# Test Credentials

## Admin (full access)
- Email: `admin@consultant.com`
- Password: `Admin123!`
- Role: admin
- CMS Roles: `role_admin` (full access — all sections)

## Kept legacy members (have content, bookings, etc.)
| Membership | Email                   | Password   | Role   | Notes                                  |
|------------|-------------------------|------------|--------|----------------------------------------|
| AUX-1      | carlos@example.com      | Test123!   | member | Corporate type, NOT a mentor (column → −) |
| AUX-2      | john@example.com        | (unknown)  | member | Corporate, no level                    |
| AUX-3      | anthonytest@gmail.com   | Test123!   | member | Mentors type, mentor column → YES      |

## Sample test members (seeded via `/app/backend/scripts/seed_test_scenario.py`)
**Default password for ALL sample members: `123456789`**

| Membership | Username        | Email                      | Level      | Type      | Mentor | CMS Role            | Sponsor      |
|------------|-----------------|----------------------------|------------|-----------|--------|---------------------|--------------|
| AUX-101    | samplemember1   | samplemember1@gmail.com    | Standard   | Corporate | —      | (none)              | AUX-1        |
| AUX-102    | samplemember2   | samplemember2@gmail.com    | Free       | Corporate | —      | (none)              | AUX-2        |
| AUX-103    | samplemember3   | samplemember3@gmail.com    | Premium    | Corporate | —      | (none)              | AUX-3        |
| AUX-104    | samplemember4   | samplemember4@gmail.com    | Standard   | Corporate | —      | (none)              | AUX-101      |
| AUX-105    | samplemember5   | samplemember5@gmail.com    | Mentor     | Mentors   | YES    | (none)              | AUX-101      |
| AUX-106    | samplemember6   | samplemember6@gmail.com    | Premium    | Mentors   | YES    | (none)              | AUX-101      |
| AUX-107    | samplemember7   | samplemember7@gmail.com    | Free       | Corporate | —      | Content Editor      | AUX-101      |
| AUX-108    | samplemember8   | samplemember8@gmail.com    | Premium    | Corporate | —      | Support             | AUX-101      |
| AUX-109    | samplemember9   | samplemember9@gmail.com    | Standard   | Corporate | —      | Mentor Coordinator  | AUX-101      |
| AUX-110    | samplemember10  | samplemember10@gmail.com   | Premium    | Mentors   | YES    | CMS Manager         | AUX-101      |

## Member levels
- **Free** (order=1): membership-profile only
- **Standard** (order=2): membership-profile, my-sponsor, my-community, portfolios, global-calendar, calendar-sync
- **Premium** (order=3): everything except earnings + my-calendar
- **Mentor** (order=4): all 13 My Account sections incl. earnings + my-calendar

## CMS roles (custom)
- **CMS Manager** — all CMS sections except Backup and Roles & Permissions
- **Content Editor** — Landing pages, Aurex Sections, Portfolio, SEO
- **Support** — Members, Contacts, Contact Section, Purchases
- **Mentor Coordinator** — Calendar group only

## Reset / reseed
```
cd /app/backend
python3 scripts/seed_test_scenario.py
```
Hard-deletes everyone except admin + AUX-1/2/3, recreates the table above.

## Documentation
A live "Testing Manual" doc at `/api/docs/testing-manual` (linked from CMS → System → Documentation) auto-renders the same matrix from the database, plus 10 suggested test scenarios.
