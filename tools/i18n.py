"""CropConnect translation tool.

Translations live in   locale/<code>/LC_MESSAGES/django.po   (open with Poedit or any text editor).
After editing translations, run from the project folder:

    python tools/i18n.py build

It does three things:
  1. Makes sure every language file contains every message (an empty translation
     means "show the English text").
  2. Compiles each .po file to .mo, which Django needs before it will accept a language.
  3. Writes static/i18n/<code>.js, the dictionary the browser uses to translate the
     text that the site shows on each page.

To add a language: add it to LANGUAGES in e_paddy_portal/settings.py, then run build.
"""
import ast
import json
import os
import sys

import polib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_DIR = os.path.join(ROOT, 'locale')
STATIC_I18N = os.path.join(ROOT, 'static', 'i18n')
SOURCE_LANG = 'en'


def configured_languages():
    """Read the LANGUAGES list from settings.py without importing Django."""
    path = os.path.join(ROOT, 'e_paddy_portal', 'settings.py')
    tree = ast.parse(open(path, encoding='utf-8').read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'LANGUAGES' for t in node.targets):
            return [elt.elts[0].value for elt in node.value.elts]
    raise SystemExit('LANGUAGES was not found in settings.py')


def po_path(code):
    return os.path.join(LOCALE_DIR, code, 'LC_MESSAGES', 'django.po')


def build():
    codes = [c for c in configured_languages() if c != SOURCE_LANG]

    # Collect every message key, keeping first-seen order (Telugu first, so its order is kept).
    master = []
    for code in codes:
        if os.path.exists(po_path(code)):
            for entry in polib.pofile(po_path(code)):
                if entry.msgid and entry.msgid not in master:
                    master.append(entry.msgid)

    os.makedirs(STATIC_I18N, exist_ok=True)
    for code in codes:
        path = po_path(code)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        po = polib.pofile(path) if os.path.exists(path) else polib.POFile()
        po.metadata = {
            'Project-Id-Version': 'CropConnect',
            'Language': code,
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=UTF-8',
            'Content-Transfer-Encoding': '8bit',
        }
        existing = {e.msgid for e in po}
        for key in master:
            if key not in existing:
                po.append(polib.POEntry(msgid=key, msgstr=''))
        po.save(path)
        po.save_as_mofile(path[:-3] + '.mo')

        translations = {e.msgid: e.msgstr for e in po if e.msgstr and not e.fuzzy}
        with open(os.path.join(STATIC_I18N, code + '.js'), 'w', encoding='utf-8') as f:
            f.write('window.CC_I18N = ' + json.dumps({'lang': code, 'dict': translations}, ensure_ascii=False) + ';\n')
        print(f'{code}: {len(translations)} of {len(master)} messages translated')

    with open(os.path.join(STATIC_I18N, SOURCE_LANG + '.js'), 'w', encoding='utf-8') as f:
        f.write('window.CC_I18N = {"lang": "en", "dict": {}};\n')
    print('en: English is the source text')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'build':
        build()
    else:
        print(__doc__)
