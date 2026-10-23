"""Gera favicon-16.png (de favicon-16.svg), favicon-32.png, favicon.ico (16/32/48), apple-touch-icon.png e og.png (1200x630) a partir de favicon.svg e da página.

Não roda no CI: as imagens ficam versionadas. Requer Playwright + Chrome e o site servido localmente
(python -m http.server 8765 na raiz, com data/setores.json gerado por scripts/fetch_data.py).
Uso: python scripts/make_assets.py [URL do site local] [caminho do Chrome]
"""

import io
import os
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(__file__), "..")
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"
CHROME = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/google-chrome"

OG = """<html><head><style>@font-face{font-family:Inter;src:url(%(url)scss/inter-latin-wght-normal.woff2)}
body{margin:0;width:1200px;height:630px;background:#050506;color:#f4f1ea;font-family:Inter;display:flex;overflow:hidden}
.l{width:500px;padding:56px 0 48px 64px;display:flex;flex-direction:column}
.e{font:15px ui-monospace,Menlo,monospace;letter-spacing:.14em;color:#2dd4bf;text-transform:uppercase;margin-top:70px}
h1{font:400 50px "Iowan Old Style",Palatino,Georgia,serif;line-height:1.1;margin:18px 0}
p{color:#a1a1aa;font-size:19px;line-height:1.5;margin:0}.f{margin-top:auto;font:15px ui-monospace,Menlo,monospace;color:#71717a}
.r{flex:1;padding:40px 40px 40px 10px;display:flex;align-items:center}.r img{width:100%%;border:1px solid #1c1c1f;border-radius:16px}</style></head>
<body><div class="l"><img src="%(url)sfavicon.svg" width="56" height="56"><div class="e">Performance setorial</div>
<h1>Quais setores estão puxando a bolsa?</h1><p>EUA (ETFs SPDR) e Brasil (índices B3): retorno acumulado e rotação. Dados reais, atualizados todo dia útil.</p>
<div class="f">celowiz.github.io/setores</div></div><div class="r"><img src="data:image/png;base64,%(shot)s"></div></body></html>"""


def main():
    import base64

    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)

        def render(svg, size, bg="transparent"):
            pg = b.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
            pg.set_content(f'<body style="margin:0;background:{bg}"><img src="{URL}{svg}" width="{size}" height="{size}"></body>')
            pg.wait_for_timeout(300)
            img = Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert("RGBA")
            pg.close()
            return img

        # 16 px usa o desenho simplificado (favicon-16.svg); os demais tamanhos, o favicon.svg
        i16, i32, i48 = render("favicon-16.svg", 16), render("favicon.svg", 32), render("favicon.svg", 48)
        i16.save(os.path.join(ROOT, "favicon-16.png"))
        i32.save(os.path.join(ROOT, "favicon-32.png"))
        i48.save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=[i16, i32])
        render("favicon.svg", 180, "#050506").convert("RGB").save(os.path.join(ROOT, "apple-touch-icon.png"))

        # og.png: texto + recorte do gráfico real (EUA, YTD)
        pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
        pg.goto(URL)
        pg.wait_for_selector("body.ready")
        pg.wait_for_timeout(800)
        shot = base64.b64encode(pg.locator(".chartcard").screenshot()).decode()
        og = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        og.set_content(OG % {"url": URL, "shot": shot})
        og.wait_for_timeout(600)
        og.screenshot(path=os.path.join(ROOT, "og.png"))
        b.close()
    print("ok: favicon-16.png, favicon-32.png, favicon.ico, apple-touch-icon.png, og.png")


if __name__ == "__main__":
    main()
