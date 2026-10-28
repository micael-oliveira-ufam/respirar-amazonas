"""Testa tool/publicar_dados_firestore.py SEM Firebase real: documentos fictícios, geocoder e ar simulados."""

import csv
import datetime as dt
import importlib.util
import io
import json
import sys
import uuid
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "server"))
spec = importlib.util.spec_from_file_location("publicar_dados_firestore", RAIZ / "tool" / "publicar_dados_firestore.py")
pdf = importlib.util.module_from_spec(spec)
sys.modules["publicar_dados_firestore"] = pdf
spec.loader.exec_module(pdf)

from app import qualidade_ar as qar  # noqa: E402

AGORA = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)  # o painel conta períodos a partir de "agora" real
SINTOMAS = ["cough", "throat", "nose", "wheeze", "dyspnea", "eyes", "chest", "palpitation", "headache", "dizzy", "fatigue"]


def doc(dias_atras=0, **over):
    """Documento como o app grava (campos do POST) + recebido_em (hora do Firebase)."""
    sid = str(uuid.uuid4())
    recebido = AGORA - dt.timedelta(days=dias_atras)
    d = {
        "submission_id": sid,
        "registrado_em": recebido.isoformat(),
        "lat": -3.12, "lon": -60.02,
        "nivel": "moderate", "pontos": 9, "exposicao": "under1h",
        "perfil": {"idoso": False, "gestante": False, "crianca": False, "doenca_respiratoria": False, "doenca_cardiaca": False},
        "sintomas": {k: (2 if k == "cough" else 0) for k in SINTOMAS},
        "app_version": "1.21.0",
        "recebido_em": recebido,
    }
    d.update(over)
    return d["submission_id"], d


def servico_ar():
    def http_get(url, params=None, timeout=None, headers=None):
        class R:
            status_code = 200

            def json(self):
                return [{"current": {"us_aqi": 42, "pm2_5": 8.4, "pm10": 14.2, "time": "2026-10-27T11:00"}} for _ in range(62)]
        return R()
    return qar.QualidadeAr("http://x", 1800, http_get=http_get)


def geo(lat, lon):
    return {"bairro": "Centro", "cidade": "Manaus"}


def gerar(tmp_path, docs, **kw):
    saida = tmp_path / "docs" / "dados"
    saida.parent.mkdir(exist_ok=True)
    kw.setdefault("geocoder", geo)
    kw.setdefault("qualidade_ar", servico_ar())
    kw["agora"] = lambda: AGORA
    return pdf.gerar(docs, saida, "respirar-as", **kw), saida


def test_gera_os_mesmos_arquivos_do_fluxo_por_servidor(tmp_path):
    m, saida = gerar(tmp_path, [doc(), doc(1), doc(10)])
    for d in (1, 7, 30, 90):
        assert (saida / f"painel-{d}.json").is_file()
    assert len(m["csv"]) == 6 * 4 + 1
    assert m["fonte"] == "firestore://respirar-as"
    assert m["_resumo"]["novos"] == 3 and m["_resumo"]["recusados"] == []


def test_periodo_usa_a_hora_de_recebimento_do_firebase_e_nao_a_de_hoje(tmp_path):
    # 1 resposta de hoje, 1 de 5 dias atrás, 1 de 40 dias atrás
    m, saida = gerar(tmp_path, [doc(0), doc(5), doc(40)])
    totais = {d: json.loads((saida / f"painel-{d}.json").read_text())["total_respostas"] for d in (1, 7, 30, 90)}
    assert totais == {1: 1, 7: 2, 30: 2, 90: 3}


def test_resposta_invalida_e_recusada_e_nunca_publicada(tmp_path):
    ruim_id, ruim = doc(nivel="medium")  # nível fora da lista: o servidor devolve 422
    sem_hora_id, sem_hora = doc()
    del sem_hora["recebido_em"]
    outro_id, outro = doc()
    outro["submission_id"] = str(uuid.uuid4())  # id do documento diferente do conteúdo
    m, saida = gerar(tmp_path, [doc(), (ruim_id, ruim), (sem_hora_id, sem_hora), (outro_id, outro)])
    r = m["_resumo"]
    assert r["novos"] == 1 and len(r["recusados"]) == 3
    assert json.loads((saida / "painel-30.json").read_text())["total_respostas"] == 1


def test_campos_extras_sao_recusados_pela_validacao_do_servidor(tmp_path):
    i, d = doc()
    d["telefone"] = "9299999999"
    m, _ = gerar(tmp_path, [(i, d)])
    assert m["_resumo"]["novos"] == 0 and len(m["_resumo"]["recusados"]) == 1


def test_csv_nunca_traz_submission_id_nem_coordenada_exata(tmp_path):
    docs = [doc() for _ in range(3)]
    _, saida = gerar(tmp_path, docs)
    texto = "".join(p.read_text(encoding="utf-8") for p in (saida / "csv").glob("*.csv"))
    for sid, _d in docs:
        assert sid not in texto
    assert "-60.0217" not in texto


def test_bairro_vem_do_geocoder_e_pode_ser_pulado(tmp_path):
    docs = [doc() for _ in range(2)]
    _, saida = gerar(tmp_path, docs)
    linhas = list(csv.reader(io.StringIO((saida / "csv" / "bairros-30d.csv").read_text(encoding="utf-8"))))
    assert any("Centro" in ",".join(l) for l in linhas[1:])
    _, saida2 = gerar(tmp_path, docs, resolver_bairros=False)
    linhas2 = list(csv.reader(io.StringIO((saida2 / "csv" / "bairros-30d.csv").read_text(encoding="utf-8"))))
    assert len(linhas2) == 1  # só o cabeçalho


def test_sem_documentos_ainda_gera_o_retrato_vazio(tmp_path):
    m, saida = gerar(tmp_path, [])
    assert json.loads((saida / "painel-30.json").read_text())["total_respostas"] == 0
    assert m["_resumo"]["novos"] == 0


def test_falha_do_ar_nao_altera_o_que_ja_estava_publicado(tmp_path):
    saida = tmp_path / "docs" / "dados"
    saida.mkdir(parents=True)
    (saida / "manifest.json").write_text('{"antigo": true}')

    def http_get(*a, **k):
        import requests
        raise requests.ConnectionError("sem rede")
    with pytest.raises(RuntimeError):
        pdf.gerar([doc()], saida, "respirar-as", geocoder=geo, qualidade_ar=qar.QualidadeAr("http://x", 1, http_get=http_get))
    assert json.loads((saida / "manifest.json").read_text()) == {"antigo": True}


def test_chave_ausente_da_mensagem_clara(tmp_path, capsys):
    assert pdf.main(["--chave", str(tmp_path / "nao-existe.json"), "--saida", str(tmp_path / "x")]) == 1
    assert "chave de conta de serviço não encontrada" in capsys.readouterr().err
