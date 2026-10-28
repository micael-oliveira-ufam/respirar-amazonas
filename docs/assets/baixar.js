/* Cabeçalho "Baixe o aplicativo" (link + QR code) e seção "Baixar os dados (CSV)". */
(function () {
  'use strict';

  function $(id) { return document.getElementById(id); }
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'text') el.textContent = attrs[k]; else el.setAttribute(k, attrs[k]);
    });
    for (var i = 2; i < arguments.length; i++) {
      var c = arguments[i]; if (c == null) continue;
      el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return el;
  }
  function limpar(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
  function mb(b) { return (b / 1048576).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' MB'; }

  // ------------------------------------------------------------- download do app
  // Sem servidor (GitHub Pages independente): o APK fica nas "versões" do GitHub e o QR code é um arquivo do site.
  function appEstatico() {
    var box = limpar($('app-conteudo'));
    var url = window.RESPIRAR_APK_URL;
    var arquivo = decodeURIComponent(url.split('/').pop());
    var qr = h('img', { src: 'assets/qr-app.svg', alt: 'QR code para baixar o aplicativo no celular', width: '132', height: '132' });
    var texto = h('div', { class: 'app-txt' },
      h('a', { class: 'btn', href: url, download: arquivo }, 'Baixar para Android'),
      h('p', { class: 'app-meta' }, h('code', { text: arquivo })),
      h('p', { class: 'app-nota', text: 'Aponte a câmera do celular para o QR code. Ao abrir o arquivo, o Android pode pedir permissão para instalar apps desta origem. Versão para iPhone: ainda não disponível.' }),
      h('p', { class: 'app-nota' }, h('a', { href: 'assets/Manual-Instalacao-RespirAR-Amazonas.pdf', download: 'Manual-Instalacao-RespirAR-Amazonas.pdf' }, 'Baixar o manual de instalação (PDF, com imagens)')));
    box.appendChild(h('div', { class: 'app-linha' }, h('div', { class: 'qr' }, qr), texto));
  }

  function app() {
    if (window.RESPIRAR_MODO === 'estatico') { appEstatico(); return; }
    fetch(respirarUrl('/publico/app'), { headers: { Accept: 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (i) {
        var box = limpar($('app-conteudo'));
        if (!i.disponivel) {
          box.appendChild(h('p', { class: 'app-nd', text: 'O download do aplicativo ainda não está disponível neste endereço.' }));
          box.appendChild(h('p', { class: 'app-nota', text: 'Versão para iPhone: ainda não disponível.' }));
          return;
        }
        var data = new Date(i.atualizado_em);
        var meta = [i.plataforma + ' (APK)', i.versao ? 'versão ' + i.versao : null, mb(i.tamanho_bytes),
          isFinite(data) ? 'atualizado em ' + data.toLocaleDateString('pt-BR') : null].filter(Boolean).join(' · ');
        var qr = h('img', { src: respirarUrl('/publico/qr.svg?alvo=app'), alt: 'QR code para baixar o aplicativo no celular', width: '132', height: '132' });
        var texto = h('div', { class: 'app-txt' },
          h('a', { class: 'btn', href: respirarUrl(i.url), download: i.arquivo }, 'Baixar para Android'),
          h('p', { class: 'app-meta' }, h('code', { text: i.arquivo })),
          h('p', { class: 'app-meta', text: meta }),
          h('p', { class: 'app-nota', text: 'Aponte a câmera do celular para o QR code. Ao abrir o arquivo, o Android pode pedir permissão para instalar apps desta origem. Versão para iPhone: ainda não disponível.' }),
          (i.manual_url ? h('p', { class: 'app-nota' }, h('a', { href: respirarUrl(i.manual_url), download: 'Manual-Instalacao-RespirAR-Amazonas.pdf' }, 'Baixar o manual de instalação (PDF, com imagens)')) : null),
          h('details', {}, h('summary', { text: 'Conferir a integridade (SHA-256)' }), h('code', { class: 'hash', text: i.sha256 })));
        var linha = h('div', { class: 'app-linha' }, h('div', { class: 'qr' }, qr), texto);
        limpar($('app-conteudo')).appendChild(linha);
      })
      .catch(function () {
        limpar($('app-conteudo')).appendChild(h('p', { class: 'app-nd', text: 'Não foi possível verificar o download agora. Tente recarregar a página.' }));
      });
  }

  // ----------------------------------------------------------------- CSV
  var CONJUNTOS = [
    ['sintomas', 'Sintomas relatados', 'leve, moderado e intenso, por sintoma', true],
    ['niveis', 'Nível de risco', 'respostas por nível calculado pelo app', true],
    ['serie_diaria', 'Respostas por dia', 'série diária (UTC)', true],
    ['bairros', 'Bairros de Manaus', 'só bairros com respostas suficientes', true],
    ['areas', 'Áreas do mapa (~1 km)', 'centro da área, respostas e pior nível', true],
    ['perfil_contexto', 'Perfil e situação', 'grupos de atenção, exposição e contexto', true],
    ['qualidade_ar', 'Qualidade do ar', 'índice, PM2,5 e PM10 por município (modelo)', false]
  ];

  function periodo() {
    var on = document.querySelector('#periodo button.on');
    return on ? on.getAttribute('data-dias') : '30';
  }
  var manifesto = null;   // modo estático: dados/manifest.json lista os CSV publicados
  function dataRetrato() {   // dd/mm/aaaa no horário de Manaus (UTC-4)
    var t = manifesto && Date.parse(manifesto.gerado_em); if (!isFinite(t)) return null;
    var d = new Date(t - 4 * 3600 * 1000), p = function (n) { return (n < 10 ? '0' : '') + n; };
    return p(d.getUTCDate()) + '/' + p(d.getUTCMonth() + 1) + '/' + d.getUTCFullYear();
  }
  function linksEstaticos() {
    var d = periodo(), rot = d === '1' ? 'últimas 24 h' : 'últimos ' + d + ' dias';
    $('csv-periodo').textContent = rot;
    var el = limpar($('csv-lista'));
    var itens = manifesto ? manifesto.csv.filter(function (x) { return !x.dias || String(x.dias) === d; }) : [];
    if (!itens.length) {
      el.appendChild(h('p', { class: 'sub', text: 'Os arquivos CSV serão disponibilizados aqui conforme os relatos forem publicados.' }));
      return;
    }
    itens.forEach(function (x) {
      var c = CONJUNTOS.filter(function (k) { return k[0] === x.conjunto; })[0];
      el.appendChild(h('a', { class: 'csv-item', href: 'dados/' + x.arquivo, download: '' },
        h('b', { text: c ? c[1] : x.conjunto }), h('span', { text: (c ? c[2] : '') + (x.dias ? ' · ' + rot : '') + (dataRetrato() ? ' · retrato de ' + dataRetrato() : '') }), h('em', { text: 'Baixar CSV' })));
    });
  }
  function links() {
    if (window.RESPIRAR_MODO === 'estatico') { linksEstaticos(); return; }
    var d = periodo(), rot = d === '1' ? 'últimas 24 h' : 'últimos ' + d + ' dias';
    $('csv-periodo').textContent = rot;
    var el = limpar($('csv-lista'));
    CONJUNTOS.forEach(function (c) {
      var href = respirarUrl('/publico/export.csv?conjunto=' + c[0] + (c[3] ? '&dias=' + d : ''));
      el.appendChild(h('a', { class: 'csv-item', href: href, download: '' },
        h('b', { text: c[1] }), h('span', { text: c[2] + (c[3] ? ' · ' + rot : '') }), h('em', { text: 'Baixar CSV' })));
    });
  }
  $('periodo').addEventListener('click', function () { setTimeout(links, 0); }); // depois de publico.js marcar o botão
  if (window.RESPIRAR_MODO === 'estatico') {
    fetch('dados/manifest.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { manifesto = m; links(); }).catch(function () { links(); });
  } else links();
  app();
})();
