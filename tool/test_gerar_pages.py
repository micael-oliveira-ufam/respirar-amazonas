"""Testa tool/gerar_pages.py: site estático do GitHub Pages (pasta docs/)."""

import filecmp
import importlib.util
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("gerar_pages", RAIZ / "tool" / "gerar_pages.py")
gp = importlib.util.module_from_spec(spec)
sys.modules["gerar_pages"] = gp
spec.loader.exec_module(gp)

API = "https://respirar-amazonas.cloud"


def _gerar(tmp_path, api=API):
    saida = tmp_path / "site"
    build = gp.gerar(saida, api, "https://usuario.github.io/repo")
    return saida, build


def test_caminhos_relativos_e_sem_dependencia_do_servidor(tmp_path):
    saida, _ = _gerar(tmp_path)
    html = (saida / "index.html").read_text(encoding="utf-8")
    assert not re.findall(r'(?:src|href)="/[^"/]', html)          # nada absoluto: o Pages usa /repo/ como base
    assert 'src="assets/config.js' in html and 'href="vendor/leaflet/leaflet.css"' in html
    assert f'href="{API}/publico/painel?dias=30"' in html
    assert "{{" not in html                                       # todos os marcadores foram trocados
    assert 'href="https://usuario.github.io/repo/"' in html       # canonical no endereço do Pages
    for p in ("assets/publico.js", "assets/ar.js", "assets/baixar.js", "assets/amazonia.js", "assets/mapas.js",
              "assets/atualizar.js", "vendor/leaflet/leaflet.js", "vendor/leaflet-heat/leaflet-heat.js",
              "favicon.ico", ".nojekyll", "404.html", "versao.json"):
        assert (saida / p).is_file(), p
    assert not (saida / "assets" / "publico.html").exists()


def test_config_aponta_para_a_api_e_csp_libera_so_ela(tmp_path):
    saida, _ = _gerar(tmp_path)
    assert f"window.RESPIRAR_API = '{API}';" in (saida / "assets" / "config.js").read_text(encoding="utf-8")
    html = (saida / "index.html").read_text(encoding="utf-8")
    meta = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1)
    assert f"connect-src 'self' {API}" in meta and "script-src 'self';" in meta
    assert "unsafe-eval" not in meta and "script-src 'self' 'unsafe" not in meta


def test_saida_deterministica(tmp_path):
    a, ba = _gerar(tmp_path / "a")
    b, bb = _gerar(tmp_path / "b")
    assert ba == bb
    cmp = filecmp.dircmp(a, b)
    assert not cmp.diff_files and not cmp.left_only and not cmp.right_only


@pytest.mark.parametrize("ruim", ["ftp://x.org", "https://x.org/caminho", "x.org", "https://x.org/?a=1", "https://x y.org", ""])
def test_api_invalida_e_recusada(ruim):
    with pytest.raises(SystemExit):
        gp.origem(ruim)


def test_docs_publicado_esta_atualizado():
    """docs/ é o que o GitHub Pages serve. Se este teste falhar: python3 tool/gerar_pages.py"""
    docs = RAIZ / "docs"
    assert docs.is_dir(), "docs/ não existe: rode python3 tool/gerar_pages.py"
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        gp.gerar(Path(t) / "x", API, gp.URL_PADRAO)
        novo = Path(t) / "x"
        arquivos = sorted(p.relative_to(novo) for p in novo.rglob("*") if p.is_file())
        assert arquivos == sorted(p.relative_to(docs) for p in docs.rglob("*") if p.is_file())
        defasados = [str(a) for a in arquivos if (novo / a).read_bytes() != (docs / a).read_bytes()]
        assert not defasados, f"docs/ desatualizado ({defasados[:3]}...): rode python3 tool/gerar_pages.py"
