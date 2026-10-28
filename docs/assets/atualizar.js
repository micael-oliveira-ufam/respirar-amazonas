/* Aviso de nova versão da página: quem deixa a aba aberta não fica com código antigo.
   Consulta /publico/versao (ou, no GitHub Pages, versao.json do próprio site); se o "build" mudar em relação ao da carga, mostra um aviso para recarregar.
   Nunca recarrega sozinho (não perde o que a pessoa está lendo). */
(function () {
  'use strict';
  var INTERVALO_MS = 5 * 60 * 1000;
  var inicial = null;
  var avisado = false;

  function aviso() {
    if (avisado) return;
    avisado = true;
    var d = document.createElement('div');
    d.className = 'atualizar';
    d.setAttribute('role', 'status');
    var t = document.createElement('span');
    t.textContent = 'Há uma nova versão deste painel.';
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = 'Atualizar agora';
    b.addEventListener('click', function () { location.reload(); });
    d.appendChild(t);
    d.appendChild(b);
    document.body.appendChild(d);
  }

  function rotuloServidor(j) {
    var v = document.getElementById('versao-servidor');
    if (v && j && j.servidor) v.textContent = 'servidor v' + j.servidor;
  }
  function conferirBuild(j) {
    if (!j || !j.build) return;
    if (inicial === null) inicial = j.build;
    else if (j.build !== inicial) aviso();
  }
  function lerJson(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; });
  }

  function checar() {
    var comApi = !!window.RESPIRAR_API;   // GitHub Pages: o "build" da página é o do próprio site (versao.json)
    var url = comApi ? 'versao.json' : '/publico/versao';
    lerJson(url)
      .then(function (j) { conferirBuild(j); if (!comApi) rotuloServidor(j); })
      .catch(function () { /* sem rede: tenta de novo no próximo ciclo */ });
    if (comApi) {
      lerJson(respirarUrl('/publico/versao')).then(rotuloServidor).catch(function () {});
    }
  }

  checar();
  setInterval(checar, INTERVALO_MS);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) checar();
  });
})();
