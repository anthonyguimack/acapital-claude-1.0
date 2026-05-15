# AWS Installation Guide

This guide walks you through deploying this consultant CMS on a fresh AWS Ubuntu server, from a brand-new EC2 instance to a working production site. No prior server experience required — every command is copy-pasteable.

> Need to read this from the CMS instead? Open **CMS → Documentation → AWS Installation Guide**.

---

## 1. Minimum Server Requirements

| Item              | Minimum               | Recommended                       |
|-------------------|-----------------------|-----------------------------------|
| **Operating System** | Ubuntu Server 22.04 LTS | Ubuntu Server 24.04 LTS            |
| **CPU**           | 2 vCPU                | 4 vCPU                            |
| **RAM**           | 4 GB                  | 8 GB                              |
| **Disk**          | 20 GB SSD             | 40 GB SSD                         |
| **AWS instance**  | `t3.medium`           | `t3.large` or `t3a.large`         |
| **Network**       | Public IPv4 + ports listed in §10 |   |

The application itself is light, but MongoDB likes RAM and Node's build step temporarily peaks around 2 GB.

---

## 2. Technology Stack (exact versions used in this project)

| Layer | Tool / library | Version |
|---|---|---|
| Runtime | Python | **3.11.x** |
| Runtime | Node.js | **20.x** (Active LTS) |
| Package manager | Yarn | **1.22.x** |
| Database | MongoDB Community Edition | **7.0.x** |
| Reverse proxy | Nginx | **1.18+** |
| Web framework | FastAPI | **0.110.1** |
| ASGI server | Uvicorn | **0.25.0** |
| ODM driver | Motor (async MongoDB) | **3.3.1** |
| Auth | bcrypt + python-jose JWT | bcrypt 4.1.3 |
| Frontend | React | **19** |
| Frontend toolchain | react-scripts | **5.0.1** |
| Frontend router | react-router-dom | **7** |
| UI primitives | shadcn/ui + Tailwind CSS | (see `package.json`) |
| Icons | lucide-react | **0.507** |
| Drag/drop | @dnd-kit/core | **6.3** |
| HTTP client | axios | **1.8** |
| Toasts | sonner | **2.0** |
| Payments | Stripe | sk_test_/sk_live_ (configured in CMS) |
| Email | aiosmtplib | 5.1 (optional) |

> The full Python `requirements.txt` is in `/app/backend/requirements.txt`. The full JS dependency tree is in `/app/frontend/package.json`.

---

## 3. Preparing the Ubuntu Server

SSH into your EC2 instance:

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

Update everything and install base tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential ca-certificates gnupg lsb-release ufw
```

Set the timezone (optional but recommended):

```bash
sudo timedatectl set-timezone UTC
```

Enable a basic firewall (we'll open the right ports later):

```bash
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## 4. Installing All Dependencies

### 4.1 Python 3.11

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 --version   # should print Python 3.11.x
```

### 4.2 Node.js 20.x + Yarn

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn
node --version    # v20.x
yarn --version    # 1.22.x
```

### 4.3 MongoDB 7.0 Community Edition

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod --no-pager   # should say active (running)
```

> **Ubuntu 24.04 note:** if the install fails because of a missing `libssl1.1`, use Ubuntu 22.04 instead — MongoDB 7.0 official packages don't yet support 24.04 cleanly.

### 4.4 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

### 4.5 Process supervisor (optional — choose one of two paths)

Pick one:

* **Path A (recommended) — systemd**: built into Ubuntu, no extra install. We'll use this in §8.
* **Path B — supervisor**: `sudo apt install -y supervisor`. Mirrors the Emergent setup; useful if your team is already familiar with it.

---

## 5. Configuring the Project

### 5.1 Copy the project files to the server

If you have the project in a Git repo:

```bash
cd /opt
sudo mkdir consultant-cms && sudo chown $USER:$USER consultant-cms
cd consultant-cms
git clone <your-repo-url> .
```

Or if you're uploading from your laptop:

```bash
# From your local computer:
scp -i your-key.pem -r ./consultant-cms ubuntu@your-ec2-public-ip:/opt/consultant-cms
```

The project structure should look like:

```
/opt/consultant-cms/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   ├── routes/
│   ├── models/
│   └── scripts/
│       └── seed_dump/         <-- database dump (see §6)
└── frontend/
    ├── package.json
    └── src/
```

### 5.2 Backend `.env`

Create `/opt/consultant-cms/backend/.env`:

```bash
nano /opt/consultant-cms/backend/.env
```

Paste and edit:

```ini
MONGO_URL=mongodb://localhost:27017
DB_NAME=consultant_cms
CORS_ORIGINS=https://your-domain.com,http://your-ec2-public-ip
JWT_SECRET=replace-with-a-long-random-string
ADMIN_EMAIL=admin@your-domain.com
ADMIN_PASSWORD=replace-with-strong-password
STRIPE_API_KEY=
SITE_URL=https://your-domain.com
```

What each variable means:

| Variable | What to put | Required? |
|---|---|---|
| `MONGO_URL` | Connection string to MongoDB. `mongodb://localhost:27017` if Mongo runs on the same server. | Yes |
| `DB_NAME` | Any name — typically `consultant_cms`. The app creates collections automatically. | Yes |
| `CORS_ORIGINS` | Comma-separated list of frontend URLs allowed to talk to the API. | Yes |
| `JWT_SECRET` | Long random string used to sign login tokens. Generate one: `openssl rand -hex 32` | Yes |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | First admin account auto-created on first boot. | Yes |
| `STRIPE_API_KEY` | Leave blank — you'll set it from the CMS UI. (See §12.) | No |
| `SITE_URL` | Optional fallback when no CMS site_url is saved yet. | No |

Generate a strong JWT secret:

```bash
openssl rand -hex 32
```

### 5.3 Frontend `.env`

Create `/opt/consultant-cms/frontend/.env`:

```ini
REACT_APP_BACKEND_URL=https://your-domain.com
```

> Important: `REACT_APP_BACKEND_URL` must NOT have a trailing slash and must be the **public URL** users hit in their browser. When Nginx proxies `/api` to the backend (see §9), use the same domain you give to users.

If you don't have a domain yet, use the EC2 public IP:

```ini
REACT_APP_BACKEND_URL=http://your-ec2-public-ip
```

You'll change it later when you point a domain to the server.

### 5.4 Install backend dependencies

```bash
cd /opt/consultant-cms/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations==0.1.0 \
  --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

The last line installs the Stripe wrapper from Emergent's public package index (no auth required — it's just hosted outside PyPI). If you don't sell paid mentorship/bundles you can skip this — only the 7 paid-Stripe endpoints need it.

> **Important — Motor (MongoDB driver):**
> The `motor` package is **already listed in `requirements.txt`** (pinned to `motor==3.3.1`) and is installed automatically by the step above. It is the async MongoDB driver that FastAPI uses to talk to your database — without it, the backend crashes on startup with `ModuleNotFoundError: No module named 'motor'`.
>
> If you ever see that error, it almost always means the install ran against the wrong Python. Two quick checks:
>
> 1. **The virtualenv is active.** Your prompt should start with `(venv)`. If not:
>    ```bash
>    cd /opt/consultant-cms/backend
>    source venv/bin/activate
>    ```
>
> 2. **Install Motor explicitly (fallback):**
>    ```bash
>    pip install motor==3.3.1
>    ```
>
> Then restart the backend (`sudo systemctl restart consultant-backend`) and verify it boots without errors:
> ```bash
> sudo journalctl -u consultant-backend -n 30 --no-pager
> ```

### 5.5 Install frontend dependencies

```bash
cd /opt/consultant-cms/frontend
yarn install
```

This step downloads ~250 MB of node_modules and takes a few minutes.

---

## 6. Database — Importing the Seed Dump

A pre-seeded MongoDB dump ships with the project at:

```
/opt/consultant-cms/backend/scripts/seed_dump/
```

It contains your roles, levels, sample members, settings — the full state your CMS was in when this guide was generated.

### 6.1 Restore the dump

```bash
cd /opt/consultant-cms/backend/scripts
mongorestore --db consultant_cms --drop seed_dump/test_database/
```

Notes:
* Replace `consultant_cms` with whatever you put in `DB_NAME`.
* `--drop` clears existing collections before restoring — safe on a fresh install, **destructive** on an existing one. Remove the flag to merge instead.
* The dump's source database is named `test_database`; that's why the path ends in `seed_dump/test_database/`.

### 6.2 Verify

```bash
mongosh
> show dbs                                        # should list consultant_cms
> use consultant_cms
> db.members.countDocuments()                     # should print 14 (admin + AUX-1..3 + 10 sample)
> db.cms_roles.countDocuments()                   # should print 6
> db.member_levels.countDocuments()               # should print 4
> exit
```

### 6.3 Reset later (optional)

If you ever want to wipe back to a known matrix of test members:

```bash
cd /opt/consultant-cms/backend
source venv/bin/activate
python3 scripts/seed_test_scenario.py
```

This rebuilds 10 sample members, 4 levels, 4 roles. Idempotent — safe to run multiple times.

---

## 7. Deploying the React Frontend

Build the production bundle:

```bash
cd /opt/consultant-cms/frontend
yarn build
```

This creates `/opt/consultant-cms/frontend/build/` — a folder of static HTML/JS/CSS that any web server can serve.

Don't run `yarn start` in production — it's a slow dev server. Nginx will serve `build/` directly (see §9).

> **Re-deploys**: any time you change frontend code or `REACT_APP_BACKEND_URL`, re-run `yarn build`. The new files in `build/` will be picked up on next request.

---

## 8. Deploying the FastAPI Backend (systemd service)

Create the service file:

```bash
sudo nano /etc/systemd/system/consultant-backend.service
```

Paste:

```ini
[Unit]
Description=Consultant CMS — FastAPI backend
After=network.target mongod.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/consultant-cms/backend
EnvironmentFile=/opt/consultant-cms/backend/.env
ExecStart=/opt/consultant-cms/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001 --workers 2
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/consultant-backend.log
StandardError=append:/var/log/consultant-backend.err.log

[Install]
WantedBy=multi-user.target
```

> If you uploaded the project as a different user than `ubuntu`, change `User=` and `Group=` to match.
> `--host 127.0.0.1` keeps the backend internal — Nginx is the only thing that talks to port 8001 from outside.

Enable & start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now consultant-backend
sudo systemctl status consultant-backend --no-pager
```

Tail the logs to verify:

```bash
sudo tail -f /var/log/consultant-backend.log
```

Sanity-check the API:

```bash
curl http://127.0.0.1:8001/api/public/settings
```

Should return JSON.

---

## 9. Nginx Configuration

Nginx will:
* Serve the React `build/` folder for everything except `/api`.
* Proxy `/api/...` to FastAPI on port 8001.
* Force HTTPS once SSL is configured (§11).

### 9.1 Without a domain (just IP, HTTP only)

```bash
sudo nano /etc/nginx/sites-available/consultant-cms
```

```nginx
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 50M;

    # Frontend static files
    root /opt/consultant-cms/frontend/build;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }

    # Uploaded images / static asset routes (if used)
    location /uploads/ {
        alias /opt/consultant-cms/backend/uploads/;
    }
}
```

### 9.2 With a domain

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 50M;

    root /opt/consultant-cms/frontend/build;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }

    location /uploads/ {
        alias /opt/consultant-cms/backend/uploads/;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/consultant-cms /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t                        # syntax check — must say "ok"
sudo systemctl reload nginx
```

Browse to `http://your-ec2-public-ip` (or `http://your-domain.com`) — you should see the landing page.

---

## 10. Required Ports (AWS Security Group)

Open these in the EC2 instance's Security Group:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| **22**  | TCP | Your IP only | SSH for server admin. |
| **80**  | TCP | 0.0.0.0/0    | HTTP (Nginx). Required by Let's Encrypt for the certificate challenge. |
| **443** | TCP | 0.0.0.0/0    | HTTPS (Nginx, after SSL). |
| 8001 | TCP | (do NOT open) | FastAPI — only Nginx talks to it via `127.0.0.1`. |
| 3000 | TCP | (do NOT open) | Not used in production. |
| 27017 | TCP | (do NOT open) | MongoDB — only the local backend connects. |

> If MongoDB ever runs on a separate machine, restrict 27017 to that machine's private IP only. Never expose MongoDB to the public internet.

Update UFW on the server too:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

---

## 11. SSL Installation (Let's Encrypt — free)

You'll need a domain pointing to your EC2 public IP first. Wait ~5 minutes after creating the DNS A record before continuing.

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will:
1. Verify domain ownership over port 80.
2. Issue the certificate.
3. Edit your Nginx config to redirect HTTP → HTTPS automatically.

Verify auto-renewal works:

```bash
sudo certbot renew --dry-run
```

Then update `REACT_APP_BACKEND_URL` in `/opt/consultant-cms/frontend/.env` to use `https://` and rebuild:

```bash
cd /opt/consultant-cms/frontend
yarn build
```

Also update CMS → Settings → General → Site URL to `https://your-domain.com` (no trailing slash).

---

## 12. Stripe Configuration

### 12.1 Get your Stripe API key

1. Go to <https://dashboard.stripe.com/apikeys>.
2. Copy the **Secret key**:
   * `sk_test_...` for testing (no real money).
   * `sk_live_...` for production.

### 12.2 Save the key in the CMS

1. Log in at `https://your-domain.com/admin/login`.
2. Go to **Settings → Stripe**.
3. Paste the secret key in **Stripe Secret Key**.
4. Click **Test connection** — you should see ✅ Connection successful with your business name.
5. Click **Save Settings** at the bottom.

The key is stored in MongoDB and applied immediately — no backend restart needed.

### 12.3 Register the webhook in Stripe

1. In **CMS → Settings → Stripe**, copy the **Webhook URL** shown (something like `https://your-domain.com/api/webhook/stripe`).
2. Go to <https://dashboard.stripe.com/webhooks> → **Add endpoint**.
3. Paste the URL.
4. Select event: at minimum `checkout.session.completed`.
5. Click **Add endpoint**.

That's it — paid mentorship slots and session bundles will now process correctly.

---

## 13. Final Verification

Run through this checklist:

- [ ] `sudo systemctl status mongod` says **active (running)**.
- [ ] `sudo systemctl status consultant-backend` says **active (running)**.
- [ ] `sudo systemctl status nginx` says **active (running)**.
- [ ] `curl https://your-domain.com/api/public/settings` returns JSON (not HTML).
- [ ] `https://your-domain.com` shows the landing page.
- [ ] `https://your-domain.com/admin/login` accepts the admin credentials from `.env`.
- [ ] CMS → Documentation → AWS Installation Guide opens.
- [ ] CMS → Settings → Stripe → **Test connection** returns ✅.
- [ ] DNS A record points to your EC2 IP and SSL padlock shows in browser.
- [ ] No console errors in the browser dev tools.

If every box is checked, you're production-ready.

---

## 14. Troubleshooting Common Issues

### Backend won't start — `ModuleNotFoundError: No module named 'emergentintegrations'`

You're using paid Stripe endpoints. Install the package:

```bash
cd /opt/consultant-cms/backend
source venv/bin/activate
pip install emergentintegrations==0.1.0 \
  --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
sudo systemctl restart consultant-backend
```

### `502 Bad Gateway` on every page

Backend isn't running. Check:

```bash
sudo systemctl status consultant-backend
sudo tail -50 /var/log/consultant-backend.err.log
```

Common fixes: wrong `MONGO_URL` in `.env`, MongoDB not running, virtualenv path wrong.

### Frontend shows the page but API calls fail with CORS errors

`CORS_ORIGINS` in backend `.env` is missing your frontend URL. Add it (comma-separated, no trailing slash) and restart the backend.

### Login stuck — "Invalid credentials" with the right email/password

Either:
* Wrong `JWT_SECRET` between server restarts (each restart invalidates issued tokens — log in again).
* The seeded admin from the dump has a different password than your `.env`. Run:
  ```bash
  cd /opt/consultant-cms/backend
  source venv/bin/activate
  python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('NEWPASSWORD'))"
  # then mongosh:
  # use consultant_cms
  # db.members.updateOne({email:'admin@...'}, {$set:{password_hash:'<paste hash>'}})
  ```

### `yarn build` runs out of memory on `t3.small`

```bash
NODE_OPTIONS=--max_old_space_size=2048 yarn build
```

Or upgrade to `t3.medium`.

### MongoDB refuses to start after reboot

```bash
sudo journalctl -u mongod -n 50 --no-pager
sudo chown -R mongodb:mongodb /var/lib/mongodb /var/log/mongodb
sudo systemctl restart mongod
```

### Stripe webhook events never arrive

* Make sure port 443 is open in the AWS security group.
* In the Stripe dashboard, the webhook URL must be the **public** URL, not `127.0.0.1`.
* Open Stripe → Webhooks → click the endpoint → check the **Recent events** tab for the actual error message.

### Site URL changes don't take effect

The CMS *Site URL* field is now applied without restart, but the React frontend bakes `REACT_APP_BACKEND_URL` at build time. Anytime that value changes, re-run `yarn build`. Then hard-reload the browser (`Ctrl+Shift+R`).

### Need to roll back to a clean test state

```bash
cd /opt/consultant-cms/backend
source venv/bin/activate
python3 scripts/seed_test_scenario.py
```

---

That's it. You're live. 🎉

For day-to-day operation, every CMS-side configuration (Stripe key, Site URL, branding, colors, sections) can be changed from `https://your-domain.com/admin` without touching the server.
