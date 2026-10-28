#!/usr/bin/env python3
"""Confere que firebase/firestore.rules e o app/servidor falam do MESMO formato de resposta.

Isto NÃO executa as regras (isso exige o emulador do Firebase); só impede que uma lista do app
(sintomas, contexto, perfil, níveis) mude sem a regra acompanhar, o que faria o Firestore recusar envios.
"""
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "server"))

REGRAS = (RAIZ / "firebase" / "firestore.rules").read_text(encoding="utf-8")


def lista_da_funcao(nome: str, depois_de: str) -> set[str]:
    trecho = REGRAS[REGRAS.index(f"function {nome}"):]
    trecho = trecho[trecho.index(depois_de):]
    return set(re.findall(r"'([a-z0-9_]+)'", trecho[: trecho.index("]")]))


class RegrasCoincidemComOApp(unittest.TestCase):
    def test_sintomas_do_app(self):
        dart = (RAIZ / "lib/logic/risk_assessment.dart").read_text(encoding="utf-8")
        ids = set(re.findall(r"SymptomItem\('([a-z0-9_]+)'", dart))
        self.assertGreaterEqual(len(ids), 1)
        self.assertEqual(ids, lista_da_funcao("sintomasValidos", "hasOnly(["))

    def test_contexto_do_servidor(self):
        from app.schemas import CONTEXTO_CAMPOS

        self.assertEqual(set(CONTEXTO_CAMPOS), lista_da_funcao("contextoValido", "hasOnly(["))

    def test_perfil_do_servidor(self):
        from app.schemas import Perfil

        self.assertEqual(set(Perfil.model_fields), lista_da_funcao("perfilValido", "hasOnly(["))

    def test_campos_raiz_do_servidor(self):
        from app.schemas import RespostaIn

        raiz = lista_da_funcao("respostaValida", "hasOnly([")
        self.assertEqual(raiz - {"recebido_em"}, set(RespostaIn.model_fields))

    def test_niveis_e_exposicoes_do_app(self):
        dart = (RAIZ / "lib/logic/risk_assessment.dart").read_text(encoding="utf-8")
        exp = re.search(r"enum Exposure \{([^}]*)\}", dart).group(1)
        for nome in re.findall(r"[a-z0-9]+", exp):
            self.assertIn(f"'{nome}'", REGRAS)
        for nivel in ("low", "moderate", "high", "emergency"):
            self.assertIn(f"'{nivel}'", REGRAS)

    def test_app_nunca_le_nem_altera(self):
        self.assertIn("allow read, update, delete: if false;", REGRAS)
        self.assertIn("allow read, write: if false;", REGRAS)


if __name__ == "__main__":
    unittest.main()
