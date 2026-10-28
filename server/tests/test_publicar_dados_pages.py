"""As listas de tool/publicar_dados_pages.py devem acompanhar o servidor e a página."""

import importlib.util
import re
import sys
from pathlib import Path

from app import exportacao, publico

RAIZ = Path(__file__).resolve().parents[2]


def _pdp():
    spec = importlib.util.spec_from_file_location("pdp_t", RAIZ / "tool" / "publicar_dados_pages.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["pdp_t"] = m
    spec.loader.exec_module(m)
    return m


def test_periodos_e_conjuntos_acompanham_o_servidor_e_o_baixar_js():
    pdp = _pdp()
    assert tuple(pdp.PERIODOS) == tuple(publico.PERIODOS)
    for c in pdp.CONJUNTOS_POR_PERIODO:
        assert exportacao.CONJUNTOS[c][1] is True, c
    for c in pdp.CONJUNTOS_SEM_PERIODO:
        assert exportacao.CONJUNTOS[c][1] is False, c
    js = (RAIZ / "server" / "app" / "static_publico" / "baixar.js").read_text(encoding="utf-8")
    na_pagina = re.findall(r"\['(\w+)', '[^']+', '[^']+', (true|false)\]", js)
    assert sorted(c for c, _ in na_pagina) == sorted(pdp.CONJUNTOS_POR_PERIODO + pdp.CONJUNTOS_SEM_PERIODO)
