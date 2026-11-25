"""Testes do formulário do site (server/app/static_publico/responder*.js e responder.html).

Garante que o formulário do navegador continua igual ao app e às regras do Firestore:
  - a pontuação e os níveis batem com os casos de test/risk_assessment_test.dart (mesmos valores);
  - o documento montado tem exatamente os campos que firebase/firestore.rules aceita;
  - o termo de consentimento está em dia com lib/data/lgpd_terms.dart (tool/gerar_termo_site.py --verificar);
  - o texto de pontuação é o de lib/data/references.dart (scoringNotice);
  - o SDK do Firebase na página e a política de segurança (CSP) do formulário estão coerentes.

Uso: python3 -m pytest tool/test_responder_site.py -q   (precisa de node no PATH)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tool"))
import gerar_pages  # noqa: E402
import gerar_termo_site  # noqa: E402

FONTE = RAIZ / "server" / "app" / "static_publico"
LOGICA = FONTE / "responder_logica.js"
JS_RESPONDER = FONTE / "responder.js"
TERMO_JS = FONTE / "responder_termo.js"
HTML_RESPONDER = FONTE / "responder.html"
REGRAS = RAIZ / "firebase" / "firestore.rules"
DART_REFERENCIAS = RAIZ / "lib" / "data" / "references.dart"
DART_TERMO = RAIZ / "lib" / "data" / "lgpd_terms.dart"
DART_RISCO = RAIZ / "lib" / "logic" / "risk_assessment.dart"

_LITERAL = r"'((?:[^'\\\n]|\\.)*)'"


def _node(script: str):
    if shutil.which("node") is None:
        pytest.skip("node não encontrado no PATH")
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=False, cwd=RAIZ
    )
    assert r.returncode == 0, f"node falhou: {r.stderr}"
    return json.loads(r.stdout)


def _logica_js(corpo: str) -> str:
    """Executa `corpo` com a lógica do formulário já carregada como `L`; devolve o JSON impresso."""
    return (
        f"const L = require({json.dumps(str(LOGICA))});\n"
        f"const out = {{}};\n{corpo}\n"
        "console.log(JSON.stringify(out));\n"
    )


# ---------------------------------------------------------------- pontuação (paridade com o Dart)


def test_constantes_de_risco_iguais_ao_dart():
    dart = DART_RISCO.read_text(encoding="utf-8")
    assert int(re.search(r"const vulnerablePoints = (\d+);", dart).group(1)) == 3
    assert int(re.search(r"const moderateThreshold = (\d+);", dart).group(1)) == 8
    assert int(re.search(r"const highThreshold = (\d+);", dart).group(1)) == 15
    js = _node(_logica_js("out.v = L.PONTOS_VULNERAVEL; out.m = L.LIMIAR_MODERADO; out.a = L.LIMIAR_ALTO;"))
    assert (js["v"], js["m"], js["a"]) == (3, 8, 15)


def test_casos_do_dart_batem_no_formulario():
    """Os mesmos casos de test/risk_assessment_test.dart, com os mesmos valores esperados."""
    corpo = """
out.baixo = L.avaliar({}, 'under1h', {});
out.peito = L.avaliar({chest: 3}, 'under1h', {});
out.falta_cronica = L.avaliar({dyspnea: 2}, 'under1h', {doenca_respiratoria: true});
out.falta_sem_cronica = L.avaliar({dyspnea: 2}, 'under1h', {});
out.idoso_base = L.avaliar({}, 'between1and4h', {});
out.idoso = L.avaliar({}, 'between1and4h', {idoso: true});
out.moderado = L.avaliar({cough: 3, throat: 3, wheeze: 2}, 'between1and4h', {});
out.alto = L.avaliar({eyes: 3, cough: 3, throat: 3, headache: 3, fatigue: 3}, 'over4h', {});
try { L.avaliar({cough: 4}, 'under1h', {}); out.fora = 'sem erro'; } catch (e) { out.fora = e.name; }
"""
    r = _node(_logica_js(corpo))

    assert r["baixo"]["nivel"] == "low" and r["baixo"]["pontos"] == 0 and r["baixo"]["efeitos"] == []
    assert r["peito"]["nivel"] == "emergency"
    assert r["falta_cronica"]["nivel"] == "emergency"
    assert r["falta_sem_cronica"]["nivel"] != "emergency"
    assert r["idoso"]["pontos"] - r["idoso_base"]["pontos"] == 3  # vulnerablePoints
    assert r["moderado"]["pontos"] == 10 and r["moderado"]["nivel"] == "moderate"
    assert "respiratory" in r["moderado"]["efeitos"]
    assert r["alto"]["pontos"] == 19 and r["alto"]["nivel"] == "high"
    assert r["fora"] == "RangeError"


# ---------------------------------------------------------------- documento x regras do Firestore


def _listas_das_regras() -> dict[str, list[str]]:
    texto = REGRAS.read_text(encoding="utf-8")
    listas = {}
    for m in re.finditer(r"hasOnly\(\[([^\]]*)\]\)", texto, flags=re.S):
        chaves = re.findall(r"'([^']+)'", m.group(1))
        if "submission_id" in chaves:
            listas["resposta"] = chaves
        elif "cough" in chaves:
            listas["sintomas"] = chaves
        elif "idoso" in chaves:
            listas["perfil"] = chaves
        elif "local" in chaves:
            listas["contexto"] = chaves
    assert set(listas) == {"resposta", "sintomas", "perfil", "contexto"}, listas
    return listas


def _documento_completo() -> dict:
    corpo = """
const r = L.montarPayload({
  submissionId: '11111111-2222-4333-8444-555555555555',
  registradoEm: new Date('2026-11-25T12:00:00Z'),
  gravidades: {cough: 1, dyspnea: 2, chest: 0},
  exposicao: 'between1and4h',
  perfil: {idoso: true, gestante: false, crianca: false, doenca_respiratoria: false, doenca_cardiaca: false},
  contexto: {local: 'ar_livre', fumaca_visivel: true, mascara: 'pff2_n95', atividade_fisica_ar_livre: false,
    ar_filtrado: true, trabalho_ar_livre: false, imunologica: false, medicacao_a_mao: true,
    medicacao_nao_alivia: false, piorando: true},
  localizacao: {lat: -3.1190275, lon: -60.0217314},
  appVersion: 'site'
});
out.payload = r.payload;
"""
    return _node(_logica_js(corpo))["payload"]


def test_campos_do_documento_sao_aceitos_pelas_regras():
    listas = _listas_das_regras()
    doc = _documento_completo()

    # recebido_em é acrescentado na gravação (hora do servidor), por isso não faz parte do payload montado.
    assert set(doc) <= set(listas["resposta"]) - {"recebido_em"}
    assert set(listas["resposta"]) - {"lat", "lon", "app_version", "contexto", "recebido_em"} <= set(doc)
    assert set(doc["sintomas"]) == set(listas["sintomas"])
    assert all(v in (0, 1, 2, 3) for v in doc["sintomas"].values())
    assert set(doc["perfil"]) == set(listas["perfil"])
    assert set(doc["contexto"]) <= set(listas["contexto"])
    assert len(doc["submission_id"]) == 36
    assert doc["nivel"] in ("low", "moderate", "high", "emergency")
    assert doc["exposicao"] in ("under1h", "between1and4h", "over4h")


def test_localizacao_arredondada_como_o_dart():
    doc = _documento_completo()
    assert doc["lat"] == -3.12 and doc["lon"] == -60.02  # 2 casas, como (v * 100).round() / 100 do Dart


def test_arredondamento_meio_para_longe_de_zero():
    # 2.346 * 100 = 234.6 -> 235 (meio para longe de zero no Dart e aqui). 2.345 não serve: 2.345 * 100
    # é 234.4999... em ponto flutuante, e o Dart também arredondaria para 234.
    js = _node(_logica_js("out.p = L.arredondar2(2.346); out.n = L.arredondar2(-2.346);"))
    assert js["p"] == 2.35 and js["n"] == -2.35


# ---------------------------------------------------------------- termo e texto de pontuação


def _literais_juntos(trecho: str) -> str:
    return "".join(re.findall(_LITERAL, trecho))


def test_termo_do_site_em_dia_com_o_app():
    assert gerar_termo_site.main(["--verificar"]) == 0
    versao = re.search(r"const kLgpdTermsVersion\s*=\s*'([^']+)'", DART_TERMO.read_text(encoding="utf-8")).group(1)
    assert f'"versao": "{versao}"' in TERMO_JS.read_text(encoding="utf-8")


def test_texto_de_pontuacao_igual_ao_do_app():
    dart = re.search(r"const scoringNotice\s*=(.*?);", DART_REFERENCIAS.read_text(encoding="utf-8"), re.S).group(1)
    js = re.search(r"var TEXTO_PONTUACAO\s*=(.*?);", JS_RESPONDER.read_text(encoding="utf-8"), re.S).group(1)
    assert _literais_juntos(js) == _literais_juntos(dart)


# ---------------------------------------------------------------- SDK, CSP e página


def test_sdk_firebase_e_o_do_formulario():
    js = JS_RESPONDER.read_text(encoding="utf-8")
    versao = re.search(r"VERSAO_SDK = '([^']+)'", js).group(1)
    assert versao == "13.3.0"
    assert "https://www.gstatic.com/firebasejs/' + VERSAO_SDK" in js
    assert "firebase-firestore.js" in js and "firebase-app.js" in js


def test_csp_do_formulario_libera_so_o_necessario():
    csp = gerar_pages._CSP_RESPONDER
    assert "script-src 'self' https://www.gstatic.com" in csp
    assert "connect-src 'self' https://*.googleapis.com" in csp
    assert "unsafe-eval" not in csp


def test_pagina_do_formulario_gerada_com_csp_e_caminhos_relativos(tmp_path):
    gerar_pages.gerar_responder(tmp_path)
    html = (tmp_path / "responder" / "index.html").read_text(encoding="utf-8")
    assert 'http-equiv="Content-Security-Policy"' in html
    assert not re.findall(r'(?:src|href)="/[^"/]', html)  # nenhum caminho absoluto (quebraria no Pages)
    assert '../assets/responder_logica.js' in html and '../assets/firebase_web.js' in html


def test_link_do_formulario_so_no_modo_estatico():
    txt = (FONTE / "publico.html").read_text(encoding="utf-8")
    estatico = gerar_pages.transformar_html(txt, None, gerar_pages.URL_PADRAO, "0")
    conectado = gerar_pages.transformar_html(txt, "https://respirar-amazonas.cloud", gerar_pages.URL_PADRAO, "0")
    assert 'href="responder/"' in estatico and "data-so-estatico" not in estatico
    assert "responder-link" not in conectado
