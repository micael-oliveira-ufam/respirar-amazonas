# Changelog

Todas as mudanças notáveis do Alerta Fumaça AM (app e servidor) estão aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e a versão segue [SemVer](https://semver.org/lang/pt-BR/):

- **MAIOR**: mudança que quebra compatibilidade (API, formato de dados ou fluxo que exige reinstalação).
- **MENOR**: funcionalidade nova compatível com as anteriores.
- **PATCH**: correção sem funcionalidade nova.

Cada versão aponta para o commit de release (tag `vX.Y.Z`). Como publicar: `tool/versao.py` (ver README, seção "Versionamento").

## [Não lançado]

Nenhuma mudança desde a 1.22.2.

## [1.22.2] - 2026-10-29

### Corrigido
- **Acento errado nos focos baixados pelo celular** (`flutter test` real do usuário em 29/10/2026, versão 1.22.0: 171 aprovados, 1 falho em `inpe_csv_test.dart`, "Expected: 'LÁBREA' / Actual: 'L�BREA'"). O app lia o CSV do INPE sempre como UTF-8 e trocava bytes inválidos por "�". Agora `decodeCsvBytes` tenta UTF-8 e, se não for UTF-8 válido, lê como Latin-1. **Qual codificação o INPE usa de verdade continua NÃO verificada**; o app passa a aceitar as duas. O teste que falhava montava a resposta com `http.Response(texto)` (Latin-1 por padrão), o que agora também funciona; 2 testes novos do decodificador (não executados aqui: sem Flutter).

Nenhuma mudança desde a 1.22.1.

## [1.22.1] - 2026-10-29

### Corrigido
- **Workflow falhava ao rodar de novo uma execução antiga (*Re-run*)** (visto em 29/10/2026, execução #1, passo "Publicar"): o *re-run* usa o commit ORIGINAL do run (0b2feb0), então o `git pull --rebase` encontrava os arquivos gerados pelo run anterior e dava conflito `add/add` em `docs/dados/csv/*.csv`. Agora usa `git pull --rebase -X theirs`: no conflito vence o retrato recém-gerado. O problema foi reproduzido e a correção testada num repositório de teste local. Execuções agendadas (sempre sobre o `main` atual) não eram afetadas.
- **Aviso "Node.js 20 is deprecated"**: `actions/checkout` v4 → **v7** e `actions/setup-python` v5 → **v7**, as versões "Latest" nas páginas de releases dos dois repositórios (lidas em 29/10/2026). A versão do Node que cada uma usa NÃO foi lida; o aviso deve sumir (conferir na próxima execução). As mudanças "BREAKING" listadas no checkout são sobre `pull_request_target`, que este workflow não usa.

Nenhuma mudança desde a 1.22.0.

## [1.22.0] - 2026-10-29

### Adicionado
- **Atualização automática do site pelo GitHub Actions** (pedido do usuário, 29/10/2026: "gerar uma automação no GitHub Actions para sempre atualizar o site com os dados do Firestore"; escolhas: a cada 6 horas, cache de bairros no repositório). `.github/workflows/atualizar-dados.yml`: agenda `17 */6 * * *` UTC + execução manual, lê o segredo `FIREBASE_SERVICE_ACCOUNT`, roda `tool/publicar_dados_firestore.py`, faz commit/push de `docs/dados` e `firebase/cache-bairros.json` só se mudou e pede a publicação do Pages. Sem APK e sem Flutter no workflow.
- **`firebase/cache-bairros.json`** (novo `--cache-bairros` no script): bairros já descobertos pelo Nominatim, em ordem fixa; as execuções seguintes só consultam áreas novas (política de 1 consulta/s). Falha do Nominatim não grava no cache.
- `tool/test_workflow_atualizar_dados.py` (estrutura do workflow: agenda, permissões mínimas, segredo nunca impresso, só commita o público) e 2 testes do cache. O workflow em si **só pode ser executado pelo GitHub**.

### Alterado
- **Regra "sem GitHub Actions" revogada pelo usuário para este workflow** (CLAUDE.md 1.4 atualizado); continua proibido compilar o APK ou guardar APK no repositório.

## [1.21.3] - 2026-10-29

### Alterado
- **README: receita completa e em ordem do Firebase** (pedido do usuário, 29/10/2026: incluir todos os comandos para reproduzir): clonar, console do Firebase, onde colocar os dois JSON, testes e APK, ambiente Python 3.12, atualização do retrato, `git pull/add/commit/push` e publicação de versão. Também explica por que `git add` falha na pasta extraída do `.zip` (sem `.git`) e que o site do Pages não atualiza sozinho.

Nenhuma mudança desde a 1.21.2.

## [1.21.2] - 2026-10-29

### Corrigido
- **`pip install -r server/requirements.txt` falhava com "No matching distribution found for fastapi==0.146.0"** (saída real do usuário, 29/10/2026): o log mostra que todas as versões do FastAPI a partir da 0.129 exigem Python >= 3.10, e o `python3` usado era mais antigo (a versão exata dele não consta no log; provável 3.9 do macOS, NÃO confirmado). README ensina a criar um ambiente virtual com `python3.12`, e `tool/publicar_dados_firestore.py` agora avisa com mensagem clara se o Python for < 3.10.

Nenhuma mudança desde a 1.21.1.

## [1.21.1] - 2026-10-29

### Alterado
- **Tela "Sobre o aplicativo" mostra o site público** (pedido do usuário, 29/10/2026): o cartão "Plataforma online" passa a exibir e abrir `https://micael-oliveira-ufam.github.io/respirar-amazonas/` (GitHub Pages), em vez do endereço do servidor definido na compilação. Antes, sem servidor, o cartão dizia "Endereço ainda não disponível". O texto do cartão deixou de citar "focos de calor", que não aparecem mais na página pública desde a 1.13.0. Teste de widget `test/platform_card_test.dart` (não executado: sem Flutter aqui) e teste Python que confere que o endereço do app é o mesmo de `URL_PADRAO` em `tool/gerar_pages.py`.

## [1.21.0] - 2026-10-27

### Adicionado
- **Respostas do app gravadas no Firebase (Firestore)** (pedido do usuário, 27/10/2026: "Integre o armazenamento das respostas do aplicativo ao firebase"; escolha: "Só Firestore"). Ao dizer "Sim" no fim do questionário, o app grava a resposta em `respostas/{submission_id}` no projeto `respirar-as` (`lib/services/answer_sink.dart`, `FirestoreAnswerSink`); o app **não envia mais ao servidor FastAPI**. O `submission_id` é o id do documento, então reenviar a mesma resposta não duplica. A fila de reenvio local (`AnswerSync`) continua: falha de rede/prazo = fica na fila; recusa do Firebase (`permission-denied`, `invalid-argument`, `already-exists`, `failed-precondition`) = descartada, sem repetir. Cache em disco do Firestore desligado (a fila é a do app).
- **`firebase/firestore.rules`**: o app só pode CRIAR um documento com o formato exato do questionário (campos, tipos, faixas e listas de valores iguais às do servidor); leitura, alteração e exclusão pelo app são negadas. `tool/test_firestore_rules.py` confere que as listas das regras coincidem com as do app e do servidor (NÃO executa as regras: isso exige o emulador do Firebase).
- **`tool/publicar_dados_firestore.py`** ("retrato via script"): lê o Firestore com uma chave de conta de serviço (fora do Git), passa cada documento pela MESMA validação do servidor num SQLite temporário, usa o `recebido_em` do Firebase como data de chegada (para os filtros de 1/7/30/90 dias), resolve bairros de Manaus (Nominatim) e grava `docs/dados/` no mesmo formato do `publicar_dados_pages.py`. Tudo ou nada; documentos inválidos são contados e nunca publicados. 9 testes (`tool/test_publicar_dados_firestore.py`).
- **Build Android com Firebase**: `tool/apply_platform_config.py` copia `firebase/google-services.json` (ignorado pelo Git) para `android/app/` e liga o plugin `com.google.gms.google-services` 4.5.0 (versão do console do usuário) no Gradle. Sem o arquivo, nada do Firebase é aplicado e o APK sai em modo local.
- Dependências do app: `firebase_core ^5.1.0` e `cloud_firestore ^7.1.0` (versões das notas de lançamento do Firebase para Flutter, BoM Android 35.1.0, lidas em 27/10/2026; **não compiladas**).

### Alterado
- Termo LGPD 1.5 (reaceite): os dados compartilhados ficam no Firebase (Google), possível transferência internacional (art. 33), acesso de leitura restrito à equipe; a frase "o servidor não grava o IP" virou "o app não grava o IP" (o provedor de nuvem pode manter registros técnicos).
- A tela de estatísticas entrega a fila pendente ao Firestore mesmo sem servidor configurado.

### Atenção (limites conhecidos)
- **iOS não usa Firebase ainda** (falta o `GoogleService-Info.plist`): no iOS o app segue em modo local, sem o cartão de compartilhamento.
- As **estatísticas dentro do app** e o **painel do servidor** continuam lendo o servidor FastAPI, que deixa de receber respostas novas. O site do Pages passa a ser alimentado pelo script acima.
- Reenvio de uma resposta já gravada (confirmação perdida na rede) volta como `permission-denied` e é descartado: o dado já está no Firestore, mas a tela diz "não compartilhado" nesse caso raro.

## [1.20.3] - 2026-10-27

### Corrigido
- **Site do Pages sem relatos publicados parecia cinza/desativado** (pedido do usuário, 27/10/2026): sem `docs/dados/`, os gráficos, os KPIs e o mapa de relatos nem apareciam e a barra de estado ficava vermelha. Agora a página aparece completa, com gráficos e mapa zerados e a mensagem verde "Ainda não há relatos publicados neste site. Eles serão atualizados ao longo do tempo." O painel vazio (`painel_vazio.js`) é igual ao que o servidor devolve com o banco vazio; o teste `test_painel_vazio_js.py` compara os dois nos 4 períodos. O texto da lista de CSV também ficou neutro ("serão disponibilizados aqui conforme os relatos forem publicados").

Nenhuma mudança desde a 1.20.2.

## [1.20.2] - 2026-10-27

### Alterado
- **Site do Pages: "Baixar para Android" e o QR code vão direto para o APK da Release** (`.../releases/download/v.1.20.0/RespirAR-Amazonas-v1.20.0.apk`, endereço informado pelo usuário), e não mais para a página de versões. O endereço fica em `APK_URL_PADRAO` (`tool/gerar_pages.py`) e pode ser trocado com `--apk-url`; só aceita `https` e sem caracteres que quebrem o JavaScript. Como o nome do arquivo leva a versão, **a cada APK novo é preciso regenerar o site com o novo endereço**.

Nenhuma mudança desde a 1.20.1.

## [1.20.1] - 2026-10-27

### Corrigido
- **`tool/gerar_apk.sh` no macOS parava no Gradle com "Unable to locate a Java Runtime".** Causa: no macOS o `/usr/bin/java` é só um atalho que imprime essa mensagem enquanto não há JDK, e `tool/_ambiente.sh` só procurava JDK em `/usr/lib/jvm` (Linux). Agora procura também `java_home`, Homebrew (`openjdk@17/21`, Apple Silicon e Intel), `~/Library/Java/JavaVirtualMachines`, `/Library/Java/JavaVirtualMachines` e o JDK do Android Studio, e só aceita um JDK que execute de verdade. O `gerar_apk.sh` confere o Java antes de começar e, se faltar, diz como instalar (`brew install openjdk@17`). `tool/instalar_requisitos_macos.sh` ganhou o passo do JDK 17. Testes: `tool/test_ambiente_java.py` (7, com pastas simuladas).

Nenhuma mudança desde a 1.20.0.

## [1.20.0] - 2026-10-27

### Alterado
- **O site do GitHub Pages agora é independente do servidor (modo estático, padrão de `tool/gerar_pages.py`).** Pedido do usuário (27/10/2026). O modo que lê a API continua disponível com `--api`.
  - **Qualidade do ar:** o navegador consulta o Open-Meteo direto (`ar_modelo.js`), com a mesma lógica de `qualidade_ar.py`. A paridade é testada no Node com a mesma resposta do Open-Meteo (casos de empate no arredondamento, valores ausentes, negativos, `time` em vários formatos).
  - **Relatos e CSV:** arquivos em `docs/dados/` (retrato publicado por `tool/publicar_dados_pages.py`, tudo-ou-nada); a página diz "Retrato publicado em … Não é ao vivo". Sem retrato, mostra que os relatos ainda não foram publicados.
  - **Download do app:** botão para a página de versões do GitHub (`releases/latest`), QR code estático e manual em PDF dentro do site.
  - CSP do Pages: só o Open-Meteo além da própria origem; nenhum endereço do servidor.
  - `docs/dados/` é preservada ao regenerar o site. O aviso "nova versão" e o rodapé usam o `versao.json` do próprio site.
  - Testes: paridade JS/Python (7), `tool/test_publicar_dados_pages.py` (3), modo estático e preservação de `docs/dados` em `tool/test_gerar_pages.py`.

Nenhuma mudança desde a 1.19.0.

## [1.19.0] - 2026-10-27

### Adicionado
- **Site no GitHub Pages (pasta `docs/`).** A página pública passou a poder ser servida como site estático, então abrir o site não depende mais de um servidor ligado no seu computador. Os DADOS (respostas agregadas, qualidade do ar, download do app, CSV) continuam vindo da API em `https://respirar-amazonas.cloud`; o servidor segue necessário só para receber as respostas do app e servir esses dados.
  - `tool/gerar_pages.py`: gera `docs/` a partir da página do servidor (caminhos relativos, `config.js` com o endereço da API, CSP em `<meta>`, `versao.json`, `.nojekyll`, `404.html`). Saída determinística.
  - `config.js` (`RESPIRAR_API`, `respirarUrl`): vazio no servidor (tudo igual a antes); com a API no Pages.
  - CORS de leitura (GET/HEAD/OPTIONS) em `/publico/*` no servidor; fora de `/publico/` nada muda (`/respostas` continua sem CORS).
  - Aviso "nova versão" no Pages compara o `versao.json` do próprio site.
  - Sem GitHub Actions (regra do repositório): publicar em Settings > Pages > Deploy from a branch > `main` > `/docs`.
  - Testes: `tool/test_gerar_pages.py` (inclui conferir que `docs/` não está desatualizado) e `server/tests/test_pages_csp.py`, `test_cors_publico.py`.

## [1.18.0] - 2026-10-21

### Adicionado
- **Backup e restauração do banco ao atualizar a plataforma.** Causa do problema: cada pasta de versão vira um projeto Docker com o PRÓPRIO volume `pgdata`; subir a versão nova em outra pasta cria um banco vazio, e `docker compose down -v` ou `parar_tudo.sh --apagar` apagam as respostas.
  - `tool/backup_dados.sh`: `pg_dump` (formato custom) para `~/respirar-backups` (fora da pasta do projeto; mude com `BACKUP_DIR`), com `.sha256` e `.txt` (data, versão, contagem de linhas por tabela); descarta backup vazio ou ilegível. Opções `--container`, `--todos`, `--rotulo`.
  - `tool/restaurar_dados.sh`: confere o SHA-256, guarda o banco atual (rótulo `antes-da-restauracao`) se tiver dados, para API e painel, restaura com `pg_restore --clean`, compara as contagens com o `.txt` e sobe API e painel. Pede a palavra RESTAURAR (ou `--sim`).
  - `tool/parar_tudo.sh --apagar` agora faz o backup ANTES de apagar e, se falhar, não apaga (`--sem-backup` para dispensar).
  - `tool/iniciar_servidor.sh` avisa quando o banco da pasta está vazio e há backups.
  - Testes: `tool/test_backup_dados.py` (6, com `docker` de mentira) e ciclo real com PostgreSQL 16 (37 respostas, 37 sintomas, 2 células: backup, banco apagado, restauração, contagens iguais).

## [1.17.1] - 2026-10-21

### Corrigido
- **Plataforma: as atualizações automáticas (a cada 15 s) reiniciavam o mapa** de relatos e atrapalhavam quem explorava. Causa: `desenharMapa()` chamava `fitBounds` e recriava todas as bolinhas a cada atualização. Agora o mapa só é enquadrado na primeira vez e ao trocar o período, e as bolinhas só são redesenhadas se os dados mudaram (o mesmo vale para o mapa de qualidade do ar, que atualiza a cada 15 min). Verificado no Chromium: zoom e posição mantidos após atualizações e após um ciclo real de 15 s; trocar o período enquadra de novo uma vez.

### Adicionado
- **Qualidade do ar: data da última atualização dos dados**, com ano e no horário de Manaus ("Última atualização dos dados do modelo: 20/10/2026 10:00 (horário de Manaus). Consultados pelo servidor em 21/10/2026 00:32."); o quadro "Referência do modelo" também passou a mostrar a data completa. Se o serviço não informar a data do modelo, a página diz isso (não inventa).

## [1.17.0] - 2026-10-21

### Alterado
- **App: os focos de calor agora são baixados pela internet do próprio celular** (pedido do usuário: o servidor dele não alcança o INPE, o celular em dados móveis alcança). O app baixa direto os CSV diários dos Dados Abertos do INPE (`dataserver-coids.inpe.br/.../focos_diario_br_AAAAMMDD.csv`: hoje, e para 48 h também os dois dias anteriores), em paralelo, filtra Amazonas/satélites/janela no aparelho e guarda a cópia local. Se o download direto falhar e houver servidor próprio, o app usa o servidor como reserva. Cópia com menos de 15 min é reaproveitada para poupar dados móveis (cada arquivo tem 2 a 6 MB; **48 h pode baixar ~10 a 15 MB**). Valores "-999" do INPE viram "sem dado". Dart **não compilado** aqui; testes novos em `test/inpe_csv_test.dart`.
- **Pergunta do questionário** "O remédio que você costuma usar não está aliviando?" (confusa: dupla negativa) → "Você tomou o seu remédio de costume e os sintomas continuam?", com explicação de quando responder Sim ou Não. O significado do dado não mudou (`medicacao_nao_alivia` = Sim).

## [1.16.1] - 2026-10-20

### Corrigido
- **Único teste do app que falhava** (`context_test.dart`, "toda pergunta cita referências existentes"; saída real do `flutter test` do usuário na 1.16.0: 149 passaram, 1 falhou). Causa: o teste só procurava as fontes 1 a 3 (`references`), mas "Máscara usada" cita as fontes 8 e 11, que ficam em `extraReferences` (pdf_content.dart). Era erro do teste, não do app: o teste agora junta as duas listas. `flutter analyze`: sem problemas.

## [1.16.0] - 2026-10-20

### Adicionado
- **Focos de calor: terceira via, os CSV dos dados abertos do INPE** (`server/app/focos_inpe_csv.py`). O WFS antigo do TerraBrasilis responde 404 desde 20/10/2026; os arquivos diários `https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/focos_diario_br_AAAAMMDD.csv` continuam publicados (listagem lida em 20/10/2026, arquivos de 11 a 20/10). Ordem agora: WFS do INPE -> CSV do INPE -> NASA FIRMS (se houver chave). O servidor filtra Amazonas e satélites, converte para o mesmo GeoJSON e o app **não precisou mudar**. O WFS que falha fica 10 min em pausa (o app não espera mais por ele), os downloads dos CSV são guardados 5 min e o pré-aquecimento passou a cobrir a combinação de satélites padrão do app.
- `tool/gerar_apk.sh`: `flutter analyze --no-fatal-infos` e **testes com falha não impedem o APK** (log em `dist/flutter-test.log`, aviso no fim); `EXIGIR_TESTES=1` restaura o bloqueio.

### Removido
- **App: avisos de falha de envio** (pedido do usuário: assustam). Saíram a barra "Não foi possível enviar agora…", o cartão vermelho "O servidor não aceitou o envio" e os "Detalhes técnicos". Em falha inesperada a pergunta apenas volta (pode tocar de novo); com fila, a mensagem passa a ser "Suas respostas foram guardadas e serão enviadas assim que possível."

## [1.15.0] - 2026-10-20

### Adicionado
- **APK com nome e versão** (`dist/RespirAR-Amazonas-vX.Y.Z.apk`); o servidor serve o de maior versão (comparação numérica) e o download já sai com esse nome. O quadro "Baixe o aplicativo" mostra o nome do arquivo.
- **Entrega automática ao servidor publicado:** `tool/publicar_apk.sh` (chamado no fim de `tool/gerar_apk.sh`) copia o APK, `VERSION.txt`, `SHA256SUMS.txt` e o manual para `APK_HOST_DIR` e para a pasta montada em `/srv/dist` por contêineres em execução, remove APKs antigos e confere dentro do contêiner. Corrige o caso "o download ainda não está disponível" quando o APK foi gerado numa pasta e o servidor roda noutra. `docker-compose.yml`: volume `${APK_HOST_DIR:-./dist}`.
- **Manual de instalação em PDF** (`GET /baixar/manual.pdf`, link no quadro de download): nome RespirAR Amazonas, versão e tela de abertura (splash) na capa; etapas refeitas para baixar pela plataforma. Gerado por `tool/gerar_manual.py` (assets em `assets/manual/`); cópia embutida em `server/app/manual/` como reserva.
- Limitações: as capturas de tela do Android (etapas 2 a 7) são de uma versão anterior (mostram `alerta_fumaca_AM_v0.7.1.apk`/`alerta_fumaca_am`) e estão legendadas assim; a captura da plataforma é uma ilustração gerada com um APK de teste; a splash anexada mostra "Versão 1.13.6".

## [1.14.1] - 2026-10-20

### Alterado
- **Sem mínimo por área do mapa e por bairro** (pedido do usuário): `MIN_RESPOSTAS_CELULA` padrão 3 → **1**. Áreas de ~1 km e bairros aparecem com qualquer número de respostas; a contagem de perfil/contexto também deixa de virar "menos de 3". Textos da página pública ajustados ao valor configurado. Um `.env` antigo com `MIN_RESPOSTAS_CELULA=3` continua valendo.
- **Termo LGPD 1.3 → 1.4** (sem número mínimo de respostas; re-aceite no app).
- **Risco residual maior:** com 1 resposta, o ponto no mapa mostra a área (~1 km) de uma única pessoa, e o bairro dela fica identificável a quem souber que ela respondeu. Sem nome/contato/IP, mas é a mudança mais sensível até aqui; para reverter, `MIN_RESPOSTAS_CELULA=3` no `.env`.

## [1.14.0] - 2026-10-20

### Alterado
- **Painel público sem mínimo de respostas** (pedido do usuário: o nome da pessoa não é identificado): `MIN_RESPOSTAS_PUBLICAS` passa de 5 para **0**; os gráficos (sintomas, níveis, série diária, perfil, exposição) aparecem sempre, inclusive com 0 respostas, com mensagens de vazio ("Nenhum sintoma relatado no período.", "Nenhuma resposta neste período ainda."). **Mantidos:** área do mapa/bairro só com 3+ respostas e contagens de perfil/contexto menores que 3 como "menos de 3". Quem definir `MIN_RESPOSTAS_PUBLICAS` no `.env` continua valendo (um `.env` antigo com `=5` mantém o comportamento antigo).
- **Termo LGPD 1.2 → 1.3**: o texto "estatísticas só aparecem com ao menos 5 respostas" deixaria de ser verdadeiro; o app pede nova leitura/aceite após atualizar.
- Risco residual: com poucas respostas, um gráfico agregado pode permitir inferência sobre um envio isolado (ex.: 1 resposta = 1 pessoa). Sem nome/contato/IP e com localização a ~1 km, o risco é baixo, mas não nulo.

## [1.13.7] - 2026-10-20

### Corrigido
- **A fila local de reenvio do app falhava em build de release** (diagnóstico real, graças aos "Detalhes técnicos" da 1.13.5): `PlatformException ... NoSuchMethodError ... SharedPreferencesApiRegistrar.getAll`. Causa (apontada por relato público de outro projeto, não reproduzida aqui): `shared_preferences_android` 2.5.0 passou a usar JNI e o R8 remove o método em release. Correção: `dependency_overrides` fixando `shared_preferences_android: 2.4.28` (versão confirmada no pub.dev). Efeitos do defeito: a fila de reenvio e as outras gravações locais (estatísticas em cache, ajustes de alertas) não funcionavam no APK release. **Não testado em aparelho**; remover o pin quando houver versão corrigida confirmada.
- O envio ao servidor já funcionava (o app enviou); o erro só aparecia nos "Detalhes técnicos".
- **"Detalhes técnicos" agora ficam recolhidos** (pedido do usuário): só aparecem se a pessoa tocar em "Mostrar detalhes técnicos", e só em falhas. Envio bem-sucedido não mostra a opção. Dart não compilado.

Nenhuma mudança desde a 1.13.6.

## [1.13.6] - 2026-10-20

### Corrigido
- 11 avisos do `flutter analyze` (saída real do usuário na 1.13.4; todos *info*: `unnecessary_const` e `prefer_const_constructors`) em `about_screen`, `guidance_screen`, `home_screen`, `air_quality_tab`, `questionnaire_screen` e `splash_screen`. Mudança só de `const`, sem efeito visual. **Não executei `flutter analyze` de novo** (sem Flutter aqui); conferir.
- Aviso do Flutter sobre o plugin `workmanager_android` aplicar o Kotlin Gradle Plugin: é aviso de futuras versões do Flutter, não erro; o build da 1.13.4 seguiu. Nada alterado.

Nenhuma mudança desde a 1.13.5.

## [1.13.5] - 2026-10-20

### Corrigido
- **Questionário: o app mostrava "Não foi possível enviar agora" sem dizer o motivo.** Agora a falha vem acompanhada de **"Detalhes técnicos"** (etapa, tipo do erro, código HTTP e trecho da resposta do servidor, mais o servidor usado), selecionável para copiar. Sem isso era impossível distinguir erro de rede, de fila local ou de servidor. O envio também não é mais interrompido por falha na fila local de reenvio. Nenhum dado pessoal entra nesse texto. Dart **não compilado**; testes novos em `test/api_client_test.dart` ainda sem execução.

Nenhuma mudança desde a 1.13.4.

## [1.13.4] - 2026-10-20

### Corrigido
- **Painel: seção "Amazônia · camadas" sem estilo e sem mapa** (print do usuário, 20/10/2026: botões com aparência padrão do navegador e nenhum mapa). Causa **provável, não confirmada**: o navegador/Cloudflare serviu um `publico.css` antigo (sem as regras de `.camadas` e do mapa) junto com o HTML novo, já que antes os arquivos de `/assets` eram guardados por 4 h. Correções: os arquivos CSS/JS agora levam a versão na URL (`?v=1.13.4`), forçando baixar o arquivo novo a cada versão, e o mapa da Amazônia tem altura definida no próprio HTML (não colapsa mesmo com CSS velho). A legenda gráfica do INPE **carregou** no print (quadrado laranja do bioma), o que indica que o serviço do INPE responde por WMS.

Nenhuma mudança desde a 1.13.3.

## [1.13.3] - 2026-10-20

### Alterado
- Imagem do túnel `cloudflare/cloudflared` atualizada de `2024.12.2` para `2026.10.2` (`tunnel` e `tunnel_dominio`), a pedido do usuário. **Verificado:** a tag existe no Docker Hub (`last_updated` 2026-10-20, status ativo). **Não verificado:** que as opções usadas (`--no-autoupdate`, `--metrics`, `run` com `TUNNEL_TOKEN`) continuam aceitas nessa versão; se o túnel não subir, veja `docker compose logs tunnel_dominio` e me envie.

Nenhuma mudança desde a 1.13.2.

## [1.13.2] - 2026-10-20

### Adicionado
- `tool/parar_tudo.sh`: para (ou, com `--apagar` e confirmação digitada, apaga) todos os contêineres, túneis, volumes, redes e imagens cujo nome começa com `respirar-amazonas`, em qualquer pasta. Motivo (20/10/2026): o usuário tinha cinco conjuntos rodando, quatro conectados ao mesmo túnel da Cloudflare, e o domínio respondia versões diferentes a cada visita. Verificado com `docker` simulado (parar, apagar cancelado, apagar confirmado; projetos `gaia-*`/`icam-*` intocados); **não testado em Docker real**. README ganhou a seção "Parar ou limpar tudo".

Nenhuma mudança desde a 1.13.1.

## [1.13.1] - 2026-10-20

### Corrigido
- **Questionário: "Enviando suas respostas…" sem fim.** A etapa de envio não tinha proteção contra demora ou erro inesperado (localização, fila local ou rede): qualquer falha fora do esperado deixava a tela presa. Agora a localização tem limite de 20 s (sem ela o envio segue, sem a área aproximada), o envio todo tem limite de 75 s e, em erro inesperado, a pergunta volta com um aviso para tentar de novo. **Causa exata no aparelho do usuário NÃO confirmada**; Dart não compilado nem testado aqui.

Nenhuma mudança desde a 1.13.0.

## [1.13.0] - 2026-10-20

### Removido
- Seção **"Focos de calor · INPE"** do painel público (e o botão de CSV de focos), a pedido do usuário: o serviço do INPE mudou de endereço e nada carregava. O servidor mantém `/focos`, a reserva NASA FIRMS e `/app/focos` (usados pelo app).

### Adicionado
- **Barra de progresso** do mapa da Amazônia: conta as imagens baixadas (`N de M`, %), diz quais camadas ainda carregam e informa quantas falharam.
- **Legenda** por camada: texto explicativo e, para as camadas do INPE, a legenda gráfica oficial do GeoServer (`GetLegendGraphic`; não verificada ao vivo, com aviso se não carregar). Para as camadas da NASA, texto sobre o que cada ponto/cor representa.
- **Restrição automática ao fundo Satélite** quando qualquer camada de desmatamento (DETER, PRODES, acumulado, sem floresta) está ligada; os fundos Mapa e Relevo ficam desabilitados e voltam ao desligar.

Nenhuma mudança desde a 1.12.2.

## [1.12.2] - 2026-10-20

### Corrigido
- Arquivos do painel (`/assets`) agora saem com `Cache-Control: no-cache` (revalidação por ETag). O Cloudflare estava aplicando `max-age=14400` (4 h), o que faz o site e a logo parecerem não atualizar depois de uma versão nova. Visto na saída do `curl -sI` do usuário (20/10/2026).

Nenhuma mudança desde a 1.12.1.

## [1.12.1] - 2026-10-20

### Corrigido
- **Logo do cabeçalho não aparecia** (print do usuário: ícone de imagem quebrada). Causa **não confirmada** no servidor dele (aqui `/assets/logo.png` responde 200 `image/png`; hipóteses: cache de 404 antigo no Cloudflare, ou arquivo ausente na imagem Docker). A logo agora vai **embutida no HTML** (data URI de 128 px, ~10 KB), sem depender de `/assets` nem de cache. Favicon e prévia de compartilhamento continuam em arquivos.

Nenhuma mudança desde a 1.12.0.

## [1.12.0] - 2026-10-20

### Adicionado
- **Seção "Amazônia · camadas oficiais"** no painel público: mapa com botões para ligar/desligar camadas (desmatamento DETER e PRODES, bioma, Amazônia Legal, estados, municípios, hidrografia, unidades de conservação, terras indígenas, aerossóis e anomalias térmicas da NASA) e três mapas de fundo. Os nomes das camadas vêm do catálogo do GeoServer do TerraBrasilis lido na máquina do usuário em 20/10/2026; o carregamento por WMS **não foi verificado** (INPE inacessível do ambiente do agente). A política de segurança da página passou a permitir imagens de `terrabrasilis.dpi.inpe.br`.
- Decisão do usuário (20/10/2026): parar de insistir no WFS de focos do INPE (caminho antigo retorna 404 e o catálogo novo só traz desmatamento) e priorizar camadas da Amazônia. Os focos seguem pela NASA FIRMS.

Nenhuma mudança desde a 1.11.0.

## [1.11.0] - 2026-10-20

### Adicionado
- **Segunda fonte de focos de calor: NASA FIRMS** (`server/app/focos_firms.py`). Se o INPE falhar, o servidor usa o FIRMS como reserva; no painel público há o seletor *INPE | NASA FIRMS* (só aparece se o servidor tem chave). A página mostra a origem real dos dados, avisa quando houve reserva e, no FIRMS, oculta a tabela de municípios (o FIRMS não informa município). Cabeçalhos `X-Fonte` e `X-Fonte-Solicitada`; `/focos?fonte=inpe|firms`; `/focos/fontes`; CSV de focos com coluna `fonte`; `/app/focos` informa `fonte_id` (os alertas do app também usam a reserva). A chave é configurada em `FIRMS_MAP_KEY` no `.env` (nunca no repositório).
- `INPE_WFS_URL` (opcional) para trocar o endereço do WFS do INPE sem alterar o código; o diagnóstico (`tool/diagnostico_inpe.sh`) agora procura caminhos candidatos.

### Descoberto
- Diagnóstico real do usuário (20/10/2026): o INPE respondia **HTTP 404 (Tomcat)** em `/queimadas/geoserver/ows`, com DNS e HTTPS funcionando. Ou seja, o caminho do serviço mudou; o novo endereço **não foi confirmado** (inacessível do ambiente do agente). O FIRMS cobre a lacuna enquanto isso.

Nenhuma mudança desde a 1.10.2.

## [1.10.2] - 2026-10-20

### Adicionado
- O rodapé do painel público mostra a **versão do servidor** que entregou a página ("servidor v1.10.2"), para confirmar se o contêiner foi reconstruído depois de uma atualização (os arquivos da página ficam dentro da imagem: é preciso `docker compose up -d --build`).

## [1.10.1] - 2026-10-20

### Adicionado
- **Logo do app no painel público:** no cabeçalho, no ícone da aba (favicon e `apple-touch-icon`) e na prévia ao compartilhar o link (Open Graph e Twitter Card, imagem 1200×630 `og-imagem.png`). Os endereços absolutos da prévia usam `PUBLIC_URL` (ou o Host da requisição).
- `tool/diagnostico_inpe.sh`: roda DNS, HTTPS e uma consulta ao INPE de dentro do contêiner da API e mostra os logs recentes, para achar por que os focos não carregam.

### Corrigido
- **Focos do INPE:** a página mostrava só "não foi possível obter". Agora o servidor informa o **motivo** (tempo esgotado, falha de DNS, certificado, HTTP 5xx, formato), registra a causa no log, envia `User-Agent` próprio, usa tempo de leitura de 90 s (antes 40 s) e tenta 2 vezes; a página tenta de novo sozinha a cada minuto. Com `FOCOS_PREAQUECER=true` (padrão no compose) o servidor busca os focos em segundo plano, e a página abre já com dados.
- **A causa raiz da falha na máquina do usuário continua NÃO confirmada** (o INPE é inacessível no ambiente do agente).

## [1.10.0] - 2026-10-20

### Adicionado
- **App: alerta de focos de calor** na tela "Alertas: ar e focos de calor". Notifica quando o INPE detecta focos nas últimas 24 h dentro de um raio (10, 25, 50 ou 100 km) da sede do município escolhido. Avisa na primeira detecção, quando o total cresce (pelo menos +5 e +50%) ou após 24 h ainda com focos; zera quando não há focos. O texto traz o horário da última detecção em Manaus e diz que são detecções por satélite, não incêndios confirmados.
- Servidor: `GET /app/focos?cod=<IBGE>&raio_km=` (contagem 24 h/48 h, foco mais próximo, última detecção, FRP máximo), usando o cache do INPE já existente (sem consulta extra ao INPE por aparelho).
- A checagem em segundo plano passa a cobrir ar e focos (`AirAlertService.checkAll`).

### Limites conhecidos
- Só entram focos registrados no estado do Amazonas (a consulta ao INPE é filtrada por estado) e o raio parte da **sede** do município (coordenada de `municipios_am.csv`), não do limite urbano nem municipal.
- Foco de calor não é incêndio confirmado (pode ser queimada controlada) e depende da passagem do satélite e de nuvens.

## [1.9.0] - 2026-10-20

### Adicionado
- **App: alertas de qualidade do ar por notificação** (Android). Tela "Alertas de qualidade do ar" (início do app): liga/desliga, escolha do município (62) e do limite (Moderada ≥51, Ruim para grupos sensíveis ≥101 [padrão], Ruim ≥151). O app confere cerca de 1 vez por hora em segundo plano (`workmanager`) e ao ser aberto, e notifica (`flutter_local_notifications`, notificações locais; sem Firebase). Só avisa na primeira vez, se a faixa piorar ou após 12 h com o índice ainda alto; não avisa com dado desatualizado. A notificação diz que é estimativa de modelo (~45 km).
- Servidor: `GET /app/ar?cod=<IBGE>` (leitura compacta de um município, usa o mesmo cache de 30 min).
- `tool/apply_platform_config.py` liga o *core library desugaring* no Gradle do app (exigido pelo `flutter_local_notifications`), de forma idempotente e testada.

### Limites conhecidos
- O Android (e a economia de bateria de cada fabricante) decide quando executar a checagem em segundo plano; o aviso pode atrasar. Não há aviso por servidor (push), que exigiria Firebase.
- Alertas só no Android; no iPhone a tela informa que ainda não há suporte.

## [1.8.0] - 2026-10-20

### Adicionado
- **Painel público:** download dos dados em **CSV** (`GET /publico/export.csv?conjunto=&dias=`), com conjuntos de sintomas, níveis, série diária, bairros, áreas, perfil/contexto, focos do INPE e qualidade do ar. Os CSV reutilizam os mesmos dados e regras de privacidade da página (mínimos de respostas; nada individual), usam UTF-8 com BOM e protegem contra injeção de fórmula em planilhas.
- **Painel público:** seção **Qualidade do ar do Amazonas** (62 municípios, US AQI, PM2,5, PM10 e fração fina PM2,5/PM10), com mapa, tabela e legenda. Fonte: Open-Meteo/CAMS por proxy do servidor com cache (`GET /publico/qualidade-ar`). É **estimativa de modelo (~45 km)**: por isso **não há valor por bairro de Manaus** (seria o mesmo número repetido); Manaus aparece com o valor do município.
- **Painel público:** **horário detalhado dos focos** (última detecção em Manaus e UTC, quando o servidor consultou o INPE, quando a página atualizou, aviso se os dados estão desatualizados) e tabela por satélite com a última detecção. Cabeçalho `X-Consultado-Em` em `GET /focos`.
- **Painel público:** mais mapas: relevo (OpenTopoMap), satélite em cor real e camadas NASA GIBS (aerossóis MODIS e focos VIIRS 375 m); seção de **fontes oficiais** (BDQueimadas, dados abertos do INPE, TerraBrasilis, MapBiomas Fogo).
- **Painel público:** **cabeçalho com download do app Android e QR code** (`GET /publico/app`, `/baixar/app.apk`, `/publico/qr.svg`), com tamanho, versão e SHA-256. O APK vem de `dist/` (montado no contêiner).
- **Atualização do app instalado:** `GET /app/versao` informa a última versão (de `dist/VERSION.txt`) e a mínima (`APP_VERSAO_MINIMA`); o app avisa na tela inicial e abre o download. O Android exige a confirmação da pessoa para instalar; o app não se atualiza em silêncio.
- **Atualização da página aberta:** `GET /publico/versao` (hash do conteúdo da página); a página avisa "Há uma nova versão" sem recarregar sozinha.

### Corrigido
- **App, tela "Sintomas mais relatados":** podia ficar girando por dezenas de segundos ou em branco sem servidor/banco (a entrega da fila de envios era aguardada antes da consulta, e erros que não fossem de rede não eram tratados). Agora os dados do aparelho aparecem na hora, o servidor tem limite de 8 s, a **última cópia recebida do servidor** é usada se ele falhar, e os gráficos aparecem zerados se não houver dado algum.
- `tool/gerar_apk.sh` grava `dist/VERSION.txt`; `dist/` entrou no `.gitignore`.

## [1.7.1] - 2026-10-20

### Corrigido
- O domínio fixo estava escrito `respira-amazonas.cloud` (sem o "r"); o domínio real é **`respirar-amazonas.cloud`** (confirmado na tela de DNS da Cloudflare do usuário). Por isso o navegador devolvia `DNS_PROBE_FINISHED_NXDOMAIN`. Corrigido em `tool/_ambiente.sh` (URL padrão do app), `tool/iniciar_servidor.sh`, `docker-compose.yml`, `.env.example`, README e teste. **APKs compilados na 1.7.0 apontam para o nome errado e precisam ser recompilados.**

## [1.7.0] - 2026-10-20

### Corrigido
- `tool/instalar_requisitos_linux.sh`: o `flutter doctor` acusava "No valid Android SDK platforms found" porque o instalador só baixava `platform-tools`. Agora também instala a plataforma (`platforms;android-N`) e o `build-tools` mais recentes (só versões finais, sem `-rc`/`-ext`), descobertos por `sdkmanager --list`; `--sdk_root` é passado explicitamente. Se a lista não puder ser obtida, o script mostra o comando manual.
- O fim do instalador explica que os itens "Linux toolchain" (clang, CMake, GTK) do doctor são só para apps de desktop e não afetam o APK.

## [1.6.9] - 2026-10-20

### Corrigido
- `tool/instalar_requisitos_linux.sh`: terminava com "FileSystemException ... Broken pipe" (ao rodar `flutter --version` na primeira vez). Causa: a saída era cortada com `| head -1`, o que fecha o pipe enquanto o Flutter ainda escreve. Agora a saída é capturada inteira e só a primeira linha é exibida; se o Flutter não iniciar, o erro real aparece. O instalador é reexecutável: o que já foi instalado é reaproveitado.

## [1.6.8] - 2026-10-20

### Corrigido
- Mapas das páginas web (painel público e do administrador) mostravam "Access blocked ... 403" no lugar do mapa. Causa: o servidor enviava `Referrer-Policy: no-referrer` e o OpenStreetMap recusa tiles sem o cabeçalho Referer (política de uso de tiles). Agora é `strict-origin-when-cross-origin` (só a origem vai a terceiros, nunca o caminho). Teste novo em `server/tests/test_publico.py`.

## [1.6.7] - 2026-10-20

Nenhuma mudança desde a 1.6.6.

## [1.6.6] - 2026-10-20

### Adicionado
- `tool/instalar_requisitos_linux.sh`: instala no Linux (apt, dnf ou pacman) as dependências do Flutter, o Java 17, o Flutter (clone do repositório oficial, ramo `stable` por padrão) e o Android SDK (command-line tools, `platform-tools`, licenças), grava o PATH em `~/.bashrc` e `~/.profile` e roda `flutter doctor -v`.
- `tool/_ambiente.sh`: localiza Flutter (`~/development/flutter`, `~/flutter`, `/opt/flutter`…), Android SDK (`~/Android/Sdk`) e Java 17 já instalados e os põe no PATH da execução.

### Alterado
- `tool/gerar_apk.sh` e `tool/_preparar.sh`: usam a detecção acima e, se o Flutter não existir, indicam o instalador do sistema certo (Linux ou macOS) em vez de só apontar a documentação.

## [1.6.5] - 2026-10-20

### Alterado
- `tool/iniciar_servidor.sh`: se o Docker recusar uma porta mesmo depois do teste prévio, o script troca a porta que falhou (painel ou API) pela próxima livre e tenta de novo, até 5 vezes, sem intervenção.

## [1.6.4] - 2026-10-20

### Corrigido
- `tool/iniciar_servidor.sh`: falhava com "Bind for 0.0.0.0:8080 failed: port is already allocated" quando outro programa já usava a porta do painel (ou da API). Agora detecta a porta ocupada, escolhe a próxima livre, grava no `.env` e mostra o endereço certo.

## [1.6.3] - 2026-10-20

### Corrigido
- `tool/iniciar_servidor.sh` no Linux: falhava com `unknown shorthand flag: 'd' in -d` quando o Docker não tem o plugin Compose. Agora usa `docker compose` ou `docker-compose`, explica como instalar se faltar, usa `sudo` quando o usuário não está no grupo `docker`, gera os segredos sem depender do `openssl` e mostra o link do túnel e o comando para compilar o app com ele.

## [1.6.2] - 2026-10-20

### Corrigido
- Telefone local do CIT: o (92) 3305-4700 não foi confirmado em nenhuma fonte; substituído pelo (92) 3305-4702 (Abracit e lista de CIATox do Ministério da Saúde). O 0800 722 6001 foi confirmado.
- Textos de saúde revisados contra fontes lidas: retiradas afirmações sem fonte (nebulização com soro, acroleína/formaldeído, "HEPA", raças de focinho curto, gato de boca aberta, limpeza dos olhos do pet com soro, "álcool destrói a máscara", locais de distribuição de máscaras, "sobrecarrega o coração").
- Dica de máscara de pano/cirúrgica no resultado do questionário não exibe mais texto interno.

### Alterado
- Referências ampliadas de 10 para 20 (ASBAI, OMS/OPAS, OMS Europa, VIGIAR, SES-AM/FVS-RCP, CRMV-AM no lugar do CFMV, Anvisa, 3M, DGS, Manual MSD, EPA, imprensa especializada), todas lidas em 20/10/2026.

## [1.6.1] - 2026-10-20

### Corrigido
- Fotos dos desenvolvedores estavam trocadas (Micael = óculos e crachá; Elias = camiseta cinza), no app e na plataforma online.
- Referências de "Fato ou Fake?" e da farmácia caseira passaram a apontar para fontes efetivamente lidas (VIGIAR/Ministério da Saúde e SES-AM/FVS-RCP).

### Adicionado
- `tool/teste_comunicacao.py`: teste de comunicação app -> servidor com o mesmo JSON que o app envia.

## [1.6.0] - 2026-10-20

### Adicionado
- Questionário: pergunta final "Quer compartilhar suas respostas para estudos epidemiológicos?"; "Sim" envia ao servidor (com localização aproximada de ~1 km se permitida), "Não" não envia nada. Termo LGPD 1.2.
- "Sintomas mais relatados": gráficos sempre visíveis (zerados sem dados), nível de risco e **bairros de Manaus mais afetados** (`GET /bairros`, `server/app/bairros.py`, tabela `celulas_bairro`, geocodificação reversa com Nominatim; variáveis `GEOCODER_ATIVO`, `GEOCODER_URL`, `GEOCODER_CONTATO`).
- Mapa: seletor que mostra só as datas de imagem de satélite com imagem disponível (`gibs_availability.dart`).
- Sobre: link da plataforma online e desenvolvedores com foto e e-mail.
- Plataforma online: bairros, focos de calor detalhados (por satélite, dia e município; mapa de calor com `leaflet.heat` 0.2.0), links oficiais de desmatamento e desenvolvedores.

### Alterado
- Questionário: removidos os botões "Refazer" e "Compartilhar localização".
- Fato ou Fake, Farmácia Caseira, Pets e CIT: mostram só as referências, sem texto da equipe nem selo de verificação (o estado de verificação ficou nos dados e no CLAUDE.md).
- Sobre: removido "Alterar endereço".

### Corrigido
- Mapa de focos em "Hoje" nunca mostrava focos: agora usa a camada de 48 h recortada pelo dia atual de Manaus (causa provável, não confirmada ao vivo). O servidor mapeia `today` para a camada de 48 h.
- Mensagem de erro técnica quando a imagem de satélite não existe para a data.

## [1.5.1] - 2026-10-20

### Corrigido
- `tool/_preparar.sh` (usado por `abrir_emulador.sh` e `gerar_ios.sh`): `pod install` falhava com "No `Podfile' found in the project directory" quando `ios/Podfile` ainda não existia. O Flutter só cria o Podfile ao preparar o projeto iOS. Agora, se faltar, o script roda `flutter build ios --config-only --no-codesign` para gerá-lo; se ainda assim não existir, segue sem o `pod install` manual (o `flutter run` e o `flutter build ios` rodam o CocoaPods sozinhos). **Não testado num Mac real**; a lógica foi conferida com comandos simulados.

Nenhuma mudança desde a 1.5.0.

## [1.5.0] - 2026-10-20

### Adicionado
- **Painel público, sem senha**, servido pela própria API em `/` (acessível pelo link do túnel): hero com indicador "ao vivo", filtro 24 h/7/30/90 dias, indicadores-chave, ranking de **sintomas mais relatados** (barras empilhadas leve/moderado/intenso, ordenável por frequência ou intensidade), rosca de níveis de risco, respostas por dia, mapa de áreas, perfil, tempo de exposição, contexto, nota "como ler estes dados" e download do JSON agregado. Claro/escuro, responsivo, sem bibliotecas externas além do Leaflet já incluso, respeita "reduzir movimento".
- `GET /publico/painel?dias=1|7|30|90` (aberto, dados agregados, cache de 10 s). Módulos `app/publico.py` e `app/rotulos.py`; `tests/test_publico.py` (10 testes, entre eles: abre sem senha mesmo com `ADMIN_TOKEN`, nada individual vaza, mínimos de privacidade, CSV continua protegido).

### Privacidade
- O painel público respeita as regras do termo LGPD (mínimo de 5 respostas; área com 3+). Contagens pequenas de perfil e contexto são escondidas ("menos de 3"). Respostas individuais e horários exatos **não** são expostos.
- Perfil (idoso, gestante, criança...), tempo de exposição e contexto passam a aparecer publicamente **em forma agregada**. O termo cita "sintomas mais relatados, níveis de risco e mapa"; avaliar se o texto deve citar também estes agregados (mudar o texto exige subir `kLgpdTermsVersion`).

Nenhuma mudança desde a 1.4.0.

## [1.4.0] - 2026-10-20

### Adicionado
- **iOS e emuladores**: `tool/gerar_ios.sh` (simulador ou release sem assinatura, com SHA-256), `tool/abrir_emulador.sh ios|android` (baixa pacotes, abre o Simulador/emulador e roda o app), `tool/instalar_requisitos_macos.sh` (Flutter, CocoaPods, runtime do simulador, `flutter doctor`) e `tool/_preparar.sh` (funções comuns). Seção "iOS e emuladores" no README.

### Corrigido
- `tool/gerar_apk.sh`: no bash 3.2 do macOS, `"${DEFINES[@]}"` com a lista vazia falha com "unbound variable" (por causa do `set -u`) quando o script roda sem URL de servidor. Trocado por `${DEFINES[@]+"${DEFINES[@]}"}`.

Nenhuma mudança desde a 1.3.1.

## [1.3.1] - 2026-10-19

### Alterado
- **Pacote Dart `alerta_fumaca_am` -> `respirar_amazonas`** e **repositório `alerta-fumaca-am` -> `respirar-amazonas`** (nomes inferidos do nome do app). Atualizados `pubspec.yaml`, imports dos testes, scripts, README e links. O renome do repositório no GitHub precisa ser feito pelo usuário (o ambiente do agente não tem permissão).
- Atenção: o identificador do app (`br.ufam.fcf.<pacote>`) muda, então um aparelho com a versão antiga instalada receberá um segundo app, não uma atualização.

Nenhuma mudança desde a 1.3.0.

## [1.3.0] - 2026-10-19

### Alterado
- **Nome do app: "Alerta Fumaça AM" passou a "RespirAR Amazonas"** (decisão do usuário). Atualizado no app (título, início, *Sobre*, termo LGPD), no servidor (título da API e do painel), nos scripts de plataforma (`tool/apply_platform_config.py`, que grava o nome no Android e no iOS) e no README. O nome do pacote Dart (`alerta_fumaca_am`) e o repositório continuam iguais.
- Termo LGPD: versão `1.0` -> `1.1` porque o nome aparece no texto (regra do próprio arquivo: qualquer mudança de texto pede nova leitura). **O usuário verá o termo de novo na próxima abertura.**
- **Tela de abertura reformulada**: fumaça que sobe e se dissipa ao fundo, logo com anéis de pulso, entrada escalonada do nome ("Respir" + "AR" destacado), slogan "Alertas, triagem e proteção contra fumaça no Amazonas.", quatro recursos (focos do INPE, qualidade do ar, triagem, orientações sem internet), instituição, versão, aviso educativo e barra de progresso. Dura 3,8 s; um toque pula. Com "remover animações" do sistema ligado, o movimento contínuo é desligado.

### Adicionado
- `test/app_name_test.dart`.

Nenhuma mudança desde a 1.2.0.

## [1.2.0] - 2026-10-19

### Adicionado
- **App**: conteúdo do documento "TEXTOS PARA ATUALIZAÇÃO DO APLICATIVO" (`lib/data/pdf_content.dart`), embutido no app e, portanto, disponível sem internet:
  - *O que fazer agora*: cartões "Qual máscara protege" e "Purificador vs. Umidificador", e o painel do CIT (HUGV/UFAM) detalhado, com discagem direta, "Quando ligar" e segundo telefone.
  - Botão **Entenda seus sintomas** no resultado do questionário (CO, gases irritantes, PM2,5).
  - Telas **Farmácia caseira**, **E os nossos pets?** (3 cartões) e **Fato ou Fake?** (3 mitos).
  - Banner de **alerta roxo** na aba de qualidade do ar quando alguma leitura chega a AQI 201 ou mais.
  - Referências 4 a 10 na tela *Referências*, cada uma com o que foi e o que NÃO foi verificado.
  - Selo de verificação ("Conferido", "Parcialmente conferido", "Texto da equipe, fonte não consultada") em todo cartão.
- `CLAUDE.md`: ordens obrigatórias ao agente, diretrizes de comportamento anexadas, histórico detalhado e regra de sempre perguntar os próximos passos com escolhas.
- `test/pdf_content_test.dart`.

### Alterado
- Créditos: "Elias Barros" passou a "Elias de Souza Barros" (tela *Sobre* e README).
- Ajustes declarados nos textos da equipe: no CIT, confusão/desmaio manda ligar primeiro ao SAMU (192); removidas as frases sem fonte ("autoridade máxima", "ácido fraco", "diretamente na corrente sanguínea", e partes de leite/monóxido).

### Não implementado (pedido no PDF)
- Alerta laranja (mudança de vento) e notificações push: exigem previsão de vento e serviço de push que o app não tem.

### Corrigido
- Focos do INPE só carregavam depois de abrir a aba de qualidade do ar. Causa: o `TabBarView` destruía a aba que não estava visível, e a consulta só era refeita ao voltar a ela; uma primeira consulta que falhava não era repetida. Agora as abas ficam vivas (`KeepAlivePage`) e a consulta do INPE é repetida automaticamente em falha de rede ou de servidor (2 novas tentativas, com espera crescente). O tempo limite caiu de 60 s para 30 s.
- Sete sugestões do analisador (`prefer_const_constructors` e `prefer_const_literals_to_create_immutables`) aplicadas em `about_screen`, `guidance_screen`, `home_screen`, `air_quality_tab`, `questionnaire_screen` e `cit_card`.
- `tool/gerar_apk.sh` remove o `test/widget_test.dart` padrão do `flutter create`, que não compila neste projeto.
- `tool/gerar_apk.sh` avisa quando o caminho do projeto tem acentos ou espaços, causa provável de `flutter analyze` falhar com "Unexpected end of input". O README ganhou essa linha no diagnóstico.
- Tela de LGPD: a cor de fundo da área de aceite estava num `DecoratedBox` acima do `CheckboxListTile`, o que escondia o efeito de toque (falha em `test/lgpd_test.dart`). A cor agora fica num `Material`.
- Adicionado `analysis_options.yaml` (estava ausente, então as regras do `flutter_lints` não eram aplicadas e o analisador não tinha configuração explícita).
- `tool/iniciar_servidor.sh` e `tool/gerar_apk.sh` funcionam no macOS: o `sed -i` (sintaxe do GNU) foi trocado por `awk`, e `sha256sum` por `shasum -a 256` quando necessário. O script também confere se o Docker está rodando.

## [1.1.0] - 2026-10-19

Servidor próprio com painel em tempo real, questionário ampliado e interface circular.

### Adicionado
- **App**: questionário em 4 etapas com botões circulares; 10 perguntas de contexto opcionais (local, fumaça visível, máscara, exercício, trabalho ao ar livre, ar filtrado, imunidade, medicação à mão, piora, medicação que não alivia). Não alteram a pontuação e geram cuidados por situação.
- **App**: tela **Referências** com as fontes de cada pergunta (CDC HAN 00495, EPA-452/R-21-901, nota do Ministério da Saúde via imprensa), com ressalvas do que foi verificado.
- **App**: mapas sem rotação, botões de zoom, minha localização, visão inicial, camadas (fundo Ruas ou Satélite NASA GIBS; sobreposições de fumaça/aerossóis e focos VIIRS) e barra de escala.
- **App**: tela cheia (modo imersivo) e nome exibido "Alerta Fumaça AM".
- **App**: termo de privacidade (LGPD) na primeira abertura (commit `638ded1`).
- **App**: endereço do servidor configurável em *Sobre*, com aviso de consentimento.
- **Servidor**: painel em tempo real (KPIs, série de 48 h, mapa, últimas respostas, contexto agregado) protegido por `ADMIN_TOKEN`.
- **Servidor**: túnel Cloudflare com link aleatório a cada início, exibido no painel com QR code.
- **Servidor**: coluna `contexto` (opcional) em `respostas`, com migração que adiciona a coluna em bancos existentes.
- **Servidor**: colunas `ctx_*` no CSV de exportação.
- **Operação**: `tool/iniciar_servidor.sh` (gera `.env` com segredos e sobe o Docker Compose) e `tool/gerar_apk.sh` (gera o APK de release com SHA-256).

### Alterado
- Menu inicial com botões circulares; botões com formato de pílula.
- O questionário envia o contexto apenas se a pessoa respondeu, e "Não sei" não é enviado.
- Repositório sem GitHub Actions: os testes passam a ser rodados localmente (ver README).

### Removido
- Workflows `ci.yml` e `release.yml` do GitHub Actions, e o APK publicado em Releases.
- `tool/ci_annotate.py`.

### Corrigido
- Remoção de import não usado apontado pelo `flutter analyze` (commit `10e36d5`).
- CSP do painel: `img-src` agora libera `https://tile.openstreetmap.org` (o domínio curinga não cobria o domínio raiz).
- Colunas de horário do painel não quebram linha.

## [1.0.0] - 2026-10-19

Primeira versão: orientação e triagem educativa durante episódios de fumaça no Amazonas.

### Adicionado
- Focos de calor do INPE/Programa Queimadas por satélite (MODIS, NOAA-20, Suomi NPP), com recorte do Amazonas e do Brasil.
- Qualidade do ar estimada por modelo (Open-Meteo, CAMS) para 9 sedes do Amazonas.
- Mapa da comunidade com registros anonimizados e agregados por área (~1 km).
- Questionário de sintomas com triagem em 4 níveis e perfil de vulnerabilidade.
- Orientações por nível de risco e cartão do CIT-AM.
- API FastAPI com PostgreSQL 16, Docker Compose e testes automatizados.
- Pipeline no GitHub Actions: testes do servidor (SQLite e PostgreSQL), teste do Compose, análise e testes do Flutter, e APK anexado ao release ao enviar a tag `vX.Y.Z`.

[Não lançado]: https://github.com/micael-oliveira-ufam/respirar-amazonas/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/micael-oliveira-ufam/respirar-amazonas/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/micael-oliveira-ufam/respirar-amazonas/releases/tag/v1.0.0
