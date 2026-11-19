#!/usr/bin/env python3
"""Before / after sheet per trader from the QA sheets of blender/render_character_qa.py.

    python3 scripts/compare_characters.py      -> previews/characters/compare_<role>.png

Row 1 = before (previews/characters/before), row 2 = after (previews/characters/after), same cameras:
front, three-quarter, head front, eyes, right hand, clothing.  Needs Pillow.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ROLES = ("selma", "nyra", "lio", "aron", "esme")
TILES = (0, 3, 4, 6, 7, 9)            # indices in the 4-column views sheet


def tiles(path):
    img = Image.open(path)
    size = img.width // 4
    return [img.crop(((k % 4) * size, (k // 4) * size, (k % 4 + 1) * size, (k // 4 + 1) * size)) for k in TILES], size


def main():
    for role in ROLES:
        before, size = tiles(ROOT / f"previews/characters/before/{role}_views.png")
        after, _ = tiles(ROOT / f"previews/characters/after/{role}_views.png")
        label = 28
        out = Image.new("RGB", (size * len(TILES), 2 * size + 2 * label), (24, 24, 28))
        draw = ImageDraw.Draw(out)
        for row, (name, row_tiles) in enumerate((("vorher", before), ("nachher", after))):
            y = row * (size + label)
            draw.text((8, y + 6), f"{role} - {name}", fill=(235, 235, 235))
            for k, t in enumerate(row_tiles):
                out.paste(t, (k * size, y + label))
        path = ROOT / f"previews/characters/compare_{role}.png"
        out.save(path)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
