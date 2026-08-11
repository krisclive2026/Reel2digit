ReelToDigit — Cassette-to-MP3 Digitization Portal (Python Stack)

ReelToDigit is a cassette-to-MP3 digitization web portal built using Python, FastAPI, Jinja2 templates, and SQLAlchemy (SQLite).

Features
Authentication & User Profile: Registration, login, logout, and full profile & shipping address management.
Dynamic Order Wizard: Custom cassette count selection, live pricing calculation, and unique per-cassette tag names.
Pricing Engine: Automated calculation (subtotal = cassette_count * unit_price, shipping = flat_rate). Rates are editable by admin without redeploying.
Shipping Label Generator: Printable 4x6 India Post-formatted shipping label stub with tracking number.
Order Lifecycle & Tracking Timeline: Step-by-step order tracking (draft → paid → label_ready → in_transit → received → processing → completed).
Free Pre-Transit Cancellation: Instant free order cancellation before shipment transit.
MP3 Asset Downloads: Secure audio download links for completed orders.
Feedback & Rating: 1 to 5 star rating and comment form post-completion.
Admin Operations Portal: Cross-user order listing, status advancing, MP3 asset uploader, pricing configuration editor, and user role management.
Quick Start Guide
1. Requirements
Python 3.10+
Installed packages in requirements.txt: pip install -r requirements.txt
2. Seed Database

Run the database seed script to set up default pricing and test accounts:

bash
python -m app.seed

Seeded Test Accounts:

Customer Account: customer@example.com / Customer123!
Admin Account: admin@reeltodigit.com / Admin123!
3. Run FastAPI Dev Server

Start the application with Uvicorn:

bash
uvicorn app.main:app --reload --port 8000

Open your browser at http://127.0.0.1:8000.

Operations (Production / Lightsail)

These commands assume you're SSH'd into the Lightsail instance, inside /opt/reeltodigit, with the Docker Compose stack (app, db, minio, nginx) running.

Viewing the database (Postgres)
bash
# Interactive session
docker compose exec db psql -U reeltodigit -d reeltodigit

# One-off query
docker compose exec db psql -U reeltodigit -d reeltodigit -c "SELECT * FROM orders;"

Useful queries once inside psql:

sql
\dt                              -- list all tables
SELECT * FROM orders;
SELECT * FROM users;
SELECT * FROM payments;
\q                                -- quit
Viewing object storage (MinIO)

Command line — list files without opening the console:

bash
docker compose exec minio mc alias set local http://localhost:9000 <MINIO_ROOT_USER> <MINIO_ROOT_PASSWORD>
docker compose exec minio mc ls local/reeltodigit-media --recursive

(re-run mc alias set if you get "Access Denied" — the alias resets whenever the MinIO container restarts)

Web console (visual) — port 9001 isn't publicly exposed, so tunnel in first:

bash
# From your own PC/WSL, in a separate terminal:
ssh -i ~/.ssh/reeltodigit.pem -L 9001:localhost:9001 ubuntu@<your-static-ip>

Then open http://localhost:9001 in your browser and log in with MINIO_ROOT_USER / MINIO_ROOT_PASSWORD. Requires the 9001:9001 port mapping to be uncommented in docker-compose.yml's minio service — comment it back out and docker compose up -d when done, to keep it closed to the public.

Deploying a code change
bash
cd /opt/reeltodigit
git pull
docker compose up -d --build
Managing the stack
bash
docker compose ps                    # check status of all services
docker compose logs app --tail 50    # view recent app logs
docker compose logs nginx --tail 50  # view recent nginx logs
docker compose restart app           # restart just the app
docker compose down                  # stop everything
docker compose up -d                 # start everything (without rebuilding)
Seeding pricing + test accounts on a fresh database
bash
docker compose exec app python -m app.seed
Project Structure
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
