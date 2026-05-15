from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from models.database import db, require_admin
from datetime import datetime

router = APIRouter()

PRINT_CSS = """
@media print {
  body { margin: 0; padding: 20px; }
  .no-print { display: none !important; }
  .page-break { page-break-before: always; }
}
@page { margin: 1cm; }
"""

BASE_CSS = """
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #fff; color: #1a2332; line-height: 1.6; }
.cover { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: linear-gradient(135deg, #1a2332 0%, #0D9488 100%); color: #fff; text-align: center; padding: 40px; }
.cover h1 { font-size: 36px; margin-bottom: 10px; font-weight: 700; }
.cover .subtitle { font-size: 18px; opacity: 0.85; margin-bottom: 30px; }
.cover .meta { font-size: 14px; opacity: 0.65; }
.content { max-width: 900px; margin: 0 auto; padding: 40px 30px; }
h1 { color: #1a2332; font-size: 28px; border-bottom: 3px solid #0D9488; padding-bottom: 8px; margin-top: 40px; }
h2 { color: #0D9488; font-size: 22px; margin-top: 30px; }
h3 { color: #374151; font-size: 18px; margin-top: 20px; }
p { margin: 10px 0; }
table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px; }
th { background: #0D9488; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; }
td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; }
tr:nth-child(even) { background: #f8fafb; }
code { background: #f1f5f9; padding: 2px 6px; border-radius: 3px; font-size: 13px; color: #0D9488; }
pre { background: #1a2332; color: #e5e7eb; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
.info-box { background: #f0fdfa; border-left: 4px solid #0D9488; padding: 12px 16px; margin: 15px 0; border-radius: 0 4px 4px 0; }
.warn-box { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 15px 0; border-radius: 0 4px 4px 0; }
.toolbar { position: fixed; top: 0; left: 0; right: 0; background: #1a2332; color: #fff; padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; z-index: 100; }
.toolbar a, .toolbar button { color: #c9a84c; text-decoration: none; cursor: pointer; background: none; border: 1px solid #c9a84c; padding: 6px 16px; border-radius: 4px; font-size: 13px; }
.toolbar a:hover, .toolbar button:hover { background: #c9a84c; color: #1a2332; }
.spacer { height: 60px; }
ul, ol { padding-left: 24px; }
li { margin: 5px 0; }
"""


@router.get("/docs/flow-diagram", response_class=HTMLResponse)
async def flow_diagram():
    """Serve the use case flow diagram as an interactive HTML/SVG page."""
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Use Case & Business Flow Diagram</title>
<style>{BASE_CSS}{PRINT_CSS}
svg {{ max-width: 100%; height: auto; }}
.diagram-container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
</style></head><body>
<div class="toolbar no-print">
  <span style="font-weight:600;">Use Case & Business Flow Diagram</span>
  <div><button onclick="window.print()">Save as PDF</button> <a href="/admin/documentation">Back to Docs</a></div>
</div>
<div class="spacer no-print"></div>
<div class="diagram-container">
<svg viewBox="0 0 1100 2200" xmlns="http://www.w3.org/2000/svg" style="font-family:Segoe UI,sans-serif;">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#374151"/></marker>
    <marker id="arrow-blue" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#2563eb"/></marker>
    <marker id="arrow-green" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#059669"/></marker>
    <marker id="arrow-orange" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#d97706"/></marker>
  </defs>

  <!-- TITLE -->
  <text x="550" y="35" text-anchor="middle" font-size="24" font-weight="700" fill="#1a2332">System Use Case &amp; Business Flow Diagram</text>
  <text x="550" y="55" text-anchor="middle" font-size="12" fill="#6b7280">Acapital Group LLC - Membership Platform</text>

  <!-- ACTORS -->
  <circle cx="120" cy="100" r="16" fill="#2563eb"/><text x="120" y="135" text-anchor="middle" font-size="11" fill="#2563eb" font-weight="600">Visitor</text>
  <circle cx="300" cy="100" r="16" fill="#059669"/><text x="300" y="135" text-anchor="middle" font-size="11" fill="#059669" font-weight="600">New Member</text>
  <circle cx="500" cy="100" r="16" fill="#c9a84c"/><text x="500" y="135" text-anchor="middle" font-size="11" fill="#c9a84c" font-weight="600">Member</text>
  <circle cx="700" cy="100" r="16" fill="#d97706"/><text x="700" y="135" text-anchor="middle" font-size="11" fill="#d97706" font-weight="600">Sponsor</text>
  <circle cx="900" cy="100" r="16" fill="#dc2626"/><text x="900" y="135" text-anchor="middle" font-size="11" fill="#dc2626" font-weight="600">Administrator</text>

  <!-- SECTION 1: LANDING PAGE -->
  <rect x="50" y="160" width="1000" height="250" rx="8" fill="#f0f9ff" stroke="#bfdbfe" stroke-width="1.5"/>
  <text x="80" y="185" font-size="15" font-weight="700" fill="#1e40af">SECTION 1: Landing Page ( / )</text>

  <!-- Visitor enters site -->
  <rect x="120" y="210" width="180" height="40" rx="20" fill="#2563eb" stroke="none"/><text x="210" y="235" text-anchor="middle" font-size="12" fill="#fff">Visitor enters site</text>

  <!-- Decision: LP Active? -->
  <polygon points="550,210 630,240 550,270 470,240" fill="#fff" stroke="#d97706" stroke-width="2"/>
  <text x="550" y="244" text-anchor="middle" font-size="11" fill="#374151">LP Active?</text>

  <!-- Arrow from visitor to decision -->
  <line x1="300" y1="230" x2="468" y2="240" stroke="#374151" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- Yes: Coming Soon -->
  <rect x="680" y="200" width="160" height="36" rx="4" fill="#fff" stroke="#d97706" stroke-width="1.5"/><text x="760" y="223" text-anchor="middle" font-size="11" fill="#374151">Coming Soon Page</text>
  <line x1="630" y1="234" x2="678" y2="220" stroke="#d97706" stroke-width="1.5" marker-end="url(#arrow-orange)"/>
  <text x="645" y="218" font-size="9" fill="#d97706" font-weight="600">Yes</text>

  <!-- Decision: Launch Date Met? -->
  <polygon points="760,270 830,300 760,330 690,300" fill="#fff" stroke="#d97706" stroke-width="2"/>
  <text x="760" y="303" text-anchor="middle" font-size="10" fill="#374151">Launch Date</text>
  <text x="760" y="314" text-anchor="middle" font-size="10" fill="#374151">Met?</text>
  <line x1="760" y1="236" x2="760" y2="268" stroke="#d97706" stroke-width="1.5" marker-end="url(#arrow-orange)"/>

  <!-- No: Main Website -->
  <rect x="380" y="290" width="160" height="36" rx="4" fill="#fff" stroke="#2563eb" stroke-width="1.5"/><text x="460" y="313" text-anchor="middle" font-size="11" fill="#374151">Main Website</text>
  <line x1="550" y1="270" x2="500" y2="290" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="510" y="278" font-size="9" fill="#2563eb" font-weight="600">No</text>

  <!-- Launch date Yes -> Main Website -->
  <line x1="690" y1="300" x2="542" y2="308" stroke="#059669" stroke-width="1.5" marker-end="url(#arrow-green)"/>
  <text x="610" y="295" font-size="9" fill="#059669" font-weight="600">Yes</text>

  <!-- Auto-switch note -->
  <rect x="820" y="340" width="200" height="36" rx="4" fill="#fef3c7" stroke="#f59e0b" stroke-width="1"/><text x="920" y="357" text-anchor="middle" font-size="10" fill="#92400e">Client-side auto-switch</text><text x="920" y="369" text-anchor="middle" font-size="10" fill="#92400e">(no reload)</text>
  <line x1="830" y1="300" x2="850" y2="340" stroke="#f59e0b" stroke-width="1" stroke-dasharray="4"/>

  <!-- SECTION 2: REGISTRATION PATHS -->
  <rect x="50" y="430" width="1000" height="600" rx="8" fill="#f0fdf4" stroke="#bbf7d0" stroke-width="1.5"/>
  <text x="80" y="455" font-size="15" font-weight="700" fill="#166534">SECTION 2: Two Registration Paths</text>

  <!-- Sponsor generates invite code (center top) -->
  <rect x="370" y="470" width="260" height="44" rx="22" fill="#d97706" stroke="none"/><text x="500" y="497" text-anchor="middle" font-size="12" fill="#fff" font-weight="600">Sponsor Generates Invite Code</text>

  <!-- Split arrow -->
  <line x1="430" y1="514" x2="250" y2="560" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow-blue)"/>
  <line x1="570" y1="514" x2="750" y2="560" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>

  <!-- PATH A -->
  <rect x="100" y="560" width="300" height="44" rx="6" fill="#2563eb" stroke="none"/><text x="250" y="587" text-anchor="middle" font-size="13" fill="#fff" font-weight="700">PATH A: /my-account/register</text>
  <rect x="120" y="620" width="260" height="30" rx="4" fill="#fff" stroke="#2563eb" stroke-width="1.5"/><text x="250" y="640" text-anchor="middle" font-size="11" fill="#374151">Simplified Registration Form</text>
  <rect x="120" y="660" width="260" height="30" rx="4" fill="#fff" stroke="#2563eb" stroke-width="1.5"/><text x="250" y="680" text-anchor="middle" font-size="11" fill="#374151">Invite Code + Name + Email + Password</text>
  <line x1="250" y1="604" x2="250" y2="618" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <line x1="250" y1="650" x2="250" y2="658" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow-blue)"/>

  <!-- PATH B -->
  <rect x="600" y="560" width="350" height="44" rx="6" fill="#059669" stroke="none"/><text x="775" y="587" text-anchor="middle" font-size="13" fill="#fff" font-weight="700">PATH B: /membership-enrollment</text>
  <rect x="620" y="620" width="310" height="26" rx="4" fill="#fff" stroke="#059669" stroke-width="1.5"/><text x="775" y="638" text-anchor="middle" font-size="10" fill="#374151">Step 1: Invite Code + Email + Password</text>
  <rect x="620" y="652" width="310" height="26" rx="4" fill="#fff" stroke="#059669" stroke-width="1.5"/><text x="775" y="670" text-anchor="middle" font-size="10" fill="#374151">Step 2: Clarity Statement (37 fields)</text>
  <rect x="620" y="684" width="310" height="26" rx="4" fill="#fff" stroke="#059669" stroke-width="1.5"/><text x="775" y="702" text-anchor="middle" font-size="10" fill="#374151">Step 3: Legal Agreements + Signature</text>
  <rect x="620" y="716" width="310" height="26" rx="4" fill="#fff" stroke="#059669" stroke-width="1.5"/><text x="775" y="734" text-anchor="middle" font-size="10" fill="#374151">Step 4: Confirm &amp; Submit</text>
  <line x1="775" y1="604" x2="775" y2="618" stroke="#059669" stroke-width="1.5" marker-end="url(#arrow-green)"/>
  <line x1="775" y1="646" x2="775" y2="650" stroke="#059669" stroke-width="1.2"/>
  <line x1="775" y1="678" x2="775" y2="682" stroke="#059669" stroke-width="1.2"/>
  <line x1="775" y1="710" x2="775" y2="714" stroke="#059669" stroke-width="1.2"/>

  <!-- CONVERGENCE -->
  <line x1="250" y1="690" x2="250" y2="780" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow-blue)"/>
  <line x1="775" y1="742" x2="775" y2="780" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>

  <!-- Validate invite code diamond -->
  <polygon points="500,780 600,815 500,850 400,815" fill="#fff" stroke="#374151" stroke-width="2"/>
  <text x="500" y="812" text-anchor="middle" font-size="11" fill="#374151">Invite Code</text>
  <text x="500" y="824" text-anchor="middle" font-size="11" fill="#374151">Valid?</text>
  <line x1="250" y1="780" x2="398" y2="810" stroke="#2563eb" stroke-width="1.5"/>
  <line x1="775" y1="780" x2="602" y2="810" stroke="#059669" stroke-width="1.5"/>

  <!-- Invalid: Error -->
  <rect x="650" y="850" width="120" height="30" rx="4" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/><text x="710" y="870" text-anchor="middle" font-size="11" fill="#dc2626">Error: Invalid</text>
  <line x1="580" y1="830" x2="648" y2="855" stroke="#dc2626" stroke-width="1.5"/>
  <text x="610" y="838" font-size="9" fill="#dc2626" font-weight="600">No</text>

  <!-- Valid: Create account -->
  <line x1="500" y1="850" x2="500" y2="880" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="520" y="868" font-size="9" fill="#059669" font-weight="600">Yes</text>

  <rect x="370" y="882" width="260" height="40" rx="6" fill="#0D9488" stroke="none"/><text x="500" y="907" text-anchor="middle" font-size="12" fill="#fff" font-weight="600">Create Account (Level 1)</text>
  <line x1="500" y1="922" x2="500" y2="940" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>

  <rect x="350" y="942" width="300" height="36" rx="6" fill="#fff" stroke="#0D9488" stroke-width="2"/><text x="500" y="965" text-anchor="middle" font-size="11" fill="#374151">Assign membership_id &amp; sponsor_id</text>
  <line x1="500" y1="978" x2="500" y2="996" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>

  <rect x="380" y="998" width="240" height="36" rx="18" fill="#c9a84c" stroke="none"/><text x="500" y="1021" text-anchor="middle" font-size="12" fill="#1a2332" font-weight="600">Auto-login &amp; Redirect</text>

  <!-- SECTION 3: MY ACCOUNT -->
  <rect x="50" y="1060" width="1000" height="280" rx="8" fill="#fffbeb" stroke="#fde68a" stroke-width="1.5"/>
  <text x="80" y="1085" font-size="15" font-weight="700" fill="#92400e">SECTION 3: My Account ( /my-account )</text>

  <rect x="100" y="1105" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="190" y="1126" text-anchor="middle" font-size="11" fill="#374151">Membership Profile</text>
  <rect x="300" y="1105" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="390" y="1126" text-anchor="middle" font-size="11" fill="#374151">Mentorship Profile</text>
  <rect x="500" y="1105" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="590" y="1126" text-anchor="middle" font-size="11" fill="#374151">My Sponsor</text>
  <rect x="700" y="1105" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="790" y="1126" text-anchor="middle" font-size="11" fill="#374151">My Ebank</text>

  <rect x="100" y="1155" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="190" y="1176" text-anchor="middle" font-size="11" fill="#374151">My Community</text>
  <rect x="300" y="1155" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="390" y="1176" text-anchor="middle" font-size="11" fill="#374151">Portfolios</text>
  <rect x="500" y="1155" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="590" y="1176" text-anchor="middle" font-size="11" fill="#374151">Invite Codes</text>
  <rect x="700" y="1155" width="180" height="32" rx="4" fill="#fff" stroke="#c9a84c" stroke-width="1.5"/><text x="790" y="1176" text-anchor="middle" font-size="11" fill="#374151">Business QR</text>

  <!-- QR Flow -->
  <rect x="130" y="1210" width="380" height="110" rx="6" fill="#fff" stroke="#d97706" stroke-width="1.5"/>
  <text x="150" y="1232" font-size="11" font-weight="600" fill="#d97706">Invite Code Flow:</text>
  <text x="150" y="1250" font-size="10" fill="#374151">1. Sponsor generates invite code</text>
  <text x="150" y="1266" font-size="10" fill="#374151">2. Shares code/link with invitee</text>
  <text x="150" y="1282" font-size="10" fill="#374151">3. Invitee uses Path A or Path B</text>
  <text x="150" y="1298" font-size="10" fill="#374151">4. New member linked as sponsored</text>

  <rect x="540" y="1210" width="380" height="110" rx="6" fill="#fff" stroke="#d97706" stroke-width="1.5"/>
  <text x="560" y="1232" font-size="11" font-weight="600" fill="#d97706">Business QR Flow:</text>
  <text x="560" y="1250" font-size="10" fill="#374151">1. Admin enables QR permission for member</text>
  <text x="560" y="1266" font-size="10" fill="#374151">2. Member generates QR in My Account</text>
  <text x="560" y="1282" font-size="10" fill="#374151">3. QR encodes registration URL with sponsor ID</text>
  <text x="560" y="1298" font-size="10" fill="#374151">4. Scanned QR leads to /my-account/register</text>

  <!-- SECTION 4: CMS ADMIN -->
  <rect x="50" y="1360" width="1000" height="230" rx="8" fill="#fef2f2" stroke="#fecaca" stroke-width="1.5"/>
  <text x="80" y="1385" font-size="15" font-weight="700" fill="#991b1b">SECTION 4: CMS Admin Panel ( /admin )</text>

  <rect x="100" y="1405" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="185" y="1426" text-anchor="middle" font-size="10" fill="#374151">Members Manager</text>
  <rect x="290" y="1405" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="375" y="1426" text-anchor="middle" font-size="10" fill="#374151">Enrollment Fields</text>
  <rect x="480" y="1405" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="565" y="1426" text-anchor="middle" font-size="10" fill="#374151">Geo Data (CRUD)</text>
  <rect x="670" y="1405" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="755" y="1426" text-anchor="middle" font-size="10" fill="#374151">Landing Page</text>
  <rect x="860" y="1405" width="150" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="935" y="1426" text-anchor="middle" font-size="10" fill="#374151">Analytics</text>

  <rect x="100" y="1455" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="185" y="1476" text-anchor="middle" font-size="10" fill="#374151">Member Levels</text>
  <rect x="290" y="1455" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="375" y="1476" text-anchor="middle" font-size="10" fill="#374151">Member Types</text>
  <rect x="480" y="1455" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="565" y="1476" text-anchor="middle" font-size="10" fill="#374151">Settings / SMTP</text>
  <rect x="670" y="1455" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="755" y="1476" text-anchor="middle" font-size="10" fill="#374151">Colors (5 groups)</text>
  <rect x="860" y="1455" width="150" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="935" y="1476" text-anchor="middle" font-size="10" fill="#374151">Backup/Restore</text>

  <rect x="100" y="1505" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="185" y="1526" text-anchor="middle" font-size="10" fill="#374151">Hero / Carousel</text>
  <rect x="290" y="1505" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="375" y="1526" text-anchor="middle" font-size="10" fill="#374151">Pages / SEO</text>
  <rect x="480" y="1505" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="565" y="1526" text-anchor="middle" font-size="10" fill="#374151">Gallery / Portfolio</text>
  <rect x="670" y="1505" width="170" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="755" y="1526" text-anchor="middle" font-size="10" fill="#374151">Blog / Books</text>
  <rect x="860" y="1505" width="150" height="32" rx="4" fill="#fff" stroke="#dc2626" stroke-width="1.5"/><text x="935" y="1526" text-anchor="middle" font-size="10" fill="#374151">Maps</text>

  <!-- LEGEND -->
  <rect x="50" y="1620" width="1000" height="100" rx="8" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>
  <text x="80" y="1645" font-size="13" font-weight="700" fill="#374151">LEGEND</text>

  <circle cx="100" cy="1675" r="8" fill="#2563eb"/><text x="115" y="1680" font-size="11" fill="#374151">Visitor / Path A (Simplified)</text>
  <circle cx="330" cy="1675" r="8" fill="#059669"/><text x="345" y="1680" font-size="11" fill="#374151">New Member / Path B (4-Step)</text>
  <circle cx="580" cy="1675" r="8" fill="#c9a84c"/><text x="595" y="1680" font-size="11" fill="#374151">Member (Authenticated)</text>
  <circle cx="790" cy="1675" r="8" fill="#d97706"/><text x="805" y="1680" font-size="11" fill="#374151">Sponsor / Decision</text>
  <circle cx="970" cy="1675" r="8" fill="#dc2626"/><text x="985" y="1680" font-size="11" fill="#374151">Admin</text>

  <rect x="90" y="1695" width="30" height="12" rx="2" fill="none" stroke="#374151" stroke-width="1.5"/><text x="130" y="1705" font-size="10" fill="#374151">Process</text>
  <polygon points="270,1695 295,1701 270,1707 245,1701" fill="none" stroke="#374151" stroke-width="1.5"/><text x="305" y="1705" font-size="10" fill="#374151">Decision</text>
  <rect x="430" y="1695" width="30" height="12" rx="6" fill="#0D9488" stroke="none"/><text x="470" y="1705" font-size="10" fill="#374151">Action / Result</text>
  <line x1="600" y1="1701" x2="650" y2="1701" stroke="#374151" stroke-width="1.5" marker-end="url(#arrow)"/><text x="660" y="1705" font-size="10" fill="#374151">Flow Direction</text>

</svg>
</div>
</body></html>"""
    return HTMLResponse(content=html)


async def _get_settings():
    s = await db.settings.find_one({}, {"_id": 0})
    return s or {}


@router.get("/docs/technical", response_class=HTMLResponse)
async def technical_documentation():
    settings = await _get_settings()
    brand = settings.get("brand_name", "Acapital Group LLC")
    today = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Technical Documentation - {brand}</title>
<style>{BASE_CSS}{PRINT_CSS}</style></head><body>
<div class="toolbar no-print">
  <span style="font-weight:600;">Technical Documentation</span>
  <div><button onclick="window.print()">Save as PDF</button> <a href="/admin/documentation">Back to Docs</a></div>
</div>
<div class="spacer no-print"></div>

<div class="cover">
  <h1>{brand}</h1>
  <p class="subtitle">Project Technical Documentation</p>
  <p class="meta">Version 1.0 &middot; {today}</p>
</div>

<div class="content">
<h1>1. System Architecture</h1>
<h2>1.1 Overview</h2>
<p>The platform is a full-stack web application designed for membership management, financial consulting, and community engagement. It comprises a public-facing website, a member portal (My Account), a 4-step membership enrollment wizard, and a comprehensive CMS admin panel.</p>

<h2>1.2 Tech Stack</h2>
<table>
<tr><th>Layer</th><th>Technology</th><th>Details</th></tr>
<tr><td>Frontend</td><td>React 18</td><td>SPA with React Router, TailwindCSS, Shadcn/UI, Framer Motion</td></tr>
<tr><td>Backend</td><td>FastAPI (Python)</td><td>Async REST API with Motor (async MongoDB driver)</td></tr>
<tr><td>Database</td><td>MongoDB</td><td>Document-based NoSQL, accessed via Motor</td></tr>
<tr><td>Auth</td><td>JWT + Google OAuth</td><td>Emergent-managed Google Auth integration</td></tr>
<tr><td>Payments</td><td>Stripe</td><td>Test keys pre-configured</td></tr>
<tr><td>Maps</td><td>Leaflet + React-Leaflet</td><td>Interactive maps with clustering</td></tr>
<tr><td>Rich Text</td><td>React-Quill</td><td>WYSIWYG editor for content management</td></tr>
<tr><td>DnD</td><td>@dnd-kit</td><td>Drag-and-drop sorting for form fields</td></tr>
</table>

<h2>1.3 Architecture Diagram</h2>
<pre>
Browser (React SPA)
    |
    v
Kubernetes Ingress (/api/* -> :8001, /* -> :3000)
    |
    +-- Frontend (React :3000) -- Static assets + SPA routing
    |
    +-- Backend (FastAPI :8001)
            |
            +-- MongoDB (Motor async driver)
            +-- File uploads (/api/uploads/)
            +-- SMTP (configurable)
</pre>

<h1>2. Database Structure</h1>
<h2>2.1 Collections</h2>
<table>
<tr><th>Collection</th><th>Purpose</th><th>Key Fields</th></tr>
<tr><td><code>members</code></td><td>All users (members + admins)</td><td>member_id, membership_id, email, password_hash, level_id, sponsor_id, can_create_qr</td></tr>
<tr><td><code>member_levels</code></td><td>Access tiers</td><td>id, name, order, permissions</td></tr>
<tr><td><code>member_types</code></td><td>Role templates</td><td>id, name, is_mentor, corporate, allowed_pages</td></tr>
<tr><td><code>invite_codes</code></td><td>Invitation system</td><td>code, owner_member_id, status, used_by_member_id</td></tr>
<tr><td><code>enrollment_fields</code></td><td>Dynamic form config</td><td>id, step, field_key, label, field_type, order, required, visible, options</td></tr>
<tr><td><code>enrollment_applications</code></td><td>Submitted applications</td><td>id, member_id, email, form_data</td></tr>
<tr><td><code>enrollment_content</code></td><td>CMS-managed step content</td><td>key (step4), title, description</td></tr>
<tr><td><code>countries</code></td><td>Geo: 249 countries</td><td>id, name, code</td></tr>
<tr><td><code>states</code></td><td>Geo: 5,046 states</td><td>id, name, country_id, code</td></tr>
<tr><td><code>cities</code></td><td>Geo: 32,423 cities</td><td>id, name, state_id</td></tr>
<tr><td><code>settings</code></td><td>Global configuration</td><td>brand_name, site_logo, landing_enabled, smtp_*</td></tr>
<tr><td><code>theme_colors</code></td><td>CSS variable management</td><td>website, my_account, admin, landing_page, enrollment</td></tr>
<tr><td><code>portfolios</code></td><td>Investment portfolios</td><td>id, member_id, positions, shared_mode</td></tr>
<tr><td><code>hero_slides</code></td><td>Homepage carousel</td><td>id, title, subtitle, media_type, buttons</td></tr>
<tr><td><code>landing_hero_slides</code></td><td>Landing page carousel</td><td>Same structure as hero_slides</td></tr>
<tr><td><code>pages</code></td><td>Dynamic CMS pages</td><td>id, slug, title, sections (Visual Page Builder)</td></tr>
</table>

<h1>3. API Endpoints</h1>
<h2>3.1 Authentication</h2>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>POST</td><td><code>/api/auth/login</code></td><td>Admin login</td></tr>
<tr><td>POST</td><td><code>/api/member/login</code></td><td>Member login</td></tr>
<tr><td>GET</td><td><code>/api/member/me</code></td><td>Current member profile</td></tr>
<tr><td>POST</td><td><code>/api/auth/google</code></td><td>Google OAuth callback</td></tr>
</table>

<h2>3.2 Membership Enrollment</h2>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>GET</td><td><code>/api/public/enrollment-fields</code></td><td>Get visible form fields</td></tr>
<tr><td>POST</td><td><code>/api/public/enrollment/validate-code</code></td><td>Validate invite code</td></tr>
<tr><td>POST</td><td><code>/api/public/enrollment/check-email</code></td><td>Check email availability</td></tr>
<tr><td>POST</td><td><code>/api/public/enrollment/submit</code></td><td>Submit enrollment + auto-create account</td></tr>
<tr><td>GET/PUT</td><td><code>/api/public/enrollment-content/step4</code></td><td>Step 4 CMS content</td></tr>
<tr><td>CRUD</td><td><code>/api/admin/enrollment-fields</code></td><td>Admin field management</td></tr>
<tr><td>PUT</td><td><code>/api/admin/enrollment-fields/reorder</code></td><td>Drag-and-drop reorder</td></tr>
</table>

<h2>3.3 Geo Data</h2>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>GET</td><td><code>/api/geo/countries</code></td><td>List all countries</td></tr>
<tr><td>GET</td><td><code>/api/geo/states?country_id=X</code></td><td>States for a country</td></tr>
<tr><td>GET</td><td><code>/api/geo/cities?state_id=X</code></td><td>Cities for a state</td></tr>
</table>

<h2>3.4 Member Operations</h2>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>POST</td><td><code>/api/member/generate-codes</code></td><td>Generate invite codes</td></tr>
<tr><td>GET</td><td><code>/api/member/codes</code></td><td>List member's codes</td></tr>
<tr><td>POST</td><td><code>/api/member/generate-qr</code></td><td>Generate QR code for sponsorship</td></tr>
<tr><td>PUT</td><td><code>/api/member/profile</code></td><td>Update member profile</td></tr>
<tr><td>GET</td><td><code>/api/member/community</code></td><td>Get sponsored members tree</td></tr>
<tr><td>CRUD</td><td><code>/api/member/portfolios</code></td><td>Portfolio management</td></tr>
</table>

<h1>4. Authentication System</h1>
<h2>4.1 JWT Tokens</h2>
<p>The system uses JWT (JSON Web Tokens) for stateless authentication. Tokens are signed with <code>JWT_SECRET</code> from environment variables and expire after 10 days.</p>
<div class="info-box"><strong>Token payload:</strong> user_id, email, role (admin/member), exp, iat</div>

<h2>4.2 Password Security</h2>
<p>Passwords are hashed using <strong>bcrypt</strong> with automatic salt generation. Minimum password length is 8 characters, enforced on both frontend and backend.</p>

<h2>4.3 Invite Code Logic</h2>
<p>Each invite code has a unique format: <code>{{prefix}}-{{uuid_fragment}}</code>. When used, the code is marked with <code>status: used</code>, and the new member is linked via <code>sponsor_id</code> and <code>sponsor_membership_number</code>.</p>

<h2>4.4 Membership ID Logic</h2>
<p>Every new member receives a sequential membership number. The display format is <code>{{AUX_PREFIX}}-{{number}}</code> (e.g., AUX-24). The prefix is configurable via CMS &gt; Membership Settings.</p>

<h1>5. Color Scheme &amp; CSS Variables</h1>
<p>The platform uses 5 separate color groups, each with its own CSS variable prefix:</p>
<table>
<tr><th>Group</th><th>Prefix</th><th>Count</th><th>Managed In</th></tr>
<tr><td>Website</td><td><code>--color-*</code></td><td>18 vars</td><td>Settings &gt; Colors &gt; Website</td></tr>
<tr><td>My Account</td><td><code>--ma-*</code></td><td>25 vars</td><td>Settings &gt; Colors &gt; My Account</td></tr>
<tr><td>Admin</td><td><code>--ad-*</code></td><td>15 vars</td><td>Settings &gt; Colors &gt; Admin</td></tr>
<tr><td>Landing Page</td><td><code>--lp-*</code></td><td>20 vars</td><td>Settings &gt; Colors &gt; Landing Page</td></tr>
<tr><td>Enrollment</td><td><code>--me-*</code></td><td>20 vars</td><td>Settings &gt; Colors &gt; Enrollment</td></tr>
</table>

<h1>6. Environment Variables</h1>
<table>
<tr><th>Variable</th><th>File</th><th>Purpose</th></tr>
<tr><td><code>MONGO_URL</code></td><td>backend/.env</td><td>MongoDB connection string</td></tr>
<tr><td><code>DB_NAME</code></td><td>backend/.env</td><td>Database name</td></tr>
<tr><td><code>JWT_SECRET</code></td><td>backend/.env</td><td>JWT signing secret</td></tr>
<tr><td><code>ADMIN_EMAIL</code></td><td>backend/.env</td><td>Default admin email (seed)</td></tr>
<tr><td><code>ADMIN_PASSWORD</code></td><td>backend/.env</td><td>Default admin password (seed)</td></tr>
<tr><td><code>STRIPE_API_KEY</code></td><td>backend/.env</td><td>Stripe test key</td></tr>
<tr><td><code>REACT_APP_BACKEND_URL</code></td><td>frontend/.env</td><td>API base URL for frontend</td></tr>
</table>

<h1>7. Security Considerations</h1>
<ul>
<li><strong>Password encryption:</strong> bcrypt with automatic salting</li>
<li><strong>JWT expiration:</strong> 10-day token lifetime</li>
<li><strong>CORS:</strong> Configurable origins via environment variable</li>
<li><strong>MongoDB:</strong> All queries exclude <code>_id</code> and <code>password_hash</code> from responses</li>
<li><strong>Input validation:</strong> Email format, password length, invite code existence checked server-side</li>
<li><strong>Admin routes:</strong> Protected by <code>require_admin</code> middleware</li>
<li><strong>Member routes:</strong> Protected by <code>get_current_member</code> JWT verification</li>
</ul>
</div>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/docs/operator-manual", response_class=HTMLResponse)
async def operator_manual():
    settings = await _get_settings()
    brand = settings.get("brand_name", "Acapital Group LLC")
    today = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Operator Manual (CMS) - {brand}</title>
<style>{BASE_CSS}{PRINT_CSS}</style></head><body>
<div class="toolbar no-print">
  <span style="font-weight:600;">Operator Manual (CMS)</span>
  <div><button onclick="window.print()">Save as PDF</button> <a href="/admin/documentation">Back to Docs</a></div>
</div>
<div class="spacer no-print"></div>

<div class="cover">
  <h1>{brand}</h1>
  <p class="subtitle">Operator Manual &mdash; CMS Administration Guide</p>
  <p class="meta">Version 1.0 &middot; {today}</p>
</div>

<div class="content">
<h1>1. Getting Started</h1>
<h2>1.1 How to Log In</h2>
<p>Navigate to <code>/admin/login</code> and enter your admin email and password. If this is your first login, use the credentials provided by your system administrator.</p>
<div class="warn-box"><strong>Important:</strong> The admin login is separate from the member login. Admin access is at <code>/admin/login</code>, not <code>/my-account/login</code>.</div>

<h2>1.2 Dashboard Overview</h2>
<p>After login, you'll see the admin dashboard with quick stats: total members, recent enrollments, contact submissions, and page views. The left sidebar provides navigation to all management sections.</p>

<h1>2. Member Management</h1>
<h2>2.1 Members Manager</h2>
<p>Navigate to <strong>Members Manager</strong> from the sidebar. This displays all registered members in a table with their Membership ID, Name, Email, Type, Level, and Sponsor.</p>

<h3>Creating a New Member</h3>
<ol>
<li>Click <strong>+ Add Member</strong></li>
<li>Fill in the <strong>Personal</strong> tab: Name, Email, Password, Gender, Phone, Date of Birth, Address, Country/State/City</li>
<li>Switch to the <strong>Membership</strong> tab to assign Level, Sponsor, Mentor, Status, and QR permissions</li>
<li>Click <strong>Save</strong></li>
</ol>

<h3>Editing a Member</h3>
<p>Click the pencil icon next to any member. The edit dialog has 4 tabs:</p>
<table>
<tr><th>Tab</th><th>Contents</th></tr>
<tr><td>Personal</td><td>Name, email, address, geo data, avatar, passport ID, Zelle</td></tr>
<tr><td>Membership</td><td>Level, ranking, status, fee, dates, type, sponsor, mentor, QR permission, password reset</td></tr>
<tr><td>Ebank</td><td>Read-only financial data entered by the member</td></tr>
<tr><td>Business Card</td><td>Generate QR codes for the member (admin-initiated)</td></tr>
</table>

<h3>QR Code Permission</h3>
<p>In the <strong>Membership</strong> tab, the <strong>Create QR Code</strong> radio (Yes/No) controls whether the member can generate their own QR code from My Account. When set to <strong>Yes</strong>, the member sees a "Business QR" section in their Invite Code page.</p>

<h2>2.2 Member Levels</h2>
<p>Levels define access tiers. Navigate to <strong>Member Levels</strong> to create/edit levels. Each level has a name, order number, and icon. New members from enrollment start at the lowest-order level (Level 1).</p>

<h2>2.3 Member Types</h2>
<p>Types define role templates with permissions. Create types like "Mentor", "Portfolio Manager", etc. Each type can have permissions like: corporate, is_mentor, portfolio_development, application_reviewer, and specific page access.</p>

<h1>3. Membership Enrollment</h1>
<h2>3.1 Form Fields</h2>
<p>Navigate to <strong>Membership Enrollment &gt; Content</strong>. The <strong>Form Fields</strong> tab shows all fields organized by step:</p>
<ul>
<li><strong>Step 1:</strong> Invite Code, Email, Name, Password</li>
<li><strong>Step 2:</strong> Personal, financial, and knowledge assessment fields</li>
<li><strong>Step 3:</strong> Legal agreements and signatures</li>
<li><strong>Step 4:</strong> Confirmation (managed in Step 4 Content tab)</li>
</ul>

<h3>Adding a Field</h3>
<ol>
<li>Click <strong>+ Add Field</strong></li>
<li>Select the Step, Field Type (20 types available), enter Field Key and Label</li>
<li>Optionally set Placeholder, Tooltip, Icon, and Options (for selects/radios)</li>
<li>Toggle Required and Visible</li>
<li>Click <strong>Create Field</strong></li>
</ol>

<h3>Reordering Fields</h3>
<p>Drag fields using the grip handle on the left side of each row. The order is saved automatically.</p>

<h2>3.2 Step 4 Content</h2>
<p>Switch to the <strong>Step 4 Content</strong> tab to customize the confirmation message. Enter a Title and Description (rich text). This content appears when users reach the final step of enrollment.</p>

<h1>4. Geographic Data</h1>
<p>Navigate to <strong>System &gt; Countries, States, Cities</strong>. The system comes pre-loaded with 249 countries, 5,046 states, and 32,423 cities. You can:</p>
<ul>
<li>Search and browse using the breadcrumb navigation</li>
<li>Add new countries, states, or cities</li>
<li>Edit existing entries</li>
<li>Delete entries (cascade warning for states/cities)</li>
</ul>

<h1>5. Landing Page</h1>
<h2>5.1 Activation</h2>
<p>Go to <strong>Settings &gt; General</strong> and toggle <strong>Landing Page Enabled</strong>. Set the <strong>Launch Date</strong> for automatic transition to the main website.</p>

<h2>5.2 Hero Carousel</h2>
<p>Navigate to <strong>Landing Page &gt; Hero</strong>. Add multiple slides with: title, subtitle, description, countdown timer, media (photo/video), buttons, and background images.</p>

<h2>5.3 Content Sections</h2>
<p>Navigate to <strong>Landing Page &gt; Content</strong> to manage: navigation links, contact form section, waiting list section, footer, and cookie banner text.</p>

<h1>6. Website Content</h1>
<h2>6.1 Hero Section</h2>
<p>Manage homepage hero slides: images, text, call-to-action buttons, and revolution slider effects.</p>

<h2>6.2 Dynamic Pages</h2>
<p>Create custom pages with the Visual Page Builder. 16 content block types are available including text, images, galleries, maps, and more.</p>

<h2>6.3 Blog &amp; Reading List</h2>
<p>Manage blog posts with categories, and reading list items with cover images and descriptions.</p>

<h1>7. Settings</h1>
<h2>7.1 General Settings</h2>
<p>Brand name, logos, social links, landing page toggle, launch date.</p>

<h2>7.2 SMTP Configuration</h2>
<p>Configure email sending: SMTP host, port, username, password, sender name, and sender email.</p>
<div class="warn-box"><strong>Critical:</strong> Without valid SMTP credentials, enrollment welcome emails and invite emails will fail silently.</div>

<h2>7.3 Color Management</h2>
<p>5 color groups (Website, My Account, Admin, Landing Page, Enrollment) with live preview. Changes apply instantly to all connected users.</p>

<h1>8. Backup &amp; Restore</h1>
<p>Navigate to <strong>System &gt; Backup</strong>. Export the entire database as JSON, or import a previously exported backup. Always create a backup before major changes.</p>

<h1>9. Roles &amp; Permissions</h1>
<p>Navigate to <strong>Security &gt; Roles &amp; Permissions</strong>. Two roles are seeded as <em>system</em> and cannot be deleted: <strong>Administrator</strong> (full access) and <strong>Member</strong> (no CMS access). Create custom roles by selecting a subset of the CMS section catalog &mdash; the assigned CMS sections become visible to operators logging in at <code>/admin/login</code>.</p>
<p>Built-in operator roles seeded in the testing scenario:</p>
<ul>
<li><strong>CMS Manager</strong> &mdash; full CMS access except Backup and Roles &amp; Permissions.</li>
<li><strong>Content Editor</strong> &mdash; Landing Page, Aurex Sections, Portfolio and SEO.</li>
<li><strong>Support</strong> &mdash; Members, Contacts, Contact Section, Purchases.</li>
<li><strong>Mentor Coordinator</strong> &mdash; Calendar group only (events, schedule, slot templates, blocked dates, bundles, coupons, payouts).</li>
</ul>
<div class="info-box"><strong>Tip:</strong> the <strong>Testing Manual</strong> (Documentation &rarr; Testing Manual) lists every preconfigured test account with login, type, level, mentor flag and sponsor &mdash; auto-generated from the live database.</div>

<h1>10. My Account Navigation</h1>
<p>Navigate to <strong>My Account &gt; My Account Navigation</strong>. Drag rows to reorder the public member sidebar, click any row label to <em>rename</em> the section, and toggle the eye-switch to hide an item globally. The rename propagates everywhere &mdash; sidebar, page H1, breadcrumb, "Back to..." links on detail pages.</p>
</div>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/docs/user-guide", response_class=HTMLResponse)
async def user_guide():
    settings = await _get_settings()
    brand = settings.get("brand_name", "Acapital Group LLC")
    today = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>User Guide (My Account) - {brand}</title>
<style>{BASE_CSS}{PRINT_CSS}</style></head><body>
<div class="toolbar no-print">
  <span style="font-weight:600;">User Guide (My Account)</span>
  <div><button onclick="window.print()">Save as PDF</button> <a href="/admin/documentation">Back to Docs</a></div>
</div>
<div class="spacer no-print"></div>

<div class="cover">
  <h1>{brand}</h1>
  <p class="subtitle">Member User Guide &mdash; My Account</p>
  <p class="meta">Version 1.0 &middot; {today}</p>
</div>

<div class="content">
<h1>1. Getting Started</h1>
<h2>1.1 How to Log In</h2>
<p>Go to the member login page and enter your email and password. If you registered through the Membership Enrollment form, use the credentials you created during registration.</p>
<div class="info-box"><strong>Tip:</strong> If you forgot your password, contact your administrator or sponsor for assistance.</div>

<h2>1.2 Your Dashboard</h2>
<p>After login, you'll see the My Account sidebar with all available sections. Your name, avatar, and role appear at the top of the sidebar.</p>

<h1>2. Membership Profile</h1>
<h2>2.1 General Info</h2>
<p>Click <strong>Membership Profile</strong> in the sidebar. Here you can view and update your personal information:</p>
<ul>
<li>First Name, Last Name, Email</li>
<li>Phone, Date of Birth, Gender</li>
<li>Address, Country, State, City, ZIP Code</li>
<li>Profile photo (avatar)</li>
</ul>
<p>Your Membership ID and membership level are displayed at the top of the profile.</p>

<h2>2.2 Social Networks</h2>
<p>Add your social media profiles (Twitter, Facebook, LinkedIn, Instagram, YouTube, TikTok, Website). These appear on your member profile visible to other community members.</p>

<h2>2.3 Profile Completion</h2>
<p>A progress bar shows how complete your profile is. Try to fill in as many fields as possible to reach 100% completion.</p>

<h1>3. Mentorship</h1>
<h2>3.1 Mentorship Profile</h2>
<p>If you've been assigned a mentor, this section shows your mentor's profile including their name, contact information, and biography.</p>

<h1>4. My Sponsor</h1>
<p>View your sponsor's profile &mdash; the person who invited you to the platform. You can see their membership ID, name, and contact details.</p>

<h1>5. My Ebank</h1>
<p>The Ebank section allows you to manage your financial profile. You can enter and update:</p>
<ul>
<li>Investment amounts and goals</li>
<li>Monthly savings and credit information</li>
<li>Risk tolerance and investment preferences</li>
<li>Financial independence targets</li>
</ul>
<div class="info-box"><strong>Note:</strong> This information is visible to administrators and may be used for personalized financial guidance.</div>

<h1>6. My Community</h1>
<p>Explore the community of members you've sponsored. See a visual tree of your network, including:</p>
<ul>
<li>Direct sponsored members</li>
<li>Total invitations count</li>
<li>Member details when clicking on a community member</li>
</ul>
<p>Use the filters to view: All members, Direct sponsors only, or by Level.</p>

<h1>7. Invite Codes</h1>
<h2>7.1 Generating Codes</h2>
<p>At the top of the Invite Code page, enter the number of codes to generate (1-50) and click <strong>Generate Unique Key</strong>. Each code is a unique identifier your invitees can use to register.</p>

<h2>7.2 Sharing Codes</h2>
<p>For each available code, you can:</p>
<ul>
<li><strong>Copy:</strong> Click the copy icon next to the code to copy it to clipboard</li>
<li><strong>Send by email:</strong> Click the send icon to open the invitation dialog. Fill in the invitee's name, email, phone, and gender, then click Send</li>
</ul>

<h2>7.3 Business QR Code</h2>
<p>If your administrator has enabled QR code creation for your account, you'll see a <strong>Business QR</strong> section between your Membership ID and the codes table.</p>
<ul>
<li>Click <strong>Generate QR Code</strong> to create your personal QR code</li>
<li>The QR encodes a registration URL with your sponsor ID</li>
<li>Anyone who scans the QR code will be directed to the registration page as your sponsored member</li>
<li><strong>Download:</strong> Save the QR code image to share in print or digitally</li>
<li><strong>View Full:</strong> Open the QR code in a new window for easy scanning</li>
<li><strong>Regenerate:</strong> Create a fresh QR code if needed</li>
</ul>

<h1>8. Portfolios</h1>
<h2>8.1 Creating a Portfolio</h2>
<ol>
<li>Navigate to <strong>Portfolios</strong> in the sidebar</li>
<li>Click <strong>New Portfolio</strong></li>
<li>Enter a name and description</li>
<li>Add positions: ticker symbol, quantity, purchase price, purchase date</li>
<li>Set sharing preferences (share with all members or select specific members)</li>
<li>Click <strong>Save</strong></li>
</ol>

<h2>8.2 Viewing Portfolios</h2>
<p>Your portfolio list shows all your investments with current values and performance. Click on any portfolio to see detailed charts and position breakdowns.</p>

<h1>9. Tips &amp; Best Practices</h1>
<ul>
<li>Complete your profile to 100% for better community engagement</li>
<li>Generate multiple invite codes ahead of time to always have available codes</li>
<li>Use the Business QR code at networking events for easy bulk invitations</li>
<li>Check your Community section regularly to stay connected with your network</li>
<li>Keep your Ebank data updated for accurate financial tracking</li>
</ul>
</div>
</body></html>"""
    return HTMLResponse(content=html)



@router.get("/docs/testing-manual", response_class=HTMLResponse)
async def testing_manual():
    """Live testing manual: lists every test member with login, role, type,
    level, mentor flag, sponsor + the full role/level matrix. Renders directly
    from the database so it stays accurate even after seed re-runs."""
    settings = await _get_settings()
    brand = settings.get("brand_name", "Acapital Group LLC")
    if isinstance(brand, dict):
        brand = brand.get("en") or "Acapital Group LLC"
    today = datetime.now().strftime("%B %d, %Y")

    # Live data
    types_list = await db.member_types.find({}, {"_id": 0, "id": 1, "name": 1, "is_mentor": 1}).to_list(100)
    type_by_id = {t["id"]: t for t in types_list}
    type_mentor = {t["id"]: bool(t.get("is_mentor")) for t in types_list}

    levels = await db.member_levels.find({}, {"_id": 0}).sort("order", 1).to_list(100)

    roles = await db.cms_roles.find({}, {"_id": 0}).to_list(100)
    role_by_id = {r["id"]: r for r in roles}

    members = await db.members.find(
        {}, {"_id": 0, "password_hash": 0}
    ).sort("membership_number", 1).to_list(1000)

    # Sample members are those whose username starts with "samplemember"
    # but only the seed-script ones (samplemember1..samplememberN). UI-created
    # members may have email-as-username like "samplemember11@gmail.com" — those
    # should sort to the end and not crash the integer key extraction.
    import re as _re
    sample = [m for m in members if (m.get("username") or "").startswith("samplemember")]
    def _sample_sort_key(m):
        u = m.get("username") or ""
        match = _re.match(r"^samplemember(\d+)$", u)
        return (0, int(match.group(1))) if match else (1, u)
    sample.sort(key=_sample_sort_key)

    # Resolve sponsor display
    by_member_id = {m["member_id"]: m for m in members}
    def sponsor_display(m):
        sid = m.get("sponsor_id")
        if not sid:
            return "—"
        sp = by_member_id.get(sid)
        if not sp:
            return f"<code>{sid}</code>"
        return f"{sp.get('membership_id', '')} ({sp.get('first_name', '')} {sp.get('last_name', '')})"

    # ---- Build sample-member rows ----
    rows = []
    for m in sample:
        type_doc = type_by_id.get(m.get("member_type_id")) or {}
        is_mentor = type_mentor.get(m.get("member_type_id"), False)
        non_member_roles = [r for r in (m.get("cms_roles") or []) if r != "role_member"]
        role_names = [role_by_id.get(r, {}).get("name", r) for r in non_member_roles] or ["—"]
        level = next((lvl for lvl in levels if lvl.get("id") == m.get("level_id")), None)
        rows.append({
            "membership_id": m.get("membership_id", ""),
            "name": f"{m.get('first_name', '')} {m.get('last_name', '')}".strip(),
            "email": m.get("email", ""),
            "username": m.get("username", ""),
            "level": level.get("name", "—") if level else "—",
            "type": type_doc.get("name", "—"),
            "is_mentor": is_mentor,
            "cms_roles": ", ".join(role_names),
            "sponsor": sponsor_display(m),
        })

    member_rows_html = "".join(
        f"""<tr>
        <td><strong>{r['membership_id']}</strong></td>
        <td>{r['name']}</td>
        <td><code>{r['email']}</code></td>
        <td><code>123456789</code></td>
        <td>{r['level']}</td>
        <td>{r['type']}</td>
        <td>{'<span style="color:#0D9488;font-weight:700">YES</span>' if r['is_mentor'] else '—'}</td>
        <td>{r['cms_roles']}</td>
        <td>{r['sponsor']}</td>
        </tr>"""
        for r in rows
    )

    # ---- Roles matrix ----
    roles_matrix_html = "".join(
        f"""<tr>
        <td><strong>{r.get('name','')}</strong><br><code>{r.get('id','')}</code></td>
        <td>{r.get('description','—')}</td>
        <td>{'<strong>Full access</strong>' if r.get('full_access') else (str(len(r.get('permissions') or [])) + ' sections')}</td>
        <td>{'System' if r.get('is_system') else 'Custom'}</td>
        </tr>"""
        for r in roles
    )

    # ---- Levels matrix ----
    levels_matrix_html = "".join(
        f"""<tr>
        <td><strong>{lvl.get('name','')}</strong> (order {lvl.get('order','')})</td>
        <td>{', '.join(lvl.get('permissions') or []) or '—'}</td>
        <td><code>{lvl.get('id','')}</code></td>
        </tr>"""
        for lvl in levels
    )

    # ---- Reset instructions ----
    reset_block = """
<h2>How to reset / reseed the testing scenario</h2>
<p>Run the seed script from the backend container. It is <em>idempotent</em> &mdash;
safe to run multiple times.</p>
<pre>cd /app/backend
python scripts/seed_test_scenario.py</pre>
<div class="warn-box"><strong>Heads up:</strong> the seed script HARD-DELETES every
member except <code>admin@consultant.com</code>, <code>AUX-1</code>, <code>AUX-2</code>
and <code>AUX-3</code>. Their bookings, portfolios and ebank data are wiped along
with them. Use with care.</div>
"""

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Testing Manual - {brand}</title>
<style>{BASE_CSS}{PRINT_CSS}
.cred {{ font-family: 'Courier New', monospace; }}
.role-badge {{ display:inline-block; padding:2px 8px; border-radius:3px; background:#e0f2f1; color:#0D9488; font-size:12px; font-weight:600; }}
</style></head><body>
<div class="toolbar no-print">
  <span style="font-weight:600;">Testing Manual</span>
  <div><button onclick="window.print()">Save as PDF</button> <a href="/admin/documentation">Back to Docs</a></div>
</div>
<div class="spacer no-print"></div>

<div class="cover">
  <h1>{brand}</h1>
  <p class="subtitle">Testing Manual &mdash; Test Accounts &amp; Scenarios</p>
  <p class="meta">Version 1.0 &middot; {today}</p>
</div>

<div class="content">
<h1>1. Overview</h1>
<p>This manual lists every preconfigured test account, its role, type, member
level, mentor flag and sponsor. Use it to log in as different personas and
verify behaviour across the CMS and My Account.</p>

<div class="info-box"><strong>Default password for ALL sample members:</strong>
<code>123456789</code>. Login URL: <code>/my-account/login</code>. CMS login:
<code>/admin/login</code>.</div>

<h1>2. Sample test members</h1>
<p>Generated by <code>scripts/seed_test_scenario.py</code>. Each row covers a
distinct combination of <em>level</em>, <em>type</em>, <em>mentor flag</em> and
<em>CMS role</em>.</p>
<table>
<tr>
  <th>Membership ID</th><th>Name</th><th>Email / Username</th>
  <th>Password</th><th>Level</th><th>Type</th><th>Mentor</th>
  <th>CMS Roles</th><th>Sponsor</th>
</tr>
{member_rows_html}
</table>

<h1>3. CMS roles</h1>
<p>Two roles are <strong>system</strong> (Administrator + Member) and cannot be
deleted. The remaining roles are scoped operator profiles created by the seed
script.</p>
<table>
<tr><th>Role</th><th>Description</th><th>Sections</th><th>Type</th></tr>
{roles_matrix_html}
</table>

<h1>4. Member levels</h1>
<p>Levels gate which sidebar items a member can see in My Account. Visibility
also respects the global toggle in <strong>CMS &gt; My Account &gt; My Account
Navigation</strong>.</p>
<table>
<tr><th>Level</th><th>Granted permissions</th><th>ID</th></tr>
{levels_matrix_html}
</table>

<h1>5. Mentor logic</h1>
<p>The <strong>Mentor</strong> column in the Members table is now <em>derived</em>
from the assigned <strong>Member Type</strong>. A member is shown as
<strong>YES</strong> in the Mentor column if and only if their assigned type
has the <code>is_mentor</code> flag enabled. The <code>is_mentor</code> field
on the member document itself is treated as legacy and is not consulted.</p>

<h1>6. Sponsor tree (sample members)</h1>
<ul>
<li><strong>AUX-101</strong> Sample Member 1 &rarr; sponsored by <strong>AUX-1</strong></li>
<li><strong>AUX-102</strong> Sample Member 2 &rarr; sponsored by <strong>AUX-2</strong></li>
<li><strong>AUX-103</strong> Sample Member 3 &rarr; sponsored by <strong>AUX-3</strong></li>
<li><strong>AUX-104</strong> ... <strong>AUX-110</strong> &rarr; all sponsored by
<strong>AUX-101</strong> (Sample Member 1)</li>
</ul>

<h1>7. Suggested test scenarios</h1>
<ol>
<li><strong>Free level visibility:</strong> log in as <code>samplemember2</code>;
verify the My Account sidebar shows ONLY <em>Membership Profile</em>.</li>
<li><strong>Premium level:</strong> log in as <code>samplemember3</code>;
verify access to Sponsor, Community, Portfolios, AUX Calendar, Bundles,
My Reservations, Calendar Sync.</li>
<li><strong>Mentor flow:</strong> log in as <code>samplemember5</code> (Mentors
type, Mentor level); verify <em>My Calendar</em> and <em>Earnings</em> appear in
the sidebar.</li>
<li><strong>Mentor column:</strong> open CMS &gt; Members; only members with
<em>Mentors</em> type should show <strong>YES</strong> in the Mentor column.</li>
<li><strong>CMS Manager scope:</strong> log in as <code>samplemember10</code>
at <code>/admin/login</code>; verify access to every CMS section <em>except</em>
Backup and Roles &amp; Permissions.</li>
<li><strong>Content Editor:</strong> log in as <code>samplemember7</code>;
verify CMS sidebar shows only Landing Page, Aurex Sections, Portfolio and SEO.</li>
<li><strong>Support:</strong> log in as <code>samplemember8</code>; verify
access to Members, Contacts, Contact Section and Purchases.</li>
<li><strong>Mentor Coordinator:</strong> log in as <code>samplemember9</code>;
verify access only to the Calendar group.</li>
<li><strong>Hide-section URL block:</strong> in CMS &gt; My Account &gt; My Account
Navigation, hide <em>My Community</em>; visit <code>/my-account/my-community</code>
as any sample member &mdash; should redirect, not 200.</li>
<li><strong>Rename propagation:</strong> rename <em>Portfolios</em> in My Account
Navigation; verify the sidebar entry, the page H1, the Bundle/Event back-links
and the breadcrumb all pick up the new label.</li>
</ol>

<h1>8. Reset / reseed</h1>
{reset_block}

</div>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/docs/aws-install", response_class=HTMLResponse)
async def aws_install_guide():
    """Renders /app/INSTALL.md as styled HTML so admins can read the deploy
    guide directly inside the CMS at /admin/documentation. The markdown file
    is the source of truth — any edits to INSTALL.md are picked up on the
    next request without a restart."""
    import os
    from markdown_it import MarkdownIt

    settings = await _get_settings()
    brand = settings.get("brand_name", "Acapital Group LLC")
    if isinstance(brand, dict):
        brand = brand.get("en") or "Acapital Group LLC"
    today = datetime.now().strftime("%B %d, %Y")

    md_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "INSTALL.md")
    md_path = os.path.normpath(md_path)
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
    except FileNotFoundError:
        md_text = "_INSTALL.md not found at_ `" + md_path + "`."

    md = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True}).enable("table").enable("strikethrough")
    body_html = md.render(md_text)

    extra_css = """
    .content h1 { font-size: 24px; margin-top: 32px; padding-bottom: 6px; border-bottom: 2px solid #0D9488; }
    .content h2 { font-size: 18px; margin-top: 28px; color: #0D9488; }
    .content h3 { font-size: 15px; margin-top: 20px; }
    .content table { border-collapse: collapse; margin: 14px 0; width: 100%; font-size: 13px; }
    .content th, .content td { border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: top; }
    .content th { background: #f8fafc; color: #1a2332; font-weight: 600; }
    .content code { background: #f1f5f9; padding: 1px 6px; border-radius: 3px; font-size: 0.92em; }
    .content pre { background: #0f172a; color: #e2e8f0; padding: 14px 16px; border-radius: 6px; overflow-x: auto; font-size: 12px; line-height: 1.55; }
    .content pre code { background: transparent; color: inherit; padding: 0; }
    .content blockquote { border-left: 3px solid #0D9488; background: #f0fdfa; padding: 10px 14px; margin: 14px 0; border-radius: 0 4px 4px 0; }
    .content ul, .content ol { padding-left: 22px; }
    .content hr { border: none; border-top: 1px solid #e2e8f0; margin: 28px 0; }
    .content a { color: #0D9488; }
    """

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AWS Installation Guide - {brand}</title>
<style>{BASE_CSS}{PRINT_CSS}{extra_css}</style></head><body>
<div class="toolbar no-print">
  <span style="font-weight:600;">AWS Installation Guide</span>
  <div>
    <button onclick="window.print()">Save as PDF</button>
    <a href="/api/docs/aws-install/markdown" download="INSTALL.md">Download .md</a>
    <a href="/admin/documentation">Back to Docs</a>
  </div>
</div>
<div class="spacer no-print"></div>

<div class="cover">
  <h1>{brand}</h1>
  <p class="subtitle">AWS Installation Guide</p>
  <p class="meta">Step-by-step deploy &middot; {today}</p>
</div>

<div class="content">
{body_html}
</div>
</body></html>"""
    return HTMLResponse(content=html)


@router.get("/docs/aws-install/markdown")
async def aws_install_markdown():
    """Serves the raw INSTALL.md so operators can download the file."""
    import os
    from fastapi.responses import FileResponse
    md_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "INSTALL.md"
    ))
    return FileResponse(md_path, media_type="text/markdown", filename="INSTALL.md")

