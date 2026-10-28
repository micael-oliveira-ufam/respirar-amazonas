#!/usr/bin/env python3
"""Baixa do servidor um RETRATO dos dados públicos e grava em docs/dados/ para o site do GitHub Pages.

Uso (onde o servidor estiver alcançável; depois faça commit e push de docs/):
  python3 tool/publicar_dados_pages.py                              # lê https://respirar-amazonas.cloud
  python3 tool/publicar_dados_pages.py --api http://127.0.0.1:8003  # servidor local
  git add docs && git commit -m "Atualiza o retrato dos dados" && git push origin main

Grava: painel-{1,7,30,90}.json, csv/*.csv e manifest.json (data/hora do retrato e lista de arquivos).
Tudo ou nada: se qualquer download falhar ou vier inválido, docs/dados/ não é alterada.
Privacidade: são os MESMOS dados agregados que a página pública do servidor já exibe (sem respostas
individuais), mas uma vez no Git ficam no histórico do repositório para sempre; confira as regras de
mínimo (MIN_RESPOSTAS_PUBLICAS / MIN_RESPOSTAS_CELULA no .env) antes de publicar.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parent.parent
API_PADRAO = "https://respirar-amazonas.cloud"
#: Devem coincidir com publico.PERIODOS e com a lista de baixar.js (teste em server/tests/test_publicar_dados_pages.py).
PERIODOS = (1, 7, 30, 90)
CONJUNTOS_POR_PERIODO = ("sintomas", "niveis", "serie_diaria", "bairros", "areas", "perfil_contexto")
CONJUNTOS_SEM_PERIODO = ("qualidade_ar",)


def buscar_http(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "RespirAR-Amazonas-publicar-dados"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status} em {url}")
        return r.read()


def publicar(api: str, saida: Path, buscar: Callable[[str], bytes] = buscar_http,
             agora: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc)) -> dict:
    api = api.rstrip("/")
    with tempfile.TemporaryDirectory(dir=saida.parent) as t:
        tmp = Path(t) / "dados"
        (tmp / "csv").mkdir(parents=True)
        for d in PERIODOS:
            corpo = buscar(f"{api}/publico/painel?dias={d}")
            dados = json.loads(corpo)
            if not isinstance(dados, dict) or "gerado_em" not in dados:
                raise RuntimeError(f"resposta inesperada em /publico/painel?dias={d}")
            (tmp / f"painel-{d}.json").write_bytes(corpo)
        csvs = []
        for c in CONJUNTOS_POR_PERIODO:
            for d in PERIODOS:
                nome = f"csv/{c}-{d}d.csv"
                corpo = buscar(f"{api}/publico/export.csv?conjunto={c}&dias={d}")
                if not corpo.strip():
                    raise RuntimeError(f"CSV vazio: {c} {d}d")
                (tmp / nome).write_bytes(corpo)
                csvs.append({"conjunto": c, "dias": d, "arquivo": nome})
        for c in CONJUNTOS_SEM_PERIODO:
            corpo = buscar(f"{api}/publico/export.csv?conjunto={c}")
            if not corpo.strip():
                raise RuntimeError(f"CSV vazio: {c}")
            (tmp / f"csv/{c}.csv").write_bytes(corpo)
            csvs.append({"conjunto": c, "dias": None, "arquivo": f"csv/{c}.csv"})
        manifesto = {"gerado_em": agora().isoformat(timespec="seconds"), "fonte": api, "periodos": list(PERIODOS), "csv": csvs}
        (tmp / "manifest.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if saida.exists():
            shutil.rmtree(saida)
        shutil.move(str(tmp), saida)
    return manifesto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=API_PADRAO)
    ap.add_argument("--saida", default=str(RAIZ / "docs" / "dados"))
    a = ap.parse_args(argv)
    try:
        m = publicar(a.api, Path(a.saida))
    except (RuntimeError, ValueError, urllib.error.URLError, OSError) as e:
        print(f"FALHOU: {e}\ndocs/dados/ NÃO foi alterada.", file=sys.stderr)
        return 1
    print(f"Retrato de {m['gerado_em']} gravado em {a.saida}: {len(m['periodos'])} períodos, {len(m['csv'])} CSV.")
    print("Agora: git add docs && git commit && git push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
