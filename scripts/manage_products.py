#!/usr/bin/env python3
"""
manage_products.py — Robeta product catalog management

Usage:
  python3 scripts/manage_products.py --preview-update-price <ref> <new_price>
  python3 scripts/manage_products.py --apply-update-price <ref> <new_price>
  python3 scripts/manage_products.py --preview-mark-sold <ref> [size]
  python3 scripts/manage_products.py --apply-mark-sold <ref> [size]

Run from the project root: /Users/clawbernal/Projects/robeta
"""

import csv
import json
import sys
import copy
from pathlib import Path

# Always resolve relative to this script's location (scripts/)
PROJECT_DIR = Path(__file__).parent.parent
CSV_FILE = PROJECT_DIR / "admin_products.csv"

FIELDNAMES = ['nom', 'brand', 'tipus', 'ref', 'categoria', 'pvp', 'outlet',
              'quantitat', 'venut', 'talles', 'talles_esgotades']


def load_csv():
    products = []
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            row['pvp'] = float(row['pvp'])
            row['outlet'] = float(row['outlet'])
            row['quantitat'] = int(row['quantitat'])
            row['venut'] = row['venut'].strip().lower() == 'true'
            row['talles'] = [t for t in row['talles'].split('|') if t] if row['talles'] else []
            raw_esgotades = row.get('talles_esgotades', '') or ''
            row['talles_esgotades'] = [t for t in raw_esgotades.split('|') if t]
            products.append(row)
    return products


def save_csv(products):
    with open(CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter=';')
        writer.writeheader()
        for product in products:
            row = product.copy()
            row['venut'] = str(row['venut']).lower()
            row['talles'] = '|'.join(row['talles'])
            row['talles_esgotades'] = '|'.join(row['talles_esgotades'])
            writer.writerow(row)


def find_product(products, ref):
    for p in products:
        if p['ref'] == ref:
            return p
    return None


def update_price(products, ref, new_price):
    """Update outlet price for a product. Never touches pvp."""
    product = find_product(products, ref)
    if not product:
        print(f"❌ Product with ref '{ref}' not found.")
        return None, None
    before = copy.deepcopy(product)
    product['outlet'] = float(new_price)
    after = copy.deepcopy(product)
    return before, after


def mark_sold(products, ref, size=None):
    """
    Mark a size as sold. If all sizes are exhausted, set venut=true.
    If no sizes defined, mark whole product as sold.
    """
    product = find_product(products, ref)
    if not product:
        print(f"❌ Product with ref '{ref}' not found.")
        return None, None
    before = copy.deepcopy(product)

    if size:
        if size not in product['talles']:
            print(f"⚠️  Size '{size}' is not in talles for ref '{ref}'. Available: {product['talles']}")
            print("   Proceeding anyway and adding to talles_esgotades.")
        if size not in product['talles_esgotades']:
            product['talles_esgotades'].append(size)
        # Auto-mark as sold if all sizes exhausted
        if product['talles'] and set(product['talles']) <= set(product['talles_esgotades']):
            product['venut'] = True
            print(f"ℹ️  All sizes exhausted → venut set to true for ref '{ref}'")
    else:
        # No size → mark whole product sold
        product['venut'] = True

    after = copy.deepcopy(product)
    return before, after


def print_diff(before, after):
    print("\n─── BEFORE ───────────────────────────────")
    print(json.dumps(before, indent=2, ensure_ascii=False))
    print("\n─── AFTER ────────────────────────────────")
    print(json.dumps(after, indent=2, ensure_ascii=False))
    print("──────────────────────────────────────────\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    products = load_csv()
    apply_change = 'apply' in action

    if 'update-price' in action:
        if len(sys.argv) != 4:
            print("Usage: --preview/apply-update-price <ref> <new_price>")
            sys.exit(1)
        ref = sys.argv[2]
        new_price = sys.argv[3]
        before, after = update_price(products, ref, new_price)

    elif 'mark-sold' in action:
        if len(sys.argv) < 3 or len(sys.argv) > 4:
            print("Usage: --preview/apply-mark-sold <ref> [size]")
            sys.exit(1)
        ref = sys.argv[2]
        size = sys.argv[3] if len(sys.argv) == 4 else None
        before, after = mark_sold(products, ref, size)

    else:
        print(f"Unknown action: {action}")
        print(__doc__)
        sys.exit(1)

    if before is None:
        sys.exit(1)

    if not apply_change:
        print("📋 Preview (no changes saved):")
        print_diff(before, after)
        print("Run with --apply-... to save changes.")
    else:
        print_diff(before, after)
        save_csv(products)
        print(f"✅ Changes saved to {CSV_FILE}")


if __name__ == "__main__":
    main()
