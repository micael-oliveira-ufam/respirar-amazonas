#!/usr/bin/env python3
"""Gera server/app/static_publico/responder_termo.js a partir de lib/data/lgpd_terms.dart.

Motivo: o termo de consentimento tem de ser EXATAMENTE o do app (mesma versão, mesmo texto).
Copiar à mão abriria divergência; por isso o site lê o arquivo Dart e grava o JavaScript.

Uso (na raiz do repositório):
    python3 tool/gerar_termo_site.py          # grava o arquivo
    python3 tool/gerar_termo_site.py --verificar   # falha se o arquivo estiver desatualizado

Limites conhecidos: lê só strings entre aspas simples, com os escapes \\n, \\t, \\', \\\\ e a
interpolação $kLgpdTermsVersion. Qualquer outra construção faz o script parar com erro (não
inventa texto).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "lib" / "data" / "lgpd_terms.dart"
DESTINO = RAIZ / "server" / "app" / "static_publico" / "responder_termo.js"

# Um "RUN" = uma ou mais strings Dart vizinhas (concatenação implícita).
_LITERAL = r"'(?:[^'\\\n]|\\.)*'"
_RUN = rf"(?:{_LITERAL}\s*)+"


def _sem_comentarios(texto: str) -> str:
    return re.sub(r"//[^\n]*", "", texto)


def _desescapar(bruto: str, versao: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(bruto):
        c = bruto[i]
        if c == "\\":
            prox = bruto[i + 1]
            mapa = {"n": "\n", "t": "\t", "'": "'", "\\": "\\", "$": "$"}
            if prox not in mapa:
                raise SystemExit(f"Escape Dart não suportado no termo: \\{prox}")
            out.append(mapa[prox])
            i += 2
        elif c == "$":
            m = re.match(r"\$kLgpdTermsVersion\b", bruto[i:])
            if not m:
                raise SystemExit(f"Interpolação Dart não suportada no termo: {bruto[i:i+30]!r}")
            out.append(versao)
            i += m.end()
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _juntar(run: str, versao: str) -> str:
    partes = re.findall(_LITERAL, run)
    return "".join(_desescapar(p[1:-1], versao) for p in partes)


def extrair(texto_dart: str) -> dict:
    texto = _sem_comentarios(texto_dart)
    m = re.search(r"const\s+kLgpdTermsVersion\s*=\s*'([^']+)'\s*;", texto)
    if not m:
        raise SystemExit("kLgpdTermsVersion não encontrado em lgpd_terms.dart")
    versao = m.group(1)

    def _unico(padrao: str, nome: str) -> str:
        achados = re.findall(padrao, texto, flags=re.S)
        if len(achados) != 1:
            raise SystemExit(f"{nome}: esperado 1 ocorrência, achei {len(achados)}")
        return _juntar(achados[0], versao)

    resumo = _unico(rf"const\s+kLgpdSummary\s*=\s*({_RUN})\s*;", "kLgpdSummary")
    aceite = _unico(rf"const\s+kLgpdAcceptLabel\s*=\s*({_RUN})\s*;", "kLgpdAcceptLabel")
    caixa = _unico(rf"const\s+kLgpdCheckboxLabel\s*=\s*({_RUN})\s*;", "kLgpdCheckboxLabel")

    bloco = re.search(r"const\s+kLgpdSections\s*=\s*<TermsSection>\s*\[(.*?)\n\];", texto, flags=re.S)
    if not bloco:
        raise SystemExit("kLgpdSections não encontrado")
    secoes = []
    for sm in re.finditer(rf"TermsSection\(\s*({_RUN})\s*,\s*\[(.*?)\]\s*\)\s*,", bloco.group(1) + ",", flags=re.S):
        titulo = _juntar(sm.group(1), versao)
        paragrafos = [_juntar(p, versao) for p in re.findall(_RUN, sm.group(2))]
        if not paragrafos:
            raise SystemExit(f"Seção sem parágrafos: {titulo}")
        secoes.append({"titulo": titulo, "paragrafos": paragrafos})
    if not secoes:
        raise SystemExit("Nenhuma seção de termo encontrada")
    return {
        "versao": versao,
        "resumo": resumo,
        "secoes": secoes,
        "rotuloAceite": aceite,
        "rotuloCaixa": caixa,
    }


def gerar(texto_dart: str) -> str:
    dados = extrair(texto_dart)
    corpo = json.dumps(dados, ensure_ascii=False, indent=2)
    return (
        "/* GERADO por tool/gerar_termo_site.py a partir de lib/data/lgpd_terms.dart. Não editar à mão. */\n"
        f"window.RESPIRAR_TERMO = {corpo};\n"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--verificar", action="store_true", help="não grava; falha se estiver desatualizado")
    args = ap.parse_args(argv)
    novo = gerar(ORIGEM.read_text(encoding="utf-8"))
    if args.verificar:
        atual = DESTINO.read_text(encoding="utf-8") if DESTINO.exists() else ""
        if atual != novo:
            print("responder_termo.js está desatualizado: rode python3 tool/gerar_termo_site.py", file=sys.stderr)
            return 1
        print("responder_termo.js em dia.")
        return 0
    DESTINO.write_text(novo, encoding="utf-8")
    print(f"Gravado {DESTINO.relative_to(RAIZ)} (versão do termo {json.loads(novo.split('= ', 1)[1].rsplit(';', 1)[0])['versao']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
