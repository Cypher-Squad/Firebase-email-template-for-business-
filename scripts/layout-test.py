"""Renders both templates at several widths in headless Chromium and checks layout.
Run: python3 scripts/layout-test.py   (needs: pip install playwright && playwright install chromium)"""
import json, pathlib, hashlib
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
out = root / "test-output"; out.mkdir(exist_ok=True)
widths = {"mobile-360": (360, 800), "mobile-390": (390, 844), "tablet-768": (768, 1000), "desktop-1280": (1280, 900)}
results = []
# Hero identity: shipped hero must equal the supplied original minus only the black capture rows.
orig = Image.open(root / "emails/assets/originals/hero-cat-original.jpg").convert("RGB")
hero = Image.open(root / "emails/assets/hero-cat.jpg").convert("RGB")
ref = np.array(orig.crop((0, 0, orig.width, hero.height)), int)
hero_diff = float(np.abs(ref - np.array(hero, int)).mean())
hero_ok = hero.size == (orig.width, orig.height - 9) and hero_diff < 2.0
print(f"hero-cat.jpg {hero.size} vs original {orig.size}: mean pixel diff {hero_diff:.2f} (JPEG re-encode only) -> {'PASS' if hero_ok else 'FAIL'}")
print("hero-cat.jpg sha256:", hashlib.sha256((root / "emails/assets/hero-cat.jpg").read_bytes()).hexdigest()[:16])
with sync_playwright() as p:
    b = p.chromium.launch()
    for name in ["verify-email", "reset-password"]:
        for label, (w, h) in widths.items():
            pg = b.new_page(viewport={"width": w, "height": h})
            failed = []
            pg.on("requestfailed", lambda r: failed.append(r.url))
            pg.goto((root / "preview" / f"{name}.rendered.html").as_uri())
            pg.wait_for_load_state("load")
            m = pg.evaluate("""() => {
              const card = document.querySelector('table[width="600"]').getBoundingClientRect();
              const btn = document.querySelector('a.btn-link').getBoundingClientRect();
              const imgs = [...document.images].map(i => ({src: i.getAttribute('src'), ok: i.complete && i.naturalWidth > 0, w: i.naturalWidth}));
              const vw = document.documentElement.clientWidth;
              return {scrollW: document.documentElement.scrollWidth, vw, cardW: card.width, cardL: card.left, cardR: card.right,
                      btnW: btn.width, btnH: btn.height, imgs, h1: document.querySelector('h1').innerText,
                      btnText: document.querySelector('a.btn-link').innerText, href: document.querySelector('a.btn-link').href};
            }""")
            checks = {
              "no horizontal scroll": m["scrollW"] <= m["vw"],
              "card fits viewport": m["cardL"] >= 0 and m["cardR"] <= m["vw"] + 0.5,
              "card max 600px": m["cardW"] <= 600.5,
              "all images loaded": all(i["ok"] for i in m["imgs"]) and not failed,
              "button tap height >= 44px": m["btnH"] >= 44,
              "button href is set": m["href"].startswith("https://"),
              "hero is new image (1080x1088)": any(i["src"].endswith("hero-cat.jpg") and i["w"] == 1080 for i in m["imgs"]),
              "hero file matches original": hero_ok,
            }
            pg.screenshot(path=str(out / f"{name}-{label}.png"), full_page=True)
            results.append({"template": name, "viewport": label, "checks": checks, "btn": [round(m["btnW"]), round(m["btnH"])], "card": round(m["cardW"])})
            pg.close()
    b.close()
for r in results:
    bad = [k for k, v in r["checks"].items() if not v]
    print(f'{r["template"]:15} {r["viewport"]:13} card={r["card"]}px btn={r["btn"]} ->', "PASS" if not bad else "FAIL: " + ", ".join(bad))
json.dump(results, open(out / "results.json", "w"), indent=2)
