"""Creates the CropConnect database and its application user on a MySQL server (for example Aiven).

Run it once from your computer, in the project folder. Example (PowerShell):

    $env:ADMIN_USER = "avnadmin"
    $env:ADMIN_PASSWORD = "the password from your Aiven service"
    $env:DB_HOST = "your-host.aivencloud.com"
    $env:DB_PORT = "12345"
    $env:DB_SSL_CA = "C:\\Users\\you\\Downloads\\ca.pem"
    $env:DB_NAME = "cropconnect"
    $env:DB_USER = "cropconnect"
    $env:DB_PASSWORD = "choose-a-strong-password"
    python tools/create_db.py

It is safe to run again: it creates only what is missing, and updates the app user's password.
"""
import os
import sys

import pymysql


def value(name, default=None):
    v = os.environ.get(name, default)
    if v in (None, ''):
        sys.exit(f'Missing environment variable {name}. See the instructions at the top of tools/create_db.py.')
    return v


def main():
    host = value('DB_HOST')
    port = int(value('DB_PORT', '3306'))
    admin_user = value('ADMIN_USER')
    admin_password = value('ADMIN_PASSWORD')
    db_name = value('DB_NAME', 'cropconnect')
    app_user = value('DB_USER')
    app_password = value('DB_PASSWORD')
    ca_file = os.environ.get('DB_SSL_CA', '')

    options = dict(host=host, port=port, user=admin_user, password=admin_password,
                   charset='utf8mb4', connect_timeout=20)
    if ca_file:
        options['ssl_ca'] = ca_file
    else:
        options['ssl_disabled'] = False      # hosted databases require an encrypted connection

    print(f'Connecting to {host}:{port} as {admin_user} ...')
    connection = pymysql.connect(**options)
    try:
        with connection.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f'Database "{db_name}" is ready (utf8mb4).')
            cur.execute("CREATE USER IF NOT EXISTS %s@'%%' IDENTIFIED BY %s", (app_user, app_password))
            cur.execute("ALTER USER %s@'%%' IDENTIFIED BY %s", (app_user, app_password))
            cur.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO %s@'%%'", (app_user,))
            cur.execute("FLUSH PRIVILEGES")
            print(f'User "{app_user}" can now use "{db_name}".')
        connection.commit()
    finally:
        connection.close()
    print('Done. Next: put the same DB_* values into Render (see GITHUB_RENDER_AIVEN_GUIDE.md).')


if __name__ == '__main__':
    main()
