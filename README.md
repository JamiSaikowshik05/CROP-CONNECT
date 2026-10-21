# CropConnect Paddy and Groundnut Procurement Portal

A Django portal for farmer registration, crop procurement at Minimum Support Price (MSP), officer verification, payments, and a private buyer marketplace. It also includes AI and machine learning features; the AI assistant uses an Anthropic API key when configured, while the portal can run without one.

The interface supports English and Telugu. Use the navigation bar language selector; your choice is remembered as you move between pages and return to the portal.

## Requirements

- Python 3.10 or newer
- Windows PowerShell, Command Prompt, or a terminal

SQLite is used by default, so a separate database server is not required.

## Run on Windows

From this folder (`paddy_final`):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Stop the server with Ctrl+C.

For AI assistant responses, set `ANTHROPIC_API_KEY` in the terminal before starting the server. The rest of the portal works without it.

## Seeded accounts

Running `seed_data` creates these accounts if they do not already exist:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Officer | `officer1` | `officer123` |
| Buyer | `sriram_ricemill`, `ap_wholesaler`, `export_india` | `buyer123` |

Farmers register through the portal. The seed command also creates crops, procurement slots, announcements, and buyer offers.

## Optional MySQL

SQLite is the default. To use MySQL instead, create a database, set `USE_MYSQL=True` and the `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` environment variables, then run migrations. For example, in PowerShell:

```powershell
$env:USE_MYSQL = "True"
$env:DB_NAME = "cropconnect"
$env:DB_USER = "root"
$env:DB_PASSWORD = "JAMISAI"
python manage.py migrate
```

## Project layout

- `e_paddy_portal/` — Django settings and URL configuration
- `procurement/` — models, views, migrations, and management commands
- `templates/` and `static/` — website pages and assets
- `ml_models/` and `ml_data/` — machine learning models and datasets
- `DEPLOY.md` — setup, database, languages and deployment

## Database, languages and deployment

- Start here: `DEPLOY.md`. Check your copy with `python manage.py check_setup`.
- The database is **MySQL 8** by default. See `DEPLOY.md` for setup, moving existing data, and deployment.
- The site supports English and all 22 scheduled Indian languages. Translations live in `locale/`; rebuild with
  `python tools/i18n.py build`. See `DEPLOY.md` section 3.
