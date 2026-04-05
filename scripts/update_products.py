#!/usr/bin/env python3
"""
update_products.py
==================
Llegeix admin_products.csv i genera/actualitza productsData.js.

  · Si productsData.js ja existeix, preserva les imatges (imgs) de cada
    producte i només sobreescriu els camps editables del CSV.
  · Si productsData.js NO existeix, el crea des de zero amb el CSV.

Camps editables al CSV:
  pvp · outlet · quantitat · venut · talles · talles_esgotades · categoria

Els camps nom, brand, tipus, ref mai es modifiquen des del CSV.
Les imatges (imgs) es gestionen amb update_photos.py.

Ús:
    python update_products.py
    python update_products.py --dry-run          # mostra canvis sense desar
    python update_products.py --csv altre.csv    # CSV alternatiu

⚠️  ATENCIÓ (Excel):
    Les refs numèriques com 07019 es converteixen a 7019 si el CSV
    s'obre i desa amb Excel. Per evitar-ho, formata la columna 'ref'
    com a Text abans d'editar.
"""

import csv
import json
import os
import re
import shutil
import argparse
from datetime import datetime

CSV_FILE = 'admin_products.csv'
JS_FILE  = 'productsData.js'


def parse_bool(val):
    return str(val).strip().lower() in ('true', '1', 'si', 'sí', 'yes')

def parse_list(val):
    val = str(val).strip()
    return [x.strip() for x in val.split('|') if x.strip()] if val else []

def parse_float(val):
    val = str(val).strip().replace(',', '.')
    try:
        return float(val) if val else None
    except ValueError:
        return None

def parse_int(val):
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None

def read_js(js_path):
    """Llegeix productsData.js i retorna la llista de productes (o [] si no existeix)."""
    if not os.path.exists(js_path):
        return []
    with open(js_path, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'const\s+productsData\s*=\s*(\[.*\])\s*;?', content, re.DOTALL)
    if not m:
        print(f'⚠️  No s\'he pogut llegir {js_path}. Es crearà des de zero.')
        return []
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


def main():
    parser = argparse.ArgumentParser(description='Actualitza productsData.js des del CSV.')
    parser.add_argument('--csv',     default=CSV_FILE, help='Ruta al CSV')
    parser.add_argument('--js',      default=JS_FILE,  help='Ruta al JS')
    parser.add_argument('--dry-run', action='store_true', help='Mostra canvis sense desar')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f'ERROR: No es troba {args.csv}')
        return

    # Carregar estat actual per preservar imgs
    existing = read_js(args.js)
    imgs_by_ref = {p['ref']: p.get('imgs', []) for p in existing}
    from_scratch = len(existing) == 0
    if from_scratch:
        print(f'ℹ️  {args.js} no existeix o està buit → es crearà des de zero.')
    else:
        print(f'📂 {len(existing)} productes carregats de {args.js}')

    print(f'📄 Llegint {args.csv} ...')
    products = []
    changes  = 0
    existing_by_ref = {p['ref']: p for p in existing}

    with open(args.csv, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row_num, row in enumerate(reader, start=2):

            ref = str(row.get('ref', '')).strip()
            if not ref:
                print(f'  ⚠️  Fila {row_num} sense ref, ignorada.')
                continue

            pvp       = parse_float(row.get('pvp', ''))
            outlet    = parse_float(row.get('outlet', ''))
            quantitat = parse_int(row.get('quantitat', ''))
            venut     = parse_bool(row.get('venut', 'false'))
            talles    = parse_list(row.get('talles', ''))
            esgotades = parse_list(row.get('talles_esgotades', ''))
            cat       = row.get('categoria', '').strip().upper()

            # Imatges: CSV té prioritat, sinó recupera les existents
            csv_imgs = parse_list(row.get('imgs', ''))
            imgs = csv_imgs if csv_imgs else imgs_by_ref.get(ref, [])

            p = {
                'nom':              row.get('nom', '').strip(),
                'brand':            row.get('brand', '').strip().upper(),
                'tipus':            row.get('tipus', '').strip().upper(),
                'ref':              ref,
                'categoria':        cat,
                'pvp':              pvp,
                'outlet':           outlet,
                'quantitat':        quantitat,
                'venut':            venut,
                'talles':           talles,
                'talles_esgotades': esgotades,
                'imgs':             imgs,
            }

            if not from_scratch and ref in existing_by_ref:
                old  = existing_by_ref[ref]
                diff = [k for k in p if p[k] != old.get(k)]
                if diff:
                    changes += 1
                    if args.dry_run:
                        print(f'  [DRY-RUN] {p["nom"]} ({ref}): {", ".join(diff)}')

            products.append(p)

    print(f'   {len(products)} productes llegits del CSV.')

    if from_scratch:
        changes = len(products)

    if args.dry_run:
        print(f'\n[DRY-RUN] {changes} producte(s) amb canvis. No s\'ha desat res.')
        return

    if changes > 0 or from_scratch:
        if os.path.exists(args.js):
            backup_js(args.js)
        write_js(products, args.js)
        label = 'creat' if from_scratch else 'actualitzat'
        print(f'✅ {args.js} {label} — {len(products)} productes ({changes} canvis).')
    else:
        print('  Cap canvi detectat. No s\'ha modificat res.')

    print('\nFet!')


if __name__ == '__main__':
    main()
