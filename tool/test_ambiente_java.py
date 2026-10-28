"""Testa a localização do JDK em tool/_ambiente.sh (layouts do macOS e do Linux simulados em pasta temporária)."""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

JAVA_OK = '#!/bin/sh\necho "openjdk version \\"17.0.9\\"" >&2\nexit 0\n'
JAVA_FALHA = '#!/bin/sh\necho "The operation couldn\'t be completed. Unable to locate a Java Runtime." >&2\nexit 1\n'


def _jdk(base: Path, ok=True) -> Path:
    (base / "bin").mkdir(parents=True)
    j = base / "bin" / "java"
    j.write_text(JAVA_OK if ok else JAVA_FALHA)
    j.chmod(0o755)
    return base


def _rodar(raiz: Path, corpo: str, uname="Darwin", java_no_path=None):
    bin_ = raiz / "binfalso"
    bin_.mkdir(exist_ok=True)
    u = bin_ / "uname"
    u.write_text(f'#!/bin/sh\necho {uname}\n')
    u.chmod(0o755)
    if java_no_path:  # simula o /usr/bin/java do macOS (atalho que falha) no PATH
        j = bin_ / "java"
        j.write_text(java_no_path)
        j.chmod(0o755)
    env = {"PATH": f"{bin_}:/usr/bin:/bin", "HOME": str(raiz / "home"), "AMBIENTE_RAIZ": str(raiz), "URL_SERVIDOR_PADRAO": "x"}
    r = subprocess.run(["bash", "-c", f'source "{RAIZ}/tool/_ambiente.sh"; {corpo}'], env=env, capture_output=True, text=True)
    return r


def test_acha_openjdk_17_do_homebrew_no_mac_apple_silicon(tmp_path):
    jdk = _jdk(tmp_path / "opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home")
    r = _rodar(tmp_path, 'localizar_ambiente; echo "JH=$JAVA_HOME"; exigir_java && echo PRONTO', java_no_path=JAVA_FALHA)
    assert f"JH={jdk}" in r.stdout and "PRONTO" in r.stdout, r.stdout + r.stderr


def test_acha_o_jdk_do_android_studio(tmp_path):
    jdk = _jdk(tmp_path / "Applications/Android Studio.app/Contents/jbr/Contents/Home")
    r = _rodar(tmp_path, 'localizar_ambiente; echo "JH=$JAVA_HOME"; exigir_java && echo PRONTO', java_no_path=JAVA_FALHA)
    assert f"JH={jdk}" in r.stdout and "PRONTO" in r.stdout, r.stdout + r.stderr


def test_acha_jdk_pkg_em_biblioteca_do_usuario(tmp_path):
    jdk = _jdk(tmp_path / "home/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home")
    r = _rodar(tmp_path, 'localizar_ambiente; echo "JH=$JAVA_HOME"', java_no_path=JAVA_FALHA)
    assert f"JH={jdk}" in r.stdout


def test_acha_jdk_17_no_linux(tmp_path):
    jdk = _jdk(tmp_path / "usr/lib/jvm/java-17-openjdk-amd64")
    r = _rodar(tmp_path, 'localizar_ambiente; echo "JH=$JAVA_HOME"', uname="Linux")
    assert f"JH={jdk}" in r.stdout


def test_atalho_do_mac_sem_jdk_falha_com_instrucao_clara(tmp_path):
    r = _rodar(tmp_path, 'localizar_ambiente; exigir_java', java_no_path=JAVA_FALHA)
    assert r.returncode == 1
    assert "brew install openjdk@17" in r.stdout and "Unable to locate" in r.stdout


def test_prefere_17_ao_21_e_ignora_jdk_quebrado(tmp_path):
    _jdk(tmp_path / "opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home", ok=False)   # quebrado
    j21 = _jdk(tmp_path / "opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home")
    r = _rodar(tmp_path, 'localizar_ambiente; echo "JH=$JAVA_HOME"', java_no_path=JAVA_FALHA)
    assert f"JH={j21}" in r.stdout


def test_java_home_existente_e_valido_nao_e_trocado(tmp_path):
    meu = _jdk(tmp_path / "meu-jdk")
    _jdk(tmp_path / "opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home")
    r = _rodar(tmp_path, f'export JAVA_HOME="{meu}"; localizar_ambiente; echo "JH=$JAVA_HOME"')
    assert f"JH={meu}" in r.stdout
