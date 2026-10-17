"""Install your ORIGINAL flat-orange-cat file as emails/assets/hero-cat.jpg.
Usage: python3 scripts/set-hero.py /path/to/original.png
Keeps the artwork and aspect ratio: no crop, no resize (only flattens transparency
onto white, because JPEG has no alpha, and downsizes ONLY if wider than 1600px)."""
import sys, hashlib, pathlib
from PIL import Image
src = pathlib.Path(sys.argv[1])
im = Image.open(src)
if im.mode in ("RGBA", "LA", "P"):
    im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[-1]); im = bg
else:
    im = im.convert("RGB")
if im.width > 1600:
    im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
out = pathlib.Path(__file__).resolve().parent.parent / "emails" / "assets" / "hero-cat.jpg"
im.save(out, quality=93, optimize=True, subsampling=0)
print(f"source: {src.name} sha256={hashlib.sha256(src.read_bytes()).hexdigest()[:16]}")
print(f"wrote {out} {im.size}")
