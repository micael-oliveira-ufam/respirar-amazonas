"""Confere o workflow .github/workflows/atualizar-dados.yml (estrutura; NÃO o executa: isso só o GitHub faz)."""
import re
import unittest
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
TEXTO = (RAIZ / ".github" / "workflows" / "atualizar-dados.yml").read_text(encoding="utf-8")
WF = yaml.safe_load(TEXTO)
GATILHOS = WF.get("on", WF.get(True))  # PyYAML lê a chave `on` como True


class Workflow(unittest.TestCase):
    def test_agenda_a_cada_6_horas_e_permite_rodar_a_mao(self):
        self.assertEqual([c["cron"] for c in GATILHOS["schedule"]], ["17 */6 * * *"])
        self.assertIn("workflow_dispatch", GATILHOS)

    def test_permissoes_minimas(self):
        self.assertEqual(WF["permissions"], {"contents": "write", "pages": "write"})

    def test_uma_execucao_por_vez(self):
        self.assertFalse(WF["concurrency"]["cancel-in-progress"])

    def test_chave_vem_do_segredo_e_nunca_e_impressa(self):
        self.assertIn("secrets.FIREBASE_SERVICE_ACCOUNT", TEXTO)
        for linha in TEXTO.splitlines():
            if re.match(r"\s*(echo|cat|set -x)\b", linha):
                self.assertNotRegex(linha, r"\$\{?FIREBASE_SERVICE_ACCOUNT")  # o VALOR nunca vai a echo/cat
            self.assertNotIn("set -x", linha)
        self.assertIn("rm -f", TEXTO)

    def test_so_commita_o_que_e_publico_e_so_se_mudou(self):
        self.assertIn("git add docs/dados firebase/cache-bairros.json", TEXTO)
        self.assertIn("git diff --cached --quiet", TEXTO)
        self.assertNotIn("chave-servico.json docs", TEXTO)

    def test_nao_compila_apk_nem_sobe_apk(self):
        self.assertNotRegex(TEXTO.lower(), r"flutter|gerar_apk|\.apk|upload-artifact")


if __name__ == "__main__":
    unittest.main()
