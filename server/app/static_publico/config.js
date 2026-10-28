/* Modo de operação da página.
   'servidor'  : servida pelo FastAPI; os dados vêm do próprio servidor (RESPIRAR_API vazio).
   'conectado' : GitHub Pages lendo os dados da API (RESPIRAR_API = endereço do servidor).
   'estatico'  : GitHub Pages independente do servidor (qualidade do ar direto do Open-Meteo,
                 relatos e CSV em arquivos publicados em dados/, download do app pelo GitHub Releases).
   No GitHub Pages este arquivo é regenerado por tool/gerar_pages.py. */
window.RESPIRAR_MODO = 'servidor';
window.RESPIRAR_API = '';
window.respirarUrl = function (caminho) { return (window.RESPIRAR_API || '') + caminho; };
