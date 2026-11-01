# Goldcrust 🍗✨

A cloud-native, distributed Quick-Service Restaurant (QSR) and cloud kitchen dispatch platform with an asynchronous Python backend and responsive frontend.

- **🌐 Live Production URL**: [https://d2op0qoad2cd5v.cloudfront.net/](https://d2op0qoad2cd5v.cloudfront.net/)
- **📁 GitHub Repository**: [https://github.com/Black-sys-dot/Goldcrust](https://github.com/Black-sys-dot/Goldcrust)

---

## 👥 Project Team & Role Distribution

| Roll No. | Name | Primary Project Role & Contributions |
| :--- | :--- | :--- |
| **124B1F048** | **Sarvam Tarapure** | **Backend & Cloud Infrastructure** (AWS EC2, RDS PostgreSQL, CloudFront CDN, Security Hardening, Session Cryptography) |
| **124B1F049** | **Swarit Naikade** | **Backend Architecture & Database Engineering** (FastAPI Service Layer, Order Dispatching, Database Migrations, Health Diagnostics) |
| **124B1F137** | **Shatakshi Ayya** | **Frontend UI/UX & Responsive Design** (Page Layouts, Visual Hierarchy, Accessibility, Component Styling) |
| **124B1F140** | **Sailee Khambekar** | **Frontend Development & Client State** (Shopping Cart State, Dynamic Profile Prefilling, Order Tracking Views) |

---

## 🚀 Key Features

- **Interactive Menu & Customization**: Dynamic catalog browsing across Fried Chicken, Burgers, Wraps, Sides, Combos, Desserts, and Drinks with size, spice level, and addon selectors.
- **Geospatial Kitchen Dispatch**: Real-time Haversine great-circle calculation routing customer orders directly to the closest Pune kitchen hub.
- **Crockford Base-32 Tokenization**: Non-sequential random order ticket numbers (e.g. `GC HRRL2J`, over $1.07\times 10^9$ unguessable permutations) eliminating IDOR risks.
- **User Authentication & Profile Saving**: Salted `scrypt` password hashing ($N=16384$) with tamper-proof HMAC-SHA256 session cookies. Allows saving delivery addresses for instant checkout prefill.
- **Guest-to-Account State Reconciliation**: Seamless automatic migration of guest `localStorage` tickets into the permanent database ledger upon user registration or login.
- **Multi-Stage Order Tracking**: Real-time kitchen lifecycle progression (`Placed` $\rightarrow$ `Kitchen` $\rightarrow$ `Rider` $\rightarrow$ `Delivered`) on `/tickets.html`.

---

## 🛠️ Architecture & Tech Stack

- **Frontend**: Vanilla HTML5, modern CSS3, and ES6 JavaScript. Lightweight, framework-free, and optimized for mobile and desktop screens.
- **Backend API**: Python 3.12 with [FastAPI](https://fastapi.tiangolo.com/) ASGI framework and Uvicorn asynchronous worker.
- **Database**: 
  - **Production**: Amazon RDS PostgreSQL 16.14 in private VPC with KMS storage encryption.
  - **Local Development**: Adaptive fallback to SQLite3 with automatic DDL migrations.
- **Security & Cloud Infrastructure**:
  - AWS CloudFront global edge CDN with TLS 1.3 termination.
  - EC2 port 8000 locked exclusively to CloudFront Managed Prefix Lists (`pl-9aa247f3`).
  - SSH port 22 closed; out-of-band management via AWS Systems Manager (SSM).
  - IMDSv2 strictly enforced (`HttpTokens: required`).

---

## 💻 Local Development Setup

### Prerequisites
- Python 3.8+
- Git

### Installation & Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/Black-sys-dot/Goldcrust.git
   cd Goldcrust
   ```

2. **Set up a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Open `http://localhost:8000` in your browser.

---

## 📂 Project Structure

```text
├── assets/
│   ├── css/styles.css        # Responsive styling and design system
│   ├── js/app.js             # Cart state, UI drawers, modals, and auth logic
│   ├── js/data.js            # Catalog dishes, pricing rules, and categories
│   └── img/                  # High-resolution dish photography
├── auth.py                   # Salted scrypt hashing and HMAC session tokens
├── catalog.py                # Authoritative server-side pricing & discounts
├── db.py                     # Dual-driver database layer (PostgreSQL + SQLite)
├── pay.py                    # Razorpay payment verification & HMAC checks
├── main.py                   # FastAPI routing, static mounting, and APIs
├── index.html                # Landing page & featured offers
├── menu.html                 # Full catalog with filtering & dish customization
├── checkout.html             # Delivery details, address prefill, and payment
├── tickets.html              # Multi-stage kitchen tracking and lookup
└── Dockerfile                # Minimal container packaging
```

---

## 📜 License
Academic and educational project demonstration.
