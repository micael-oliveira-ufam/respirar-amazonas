#!/usr/bin/env python3
"""Gera o RETRATO público (docs/dados/) a partir das respostas guardadas no Firestore.

Fluxo (na sua máquina; depois faça commit e push de docs/):
  pip install google-cloud-firestore httpx -r server/requirements.txt     # uma vez
  python3 tool/publicar_dados_firestore.py                                # usa firebase/chave-servico.json
  python3 tool/publicar_dados_firestore.py --chave /caminho/chave.json --saida docs/dados
  git add docs && git commit -m "Atualiza o retrato dos dados" && git push origin main

Como funciona (para ser reproduzível):
 1. Lê TODOS os documentos de `respostas` com a chave de conta de serviço (que ignora as regras do
    Firestore; a chave é secreta e fica FORA do Git, ver .gitignore).
 2. Carrega cada documento num banco SQLite temporário passando pela MESMA validação e gravação do
    servidor (POST /respostas em memória). Documento inválido é contado e IGNORADO, nunca publicado.
 3. Resolve o bairro das áreas de Manaus: primeiro pelo cache firebase/cache-bairros.json (versionado), só
    o que falta vai ao Nominatim (1 consulta/s; pule tudo com --sem-bairros).
 4. Gera os mesmos arquivos de tool/publicar_dados_pages.py (painel-N.json, csv/*.csv, manifest.json)
    com as MESMAS regras de agregação do painel do servidor (app/publico.py, app/exportacao.py).
Tudo ou nada: se algo falhar, docs/dados/ NÃO é alterada. Nenhuma resposta individual é publicada,
mas o Git guarda o histórico para sempre: confira as regras de mínimo (MIN_RESPOSTAS_PUBLICAS /
MIN_RESPOSTAS_CELULA no ambiente; padrões 0 e 1) antes de publicar.
Também precisa de internet para a qualidade do ar (Open-Meteo), como o servidor.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

if sys.version_info < (3, 10):  # fastapi==0.146.0 (server/requirements.txt) exige Python >= 3.10
    sys.exit("Este script precisa de Python 3.10 ou mais novo (o seu é %d.%d). Veja README, seção "
             "'Respostas no Firebase': crie um ambiente virtual com python3.12." % sys.version_info[:2])

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "server"))

CHAVE_PADRAO = RAIZ / "firebase" / "chave-servico.json"
CACHE_BAIRROS_PADRAO = RAIZ / "firebase" / "cache-bairros.json"
COLECAO = "respostas"
#: Campos que o app não envia no formato do servidor (são metadados do Firestore).
CAMPOS_SO_DO_FIRESTORE = ("recebido_em",)


def _carregar_pdp():
    spec = importlib.util.spec_from_file_location("publicar_dados_pages", RAIZ / "tool" / "publicar_dados_pages.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def ler_firestore(chave: Path) -> list[tuple[str, dict[str, Any]]]:
    """Lê todos os documentos de `respostas`. Importa a biblioteca só aqui (dependência opcional)."""
    try:
        from google.cloud import firestore  # type: ignore
        from google.oauth2 import service_account  # type: ignore
    except ImportError as e:  # pragma: no cover - depende do ambiente do usuário
        raise RuntimeError("Falta a biblioteca: pip install google-cloud-firestore") from e
    cred = service_account.Credentials.from_service_account_file(str(chave))
    cliente = firestore.Client(project=cred.project_id, credentials=cred)
    return [(d.id, d.to_dict() or {}) for d in cliente.collection(COLECAO).stream()], cred.project_id


def para_payload(doc: dict[str, Any]) -> dict[str, Any]:
    """Documento do Firestore -> JSON do POST /respostas (tira metadados; datas viram texto ISO)."""
    out = {}
    for k, v in doc.items():
        if k in CAMPOS_SO_DO_FIRESTORE:
            continue
        out[k] = v.isoformat() if isinstance(v, (dt.datetime, dt.date)) else v
    return out


def carregar_no_banco(client, docs: Iterable[tuple[str, dict[str, Any]]], session_factory) -> dict[str, Any]:
    """Envia cada documento ao app em memória. Devolve contagens e a lista de recusados (id + motivo).

    O painel conta o período por `criado_em` (momento em que o servidor recebeu). Aqui o "servidor" é
    este script, que roda agora; por isso `criado_em` é trocado pelo `recebido_em` (hora do Firebase),
    senão toda resposta antiga pareceria ter acabado de chegar e os filtros de 1/7/30/90 dias errariam.
    """
    import uuid

    from sqlalchemy import update

    from app.models import Resposta

    novos = duplicados = 0
    recusados: list[tuple[str, str]] = []
    recebidos: dict[str, dt.datetime] = {}
    for doc_id, doc in docs:
        payload = para_payload(doc)
        recebido = doc.get("recebido_em")
        if payload.get("submission_id") != doc_id:
            recusados.append((doc_id, "submission_id diferente do id do documento"))
            continue
        if not isinstance(recebido, dt.datetime) or recebido.tzinfo is None:
            recusados.append((doc_id, "sem recebido_em (hora do Firebase) válido"))
            continue
        r = client.post("/respostas", json=payload)
        if r.status_code == 201:
            novos += 1
            recebidos[doc_id] = recebido
        elif r.status_code == 200:
            duplicados += 1
        else:
            recusados.append((doc_id, f"HTTP {r.status_code}: {r.text[:120]}"))
    with session_factory() as session:
        for doc_id, recebido in recebidos.items():
            session.execute(update(Resposta).where(Resposta.submission_id == uuid.UUID(doc_id)).values(criado_em=recebido))
        session.commit()
    return {"novos": novos, "duplicados": duplicados, "recusados": recusados}


def carregar_cache_bairros(session_factory, caminho: Path | None) -> int:
    """Põe no banco temporário os bairros já descobertos (arquivo versionado), poupando o Nominatim."""
    import json
    from decimal import Decimal

    from app.models import CelulaBairro

    if caminho is None or not caminho.exists():
        return 0
    itens = json.loads(caminho.read_text(encoding="utf-8"))
    with session_factory() as session:
        for i in itens:
            session.merge(CelulaBairro(lat=Decimal(str(i["lat"])), lon=Decimal(str(i["lon"])),
                                       bairro=i.get("bairro"), cidade=i.get("cidade")))
        session.commit()
    return len(itens)


def salvar_cache_bairros(session_factory, caminho: Path | None) -> int:
    """Grava todos os bairros conhecidos em ordem fixa (sem mudança = o Git não vê diferença)."""
    import json

    from sqlalchemy import select

    from app.models import CelulaBairro

    if caminho is None:
        return 0
    with session_factory() as session:
        linhas = session.execute(select(CelulaBairro.lat, CelulaBairro.lon, CelulaBairro.bairro, CelulaBairro.cidade)).all()
    itens = sorted(({"lat": float(a), "lon": float(b), "bairro": c, "cidade": d} for a, b, c, d in linhas),
                   key=lambda x: (x["lat"], x["lon"]))
    texto = json.dumps(itens, ensure_ascii=False, indent=1) + "\n"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not caminho.exists() or caminho.read_text(encoding="utf-8") != texto:
        caminho.write_text(texto, encoding="utf-8")
    return len(itens)


def gerar(documentos: list[tuple[str, dict[str, Any]]], saida: Path, projeto: str, *, geocoder=None,
          qualidade_ar=None, resolver_bairros: bool = True, cache_bairros: Path | None = None, agora: Callable[[], dt.datetime] | None = None) -> dict:
    from fastapi.testclient import TestClient

    from app import bairros as bairros_mod
    from app.config import Settings
    from app.db import make_engine
    from app.main import create_app
    from app.models import Base

    settings = dataclasses.replace(Settings.from_env(), database_url="sqlite://", rate_limit_per_min=0,
                                   geocoder_ativo=False, admin_token="")
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    app = create_app(settings, engine, geocoder=None, qualidade_ar=qualidade_ar) if qualidade_ar else create_app(settings, engine)
    with TestClient(app) as client:
        resumo = carregar_no_banco(client, documentos, app.state.session_factory)
        if resolver_bairros:
            resumo["bairros_do_cache"] = carregar_cache_bairros(app.state.session_factory, cache_bairros)
            geo = geocoder or bairros_mod.nominatim(settings, "firestore")
            resumo["bairros_resolvidos"] = bairros_mod.resolver_pendentes(app.state.session_factory, geo, limite=500)
            resumo["bairros_no_cache"] = salvar_cache_bairros(app.state.session_factory, cache_bairros)

        def buscar(url: str) -> bytes:
            caminho = url.split("//", 1)[1].split("/", 1)[1]  # firestore://projeto/publico/... -> publico/...
            r = client.get("/" + caminho)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code} em /{caminho}")
            return r.content

        pdp = _carregar_pdp()
        kwargs = {"agora": agora} if agora else {}
        manifesto = pdp.publicar(f"firestore://{projeto}", saida, buscar, **kwargs)
    manifesto["_resumo"] = resumo
    return manifesto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chave", default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or str(CHAVE_PADRAO),
                    help="JSON da conta de serviço (padrão: firebase/chave-servico.json)")
    ap.add_argument("--saida", default=str(RAIZ / "docs" / "dados"))
    ap.add_argument("--cache-bairros", default=str(CACHE_BAIRROS_PADRAO),
                    help="arquivo com bairros já descobertos (versionado; evita repetir consultas ao Nominatim)")
    ap.add_argument("--sem-bairros", action="store_true", help="não consulta o Nominatim (ranking de bairros fica vazio)")
    a = ap.parse_args(argv)
    chave = Path(a.chave)
    if not chave.exists():
        print(f"FALHOU: chave de conta de serviço não encontrada em {chave}.\n"
              "Baixe em Firebase > Configurações do projeto > Contas de serviço > Gerar nova chave privada,\n"
              "salve como firebase/chave-servico.json (já ignorado pelo Git) e rode de novo.", file=sys.stderr)
        return 1
    try:
        docs, projeto = ler_firestore(chave)
        m = gerar(docs, Path(a.saida), projeto, resolver_bairros=not a.sem_bairros, cache_bairros=Path(a.cache_bairros))
    except Exception as e:  # noqa: BLE001 - qualquer falha: nada é alterado
        print(f"FALHOU: {type(e).__name__}: {e}\ndocs/dados/ NÃO foi alterada.", file=sys.stderr)
        return 1
    r = m["_resumo"]
    print(f"Lidos {len(docs)} documentos de '{COLECAO}': {r['novos']} novos, {r['duplicados']} duplicados, "
          f"{len(r['recusados'])} recusados pela validação.")
    for doc_id, motivo in r["recusados"][:20]:
        print(f"  recusado {doc_id}: {motivo}")
    print(f"Retrato de {m['gerado_em']} gravado em {a.saida}: {len(m['periodos'])} períodos, {len(m['csv'])} CSV.")
    print("Agora: git add docs && git commit && git push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
