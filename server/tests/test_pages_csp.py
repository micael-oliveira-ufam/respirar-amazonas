"""A CSP do site estático (GitHub Pages) deve ser a do servidor mais a API, nada além disso."""

import importlib.util
import sys
from pathlib import Path

from app.main import _CSP_PUBLICO

RAIZ = Path(__file__).resolve().parents[2]


def _gp():
    spec = importlib.util.spec_from_file_location("gerar_pages_t", RAIZ / "tool" / "gerar_pages.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["gerar_pages_t"] = m
    spec.loader.exec_module(m)
    return m


def _diretivas(csp):
    return {d.split()[0]: set(d.split()[1:]) for d in csp.split(";") if d.strip()}


def test_csp_do_pages_so_acrescenta_a_api():
    api = "https://api.exemplo.org"
    srv = _diretivas(_CSP_PUBLICO)
    pg = _diretivas(_gp().csp(api))
    for nome, valores in srv.items():
        if nome == "frame-ancestors":  # não vale em <meta>
            continue
        extra = pg[nome] - valores
        assert extra <= {api}, (nome, extra)
        assert valores <= pg[nome], (nome, valores - pg[nome])
    assert set(pg) - set(srv) == set()
    assert api in pg["connect-src"] and api in pg["img-src"]
