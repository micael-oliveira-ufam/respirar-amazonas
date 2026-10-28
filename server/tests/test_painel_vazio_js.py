"""static_publico/painel_vazio.js (site estático sem retrato) deve igualar publico.montar() de um banco vazio."""

import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app import publico
from app.config import Settings
from app.db import make_engine, make_session_factory
from app.models import Base

JS = Path(__file__).resolve().parents[1] / "app" / "static_publico" / "painel_vazio.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js não instalado")


def _js(dias):
    r = subprocess.run(["node", "-e", "require(process.argv[1]);process.stdout.write(JSON.stringify(globalThis.RespirarPainelVazio(Number(process.argv[2]))))", str(JS), str(dias)],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


@pytest.mark.parametrize("dias", publico.PERIODOS)
def test_igual_ao_painel_do_servidor_sem_respostas(dias):
    eng = make_engine("sqlite://")
    Base.metadata.create_all(eng)
    st = Settings(database_url="sqlite://", min_respostas_publicas=0, min_respostas_celula=1, geocoder_ativo=False)
    with make_session_factory(eng)() as s:
        py = publico.montar(s, st, dias, dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc))
    js = _js(dias)
    assert js.pop("vazio") is True            # marcas só do site estático
    assert js.pop("gerado_em") is None and py.pop("gerado_em")
    assert js == py
