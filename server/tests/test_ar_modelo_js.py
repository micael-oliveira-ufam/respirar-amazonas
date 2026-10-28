"""Paridade: static_publico/ar_modelo.js (Pages sem servidor) deve produzir o mesmo que app/qualidade_ar.py."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app import qualidade_ar as qar

from .test_publico_extra import _resposta_modelo, _servico

JS = Path(__file__).resolve().parents[1] / "app" / "static_publico" / "ar_modelo.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js não instalado")

SCRIPT = """
const fs = require('fs');
require(process.argv[1]);
const {corpo, munis, consultado} = JSON.parse(fs.readFileSync(0, 'utf8'));
let saida;
try { saida = {ok: globalThis.RespirarArModelo.montar(corpo, munis, consultado)}; }
catch (e) { saida = {erro: String(e.message)}; }
process.stdout.write(JSON.stringify(saida));
"""


def _js(corpo, munis, consultado):
    entrada = json.dumps({"corpo": corpo, "munis": [{"codigo": m.codigo, "nome": m.nome, "lat": m.lat, "lon": m.lon} for m in munis],
                          "consultado": consultado})
    r = subprocess.run(["node", "-e", SCRIPT, str(JS)], input=entrada, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _python(corpo):
    servico, _ = _servico(corpo)
    return servico.obter()


def _variado():
    corpo = _resposta_modelo()
    casos = [
        {"us_aqi": 2.5, "pm2_5": 12.25, "pm10": 24.5, "time": "2026-10-20T14:00"},      # empates exatos: Python arredonda p/ par
        {"us_aqi": 3.5, "pm2_5": 1.15, "pm10": 3.0, "time": "2026-10-20T14:15"},
        {"us_aqi": 100.5, "pm2_5": 0.05, "pm10": 0.0, "time": "2026-10-20T13:00:00"},   # pm10 = 0: sem fração fina
        {"us_aqi": 150, "pm2_5": 33.3333, "pm10": 99.9999, "time": "2026-10-20T14:00Z"},
        {"us_aqi": 201, "pm2_5": 80, "pm10": 90, "time": "2026-10-20T14:00-04:00"},
        {"us_aqi": 301, "pm2_5": 250.04, "pm10": 300.06},
        {"us_aqi": None, "pm2_5": None, "pm10": None, "time": ""},
        {"us_aqi": -1, "pm2_5": -3, "pm10": float("inf") if False else 5},
        {"us_aqi": True, "pm2_5": "9", "pm10": 7, "time": 5},
        {"us_aqi": 99.5, "pm2_5": 7.45, "pm10": 7.55, "time": "lixo"},
    ]
    for i, c in enumerate(casos):
        corpo[i] = {"current": c}
    corpo[len(casos)] = {}                         # local sem `current`
    corpo[len(casos) + 1] = {"current": []}        # `current` inválido
    return corpo


@pytest.mark.parametrize("corpo", [_resposta_modelo(), _variado()], ids=["uniforme", "casos-de-borda"])
def test_resultado_igual_ao_do_python(corpo):
    py = _python(corpo)
    js = _js(corpo, qar.municipios(), py["consultado_em"])
    assert "erro" not in js, js
    assert js["ok"] == json.loads(json.dumps(py))


def test_parametros_da_consulta_iguais():
    munis = qar.municipios()
    saida = subprocess.run(
        ["node", "-e", "require(process.argv[1]);const m=JSON.parse(process.argv[2]);process.stdout.write(globalThis.RespirarArModelo.montarParams(m))",
         str(JS), json.dumps([{"codigo": m.codigo, "nome": m.nome, "lat": m.lat, "lon": m.lon} for m in munis])],
        capture_output=True, text=True, timeout=30)
    esperado = qar.montar_params(munis)
    assert saida.stdout == f"latitude={esperado['latitude']}&longitude={esperado['longitude']}&current={esperado['current']}&timezone={esperado['timezone']}"


@pytest.mark.parametrize("corpo", [{"error": True, "reason": "limite"}, [{"current": {}}] * 3, "texto", None])
def test_respostas_invalidas_sao_recusadas_nos_dois_lados(corpo):
    with pytest.raises(ValueError):
        qar.interpretar(corpo, qar.municipios())
    assert "erro" in _js(corpo, qar.municipios(), "x")
