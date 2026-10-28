"""Testa tool/publicar_dados_pages.py (sem rede: o download é injetado)."""

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("publicar_dados_pages", RAIZ / "tool" / "publicar_dados_pages.py")
pdp = importlib.util.module_from_spec(spec)
sys.modules["publicar_dados_pages"] = pdp
spec.loader.exec_module(pdp)

AGORA = lambda: dt.datetime(2026, 10, 27, 12, 0, tzinfo=dt.timezone.utc)  # noqa: E731


def _buscar_ok(url):
    if "/publico/painel" in url:
        return json.dumps({"gerado_em": "2026-10-27T12:00:00+00:00", "total": 3}).encode()
    return b"a,b\n1,2\n"


def test_publica_tudo_e_escreve_manifesto(tmp_path):
    saida = tmp_path / "docs" / "dados"
    saida.parent.mkdir()
    m = pdp.publicar("https://api.exemplo/", saida, _buscar_ok, AGORA)
    assert m["gerado_em"] == "2026-10-27T12:00:00+00:00" and m["fonte"] == "https://api.exemplo"
    for d in (1, 7, 30, 90):
        assert (saida / f"painel-{d}.json").is_file()
    assert (saida / "csv" / "sintomas-30d.csv").read_bytes() == b"a,b\n1,2\n"
    assert (saida / "csv" / "qualidade_ar.csv").is_file()
    assert json.loads((saida / "manifest.json").read_text())["csv"][0] == {"conjunto": "sintomas", "dias": 1, "arquivo": "csv/sintomas-1d.csv"}
    assert len(m["csv"]) == 6 * 4 + 1


def test_falha_no_meio_nao_altera_o_que_ja_estava_publicado(tmp_path):
    saida = tmp_path / "docs" / "dados"
    saida.mkdir(parents=True)
    (saida / "manifest.json").write_text("antigo")

    def quebra(url):
        if "conjunto=bairros" in url:
            raise RuntimeError("HTTP 502")
        return _buscar_ok(url)

    with pytest.raises(RuntimeError):
        pdp.publicar("https://api.exemplo", saida, quebra, AGORA)
    assert (saida / "manifest.json").read_text() == "antigo"
    assert not [p for p in saida.parent.iterdir() if p.name != "dados"]  # sem sobras temporárias


def test_rejeita_painel_invalido_e_csv_vazio(tmp_path):
    saida = tmp_path / "docs" / "dados"
    saida.parent.mkdir()
    with pytest.raises(RuntimeError):
        pdp.publicar("https://x", saida, lambda u: b'{"outro": 1}' if "painel" in u else b"a\n", AGORA)
    with pytest.raises(RuntimeError):
        pdp.publicar("https://x", saida, lambda u: _buscar_ok(u) if "painel" in u else b"  \n", AGORA)
    assert not saida.exists()
