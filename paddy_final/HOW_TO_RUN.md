# HOW TO RUN — CropConnect (AI Edition)
=====================================================================

## WHAT IS NEW (AI Features Added)
- 🤖 AI Farm Assistant Chatbot — floating chat button on every page
- 📊 AI Price Advisory — personalized MSP advice on farmer dashboard
- 🔍 AI Fraud/Risk Detection — officer sees risk score on each booking
- 📝 AI Rejection Explainer — farmer gets plain-language rejection explanation

---

## STEP 1 — INSTALL PYTHON

Make sure Python 3.10 or newer is installed.
Check by running:
    python --version
    (or: python3 --version)

Download Python from: https://www.python.org/downloads/

---

## STEP 2 — OPEN TERMINAL / COMMAND PROMPT

- Windows: Press Win + R → type "cmd" → Enter
- Mac/Linux: Open Terminal

---

## STEP 3 — GO TO THE PROJECT FOLDER

    cd "path/to/paddy procurement"

Example (Windows):
    cd "C:\Users\YourName\Downloads\paddy procurement"

Example (Mac/Linux):
    cd ~/Downloads/paddy\ procurement

---

## STEP 4 — CREATE A VIRTUAL ENVIRONMENT (do this only once)

    python -m venv venv

Activate it:
- Windows:    venv\Scripts\activate
- Mac/Linux:  source venv/bin/activate

You should see (venv) at the start of your terminal line.

---

## STEP 5 — INSTALL DEPENDENCIES (do this only once)

    pip install -r requirements.txt

This installs Django, ReportLab (for PDF), and the Anthropic AI SDK.

---

## STEP 6 — SET YOUR ANTHROPIC API KEY (for AI features)

Get your free API key from: https://console.anthropic.com/

### Windows (Command Prompt):
    set ANTHROPIC_API_KEY=sk-ant-your-key-here

### Mac/Linux:
    export ANTHROPIC_API_KEY=sk-ant-your-key-here

NOTE: Without the API key, the portal still works perfectly.
The AI features will show a helpful fallback message instead.

---

## STEP 7 — SET UP THE DATABASE (do this only once)

The project defaults to SQLite for local runs, so it works without MySQL installed.
If you want MySQL instead, set `DB_ENGINE=mysql` and the related `DB_*` environment variables.

    python manage.py migrate

---

## STEP 8 — CREATE TEST DATA (optional but recommended)

    python manage.py seed_data

This creates sample farmers, officers, admin, crops and bookings.

---

## STEP 9 — RUN THE SERVER

    python manage.py runserver

---

## STEP 10 — OPEN IN BROWSER

Open: http://127.0.0.1:8000

---

## TEST ACCOUNTS (after running seed_data)

| Role    | Username | Password   |
|---------|----------|------------|
| Farmer  | farmer1  | Test@12345 |
| Officer | officer1 | Test@12345 |
| Admin   | admin1   | Test@12345 |

---

## TESTING THE AI FEATURES

1. LOG IN as farmer1
   → Go to Farmer Dashboard
   → Click "Get AI Advice" to see MSP price advisory
   → The floating 🤖 button (bottom-right) opens the AI chatbot
   → Ask: "How do I book a slot?" or "What is MSP?"

2. LOG IN as officer1
   → Go to Approve Bookings
   → Click "🤖 Check Risk" on any booking
   → AI will analyze and show LOW/MEDIUM/HIGH risk with explanation

3. If a booking is REJECTED
   → Log in as farmer1
   → On dashboard, click "Why rejected?" next to any rejected booking
   → AI explains in simple language what to do next

---

## COMMON ERRORS AND FIXES

Problem: "ModuleNotFoundError: No module named 'django'"
Fix: Make sure virtual environment is activated and run: pip install -r requirements.txt

Problem: "Port already in use"
Fix: Run on a different port: python manage.py runserver 8080
Then open: http://127.0.0.1:8080

Problem: AI features not working
Fix: Check that ANTHROPIC_API_KEY is set correctly. The portal works without it too.

Problem: Database errors
Fix: Delete db.sqlite3 and run: python manage.py migrate

---

## PROJECT FOLDER STRUCTURE

    paddy procurement/
    ├── manage.py                  ← Run this to start the server
    ├── requirements.txt           ← All Python packages needed
    ├── db.sqlite3                 ← Database (auto-created)
    ├── e_paddy_portal/
    │   ├── settings.py            ← Main configuration
    │   └── urls.py
    ├── procurement/
    │   ├── models.py              ← Database tables
    │   ├── views.py               ← Page logic
    │   ├── ai_views.py            ← NEW: All AI features
    │   ├── urls.py                ← Updated: includes AI URLs
    │   └── forms.py
    ├── templates/
    │   ├── base.html              ← Updated: AI chatbot widget
    │   ├── farmer/
    │   │   └── dashboard.html     ← Updated: Price advisory + rejection explainer
    │   └── officer/
    │       └── approve_booking.html ← Updated: Fraud detection button
    └── static/
        └── css/custom.css

---

## TO STOP THE SERVER

Press Ctrl + C in the terminal.

---

## QUICK START (all commands in one place)

    cd "paddy procurement"
    python -m venv venv
    venv\Scripts\activate          (Windows) or source venv/bin/activate (Mac)
    pip install -r requirements.txt
    set ANTHROPIC_API_KEY=sk-ant-xxxx   (Windows) or export ANTHROPIC_API_KEY=sk-ant-xxxx (Mac)
    python manage.py migrate
    python manage.py seed_data
    python manage.py runserver

Then open: http://127.0.0.1:8000

═══════════════════════════════════════════════
FEATURE 8: DUAL CHANNEL BUYER MARKETPLACE
═══════════════════════════════════════════════

NEW TEST ACCOUNTS (after running seed_data):

| Role       | Username          | Password  | Company                   |
|------------|-------------------|-----------|---------------------------|
| Rice Mill  | sriram_ricemill   | buyer123  | Sri Ram Rice Mill         |
| Wholesaler | ap_wholesaler     | buyer123  | AP Agro Wholesale Pvt Ltd |
| Exporter   | export_india      | buyer123  | India Export Foods Ltd    |

HOW TO TEST DUAL CHANNEL FEATURE:

AS A FARMER:
1. Login as farmer1 → Dashboard
2. See the "⚖️ Dual Channel" banner
3. Click "🏪 Browse Private Buyers"
4. Compare Government MSP vs private offers side by side
5. Click any offer → see AI recommendation
6. Enter quantity → Submit deal request
7. Track deal in "My Deals"

AS A BUYER (e.g. sriram_ricemill / buyer123):
1. Login → Buyer Dashboard
2. See active offers and incoming deal requests
3. Click "View Deals" on any offer
4. Confirm or reject farmer deal requests
5. Mark deals as paid after delivery

AS AN ADMIN:
1. Login → Dashboard
2. Click "🏭 Manage Buyers" to approve/block buyers
3. Click "🏪 Marketplace Overview" for full stats

REGISTER A NEW BUYER:
1. Go to http://127.0.0.1:8000/buyer/register/
2. Fill in company details
3. Admin must approve before they can post offers

NEW URLS ADDED:
- /marketplace/              ← Farmer sees all offers
- /marketplace/offer/<id>/   ← Offer detail + AI advice
- /marketplace/my-deals/     ← Farmer's deal history
- /buyer/register/           ← New buyer registration
- /buyer/login/              ← Buyer login
- /buyer/dashboard/          ← Buyer management
- /buyer/create-offer/       ← Post new buying offer
- /admin-portal/buyers/      ← Admin: manage buyers
- /admin-portal/marketplace/ ← Admin: marketplace stats
