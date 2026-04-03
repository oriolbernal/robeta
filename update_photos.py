#!/usr/bin/env python3
"""
update_photos.py
-------------------
Recorre la carpeta FOTOS\ i actualitza les imatges de cada producte
dins del fitxer index.html.

Estructura esperada de carpetes:
    FOTOS/
        TINY COTTONS/
            186E56/
                blalal.jpg
                blabla2.jpg
        LOUISE MISHA/
            S0242/
                foto1.jpg

Ús:
    python update_photos.py

    # O si el HTML o la carpeta FOTOS estan en una altra ruta:
    python update_photos.py --html ruta/al/index.html --fotos ruta/a/FOTOS
"""

import os
import re
import json
import argparse

# Extensions d'imatge acceptades
IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

def normalitza(text):
    """Normalitza un nom per comparar (minúscules, sense espais extra)."""
    return text.strip().lower()

def recull_fotos(fotos_dir):
    """
    Retorna un diccionari:
        { "ref_normalitzada": ["FOTOS/MARCA/REF/img1.jpg", ...] }

    Recorre FOTOS/ → MARCA/ → REF/ → fitxers
    """
    fotos = {}
    fotos_dir = os.path.normpath(fotos_dir)

    if not os.path.isdir(fotos_dir):
        print(f"⚠️  No s'ha trobat la carpeta: {fotos_dir}")
        return fotos

    for marca in sorted(os.listdir(fotos_dir)):
        marca_path = os.path.join(fotos_dir, marca)
        if not os.path.isdir(marca_path):
            continue

        for ref in sorted(os.listdir(marca_path)):
            ref_path = os.path.join(marca_path, ref)
            if not os.path.isdir(ref_path):
                continue

            imgs = []
            for fitxer in sorted(os.listdir(ref_path)):
                ext = os.path.splitext(fitxer)[1].lower()
                if ext in IMG_EXTENSIONS:
                    # Ruta relativa amb barres normals (compatible amb navegadors)
                    ruta = f"FOTOS/{marca}/{ref}/{fitxer}"
                    imgs.append(ruta)

            if imgs:
                clau = normalitza(ref)
                fotos[clau] = imgs
                print(f"  ✓ {marca}/{ref}: {len(imgs)} imatge(s)")

    return fotos

def actualitza_html(html_path, fotos):
    """
    Llegeix el HTML, troba el bloc productsData i actualitza
    el camp 'imgs' de cada producte segons la referència.
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        contingut = f.read()

    # Troba el bloc JSON de productsData
    patro = r'(const productsData = )(\[.*?\])(;)'
    match = re.search(patro, contingut, re.DOTALL)
    if not match:
        print("❌ No s'ha trobat 'const productsData' al fitxer HTML.")
        return False

    try:
        productes = json.loads(match.group(2))
    except json.JSONDecodeError as e:
        print(f"❌ Error llegint el JSON: {e}")
        return False

    actualitzats = 0
    sense_fotos = 0

    for p in productes:
        ref_clau = normalitza(p.get('ref', ''))
        if ref_clau in fotos:
            p['imgs'] = fotos[ref_clau]
            actualitzats += 1
        else:
            # Manté les imatges que ja tenia (no les esborra)
            if not p.get('imgs'):
                p['imgs'] = []
            sense_fotos += 1

    nou_json = json.dumps(productes, ensure_ascii=False, separators=(',', ':'))
    nou_contingut = contingut[:match.start(2)] + nou_json + contingut[match.end(2):]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(nou_contingut)

    print(f"\n✅ {actualitzats} producte(s) actualitzats amb fotos.")
    print(f"   {sense_fotos} producte(s) sense carpeta de fotos (imgs buida o mantinguda).")
    return True


def main():
    parser = argparse.ArgumentParser(description='Actualitza les fotos del book de productes.')
    parser.add_argument('--html',  default='index.html', help='Ruta al fitxer HTML')
    parser.add_argument('--fotos', default='FOTOS',               help='Ruta a la carpeta FOTOS')
    args = parser.parse_args()

    print(f"📂 Llegint fotos de: {os.path.abspath(args.fotos)}")
    fotos = recull_fotos(args.fotos)

    if not fotos:
        print("⚠️  No s'han trobat imatges. Comprova l'estructura de carpetes.")
        return

    print(f"\n📝 Actualitzant: {os.path.abspath(args.html)}")
    ok = actualitza_html(args.html, fotos)

    if ok:
        print("\n🎉 Fet! Obre el HTML al navegador per veure els canvis.")

if __name__ == '__main__':
    main()