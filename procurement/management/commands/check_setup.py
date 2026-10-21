"""Shows whether this copy of CropConnect is set up correctly.

Run:  python manage.py check_setup
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = 'Checks the database, languages, translation files and pages in this copy of CropConnect.'

    def line(self, label, ok, detail=''):
        status = 'OK     ' if ok else 'PROBLEM'
        self.stdout.write(f'  [{status}] {label}' + (f' - {detail}' if detail else ''))
        return ok

    def handle(self, *args, **options):
        base = settings.BASE_DIR
        self.stdout.write('CropConnect setup check')
        self.stdout.write('-' * 60)
        results = []

        db = settings.DATABASES['default']
        engine = db['ENGINE'].rsplit('.', 1)[-1]
        self.stdout.write(f'  Database: {engine}, name "{db.get("NAME")}", host "{db.get("HOST", "-")}"')
        connected = False
        try:
            connection.ensure_connection()
            connected = True
            results.append(self.line('Database connection', True))
        except Exception as exc:
            first = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
            results.append(self.line('Database connection', False, first))
            if 'insecure transport' in str(exc) or 'SSL' in str(exc):
                self.stdout.write('           -> the server requires an encrypted connection. Set DB_SSL_CA_PEM '
                                  '(or DB_SSL_CA) to the CA certificate from your database service.')
            elif 'Access denied' in str(exc):
                self.stdout.write('           -> check DB_USER and DB_PASSWORD.')
            elif "Can't connect" in str(exc):
                self.stdout.write('           -> check DB_HOST and DB_PORT, and that the database accepts connections '
                                  'from this server (allowed IP addresses).')

        if connected:
            if connection.vendor == 'mysql':
                with connection.cursor() as cur:
                    cur.execute("SELECT @@character_set_database")
                    charset = cur.fetchone()[0]
                    cur.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
                    cipher = (cur.fetchone() or ['', ''])[1]
                results.append(self.line('Database character set is utf8mb4', charset == 'utf8mb4', charset))
                self.stdout.write(f'  [INFO   ] Encrypted connection: {"yes" if cipher else "no"}')
            executor = MigrationExecutor(connection)
            pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
            results.append(self.line('Database migrations are up to date', not pending,
                                     f'{len(pending)} waiting' if pending else ''))
        else:
            self.stdout.write('  (database checks skipped until the connection works)')

        langs = [code for code, _ in settings.LANGUAGES]
        results.append(self.line('Languages in the picker', len(langs) >= 23, f'{len(langs)} languages'))
        missing = []
        for code in langs:
            if code == 'en':
                continue
            mo = os.path.join(base, 'locale', code, 'LC_MESSAGES', 'django.mo')
            js = os.path.join(base, 'static', 'i18n', f'{code}.js')
            if not (os.path.exists(mo) and os.path.exists(js)):
                missing.append(code)
        results.append(self.line('Translation files for every language', not missing,
                                 f'missing: {", ".join(missing)} (run: python tools/i18n.py build)' if missing else ''))

        results.append(self.line('Password show/hide script present',
                                 os.path.exists(os.path.join(base, 'static', 'js', 'password-toggle.js'))))
        dash = os.path.join(base, 'templates', 'admin', 'dashboard.html')
        new_dash = os.path.exists(dash) and 'Needs your action' in open(dash, encoding='utf-8').read()
        results.append(self.line('Admin dashboard is the current version', new_dash))
        results.append(self.line('Machine-learning models present',
                                 os.path.exists(os.path.join(base, 'ml_models', 'yield_model.pkl'))))
        results.append(self.line('Debug mode', True, 'ON (development)' if settings.DEBUG else 'OFF (production)'))

        self.stdout.write('-' * 60)
        if all(results):
            self.stdout.write('Everything needed is in place.')
        else:
            self.stdout.write('Some items need attention. Lines marked PROBLEM say what to do.')
