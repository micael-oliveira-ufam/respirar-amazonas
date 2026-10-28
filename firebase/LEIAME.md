# Pasta `firebase/`

| Arquivo | No Git? | Para quê |
|---|---|---|
| `firestore.rules` | sim | Regras do Firestore (publicar no console). O app só cria respostas válidas; não lê, altera nem apaga. |
| `google-services.json` | **não** | Configuração do app Android, baixada do console. `tool/apply_platform_config.py` copia para `android/app/`. |
| `GoogleService-Info.plist` | **não** | Configuração do iOS (ainda não fornecida: iOS sem Firebase). |
| `chave-servico.json` | **não** | Chave de conta de serviço usada só por `tool/publicar_dados_firestore.py`. Dá leitura a todo o banco: guarde bem; se vazar, revogue no console. |

Procedimento completo: README, seção "Respostas no Firebase (Firestore)".
