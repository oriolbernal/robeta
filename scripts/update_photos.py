#!/usr/bin/env python3
"""
update_photos.py
================
Escaneja la carpeta FOTOS/ i actualitza les imatges de cada producte
dins de productsData.js.

Estructura esperada:
    FOTOS/
        LOUISE MISHA/
            S0242/
                IMG_8442.JPEG
        TINY COTTONS/
            186E56/
                foto.jpg

Ús:
    python update_photos.py
    python update_photos.py --dry-run       # mostra canvis sense desar
    python update_photos.py --fotos altra/ruta
"""

import os
import json
import re
import shutil
import argparse
from datetime import datetime

FOTOS_DIR = 'FOTOS'
JS_FILE   = 'productsData.js'

IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


def read_js(js_path):
    if not os.path.exists(js_path):
        print(f'ERROR: No es troba {js_path}. Executa primer update_products.py.')
        return None
    with open(js_path, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'const\s+productsData\s*=\s*(\[.*\])\s*;?', content, re.DOTALL)
    if not m:
        print(f'ERROR: Format inesperat a {js_path}.')
        return None
    return json.loads(m.group(1))

def write_js(products, js_path):
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write('const productsData = ')
        json.dump(products, f, ensure_ascii=False)
        f.write(';\n')

def backup_js(js_path):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = js_path.replace('.js', f'_backup_{ts}.js')
    shutil.copy(js_path, backup)
    print(f'  Backup: {backup}')

def scan_fotos(fotos_dir):
    """Retorna { 'ref_lower': ['FOTOS/MARCA/REF/img.jpg', ...] }"""
    result = {}
    fotos_dir = os.path.normpath(fotos_dir)
    if not os.path.isdir(fotos_dir):
        print(f'⚠️  No s\'ha trobat la carpeta: {fotos_dir}')
        return result

    for marca in sorted(os.listdir(fotos_dir)):
        marca_path = os.path.join(fotos_dir, marca)
        if not os.path.isdir(marca_path):
            continue
        for ref in sorted(os.listdir(marca_path)):
            ref_path = os.path.join(marca_path, ref)
            if not os.path.isdir(ref_path):
                continue
            imgs = [
                f'FOTOS/{marca}/{ref}/{f}'
                for f in sorted(os.listdir(ref_path))
                if os.path.splitext(f)[1].lower() in IMG_EXTENSIONS
            ]
            if imgs:
                result[ref.lower()] = imgs

    return result


def main():
    parser = argparse.ArgumentParser(description='Actualitza les fotos a productsData.js.')
    parser.add_argument('--fotos',   default=FOTOS_DIR, help='Carpeta FOTOS')
    parser.add_argument('--js',      default=JS_FILE,   help='Fitxer productsData.js')
    parser.add_argument('--dry-run', action='store_true', help='Mostra canvis sense desar')
    args = parser.parse_args()

    products = read_js(args.js)
    if products is None:
        return

    print(f'📂 Escanejant {os.path.abspath(args.fotos)} ...')
    fotos = scan_fotos(args.fotos)
    print(f'   {len(fotos)} carpetes de fotos trobades.')

    changes = 0
    for p in products:
        ref_key = p['ref'].lower()
        if ref_key in fotos:
            noves = fotos[ref_key]
            if noves != p.get('imgs', []):
                if args.dry_run:
                    print(f'  [DRY-RUN] {p["nom"]} ({p["ref"]}): {len(noves)} fotos')
                else:
                    p['imgs'] = noves
                changes += 1

    print(f'\n  {changes} producte(s) amb fotos actualitzades.')
    no_fotos = [p['ref'] for p in products if not p.get('imgs')]
    if no_fotos:
        print(f'  {len(no_fotos)} producte(s) sense fotos: {", ".join(no_fotos)}')

    if args.dry_run:
        print('[DRY-RUN] No s\'ha desat res.')
        return

    if changes > 0:
        backup_js(args.js)
        write_js(products, args.js)
        print(f'✅ {args.js} actualitzat.')
    else:
        print('  Cap canvi. No s\'ha modificat res.')

    print('\nFet!')


if __name__ == '__main__':
    main()
