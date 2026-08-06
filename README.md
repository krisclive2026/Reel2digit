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

## Project Structure

```
c:\Users\Sreejith\Desktop\R\
├── app/
│   ├── main.py              # FastAPI entrypoint & router mounts
│   ├── database.py          # SQLAlchemy engine & session setup
│   ├── models.py            # Data models (User, Order, Cassette, ShippingLabel, etc.)
│   ├── auth.py              # Security, password hashing & JWT session cookies
│   ├── pricing.py           # Subtotal, shipping & total calculation engine
│   ├── seed.py              # Seed script for initial PricingConfig & Admin user
│   ├── routes/
│   │   ├── auth.py          # Register, Login, Logout routes
│   │   ├── profile.py       # Profile CRUD & Shipping address
│   │   ├── orders.py        # Order wizard, tag inputs, payment stub, label, tracking
│   │   ├── admin.py         # Admin order list, status updater, pricing config editor
│   │   └── feedback.py      # Customer feedback routes
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       ├── css/style.css    # Responsive glassmorphism styling & print media queries
│       └── js/main.js       # Dynamic order form calculations
├── docs/
│   └── PROJECT_PLAN_PYTHON.md
├── requirements.txt
└── README.md
```
