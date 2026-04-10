#!/usr/bin/env python3
"""
optimize_photos.py
==================
Comprimeix i redimensiona totes les imatges de FOTOS/
convertint-les a WebP per reduir el pes de la web.

Ús:
    python optimize_photos.py
    python optimize_photos.py --dry-run       # mostra què faria sense fer res
    python optimize_photos.py --quality 75    # qualitat WebP (defecte: 82)
    python optimize_photos.py --max-width 1200  # amplada màxima en px (defecte: 1400)

Requisits:
    pip install Pillow
"""

import os
import argparse
from pathlib import Path
from PIL import Image

FOTOS_DIR = 'FOTOS'
IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
DEFAULT_QUALITY = 82
DEFAULT_MAX_WIDTH = 1400


def human_size(bytes):
    for unit in ['B', 'KB', 'MB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} MB"


def optimize_image(path: Path, quality: int, max_width: int, dry_run: bool) -> tuple:
    """
    Retorna (size_before, size_after, skipped)
    """
    size_before = path.stat().st_size

    if dry_run:
        return size_before, size_before, False

    with Image.open(path) as img:
        # Converteix a RGB si cal (PNG amb alpha, etc.)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')

        # Redimensiona si és més ampla que max_width
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Guarda com a WebP al mateix lloc, substitueix l'original
        webp_path = path.with_suffix('.webp')
        img.save(webp_path, 'WEBP', quality=quality, method=6)

    size_after = webp_path.stat().st_size

    # Esborra l'original si no era ja webp
    if path.suffix.lower() != '.webp':
        path.unlink()

    return size_before, size_after, False


def main():
    parser = argparse.ArgumentParser(description='Optimitza imatges a FOTOS/ per la web.')
    parser.add_argument('--fotos',     default=FOTOS_DIR, help='Carpeta FOTOS')
    parser.add_argument('--quality',   type=int, default=DEFAULT_QUALITY, help='Qualitat WebP 1-100')
    parser.add_argument('--max-width', type=int, default=DEFAULT_MAX_WIDTH, help='Amplada màxima px')
    parser.add_argument('--dry-run',   action='store_true', help='Mostra canvis sense modificar res')
    args = parser.parse_args()

    fotos_dir = Path(args.fotos)
    if not fotos_dir.is_dir():
        print(f'ERROR: No es troba la carpeta {fotos_dir}')
        return

    # Recull totes les imatges
    images = [
        p for p in fotos_dir.rglob('*')
        if p.suffix.lower() in IMG_EXTENSIONS and p.is_file()
    ]

    if not images:
        print('Cap imatge trobada.')
        return

    print(f'🖼️  {len(images)} imatges trobades a {fotos_dir}/')
    if args.dry_run:
        print('   [DRY-RUN] No es modificarà res.\n')
    print(f'   Qualitat WebP: {args.quality} | Amplada màxima: {args.max_width}px\n')

    total_before = 0
    total_after = 0
    count = 0
    errors = 0

    for img_path in sorted(images):
        try:
            before, after, skipped = optimize_image(
                img_path, args.quality, args.max_width, args.dry_run
            )
            total_before += before
            total_after += after
            count += 1

            saving_pct = (1 - after / before) * 100 if before > 0 else 0
            label = '[DRY-RUN]' if args.dry_run else f'-{saving_pct:.0f}%'
            print(f'  {label:>10}  {img_path.relative_to(fotos_dir)}  '
                  f'({human_size(before)} → {human_size(after)})')

        except Exception as e:
            print(f'  ⚠️  ERROR {img_path.name}: {e}')
            errors += 1

    # Resum
    print(f'\n{"─"*50}')
    if args.dry_run:
        print(f'[DRY-RUN] {count} imatges analitzades. No s\'ha modificat res.')
    else:
        saved = total_before - total_after
        saved_pct = (saved / total_before * 100) if total_before > 0 else 0
        print(f'✅ {count} imatges optimitzades')
        print(f'   Abans: {human_size(total_before)}')
        print(f'   Ara:   {human_size(total_after)}')
        print(f'   Estalvi: {human_size(saved)} ({saved_pct:.1f}%)')
        if errors:
            print(f'   ⚠️  {errors} errors')

    print('\nFet!')


if __name__ == '__main__':
    main()