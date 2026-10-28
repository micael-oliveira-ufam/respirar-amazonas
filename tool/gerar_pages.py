#!/usr/bin/env python3
"""Gera o site estático do GitHub Pages (pasta docs/) a partir da página pública do servidor.

Uso:
  python3 tool/gerar_pages.py                         # docs/ com a API em https://respirar-amazonas.cloud
  python3 tool/gerar_pages.py --api https://outro.exemplo --url https://usuario.github.io/repo --saida docs

O site fica na casca estática (HTML/CSS/JS, Leaflet, imagens). Os DADOS continuam vindo do servidor
(--api): /publico/painel, /publico/qualidade-ar, /publico/app, /publico/export.csv, /publico/qr.svg.
A saída é determinística (sem data/hora): a mesma entrada gera exatamente os mesmos bytes.
Publicação: Settings > Pages > Deploy from a branch > main > /docs (sem GitHub Actions).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "server" / "app" / "static_publico"
VENDOR = RAIZ / "server" / "app" / "static" / "vendor"
API_PADRAO = "https://respirar-amazonas.cloud"
URL_PADRAO = "https://micael-oliveira-ufam.github.io/respirar-amazonas"

#: Mesma política do servidor (`_CSP_PUBLICO` em main.py), com a API liberada para conexões e imagens.
#: `frame-ancestors` não funciona em <meta>, por isso não consta.
_CSP = (
    "default-src 'self'; img-src 'self' data: https://tile.openstreetmap.org https://*.tile.opentopomap.org "
    "https://gibs.earthdata.nasa.gov https://terrabrasilis.dpi.inpe.br {api}; "
    "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' {api}; base-uri 'none'"
)


def origem(url: str) -> str:
    """Valida e normaliza a URL da API (https, sem caminho): vai para o CSP e para o config.js."""
    u = urlparse(url.strip())
    if u.scheme not in ("https", "http") or not u.netloc or u.path not in ("", "/") or u.query or u.fragment:
        raise SystemExit(f"URL da API inválida: {url!r} (use algo como https://respirar-amazonas.cloud)")
    if not re.fullmatch(r"[A-Za-z0-9.\-:]+", u.netloc):
        raise SystemExit(f"URL da API inválida: {url!r}")
    return f"{u.scheme}://{u.netloc}"


def csp(api: str) -> str:
    return _CSP.format(api=api)


def transformar_html(html: str, api: str, url_site: str, versao: str) -> str:
    html = html.replace("{{BASE}}", url_site.rstrip("/")).replace("{{VERSAO}}", versao)
    html = html.replace('="/assets/', '="assets/').replace('="/vendor/', '="vendor/')
    html = html.replace('href="/favicon.ico"', 'href="favicon.ico"')
    html = html.replace('href="/publico/', f'href="{api}/publico/')
    meta = f'<meta http-equiv="Content-Security-Policy" content="{csp(api)}">'
    assert "<head>" in html
    html = html.replace("<head>", "<head>\n  " + meta, 1)
    restos = re.findall(r'(?:src|href)="(/[^"/][^"]*)"', html)
    if restos:
        raise SystemExit(f"Caminhos absolutos que sobraram no HTML (quebrariam no Pages): {restos}")
    return html


def gerar(saida: Path, api: str, url_site: str) -> str:
    versao = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
    if saida.exists():
        shutil.rmtree(saida)
    (saida / "assets").mkdir(parents=True)
    for arq in sorted(FONTE.iterdir()):
        if arq.is_file() and arq.name not in ("publico.html", "config.js"):
            shutil.copy2(arq, saida / "assets" / arq.name)
    shutil.copy2(FONTE / "favicon.ico", saida / "favicon.ico")
    for sub in ("leaflet", "leaflet-heat"):
        shutil.copytree(VENDOR / sub, saida / "vendor" / sub)
    (saida / "assets" / "config.js").write_text(
        "/* Gerado por tool/gerar_pages.py. Endereço do servidor de dados. */\n"
        f"window.RESPIRAR_API = '{api}';\n"
        "window.respirarUrl = function (caminho) { return (window.RESPIRAR_API || '') + caminho; };\n",
        encoding="utf-8")
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
    (saida / "versao.json").write_text(f'{{"build": "{build}"}}\n', encoding="utf-8")
    return build


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=API_PADRAO)
    ap.add_argument("--url", default=URL_PADRAO, help="endereço público do site no Pages (para canonical e prévias)")
    ap.add_argument("--saida", default=str(RAIZ / "docs"))
    a = ap.parse_args(argv)
    api = origem(a.api)
    build = gerar(Path(a.saida), api, a.url)
    print(f"Site gerado em {a.saida} (build {build}); dados vindos de {api}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
