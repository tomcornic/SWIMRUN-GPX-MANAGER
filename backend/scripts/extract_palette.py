"""Extrait les couleurs dominantes de docs/brand/{logo,affiche}.jpg (§2 : thème depuis la charte).

Outil ponctuel (P7) — nécessite Pillow, volontairement absent de requirements.txt (jamais utilisé
au runtime par Flask) : `pip install pillow` dans le venv avant de lancer ce script.

Usage : PYTHONPATH=backend .venv/bin/python backend/scripts/extract_palette.py
"""

from pathlib import Path

from PIL import Image

BRAND_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "brand"
IMAGES = ["logo.jpg", "affiche.jpg"]
N_COLORS = 8


def dominant_colors(
    image_path: Path, n: int = N_COLORS
) -> list[tuple[tuple[int, int, int], float]]:
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((200, 200))
    quantized = img.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    counts = quantized.getcolors()
    total = sum(count for count, _ in counts)

    résultats = []
    for count, index in sorted(counts, reverse=True):
        r, g, b = palette[index * 3 : index * 3 + 3]
        résultats.append(((r, g, b), count / total))
    return résultats


def hex_code(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def main() -> None:
    for filename in IMAGES:
        path = BRAND_DIR / filename
        if not path.exists():
            print(f"⚠ {filename} introuvable dans {BRAND_DIR}")
            continue
        print(f"\n{filename}")
        for rgb, part in dominant_colors(path):
            barre = "█" * max(1, round(part * 40))
            print(f"  {hex_code(rgb)}  {part:5.1%}  {barre}")


if __name__ == "__main__":
    main()
