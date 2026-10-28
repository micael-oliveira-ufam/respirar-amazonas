#!/usr/bin/env bash
# Instala/confere o que o macOS precisa para compilar o app para iOS e abrir os emuladores.
#
# Uso: bash tool/instalar_requisitos_macos.sh
#
# O Xcode (App Store) não pode ser instalado por script: se faltar, o script avisa e para.
# Alguns passos pedem a senha do Mac (sudo). Nada é instalado sem aparecer na tela.
set -euo pipefail

[[ "$(uname -s)" == "Darwin" ]] || { echo "ERRO: este script é só para macOS."; exit 1; }

echo "== 1/7 Homebrew"
if ! command -v brew >/dev/null; then
  echo "Homebrew não encontrado. Instale pelo site oficial (https://brew.sh) e rode este script de novo."
  exit 1
fi
brew --version | head -1

echo "== 2/7 Flutter"
if ! command -v flutter >/dev/null; then
  brew install --cask flutter
fi
flutter --version | head -1

echo "== 3/7 Xcode"
if [[ ! -d /Applications/Xcode.app ]]; then
  echo "Xcode não encontrado em /Applications. Instale pela App Store (https://apps.apple.com/app/xcode/id497799835),"
  echo "abra uma vez para aceitar os termos e rode este script de novo."
  exit 1
fi
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
echo "Se pedir, aceite a licença: sudo xcodebuild -license accept"

echo "== 4/7 Runtime do simulador iOS (pode baixar alguns GB)"
if ! xcrun simctl list runtimes 2>/dev/null | grep -q "iOS"; then
  xcodebuild -downloadPlatform iOS
else
  echo "Já existe um runtime de iOS instalado."
fi

echo "== 5/7 CocoaPods"
if ! command -v pod >/dev/null; then
  brew install cocoapods
fi
pod --version

echo "== 6/7 Java (JDK 17, necessário para gerar o APK)"
# /usr/bin/java no macOS é só um atalho; o que vale é um JDK de verdade (tool/_ambiente.sh o encontra sozinho).
if ! /usr/libexec/java_home -v 17 >/dev/null 2>&1 && [[ ! -x "$(brew --prefix 2>/dev/null)/opt/openjdk@17/bin/java" ]]; then
  brew install openjdk@17
else
  echo "JDK 17 já instalado."
fi

echo "== 7/7 Conferência final"
flutter doctor -v
echo
echo "Se o 'flutter doctor' mostrar [!] ou [✗], corrija o item indicado antes de continuar."
