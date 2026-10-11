# E-Paddy & Groundnut Procurement Portal

A production-ready Django web application for government-style paddy and groundnut procurement at Minimum Support Price (MSP).

## Tech Stack

- **Backend:** Python Django 6.x
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **Database:** SQLite (default) / MySQL
- **Architecture:** Django MVT (Model-View-Template)

## Features

### Farmer Module
- Registration with Aadhaar, bank details, land survey number
- Crop selection (Paddy / Groundnut)
- Slot booking system
- View booking & payment status
- Download PDF invoice

### Officer Module
- Verify farmer land details
- Approve slot bookings
- Validate crop weight
- Approve procurement

### Admin Module
- Manage users
- Set MSP (Minimum Support Price)
- Procurement statistics & charts
- Approve payments

## Setup

### 1. Install Dependencies

```bash
pip install django mysqlclient reportlab python-dateutil
```

### 2. Run Migrations

```bash
python manage.py makemigrations procurement
python manage.py migrate
```

### 3. Create Superuser & Seed Data

```bash
python manage.py seed_data
```

This creates:
- Crops: Paddy (₹2183/qtl), Groundnut (₹5850/qtl)
- Slots for 14 days
- Sample users: `admin`/`admin123`, `officer1`/`officer123`
- Announcements

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

## Using MySQL

Set environment variables and run:

```bash
set USE_MYSQL=True
set DB_NAME=e_paddy_procurement
set DB_USER=root
set DB_PASSWORD=yourpassword
python manage.py migrate
```

## Default Login Credentials

| Role   | Username  | Password  |
|--------|-----------|-----------|
| Admin  | admin     | admin123  |
| Officer| officer1  | officer123|

Farmers must register via the portal.

## Project Structure

```
e_paddy_portal/          # Django project
procurement/             # Main app
  models.py              # User, Farmer, LandDetails, Crop, Slot, etc.
  views.py               # All views
  forms.py               # Registration, booking forms
  urls.py                # URL routing
  decorators.py          # Role-based access
  utils.py               # PDF invoice generation
templates/               # HTML templates
static/                  # CSS, JS
database/                # SQL schema reference
```

## Security

- Password hashing (Django default: PBKDF2)
- CSRF protection enabled
- SQL injection prevention (Django ORM)
- Session-based authentication
- Role-based access control

## License

Government of India - Ministry of Agriculture & Farmers Welfare
