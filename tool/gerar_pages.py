#!/usr/bin/env python3
"""Gera o site estático do GitHub Pages (pasta docs/) a partir da página pública do servidor.

Uso:
  python3 tool/gerar_pages.py                         # modo ESTÁTICO: independente do servidor (padrão)
  python3 tool/gerar_pages.py --api https://respirar-amazonas.cloud   # modo CONECTADO: dados lidos da API

Modo estático (sem servidor):
  - qualidade do ar: o navegador consulta o Open-Meteo direto (assets/ar_modelo.js);
  - relatos dos usuários e CSV: arquivos publicados em docs/dados/ por tool/publicar_dados_pages.py
    (um RETRATO, não ao vivo; sem eles a página diz que ainda não foram publicados);
  - download do app: link DIRETO para o APK numa Release do GitHub (--apk-url) + QR code estático + manual em PDF.
    O endereço do APK tem a versão no nome: a cada APK novo, rode de novo com o novo --apk-url (ou edite APK_URL_PADRAO).
Modo conectado: igual à 1.19.0 (a API fornece relatos, ar, download e CSV).
A saída é determinística (sem data/hora): a mesma entrada gera exatamente os mesmos bytes. A pasta
docs/dados/ é preservada ao regenerar. Publicação: Settings > Pages > Deploy from a branch > main > /docs
(sem GitHub Actions).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "server" / "app" / "static_publico"
VENDOR = RAIZ / "server" / "app" / "static" / "vendor"
APK_URL_PADRAO = "https://github.com/micael-oliveira-ufam/respirar-amazonas/releases/download/v1.22.2/RespirAR-Amazonas-v1.22.2.apk"
MUNICIPIOS_CSV = RAIZ / "server" / "app" / "dados" / "municipios_am.csv"
MANUAL_PDF = RAIZ / "server" / "app" / "manual" / "Manual_Instalacao_RespirAR_Amazonas.pdf"
OPEN_METEO = "https://air-quality-api.open-meteo.com"
URL_PADRAO = "https://micael-oliveira-ufam.github.io/respirar-amazonas"

#: Mesma política do servidor (`_CSP_PUBLICO` em main.py). Modo conectado libera a API (conexões e imagens);
#: modo estático libera só o Open-Meteo (conexões). `frame-ancestors` não funciona em <meta>, por isso não consta.
_CSP = (
    "default-src 'self'; img-src 'self' data: https://tile.openstreetmap.org https://*.tile.opentopomap.org "
    "https://gibs.earthdata.nasa.gov https://terrabrasilis.dpi.inpe.br{img}; "
    "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' {conn}; base-uri 'none'"
)


def origem(url: str) -> str:
    """Valida e normaliza a URL da API (https, sem caminho): vai para o CSP e para o config.js."""
    u = urlparse(url.strip())
    if u.scheme not in ("https", "http") or not u.netloc or u.path not in ("", "/") or u.query or u.fragment:
        raise SystemExit(f"URL da API inválida: {url!r} (use algo como https://respirar-amazonas.cloud)")
    if not re.fullmatch(r"[A-Za-z0-9.\-:]+", u.netloc):
        raise SystemExit(f"URL da API inválida: {url!r}")
    return f"{u.scheme}://{u.netloc}"


def csp(api: str | None) -> str:
    """api=None: modo estático (só o Open-Meteo); api=URL: modo conectado."""
    if api is None:
        return _CSP.format(img="", conn=OPEN_METEO)
    return _CSP.format(img=" " + api, conn=api)


def transformar_html(html: str, api: str | None, url_site: str, versao: str) -> str:
    html = html.replace("{{BASE}}", url_site.rstrip("/")).replace("{{VERSAO}}", versao)
    html = html.replace('="/assets/', '="assets/').replace('="/vendor/', '="vendor/')
    html = html.replace('href="/favicon.ico"', 'href="favicon.ico"')
    if api is None:
        html = html.replace('href="/publico/painel?dias=30"', 'href="dados/painel-30.json"')
    else:
        html = html.replace('href="/publico/', f'href="{api}/publico/')
    meta = f'<meta http-equiv="Content-Security-Policy" content="{csp(api)}">'
    assert "<head>" in html
    html = html.replace("<head>", "<head>\n  " + meta, 1)
    restos = re.findall(r'(?:src|href)="(/[^"/][^"]*)"', html)
    if restos:
        raise SystemExit(f"Caminhos absolutos que sobraram no HTML (quebrariam no Pages): {restos}")
    return html


def validar_apk_url(url: str) -> str:
    """O endereço vai para o config.js (entre aspas) e para o QR code: só https e sem caracteres que quebrem o JS."""
    u = urlparse(url.strip())
    if u.scheme != "https" or not u.netloc or not re.fullmatch(r"[A-Za-z0-9._~:/%+@\-]+", url.strip()):
        raise SystemExit(f"URL do APK inválida: {url!r} (use https://, sem espaços nem aspas)")
    return url.strip()


def qr_svg(destino: str) -> bytes:
    """QR code (SVG) do endereço de download, com o mesmo estilo do servidor (/publico/qr.svg)."""
    try:
        import segno
    except ImportError:
        raise SystemExit("Falta o pacote segno (pip install segno ou pip install -r server/requirements.txt).")
    import io
    buf = io.BytesIO()
    segno.make(destino, error="m").save(buf, kind="svg", scale=6, border=2, dark="#1B5E20")
    return buf.getvalue()


def municipios_json() -> str:
    with open(MUNICIPIOS_CSV, encoding="utf-8", newline="") as f:
        lista = [{"codigo": int(r["codigo_ibge"]), "nome": r["nome"], "lat": float(r["latitude"]), "lon": float(r["longitude"])}
                 for r in csv.DictReader(f)]
    return json.dumps(lista, ensure_ascii=False, separators=(",", ":")) + "\n"


def gerar(saida: Path, api: str | None, url_site: str, apk_url: str = APK_URL_PADRAO) -> str:
    versao = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
    guardado = None
    if saida.exists():
        if (saida / "dados").is_dir():          # retratos publicados por tool/publicar_dados_pages.py
            guardado = saida.parent / (saida.name + ".dados.tmp")
            if guardado.exists():
                shutil.rmtree(guardado)
            shutil.move(str(saida / "dados"), guardado)
        shutil.rmtree(saida)
    (saida / "assets").mkdir(parents=True)
    for arq in sorted(FONTE.iterdir()):
        if arq.is_file() and arq.name not in ("publico.html", "config.js"):
            shutil.copy2(arq, saida / "assets" / arq.name)
    shutil.copy2(FONTE / "favicon.ico", saida / "favicon.ico")
    for sub in ("leaflet", "leaflet-heat"):
        shutil.copytree(VENDOR / sub, saida / "vendor" / sub)
    modo = "estatico" if api is None else "conectado"
    cfg = ("/* Gerado por tool/gerar_pages.py. Ver modos em server/app/static_publico/config.js. */\n"
           f"window.RESPIRAR_MODO = '{modo}';\n"
           f"window.RESPIRAR_API = '{api or ''}';\n")
    if api is None:
        cfg += f"window.RESPIRAR_APK_URL = '{apk_url}';\n"
        (saida / "assets" / "municipios_am.json").write_text(municipios_json(), encoding="utf-8")
        (saida / "assets" / "qr-app.svg").write_bytes(qr_svg(apk_url))
        shutil.copy2(MANUAL_PDF, saida / "assets" / "Manual-Instalacao-RespirAR-Amazonas.pdf")
    cfg += "window.respirarUrl = function (caminho) { return (window.RESPIRAR_API || '') + caminho; };\n"
    (saida / "assets" / "config.js").write_text(cfg, encoding="utf-8")
    html = transformar_html((FONTE / "publico.html").read_text(encoding="utf-8"), api, url_site, versao)
    (saida / "index.html").write_text(html, encoding="utf-8")
    (saida / "404.html").write_text(
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Página não encontrada</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<p style="font:16px system-ui;margin:2rem">Página não encontrada. '
        '<a href="./">Ir para o RespirAR Amazonas</a></p></html>\n', encoding="utf-8")
    (saida / ".nojekyll").write_text("", encoding="utf-8")
    h = hashlib.sha256(versao.encode())
    for arq in sorted(p for p in saida.rglob("*") if p.is_file()):
        h.update(str(arq.relative_to(saida)).encode())
        h.update(arq.read_bytes())
    build = h.hexdigest()[:12]
    (saida / "versao.json").write_text(json.dumps({"build": build, "versao": versao}) + "\n", encoding="utf-8")
    if guardado is not None:
        shutil.move(str(guardado), saida / "dados")
    return build


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=None, help="modo conectado: endereço do servidor de dados (omitido = modo estático)")
    ap.add_argument("--apk-url", default=APK_URL_PADRAO, help="modo estático: endereço direto do APK (Release do GitHub)")
    ap.add_argument("--url", default=URL_PADRAO, help="endereço público do site no Pages (para canonical e prévias)")
    ap.add_argument("--saida", default=str(RAIZ / "docs"))
    a = ap.parse_args(argv)
    api = origem(a.api) if a.api else None
    build = gerar(Path(a.saida), api, a.url, validar_apk_url(a.apk_url))
    print(f"Site gerado em {a.saida} (build {build}); " + (f"dados vindos de {api}." if api else "modo estático, sem servidor."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
