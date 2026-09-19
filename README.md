# ReelToDigit — Cassette-to-MP3 Digitization Portal (Python Stack)

ReelToDigit is a cassette-to-MP3 digitization web portal built using Python, FastAPI, Jinja2 templates, and SQLAlchemy (SQLite).

## Features

- **Authentication & User Profile**: Registration, login, logout, and full profile & shipping address management.
- **Dynamic Order Wizard**: Custom cassette count selection, live pricing calculation, and unique per-cassette tag names.
- **Pricing Engine**: Automated calculation (`subtotal = cassette_count * unit_price`, `shipping = flat_rate`). Rates are editable by admin without redeploying.
- **Shipping Label Generator**: Printable 4x6 India Post-formatted shipping label stub with tracking number.
- **Order Lifecycle & Tracking Timeline**: Step-by-step order tracking (`draft` → `paid` → `label_ready` → `in_transit` → `received` → `processing` → `completed`).
- **Free Pre-Transit Cancellation**: Instant free order cancellation before shipment transit.
- **MP3 Asset Downloads**: Secure audio download links for completed orders.
- **Feedback & Rating**: 1 to 5 star rating and comment form post-completion.
- **Admin Operations Portal**: Cross-user order listing, status advancing, MP3 asset uploader, pricing configuration editor, and user role management.

## Quick Start Guide

### 1. Requirements

- Python 3.10+
- Installed packages in `requirements.txt`:
  `pip install -r requirements.txt`

### 2. Seed Database

Run the database seed script to set up default pricing and test accounts:

```bash
python -m app.seed
```

**Seeded Test Accounts:**
- **Customer Account**: `customer@example.com` / `Customer123!`
- **Admin Account**: `admin@reeltodigit.com` / `Admin123!`

### 3. Run FastAPI Dev Server

Start the application with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Operations (Production / Lightsail)


open http://13.207.185.49/ (use http , not https)


lightsail ip : http://13.207.185.49/ (use http , not https)

These commands assume you're SSH'd into the Lightsail instance, inside `/opt/reeltodigit`, with the Docker Compose stack (`app`, `db`, `minio`, `nginx`) running.

### Viewing the database (Postgres)

```bash
# Interactive session
docker compose exec db psql -U reeltodigit -d reeltodigit

# One-off query
docker compose exec db psql -U reeltodigit -d reeltodigit -c "SELECT * FROM orders;"
```
Useful queries once inside `psql`:
```sql
\dt                              -- list all tables
SELECT * FROM orders;
SELECT * FROM users;
SELECT * FROM payments;
\q                                -- quit
```

### Viewing object storage (MinIO)

**Command line** — list files without opening the console:
```bash
docker compose exec minio mc alias set local http://localhost:9000 <MINIO_ROOT_USER> <MINIO_ROOT_PASSWORD>
docker compose exec minio mc ls local/reeltodigit-media --recursive
```
(re-run `mc alias set` if you get "Access Denied" — the alias resets whenever the MinIO container restarts)

**Web console** (visual) — port 9001 isn't publicly exposed, so tunnel in first:
```bash
# From your own PC/WSL, in a separate terminal:
ssh -i ~/.ssh/reeltodigit.pem -L 9001:localhost:9001 ubuntu@<your-static-ip>
```
Then open `http://localhost:9001` in your browser and log in with `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`.
Requires the `9001:9001` port mapping to be uncommented in `docker-compose.yml`'s `minio` service — comment it back out and `docker compose up -d` when done, to keep it closed to the public.

### Deploying a code change

```bash
cd /opt/reeltodigit
git pull
docker compose up -d --build
```

### Managing the stack

```bash
docker compose ps                    # check status of all services
docker compose logs app --tail 50    # view recent app logs
docker compose logs nginx --tail 50  # view recent nginx logs
docker compose restart app           # restart just the app
docker compose down                  # stop everything
docker compose up -d                 # start everything (without rebuilding)
```

### Seeding pricing + test accounts on a fresh database

```bash
docker compose exec app python -m app.seed
```

## Project Structure

```
/opt/reeltodigit/
├── app/
│   ├── main.py              # FastAPI entrypoint & router mounts
│   ├── database.py          # SQLAlchemy engine & session setup
│   ├── models.py            # Data models (User, Order, Cassette, ShippingLabel, etc.)
│   ├── auth.py              # Security, password hashing & JWT session cookies
│   ├── pricing.py           # Subtotal, shipping & total calculation engine
│   ├── payments.py          # UPI QR code + deep link generator (GPay/PhonePe/Paytm)
│   ├── storage.py           # S3/MinIO-compatible object storage client
│   ├── seed.py              # Seed script for initial PricingConfig & Admin user
│   ├── routers/
│   │   ├── auth.py          # Register, Login, Logout routes
│   │   ├── profile.py       # Profile CRUD & Shipping address
│   │   ├── orders.py        # Order wizard, tag inputs, UPI payment, label, tracking
│   │   ├── admin.py         # Admin order list, status updater, UPI payment confirmation, pricing config editor
│   │   └── feedback.py      # Customer feedback routes
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       ├── css/style.css    # Responsive glassmorphism styling & print media queries
│       └── js/main.js       # Dynamic order form calculations
├── nginx/
│   └── nginx.conf           # Reverse proxy config, incl. MinIO presigned-URL proxying
├── docker-compose.yml       # app + db (Postgres) + minio + nginx stack
├── Dockerfile
├── .github/workflows/deploy.yml  # Build, test, deploy to Lightsail on push to main
├── schema_postgres.sql
├── requirements.txt
├── LIGHTSAIL_SETUP.md
└── README.md
```





Here's the complete HTTPS setup we worked through, as a clean reference:

1. Get a free domain pointing to your IP



Since you don't have a real domain, use nip.io — no signup needed, it resolves automatically:



13.201.54.185.nip.io


2. Install certbot


bash


sudo apt install certbot -y



3. Free port 80 temporarily (certbot needs it)



bash



cd ~/reeltodigit



docker compose stop nginx




4. Get the certificate



bash


sudo certbot certonly --standalone -d 13.201.54.185.nip.io



5. Restart nginx



bash



docker compose start nginx



6. Mount the certs into the nginx container




In docker-compose.yml, under the nginx service's volumes:, add (absolute path, no ./):




yaml
- /etc/letsencrypt:/etc/letsencrypt:ro





7. Enable the SSL server block in nginx config





In nginx/nginx.conf, uncomment/add the HTTPS server block:





nginx
server {
    listen 443 ssl;
    server_name 13.201.54.185.nip.io;

    ssl_certificate     /etc/letsencrypt/live/13.201.54.185.nip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/13.201.54.185.nip.io/privkey.pem;

    client_max_body_size 200M;

    location /static/ {
        alias /srv/app/app/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://reeltodigit_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}





⚠️ Make sure any comment lines actually start with # — an unmarked comment line will crash nginx with an unknown directive error.




8. Recreate nginx to pick up both changes



bash



docker compose up -d nginx




9. Validate config



bash




docker compose exec nginx nginx -t




Should say "syntax is ok" / "test is successful".





10. Test



bash




curl https://13.201.54.185.nip.io/




Notes for renewal

Let's Encrypt certs expire every 90 days. Set up auto-renewal:




bash





sudo certbot renew --dry-run





Email Notification setup




you'll need to add those before the notification email can actually send. Here's the quick recap:

1. Get a Gmail App Password
Go to your Google Account → Security → make sure 2-Step Verification is turned on (required)
Go to https://myaccount.google.com/apppasswords
Create a new app password, name it "ReelToDigit"
Copy the 16-character password (shown only once)




3. Add to .env
bash
nano ~/reeltodigit/.env

Add these lines:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=youraccount@gmail.com
SMTP_PASSWORD=your16charapppassword
ADMIN_NOTIFY_EMAIL=youraccount@gmail.com
SMTP_USER — the Gmail address you're sending from
SMTP_PASSWORD — the 16-character app password (no spaces)
ADMIN_NOTIFY_EMAIL — where the notification should land (can be the same Gmail address, or a different inbox you check)





3. Recreate the app container (env changes need this, not just restart)
bash
cd ~/reeltodigit
docker compose up -d app




5. Verify it picked up the values
bash
docker compose exec app env | grep -E "SMTP|ADMIN_NOTIFY"

Once that's set, test again with "I've Paid" on a draft order and check the inbox. Let me know once you've got the app password and I'll help confirm it's wired up correctly.
