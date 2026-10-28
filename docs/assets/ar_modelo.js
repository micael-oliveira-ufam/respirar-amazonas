/* Qualidade do ar sem servidor: consulta o Open-Meteo (modelo CAMS) direto do navegador e monta o MESMO
 * conteúdo que o servidor devolve em /publico/qualidade-ar (server/app/qualidade_ar.py).
 *
 * Mantido em paridade com o Python: server/tests/test_ar_modelo_js.py roda este arquivo no Node com a mesma
 * resposta do Open-Meteo e compara o resultado campo a campo. Se mudar a regra em um lado, mude no outro.
 * São ESTIMATIVAS DE MODELO (~45 km), US AQI (EPA), não o IQAr oficial.
 */
(function (raiz) {
  'use strict';

  var URL_API = 'https://air-quality-api.open-meteo.com/v1/air-quality';
  var TIMEOUT_MS = 25000;
  var FONTE = 'Open-Meteo Air Quality API (modelo CAMS, Copernicus/ECMWF)';
  var ATRIBUICAO = 'Dados de qualidade do ar: Open-Meteo.com, com dados do CAMS (Copernicus Atmosphere Monitoring Service / ECMWF).';
  var RESOLUCAO_KM = 45;
  var FAIXAS = [
    [50, 'boa', 'Boa'], [100, 'moderada', 'Moderada'], [150, 'sensivel', 'Ruim para grupos sensíveis'],
    [200, 'ruim', 'Ruim'], [300, 'muito_ruim', 'Muito ruim'], [1e9, 'perigosa', 'Perigosa']
  ];

  /* round() do Python: arredonda pelo valor decimal EXATO do double e, em empate exato, para o par.
     (Math.round e toFixed arredondam empates para cima: 2,5 -> 3, mas Python dá 2.) */
  function arredondar(x, casas) {
    var s = Math.abs(x).toFixed(100);
    var ponto = s.indexOf('.');
    var corte = ponto + 1 + casas;
    var resto = s.slice(corte);
    var base = s.slice(0, corte).replace('.', '');
    var n = BigInt(base);
    if (resto.charAt(0) > '5' || (resto.charAt(0) === '5' && /[1-9]/.test(resto.slice(1)))) n += 1n;
    else if (resto.charAt(0) === '5' && n % 2n === 1n) n += 1n; // empate exato: par
    var r = Number(n) / Math.pow(10, casas);
    return x < 0 ? -r : r;
  }

  function categoria(aqi) {
    if (aqi === null) return [null, null];
    for (var i = 0; i < FAIXAS.length; i++) if (aqi <= FAIXAS[i][0]) return [FAIXAS[i][1], FAIXAS[i][2]];
    return [null, null];
  }
  function num(v) {
    if (typeof v !== 'number' || !isFinite(v) || v < 0) return null;
    return v;
  }
  function instante(v) {
    if (typeof v !== 'string' || !v.trim()) return null;
    var t = v.trim();
    if (!(t.slice(-1) === 'Z' || /[+-]/.test(t.slice(10)))) t += 'Z';
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$/.test(t)) return null;
    return isFinite(Date.parse(t)) ? t : null;
  }

  function montarParams(munis) {
    function f(x) { return x.toFixed(4); }
    return 'latitude=' + munis.map(function (m) { return f(m.lat); }).join(',') +
      '&longitude=' + munis.map(function (m) { return f(m.lon); }).join(',') +
      '&current=us_aqi,pm2_5,pm10&timezone=GMT';
  }

  function interpretar(corpo, munis) {
    var itens;
    if (corpo && typeof corpo === 'object' && !Array.isArray(corpo)) {
      if (corpo.error) throw new Error('serviço recusou a consulta: ' + (corpo.reason || 'motivo não informado'));
      itens = [corpo];
    } else if (Array.isArray(corpo)) itens = corpo;
    else throw new Error('resposta em formato inesperado');
    if (itens.length !== munis.length) throw new Error('a resposta tem ' + itens.length + ' local(is), mas foram pedidos ' + munis.length);
    return munis.map(function (m, i) {
      var item = itens[i];
      var atual = item && typeof item === 'object' ? item.current : null;
      if (!atual || typeof atual !== 'object' || Array.isArray(atual)) atual = {};
      var aqi = num(atual.us_aqi);
      aqi = aqi === null ? null : arredondar(aqi, 0);
      var pm25 = num(atual.pm2_5), pm10 = num(atual.pm10);
      var c = categoria(aqi);
      return {
        codigo_ibge: m.codigo, municipio: m.nome, latitude: m.lat, longitude: m.lon,
        us_aqi: aqi, categoria: c[0], categoria_rotulo: c[1],
        pm2_5: pm25 === null ? null : arredondar(pm25, 1),
        pm10: pm10 === null ? null : arredondar(pm10, 1),
        fracao_fina_pct: pm25 !== null && pm10 ? arredondar(100 * pm25 / pm10, 0) : null,
        referencia_modelo: instante(atual.time)
      };
    });
  }

  function maximo(lista, chave) {
    var melhor = null;
    lista.forEach(function (x) { if (melhor === null || x[chave] > melhor[chave]) melhor = x; });
    return melhor;
  }
  function resumir(linhas) {
    var comAqi = linhas.filter(function (x) { return x.us_aqi !== null; });
    var comPm = linhas.filter(function (x) { return x.pm2_5 !== null; });
    var pior = maximo(comAqi, 'us_aqi'), pmMax = maximo(comPm, 'pm2_5');
    var porCat = {};
    FAIXAS.forEach(function (f) { porCat[f[1]] = comAqi.filter(function (x) { return x.categoria === f[1]; }).length; });
    return {
      total: linhas.length, com_dado: comAqi.length,
      pior: pior === null ? null : { municipio: pior.municipio, us_aqi: pior.us_aqi, categoria_rotulo: pior.categoria_rotulo },
      pm2_5_max: pmMax === null ? null : { municipio: pmMax.municipio, pm2_5: pmMax.pm2_5 },
      por_categoria: porCat
    };
  }

  function montar(corpo, munis, consultadoEm) {
    var linhas = interpretar(corpo, munis);
    var refs = linhas.map(function (x) { return x.referencia_modelo; }).filter(Boolean);
    var manaus = linhas.filter(function (x) { return x.municipio === 'Manaus'; })[0] || null;
    return {
      fonte: FONTE, atribuicao: ATRIBUICAO, estimativa: true, resolucao_km: RESOLUCAO_KM,
      escala: 'US AQI (EPA); não é o IQAr oficial brasileiro',
      consultado_em: consultadoEm,
      referencia_modelo: refs.length ? refs.slice().sort().pop() : null,
      municipios: linhas, manaus: manaus, resumo: resumir(linhas),
      faixas: FAIXAS.map(function (f) { return { ate: f[0] >= 1e9 ? null : f[0], id: f[1], rotulo: f[2] }; }),
      nota_bairros: 'O modelo tem células de ~' + RESOLUCAO_KM + ' km: o valor de Manaus vale para toda a área urbana e não distingue bairros.',
      desatualizado: false
    };
  }

  /* Navegador: baixa a lista de municípios (assets/municipios_am.json) e consulta o Open-Meteo. */
  var ultimo = null;
  function consultar() {
    return fetch('assets/municipios_am.json', { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (munis) {
        var ctl = typeof AbortController === 'function' ? new AbortController() : null;
        var t = ctl ? setTimeout(function () { ctl.abort(); }, TIMEOUT_MS) : null;
        return fetch(URL_API + '?' + montarParams(munis), { signal: ctl ? ctl.signal : undefined })
          .then(function (r) { if (t) clearTimeout(t); if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
          .then(function (corpo) { ultimo = montar(corpo, munis, new Date().toISOString()); return ultimo; });
      })
      .catch(function (e) {
        if (ultimo) { var c = JSON.parse(JSON.stringify(ultimo)); c.desatualizado = true; return c; } // última boa, marcada
        throw e;
      });
  }

  raiz.RespirarArModelo = { montar: montar, interpretar: interpretar, resumir: resumir, montarParams: montarParams, arredondar: arredondar, consultar: consultar };
})(typeof window !== 'undefined' ? window : globalThis);
