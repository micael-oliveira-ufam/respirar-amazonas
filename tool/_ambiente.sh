#!/usr/bin/env bash
# Localiza Flutter, Java e Android SDK instalados em lugares comuns e os coloca no PATH
# desta execução. Não execute diretamente: use `source tool/_ambiente.sh`.

localizar_ambiente() {
  if ! command -v flutter >/dev/null 2>&1; then
    local d
    for d in "$HOME/development/flutter" "$HOME/flutter" "/opt/flutter" "$HOME/snap/flutter/common/flutter" "/usr/local/flutter"; do
      if [[ -x "$d/bin/flutter" ]]; then export PATH="$d/bin:$PATH"; break; fi
    done
  fi
  if [[ -z "${ANDROID_SDK_ROOT:-}" ]]; then
    local s
    for s in "$HOME/Android/Sdk" "$HOME/Library/Android/sdk" "/opt/android-sdk"; do
      if [[ -d "$s" ]]; then export ANDROID_SDK_ROOT="$s"; export ANDROID_HOME="$s"; break; fi
    done
  fi
  localizar_java
}

# Um JDK utilizável tem bin/java que executa de verdade. No macOS, /usr/bin/java é só um atalho que
# imprime "Unable to locate a Java Runtime" quando não há JDK instalado, por isso não basta "existir".
_jdk_ok() { [[ -x "$1/bin/java" ]] && "$1/bin/java" -version >/dev/null 2>&1; }

# Candidatos a JAVA_HOME, do preferido (17) ao aceitável. AMBIENTE_RAIZ só existe para os testes.
_candidatos_java() {
  local R="${AMBIENTE_RAIZ:-}" v d
  if [[ -x "$R/usr/libexec/java_home" ]]; then                      # macOS: JDKs registrados no sistema
    for v in 17 21; do "$R/usr/libexec/java_home" -v "$v" 2>/dev/null || true; done
  fi
  for d in "$R"/usr/lib/jvm/*17* "$R"/usr/lib/jvm/*21*; do printf '%s\n' "$d"; done                       # Linux
  for d in "$R/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home" \
           "$R/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home" \
           "$R/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home" \
           "$R/usr/local/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"; do printf '%s\n' "$d"; done   # Homebrew
  for d in "$HOME"/Library/Java/JavaVirtualMachines/*/Contents/Home "$R"/Library/Java/JavaVirtualMachines/*/Contents/Home; do
    printf '%s\n' "$d"                                                                                  # instaladores .pkg (Temurin etc.)
  done
  for d in "$R/Applications/Android Studio.app/Contents/jbr/Contents/Home" \
           "$R/Applications/Android Studio Preview.app/Contents/jbr/Contents/Home" \
           "$HOME/android-studio/jbr" "$R/opt/android-studio/jbr"; do printf '%s\n' "$d"; done          # JDK que acompanha o Android Studio
}

localizar_java() {
  if [[ -n "${JAVA_HOME:-}" ]] && _jdk_ok "$JAVA_HOME"; then return 0; fi
  local j
  while IFS= read -r j; do
    [[ -n "$j" ]] && _jdk_ok "$j" && { export JAVA_HOME="$j"; export PATH="$j/bin:$PATH"; return 0; }
  done < <(_candidatos_java)
  return 0
}

# Falha com instruções claras se não houver Java utilizável (o Gradle precisa dele para o APK).
exigir_java() {
  if [[ -n "${JAVA_HOME:-}" ]] && _jdk_ok "$JAVA_HOME"; then return 0; fi
  if java -version >/dev/null 2>&1; then return 0; fi
  echo "ERRO: não encontrei um Java (JDK) utilizável; o Gradle precisa dele para gerar o APK."
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "No macOS, /usr/bin/java é só um atalho ('Unable to locate a Java Runtime') enquanto não há JDK. Instale um:"
    echo "  brew install openjdk@17        (ou: bash tool/instalar_requisitos_macos.sh)"
    echo "  ou instale o Android Studio (traz um JDK, que este script encontra sozinho)."
    echo "Depois rode de novo; o script procura o JDK nos lugares comuns, sem precisar mexer em JAVA_HOME."
  else
    echo "No Linux:  bash tool/instalar_requisitos_linux.sh   (ou: sudo apt install openjdk-17-jdk)"
  fi
  return 1
}

mensagem_instalar_flutter() {
  if [[ "$(uname -s)" == "Linux" ]]; then
    echo "Flutter não encontrado. No Linux, rode:  bash tool/instalar_requisitos_linux.sh"
  elif [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Flutter não encontrado. No macOS, rode:  bash tool/instalar_requisitos_macos.sh"
  else
    echo "Flutter não encontrado. Instale: https://docs.flutter.dev/get-started/install"
  fi
}

# Endereço fixo do servidor do app. Os scripts de compilação o usam quando nenhuma URL é passada.
# Para outro servidor:  URL_SERVIDOR_PADRAO=https://outro.exemplo bash tool/gerar_apk.sh
URL_SERVIDOR_PADRAO="${URL_SERVIDOR_PADRAO:-https://respirar-amazonas.cloud}"

# Decide a URL do servidor: "--local" = app sem servidor; vazio = padrão; outro valor = esse valor.
resolver_url_servidor() {
  case "${1:-}" in
    --local) printf '' ;;
    "") printf '%s' "$URL_SERVIDOR_PADRAO" ;;
    *) printf '%s' "$1" ;;
  esac
}

localizar_ambiente
