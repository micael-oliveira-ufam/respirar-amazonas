#!/usr/bin/env python3
"""Aplica as permissões de plataforma exigidas pelo app, de forma idempotente.

Por que existe
--------------
O pacote não inclui as pastas android/ e ios/ (elas são geradas por
`flutter create`). Sem a permissão INTERNET no AndroidManifest.xml principal, um
build de *release* não acessa a rede: o INPE falha com "Failed host lookup", os
mapas não carregam. Sem ACCESS_FINE/COARSE_LOCATION, o Android nunca mostra o
pedido de GPS. Este script elimina a edição manual desses arquivos.

Uso (na raiz do projeto, depois de `flutter create --platforms=android,ios .`):

    python3 tool/apply_platform_config.py            # aplica
    python3 tool/apply_platform_config.py --check    # só verifica (código 1 se faltar algo)

Rodar duas vezes não duplica nada.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

APP_NAME = "RespirAR Amazonas"

MANIFEST = Path("android/app/src/main/AndroidManifest.xml")
PLIST = Path("ios/Runner/Info.plist")

ANDROID_PERMISSIONS = [
    "android.permission.INTERNET",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
]

DIAL_INTENT = (
    "        <intent>\n"
    '            <action android:name="android.intent.action.DIAL"/>\n'
    '            <data android:scheme="tel"/>\n'
    "        </intent>\n"
)

LOCATION_TEXT = (
    "Usamos sua localização para centralizar o mapa e, somente quando você "
    "decide compartilhar, para mapear áreas de risco de fumaça de forma anonimizada."
)


def patch_manifest(text: str) -> tuple[str, list[str]]:
    """Retorna (novo_texto, lista_do_que_foi_adicionado)."""
    added: list[str] = []

    # 1) Permissões, logo após a tag <manifest ...>.
    missing = [p for p in ANDROID_PERMISSIONS if f'android:name="{p}"' not in text]
    if missing:
        start = text.find("<manifest")
        if start == -1:
            raise ValueError("AndroidManifest.xml sem tag <manifest>.")
        end = text.find(">", start) + 1
        block = "".join(f'\n    <uses-permission android:name="{p}"/>' for p in missing)
        text = text[:end] + block + text[end:]
        added += missing

    # 1b) Nome exibido sob o ícone: "RespirAR Amazonas" (o template usa o nome do pacote, com "_").
    app_tag = re.search(r"<application\b[^>]*>", text, re.S)
    if app_tag is None:
        raise ValueError("AndroidManifest.xml sem tag <application>.")
    tag = app_tag.group(0)
    label = re.search(r'android:label="([^"]*)"', tag)
    if label is None:
        new_tag = tag.replace("<application", f'<application android:label="{APP_NAME}"', 1)
    elif label.group(1) != APP_NAME:
        new_tag = tag.replace(label.group(0), f'android:label="{APP_NAME}"', 1)
    else:
        new_tag = tag
    if new_tag != tag:
        text = text[: app_tag.start()] + new_tag + text[app_tag.end():]
        added.append(f"android:label={APP_NAME}")

    # 2) <queries> com a intenção DIAL (necessária para discar no Android 11+).
    if 'android.intent.action.DIAL' not in text:
        if "</queries>" in text:
            text = text.replace("</queries>", DIAL_INTENT + "    </queries>", 1)
        else:
            marker = "<application"
            idx = text.find(marker)
            if idx == -1:
                raise ValueError("AndroidManifest.xml sem tag <application>.")
            queries = "<queries>\n" + DIAL_INTENT + "    </queries>\n    "
            text = text[:idx] + queries + text[idx:]
        added.append("queries/DIAL")

    return text, added


DESUGAR_LIB = "com.android.tools:desugar_jdk_libs:2.1.4"


def patch_gradle(text: str, kts: bool) -> tuple[str, list[str]]:
    """Liga o "core library desugaring" exigido pelo flutter_local_notifications (alertas do app).

    Sem isto o build do APK falha ("requires core library desugaring"). Idempotente.
    """
    added: list[str] = []
    flag_on = "isCoreLibraryDesugaringEnabled" if kts else "coreLibraryDesugaringEnabled"
    if flag_on not in text:
        linha = "isCoreLibraryDesugaringEnabled = true" if kts else "coreLibraryDesugaringEnabled true"
        achou = re.search(r"compileOptions\s*\{", text)
        if achou is None:
            raise ValueError("build.gradle do app sem bloco compileOptions.")
        text = text[: achou.end()] + f"\n        {linha}" + text[achou.end():]
        added.append("coreLibraryDesugaringEnabled")
    if "coreLibraryDesugaring(" not in text and "coreLibraryDesugaring '" not in text:
        dep = f'coreLibraryDesugaring("{DESUGAR_LIB}")' if kts else f"coreLibraryDesugaring '{DESUGAR_LIB}'"
        achou = re.search(r"^dependencies\s*\{", text, re.M)
        if achou is not None:
            text = text[: achou.end()] + f"\n    {dep}" + text[achou.end():]
        else:
            text = text.rstrip("\n") + f"\n\ndependencies {{\n    {dep}\n}}\n"
        added.append("coreLibraryDesugaring dependency")
    return text, added


#: Plugin Gradle do Firebase (versão do console do Firebase do usuário em 27/10/2026; não testada aqui).
GOOGLE_SERVICES_VERSION = "4.5.0"
#: Onde o usuário guarda o arquivo baixado do console (FORA do Git: ver .gitignore).
GOOGLE_SERVICES_ORIGEM = Path("firebase/google-services.json")
GOOGLE_SERVICES_DESTINO = Path("android/app/google-services.json")


def patch_settings_gradle(text: str, kts: bool) -> tuple[str, list[str]]:
    """Declara o plugin google-services (sem aplicar) no bloco `plugins` de settings.gradle(.kts)."""
    if "com.google.gms.google-services" in text:
        return text, []
    achou = re.search(r"^plugins\s*\{", text, re.M)
    if achou is None:
        raise ValueError("settings.gradle sem bloco plugins (template de Flutter inesperado).")
    linha = (
        f'id("com.google.gms.google-services") version "{GOOGLE_SERVICES_VERSION}" apply false'
        if kts
        else f'id "com.google.gms.google-services" version "{GOOGLE_SERVICES_VERSION}" apply false'
    )
    return text[: achou.end()] + f"\n    {linha}" + text[achou.end():], ["google-services (settings)"]


def patch_app_gradle_firebase(text: str, kts: bool) -> tuple[str, list[str]]:
    """Aplica o plugin google-services no bloco `plugins` de android/app/build.gradle(.kts)."""
    if "com.google.gms.google-services" in text:
        return text, []
    achou = re.search(r"^plugins\s*\{", text, re.M)
    if achou is None:
        raise ValueError("build.gradle do app sem bloco plugins.")
    linha = 'id("com.google.gms.google-services")' if kts else 'id "com.google.gms.google-services"'
    return text[: achou.end()] + f"\n    {linha}" + text[achou.end():], ["google-services (app)"]



def patch_plist(text: str) -> tuple[str, list[str]]:
    added: list[str] = []
    entries = ""

    if "NSLocationWhenInUseUsageDescription" not in text:
        entries += (
            "\t<key>NSLocationWhenInUseUsageDescription</key>\n"
            f"\t<string>{LOCATION_TEXT}</string>\n"
        )
        added.append("NSLocationWhenInUseUsageDescription")

    if "LSApplicationQueriesSchemes" not in text:
        entries += (
            "\t<key>LSApplicationQueriesSchemes</key>\n"
            "\t<array>\n\t\t<string>tel</string>\n\t</array>\n"
        )
        added.append("LSApplicationQueriesSchemes")

    # Nome exibido sob o ícone (CFBundleDisplayName) e nome do pacote (CFBundleName).
    for key in ("CFBundleDisplayName", "CFBundleName"):
        pattern = re.compile(rf"(<key>{key}</key>\s*<string>)([^<]*)(</string>)")
        found = pattern.search(text)
        if found is None:
            entries += f"\t<key>{key}</key>\n\t<string>{APP_NAME}</string>\n"
            added.append(f"{key}={APP_NAME}")
        elif found.group(2) != APP_NAME:
            text = pattern.sub(lambda m: m.group(1) + APP_NAME + m.group(3), text, count=1)
            added.append(f"{key}={APP_NAME}")

    if entries:
        idx = text.rfind("</dict>")
        if idx == -1:
            raise ValueError("Info.plist sem </dict>.")
        text = text[:idx] + entries + text[idx:]
    return text, added


def process(path: Path, patcher, check_only: bool) -> list[str] | None:
    if not path.exists():
        print(f"[ausente] {path} (rode `flutter create --platforms=android,ios .` antes)")
        return None
    original = path.read_text(encoding="utf-8")
    patched, added = patcher(original)
    if added and not check_only:
        path.write_text(patched, encoding="utf-8")
    status = "faltava" if check_only else "adicionado"
    print(f"[{path}] " + (f"{status}: {', '.join(added)}" if added else "já estava correto"))
    return added


def configurar_firebase(root: Path, gradle_app: Path, check_only: bool) -> list[list[str] | None]:
    """Liga o Firebase no Android SE `firebase/google-services.json` existir; senão o app fica em modo local.

    O arquivo vem do console do Firebase e fica fora do Git. Sem ele, NADA do Firebase é aplicado
    (o plugin google-services quebraria o build sem o arquivo) e o APK sai em modo local.
    """
    origem = root / GOOGLE_SERVICES_ORIGEM
    if not origem.exists():
        print(f"[firebase] {GOOGLE_SERVICES_ORIGEM} ausente: o APK sai em MODO LOCAL (não envia respostas).")
        return []
    destino = root / GOOGLE_SERVICES_DESTINO
    copiado: list[str] = []
    if not destino.exists() or destino.read_bytes() != origem.read_bytes():
        copiado = ["google-services.json"]
        if not check_only:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(origem.read_bytes())
    print(f"[{GOOGLE_SERVICES_DESTINO}] " + (f"{'faltava' if check_only else 'copiado'}: google-services.json" if copiado else "já estava correto"))
    settings_kts = root / "android/settings.gradle.kts"
    settings = settings_kts if settings_kts.exists() else root / "android/settings.gradle"
    return [
        copiado,
        process(settings, lambda t: patch_settings_gradle(t, kts=settings.suffix == ".kts"), check_only),
        process(gradle_app, lambda t: patch_app_gradle_firebase(t, kts=gradle_app.suffix == ".kts"), check_only),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", help="raiz do projeto Flutter")
    parser.add_argument("--check", action="store_true", help="não altera; só verifica")
    args = parser.parse_args()

    root = Path(args.root)
    gradle_kts = root / "android/app/build.gradle.kts"
    gradle = gradle_kts if gradle_kts.exists() else root / "android/app/build.gradle"
    results = [
        process(root / MANIFEST, patch_manifest, args.check),
        process(gradle, lambda t: patch_gradle(t, kts=gradle.suffix == ".kts"), args.check),
        process(root / PLIST, patch_plist, args.check),
    ]
    results += configurar_firebase(root, gradle, args.check)
    if any(r is None for r in results):
        return 2
    if args.check and any(results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
