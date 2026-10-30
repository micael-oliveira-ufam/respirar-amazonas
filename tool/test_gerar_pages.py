"""Testa tool/gerar_pages.py: site estático do GitHub Pages (pasta docs/)."""

import filecmp
import importlib.util
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("gerar_pages", RAIZ / "tool" / "gerar_pages.py")
gp = importlib.util.module_from_spec(spec)
sys.modules["gerar_pages"] = gp
spec.loader.exec_module(gp)

API = "https://respirar-amazonas.cloud"


def _gerar(tmp_path, api=API):  # api=None: modo estático
    saida = tmp_path / "site"
    build = gp.gerar(saida, api, "https://usuario.github.io/repo")
    return saida, build


def test_caminhos_relativos_no_modo_conectado(tmp_path):
    saida, _ = _gerar(tmp_path)
    html = (saida / "index.html").read_text(encoding="utf-8")
    assert not re.findall(r'(?:src|href)="/[^"/]', html)          # nada absoluto: o Pages usa /repo/ como base
    assert 'src="assets/config.js' in html and 'href="vendor/leaflet/leaflet.css"' in html
    assert f'href="{API}/publico/painel?dias=30"' in html
    assert "{{" not in html                                       # todos os marcadores foram trocados
    assert 'href="https://usuario.github.io/repo/"' in html       # canonical no endereço do Pages
    for p in ("assets/publico.js", "assets/ar.js", "assets/baixar.js", "assets/amazonia.js", "assets/mapas.js",
              "assets/atualizar.js", "vendor/leaflet/leaflet.js", "vendor/leaflet-heat/leaflet-heat.js",
              "favicon.ico", ".nojekyll", "404.html", "versao.json"):
        assert (saida / p).is_file(), p
    assert not (saida / "assets" / "publico.html").exists()


def test_config_aponta_para_a_api_e_csp_libera_so_ela(tmp_path):
    saida, _ = _gerar(tmp_path)
    assert "window.RESPIRAR_MODO = 'conectado';" in (saida / "assets" / "config.js").read_text(encoding="utf-8")
    assert not (saida / "assets" / "municipios_am.json").exists()
    assert f"window.RESPIRAR_API = '{API}';" in (saida / "assets" / "config.js").read_text(encoding="utf-8")
    html = (saida / "index.html").read_text(encoding="utf-8")
    meta = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1)
    assert f"connect-src 'self' {API}" in meta and "script-src 'self';" in meta
    assert "unsafe-eval" not in meta and "script-src 'self' 'unsafe" not in meta


def test_modo_estatico_nao_depende_do_servidor(tmp_path):
    saida, _ = _gerar(tmp_path, api=None)
    html = (saida / "index.html").read_text(encoding="utf-8")
    cfg = (saida / "assets" / "config.js").read_text(encoding="utf-8")
    assert "window.RESPIRAR_MODO = 'estatico';" in cfg and "window.RESPIRAR_API = '';" in cfg
    assert f"window.RESPIRAR_APK_URL = '{gp.APK_URL_PADRAO}';" in cfg
    assert gp.APK_URL_PADRAO == "https://github.com/micael-oliveira-ufam/respirar-amazonas/releases/download/v1.22.2/RespirAR-Amazonas-v1.22.2.apk"
    assert "respirar-amazonas.cloud" not in html + cfg                 # nenhum endereço do servidor
    assert 'href="dados/painel-30.json"' in html and 'src="assets/ar_modelo.js' in html
    meta = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', html).group(1)
    assert "connect-src 'self' https://air-quality-api.open-meteo.com;" in meta
    assert "respirar-amazonas.cloud" not in meta
    for p in ("assets/municipios_am.json", "assets/qr-app.svg", "assets/Manual-Instalacao-RespirAR-Amazonas.pdf", "assets/ar_modelo.js"):
        assert (saida / p).is_file(), p
    import json
    munis = json.loads((saida / "assets" / "municipios_am.json").read_text(encoding="utf-8"))
    assert len(munis) == 62 and {"codigo", "nome", "lat", "lon"} == set(munis[0])
    assert (saida / "assets" / "qr-app.svg").read_text(encoding="utf-8").lstrip().startswith(("<?xml", "<svg"))
    assert json.loads((saida / "versao.json").read_text())["versao"] == (RAIZ / "VERSION").read_text().strip()


def test_regerar_preserva_os_dados_publicados(tmp_path):
    saida, _ = _gerar(tmp_path, api=None)
    (saida / "dados").mkdir()
    (saida / "dados" / "manifest.json").write_text("{}")
    gp.gerar(saida, None, "https://usuario.github.io/repo")
    assert (saida / "dados" / "manifest.json").read_text() == "{}"
    assert not list(tmp_path.glob("*.tmp"))


def test_saida_deterministica(tmp_path):
    a, ba = _gerar(tmp_path / "a", api=None)
    b, bb = _gerar(tmp_path / "b", api=None)
    assert ba == bb
    cmp = filecmp.dircmp(a, b)
    assert not cmp.diff_files and not cmp.left_only and not cmp.right_only


@pytest.mark.parametrize("ruim", ["ftp://x.org", "https://x.org/caminho", "x.org", "https://x.org/?a=1", "https://x y.org", ""])
def test_api_invalida_e_recusada(ruim):
    with pytest.raises(SystemExit):
        gp.origem(ruim)


def test_docs_publicado_esta_atualizado():
    """docs/ é o que o GitHub Pages serve. Se este teste falhar: python3 tool/gerar_pages.py"""
    docs = RAIZ / "docs"
    assert docs.is_dir(), "docs/ não existe: rode python3 tool/gerar_pages.py"
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        gp.gerar(Path(t) / "x", None, gp.URL_PADRAO)
        novo = Path(t) / "x"
        arquivos = sorted(p.relative_to(novo) for p in novo.rglob("*") if p.is_file())
        publicados = sorted(p.relative_to(docs) for p in docs.rglob("*") if p.is_file() and p.relative_to(docs).parts[0] != "dados")
        assert arquivos == publicados
        defasados = [str(a) for a in arquivos if (novo / a).read_bytes() != (docs / a).read_bytes()]
        assert not defasados, f"docs/ desatualizado ({defasados[:3]}...): rode python3 tool/gerar_pages.py"


@pytest.mark.parametrize("ruim", ["http://x.org/a.apk", "https://x.org/a'b.apk", "https://x.org/a b.apk", "ftp://x.org/a", "https://", "x"])
def test_apk_url_invalida_e_recusada(ruim):
    with pytest.raises(SystemExit):
        gp.validar_apk_url(ruim)


def test_apk_url_personalizada_vai_para_o_config_e_o_qr(tmp_path):
    saida = tmp_path / "s"
    nova = "https://github.com/u/r/releases/download/v1.21.0/RespirAR-Amazonas-v1.21.0.apk"
    gp.gerar(saida, None, "https://u.github.io/r", gp.validar_apk_url(nova))
    assert nova in (saida / "assets" / "config.js").read_text(encoding="utf-8")
    outro = tmp_path / "o"
    gp.gerar(outro, None, "https://u.github.io/r")
    assert (saida / "assets" / "qr-app.svg").read_bytes() != (outro / "assets" / "qr-app.svg").read_bytes()  # QR muda com o endereço


def test_endereco_do_site_no_app_e_o_mesmo_do_gerador():
    """O cartão 'Plataforma online' do app (Sobre) deve abrir o mesmo site que o gerador publica."""
    import re

    dart = (RAIZ / "lib/widgets/platform_card.dart").read_text(encoding="utf-8")
    no_app = re.search(r"kSitePublicoUrl = '([^']+)'", dart).group(1)
    assert no_app.rstrip("/") == gp.URL_PADRAO.rstrip("/")
