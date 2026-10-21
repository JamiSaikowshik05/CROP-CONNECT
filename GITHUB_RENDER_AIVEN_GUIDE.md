# CropConnect: from zero to a live website

You will end with:
- your code on **GitHub**,
- the database on **Aiven** (MySQL),
- the website on **Render**, which updates itself every time you push new code to GitHub.

You need: a Windows PC with internet access, an email address, and the project folder
(unzip `paddy_final_latest.zip`; you get a folder called `paddy_final`).

---

## Part 1: Install Git (once)

1. Go to **git-scm.com/download/win**, download and run the installer. Keep the default options.
2. Open **PowerShell** (Start menu > type "PowerShell" > Enter).
3. Check it works:

   ```powershell
   git --version
   ```

   You should see something like `git version 2.4x.x`.

If `python` is not found later in Part 5, install Python from **python.org** and tick
**"Add python.exe to PATH"** in the first installer screen.

---

## Part 2: Create a GitHub account and an empty repository

1. Go to **github.com**, click **Sign up**, and verify your email.
2. Click the **+** at the top right, then **New repository**.
3. Repository name: `cropconnect`. Choose **Private**.
4. Leave "Add a README", ".gitignore" and "license" **unticked**. The repository must start empty.
5. Click **Create repository**. Keep this page open. It shows an address like
   `https://github.com/YOUR-USERNAME/cropconnect.git`.

---

## Part 3: Create a GitHub access token (needed to upload code)

GitHub does not accept your normal password when you upload code from PowerShell. You create a token instead.

1. Click your profile picture (top right) > **Settings**.
2. Scroll down the left menu to **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
3. Click **Generate new token (classic)**.
4. Note: `cropconnect laptop`. Expiration: 90 days. Tick the box **repo**.
5. Click **Generate token**, then **copy the token now** (it starts with `ghp_`). GitHub shows it only once.
   Save it in a safe place, for example a password manager.

---

## Part 4: Upload the project to GitHub

In PowerShell, go into the folder that contains `manage.py` (the `paddy_final` folder):

```powershell
cd C:\Users\YOUR-NAME\Downloads\paddy_final
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git init -b main
git add .
git status
```

Read the list that `git status` prints. It **must not** contain `db.sqlite3`, `.venv`,
`staticfiles`, or `__pycache__`. It **should** contain `manage.py`, `build.sh`, `requirements.txt`,
`templates`, `static`, `locale`, `procurement`, `ml_models`.

Then upload:

```powershell
git commit -m "CropConnect first version"
git remote add origin https://github.com/YOUR-USERNAME/cropconnect.git
git push -u origin main
```

When PowerShell asks for a **username**, type your GitHub username. When it asks for a **password**,
paste the token from Part 3 (nothing appears while you paste; that is normal).

Refresh your GitHub page. You should see `manage.py`, `templates`, and so on **at the top level**.
If you see a single folder called `paddy_final` instead, tell me; the fix takes two minutes.

---

## Part 5: Create the database on Aiven

1. Go to **aiven.io**, sign up or log in at **console.aiven.io**.
2. Click **Create service**, choose **MySQL**.
3. Choose a cloud region (the closer to India, the better) and a plan, give the service a name
   such as `cropconnect-mysql`, then click **Create service**.
4. Wait until its status shows **Running** (a few minutes).
5. Open the service and find **Connection information** on the **Overview** page. Write down:
   - **Host**, for example `mysql-xxxx-yourname.aivencloud.com`
   - **Port**, a number such as `12345`
   - **User**: `avnadmin`
   - **Password**: click the eye icon to show it, then copy it.
6. On the same page, download the **CA certificate** (a file called `ca.pem`). Keep it in your
   Downloads folder. Do **not** upload it to GitHub.
7. Allow Render to connect. In the service's settings, find **Allowed IP addresses** (Aiven sometimes
   calls it the IP filter). Allow all addresses, `0.0.0.0/0`. Render's outgoing addresses can change, so
   a fixed list would break. The encrypted connection and the password still protect the database.
8. Create the CropConnect database and its user. In PowerShell, inside the `paddy_final` folder,
   replace the four values in capitals and run:

   ```powershell
   $env:ADMIN_USER = "avnadmin"
   $env:ADMIN_PASSWORD = "PASTE-THE-AIVEN-PASSWORD"
   $env:DB_HOST = "PASTE-THE-HOST"
   $env:DB_PORT = "PASTE-THE-PORT"
   $env:DB_SSL_CA = "C:\Users\YOUR-NAME\Downloads\ca.pem"
   $env:DB_NAME = "cropconnect"
   $env:DB_USER = "cropconnect"
   $env:DB_PASSWORD = "CHOOSE-A-STRONG-PASSWORD"
   python -m pip install pymysql cryptography
   python tools/create_db.py
   ```

   You should see `Database "cropconnect" is ready (utf8mb4).` and `User "cropconnect" can now use "cropconnect".`
   Safe to run again. **Write down the `DB_PASSWORD` you chose**; Render needs it.

---

## Part 6: Put the website on Render

1. Go to **render.com**, click **Get Started**, and choose **Sign in with GitHub**. This lets Render read
   your repository.
2. On the Render dashboard, click **New +** > **Web Service**.
3. If `cropconnect` does not appear in the list, click **Configure account** and allow Render to access the
   `cropconnect` repository. Then choose `cropconnect` and click **Connect**.
4. Fill in the form:
   - **Name:** `cropconnect` (your site will be `cropconnect.onrender.com`, or similar)
   - **Region:** the same as your Aiven region, if available
   - **Branch:** `main`
   - **Root Directory:** leave empty
   - **Runtime:** `Python 3`
   - **Build Command:** `bash build.sh`
   - **Start Command:** `gunicorn e_paddy_portal.wsgi:application`
   - **Instance Type:** Free, or a paid plan. The free plan sleeps when nobody visits, so the first visit can take a minute.
5. Open **Environment Variables** (or **Advanced**) and add these. Use **Add Environment Variable** for each one:

   | Key | Value |
   |---|---|
   | `PYTHON_VERSION` | `3.12.8` |
   | `SECRET_KEY` | a long random text. Create one in PowerShell with: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DEBUG` | `0` |
   | `DB_HOST` | the Aiven host from Part 5 |
   | `DB_PORT` | the Aiven port from Part 5 |
   | `DB_NAME` | `cropconnect` |
   | `DB_USER` | `cropconnect` |
   | `DB_PASSWORD` | the password you chose in Part 5 |
   | `DB_SSL_CA_PEM` | the **whole text** of `ca.pem`: open it in Notepad, press Ctrl+A, Ctrl+C, then paste here |

6. Click **Create Web Service**. Render now downloads the code and runs `build.sh`. The first build takes
   about 5 to 10 minutes. Watch the **Logs** tab.
7. When the logs end with **Your service is live**, click the address at the top of the page. The website opens.

**If the build turns red**, read the last red line in the logs:

| Message in the logs | What it means and what to do |
|---|---|
| `Set the SECRET_KEY environment variable` | Add `SECRET_KEY` (step 5), then **Manual Deploy > Deploy latest commit**. |
| `Connections using insecure transport are prohibited` | `DB_SSL_CA_PEM` is missing or empty. |
| `certificate verify failed` | The text in `DB_SSL_CA_PEM` is not the current `ca.pem`. Download it again from Aiven and replace the value. |
| `Access denied for user` | `DB_USER` or `DB_PASSWORD` differs from what you gave `tools/create_db.py`. Run Part 5 step 8 again with the same values. |
| `Can't connect to MySQL server` or a timeout | Check `DB_HOST`, `DB_PORT`, and Aiven's Allowed IP addresses (Part 5, step 7). |
| A package fails to install | Check `PYTHON_VERSION` is `3.12.8`, then redeploy. |

---

## Part 7: Create your administrator account (once)

1. In Render, open your service, then the **Shell** tab.
2. Type these two commands, pressing Enter after each:

   ```bash
   python manage.py check_setup
   python manage.py shell -c "from procurement.models import User; User.objects.create_user(username='youradmin', password='a-strong-password', role='ADMIN')"
   ```

   `check_setup` should end with **Everything needed is in place**, and it should say
   **Encrypted connection: yes**. Choose your own admin username and a strong password.
   Do not use `createsuperuser`: accounts made that way have no role and cannot log in.
3. Optional demo accounts: `python manage.py seed_data`. Change or delete the demo passwords afterwards
   (admin, officer1, sriram_ricemill).
4. Open the website, choose a language in the navigation bar, and log in as your admin.

The website starts with an empty database. Farmers and buyers register themselves.

---

## Part 8: Updating the website later

1. Change the files on your PC (or replace them with a newer copy of `paddy_final`).
2. In PowerShell, inside `paddy_final`:

   ```powershell
   git add .
   git commit -m "what you changed"
   git push
   ```

3. Render rebuilds and redeploys automatically. Follow it in the **Events** or **Logs** tab.
4. If Render does not start, click **Manual Deploy > Deploy latest commit**.

Passwords and keys never go into the code. They stay in Render's Environment tab and in your password manager.

---

## Part 9: Problems you may meet

| Problem | Fix |
|---|---|
| `git push` keeps asking for a password | Use the token from Part 3 as the password. Your normal GitHub password does not work here. |
| `git push` says `rejected` or `fetch first` | Run `git pull --rebase origin main`, then `git push` again. |
| Edge shows "Translate page?" | The website now declares itself as English and asks browsers not to translate it. If the offer still appears, open Edge **Settings > Languages** and turn off **Offer to translate pages that aren't in a language you read**. |
| The site is slow on the first visit | The free Render plan wakes up after a period without visitors. Wait about a minute and refresh. |
| You want to see the logs | Render dashboard > your service > **Logs**. |

---

## Part 10: Keep your secrets safe

- Passwords belong only in Render's Environment tab, the Aiven console, and your password manager.
- Never upload `ca.pem`, `.env` files, or database files to GitHub. The `.gitignore` file blocks the usual ones.
- If a password is exposed, change it in Aiven (user settings) and in Render (Environment tab), then deploy again.
