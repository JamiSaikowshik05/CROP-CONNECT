# CropConnect: Setup, Database, Languages and Deployment

This guide covers running CropConnect on your computer with MySQL, adding languages,
and putting the site online. Commands are shown for Windows (PowerShell) and Linux/macOS.

---

## 0. Check that this copy is complete

From the project folder, run:

```powershell
python manage.py check_setup
```

Every line should say `OK`. Any line marked `PROBLEM` says what to do. This is the quickest way to confirm
that the copy you are running has the latest changes (languages, password buttons, admin pages).

---

## 1. Run on your computer with MySQL

The project uses **MySQL 8** by default. SQLite is only used if you ask for it
(`DB_ENGINE=sqlite`), and only for quick tests.

### 1.1 Create the database (once)

Open the MySQL command line (MySQL 8.0 Command Line Client on Windows, or `mysql -u root -p`)
and run:

```sql
CREATE DATABASE cropconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cropconnect'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON cropconnect.* TO 'cropconnect'@'localhost';
FLUSH PRIVILEGES;
```

`utf8mb4` is required so Telugu, Hindi, Tamil and the other Indian scripts are stored correctly.

### 1.2 Start the project

PowerShell (Windows):

```powershell
cd path\to\paddy_final
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:DB_USER = "cropconnect"
$env:DB_PASSWORD = "choose-a-strong-password"
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Linux / macOS:

```bash
cd paddy_final
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DB_USER=cropconnect DB_PASSWORD='choose-a-strong-password'
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open http://127.0.0.1:8000

The database settings are read from these environment variables (defaults in brackets):
`DB_NAME` [cropconnect], `DB_USER` [root], `DB_PASSWORD` [empty], `DB_HOST` [127.0.0.1], `DB_PORT` [3306].

Demo accounts created by `seed_data`: admin / admin123, officer1 / officer123, sriram_ricemill / buyer123.
**Change or delete these before the site is public.**

### 1.3 Common problems

| Message | Cause and fix |
|---|---|
| `Access denied for user` | `DB_USER` or `DB_PASSWORD` is wrong. Check the values you set in this terminal. |
| `Can't connect to MySQL server` | The MySQL service is not running. Start "MySQL80" from Windows Services. |
| `Unknown database 'cropconnect'` | Run the `CREATE DATABASE` step from 1.1. |

---

## 2. Move existing SQLite data into MySQL

Only needed if you have a `db.sqlite3` with data you want to keep. Run these from the
project folder, while still using the old SQLite setup:

```powershell
$env:DB_ENGINE = "sqlite"
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.permission -e sessions -o data.json
```

Then switch back to MySQL and load the data:

```powershell
Remove-Item Env:DB_ENGINE
python manage.py migrate
python manage.py loaddata data.json
```

Check the counts afterwards (for example in the admin dashboard). This process was tested on
sample data: all 45 records loaded and the migrated schema matched the models.

---

## 3. Languages

The site uses standard gettext translation files. The English text is the source.

| Language | Status |
|---|---|
| English | Source language |
| Telugu (తెలుగు) | Complete: 823 of 823 messages |
| Hindi (हिन्दी) | Core pages: 163 of 823 messages (login, registration, home, menus, footer) |
| All other Indian languages | Shown in the language picker. Until translated, the page shows English. |

The picker lists all 22 scheduled Indian languages (plus English), each named in its own script.

### 3.1 Translate a language

1. Open `locale/<code>/LC_MESSAGES/django.po` (for example `locale/ta/LC_MESSAGES/django.po` for Tamil)
   with [Poedit](https://poedit.net), which is free and works on Windows.
2. For each entry, type the translation into the box under the English text. Leave
   empty entries alone and the page will show English for them.
3. Rebuild the translation files from the project folder:

   ```powershell
   python tools/i18n.py build
   ```

4. Reload the site and choose the language in the picker.

The build step writes `.mo` files (needed by Django) and `static/i18n/<code>.js` (used by the browser).
Commit both when you deploy.

### 3.2 Add a new language

1. Add the language to `LANGUAGES` in `e_paddy_portal/settings.py` (use the name written in its own script).
2. Run `python tools/i18n.py build`. This creates its `.po` file.
3. Translate it as in 3.1.

Some Indian languages need a Google font to display correctly. The font list is in `templates/base.html`
and `templates/login.html`; add the matching "Noto Sans <script>" family if you add a new script.

---

## 4. Deploy online (Render, step by step)

These steps assume a Render account and a MySQL 8 database that Render can reach.

### 4.1 Prepare the code

1. Put the project in a GitHub repository. Include `locale/`, `static/i18n/` and `tools/`.
   Do **not** include `.venv/`, `__pycache__/`, `staticfiles/` or `db.sqlite3`.
2. Create a MySQL 8 database with `utf8mb4` (see 1.1). Use a managed MySQL service or your
   hosting provider's MySQL, and note the host, port, database name, user and password.

### 4.2 Create the web service

1. Render: **New > Web Service** and connect the repository.
2. Settings:
   - **Runtime:** Python 3
   - **Build command:** `bash build.sh`
   - **Start command:** `gunicorn e_paddy_portal.wsgi:application`
3. **Environment variables** (Render: Environment tab):

   | Name | Value |
   |---|---|
   | `SECRET_KEY` | a long random string. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DEBUG` | `0` |
   | `DB_HOST` | your MySQL host |
   | `DB_PORT` | `3306` (or your provider's port) |
   | `DB_NAME` | `cropconnect` |
   | `DB_USER` | your MySQL user |
   | `DB_PASSWORD` | your MySQL password |
   | `DB_SSL_CA_PEM` | the CA certificate text (required by Aiven; see section 7) |

   Render normally sets `RENDER_EXTERNAL_HOSTNAME` for you, which allows the site's address. If you use your
   own domain, add it to `ALLOWED_HOSTS` (comma-separated) and to `CSRF_TRUSTED_ORIGINS`
   (for example `https://www.example.com`).

4. Deploy. The build step installs packages, collects static files and runs migrations.

### 4.3 First-time setup on the server

Open the service's **Shell** tab in Render and run:

```bash
python manage.py seed_data          # optional: demo data
```

Create your real administrator. Do not use `createsuperuser`: it does not set the role, and an account
without a role gets stuck in a redirect loop at the login page. Use this instead:

```bash
python manage.py shell -c "from procurement.models import User; User.objects.create_user(username='youradmin', password='a-strong-password', role='ADMIN')"
```

Then log in as that admin and delete or change the demo accounts from the Users page.

### 4.4 Before you go live

- `DEBUG` is `0` and `SECRET_KEY` is set. The app refuses to start otherwise, which is intended.
- Demo passwords are changed or the demo accounts are removed.
- The site is opened over HTTPS (Render provides this).
- MySQL backups are turned on with your database provider.

**Not tested here:** the Render deployment itself. The build, migrate, collectstatic and gunicorn
steps were all tested locally with `DEBUG=0`.

---

## 5. Troubleshooting

| Problem | What to do |
|---|---|
| "This page is having a problem" in Edge | Fixed in this version: the page tells the browser not to auto-translate it, which was the cause. If it still happens, open the site in a private window and clear the site's data. |
| `DisallowedHost` error | Add the address to `ALLOWED_HOSTS`. |
| `Set the SECRET_KEY environment variable...` | You set `DEBUG=0` without a secret key. Set `SECRET_KEY` (see 4.2). |
| Login page keeps redirecting | The account has no role. Set it in the shell as in 4.3. |
| A language shows English text | That language is not translated yet (see section 3). |

---

## 6. Update a site that is already live on Render (GitHub)

If your database is on Aiven, follow section 7 first, which lists every variable.

Render rebuilds the site every time new code is pushed to the GitHub branch it watches (normally `main`).

**Before you push** (otherwise the build fails):

1. In Render, open your web service, then **Environment**, and make sure these exist:
   `SECRET_KEY`, `DEBUG` = `0`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
   The database must be a MySQL 8 server that Render can reach (see 4.1).
2. Make sure the database is running and reachable from the internet, or from Render's network.

**Push the new version** (from a computer with Git installed; this assumes your repository is already cloned):

```bash
cd path/to/your-repository              # the folder that contains .git
# copy the contents of the new paddy_final folder over the repository, keeping the .git folder
git add -A                              # stages new, changed and deleted files
git status                              # check: db.sqlite3 and staticfiles/ must NOT appear
git commit -m "MySQL database, all Indian languages, password show/hide, admin pages"
git push origin main
```

If `db.sqlite3` was committed to GitHub earlier, remove it from Git (the file stays on your computer):

```bash
git rm --cached db.sqlite3
git commit -m "Stop tracking local database"
git push origin main
```

**Watch the deploy:** in Render, open the service's **Events** or **Logs** tab. A successful build ends with
`Migrations ... OK` and then "Your service is live". If Render does not start automatically, click
**Manual Deploy > Deploy latest commit**.

**After the deploy:** open **Shell** in Render and run:

```bash
python manage.py check_setup
```

Every line must say `OK`. If a line says `PROBLEM`, the message next to it says what to fix.

**Data note:** the old Render version stored its data in a local SQLite file on the server. That file is not
kept when Render rebuilds, so the new MySQL site starts empty. Run `python manage.py seed_data` in the Shell
for demo data, or ask for help moving real records (section 2 shows the export method).

---

## 7. Aiven (database) with Render (hosting): exact steps

Aiven MySQL accepts only encrypted connections. The site connects over TLS automatically, and you give it
Aiven's CA certificate so it can confirm it is talking to your own database server.

### 7.1 Prepare the database on Aiven

1. Open your MySQL service in the Aiven console. On its **Overview** page, note the **Host**, **Port**,
   **User** (usually `avnadmin`) and **Password**.
2. On the same page, find the **CA certificate** and download it (file `ca.pem`). Open it in Notepad and keep its text.
3. Create the database and an app user. From a computer with the MySQL client installed:

   ```bash
   mysql -h YOUR-HOST -P YOUR-PORT -u avnadmin -p --ssl-mode=REQUIRED --ssl-ca=ca.pem
   ```

   Then run:

   ```sql
   CREATE DATABASE cropconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'cropconnect'@'%' IDENTIFIED BY 'choose-a-strong-password';
   GRANT ALL PRIVILEGES ON cropconnect.* TO 'cropconnect'@'%';
   FLUSH PRIVILEGES;
   ```

4. Aiven **Settings > Allowed IP addresses**: Render's outbound addresses can change, so allow all addresses
   (`0.0.0.0/0`). The connection is still encrypted and protected by the password.

### 7.2 Set the Render environment variables

Render: your web service > **Environment** > add these:

| Name | Value |
|---|---|
| `SECRET_KEY` | a long random string (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DEBUG` | `0` |
| `DB_HOST` | Aiven **Host** |
| `DB_PORT` | Aiven **Port** (a number) |
| `DB_NAME` | `cropconnect` |
| `DB_USER` | `cropconnect` |
| `DB_PASSWORD` | the password from 7.1 |
| `DB_SSL_CA_PEM` | the full text of `ca.pem`, pasted as it is (line breaks are fine) |

Do **not** use `DATABASE_URL` for Aiven; the separate `DB_*` values above are the tested way.

### 7.3 Build and start commands

- **Build command:** `bash build.sh`   (installs packages, collects static files, creates the database tables)
- **Start command:** `gunicorn e_paddy_portal.wsgi:application`

Render's own address (`something.onrender.com`) is allowed automatically.

### 7.4 After the first deploy

1. Render logs should end with "Your service is live".
2. Open **Shell** and run `python manage.py check_setup`. You should see `Database connection OK` and
   `Encrypted connection: yes`.
3. Create your administrator (do not use `createsuperuser`):

   ```bash
   python manage.py shell -c "from procurement.models import User; User.objects.create_user(username='youradmin', password='a-strong-password', role='ADMIN')"
   ```

4. Optional demo data: `python manage.py seed_data` (change or delete the demo passwords afterwards).

### 7.5 If something fails

| Message you see | What to do |
|---|---|
| `Connections using insecure transport are prohibited` | Add `DB_SSL_CA_PEM` (7.2), then redeploy. |
| `certificate verify failed` | The CA text does not match this service. Download `ca.pem` again from the same Aiven service. |
| `Access denied for user` | Check `DB_USER` and `DB_PASSWORD`, and that the user has rights on `cropconnect` (7.1). |
| `Unknown database 'cropconnect'` | Create it (7.1). |
| `Can't connect to MySQL server` or a timeout | Check `DB_HOST`, `DB_PORT`, and Aiven's allowed IP addresses (7.1, step 4). |
| The build stops at `migrate` | Fix the variables above, then **Manual Deploy > Deploy latest commit**. |

**Tested here:** the encrypted connection, the certificate options and the full migrations, using a MySQL 8
server set to refuse unencrypted connections, the same rule Aiven applies. **Not tested here:** Aiven and
Render themselves, because this environment cannot reach them.
