/*
 * Ícones do formulário do site (e do botão que leva a ele). Desenho próprio, em SVG embutido:
 * sem biblioteca externa e sem rede, então a política de segurança (CSP) das páginas não muda.
 *
 * Grade 24x24, traço de 1,8, cantos arredondados, cor = `currentColor` (segue o tema claro/escuro).
 * Cada ícone é só o miolo do <svg> (path, circle, rect, ellipse, line, polyline). A cobertura de
 * perguntas é conferida em tool/test_responder_site.py: pergunta nova sem ícone faz o teste falhar.
 *
 * Os ícones são decorativos (aria-hidden): o texto de cada pergunta já diz o que ela é.
 */
(function (raiz) {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';

  // Pulmões (base de "falta de ar" e "doença respiratória").
  var PULMOES =
    '<path d="M12 3v8"/>' +
    '<path d="M10.5 9c-3.5.5-6 4-6 8 0 2 1 3 2.5 3 2 0 3.5-1 3.5-3z"/>' +
    '<path d="M13.5 9c3.5.5 6 4 6 8 0 2-1 3-2.5 3-2 0-3.5-1-3.5-3z"/>';

  // Coração (base de "aperto no peito", "palpitações" e "doença cardíaca").
  var CORACAO =
    '<path d="M12 20.5C7 17.2 3.5 14 3.5 10.2A4.2 4.2 0 0 1 12 8.2a4.2 4.2 0 0 1 8.5 2C20.5 14 17 17.2 12 20.5z"/>';

  // Cápsula de remédio (base de "medicação à mão" e "remédio não alivia").
  var CAPSULA =
    '<rect x="3" y="8.5" width="18" height="7" rx="3.5" transform="rotate(-45 12 12)"/>' +
    '<path d="M12 8.5v7" transform="rotate(-45 12 12)"/>';

  var ICONES = {
    // --- Etapas ---
    termometro:
      '<path d="M10 14.5V5a2 2 0 0 1 4 0v9.5a4 4 0 1 1-4 0z"/><path d="M12 10v6.5"/>',
    vento:
      '<path d="M3 8h10.5a2.5 2.5 0 1 0-2.5-2.5"/><path d="M3 12h15.5a2.5 2.5 0 1 1-2.5 2.5"/><path d="M3 16h7"/>',
    pessoa:
      '<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    alerta:
      '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5"/><path d="M12 16.5h.01"/>',

    // --- Sintomas (mesmos ids de responder_logica.js) ---
    cough:
      '<ellipse cx="7" cy="12" rx="3.2" ry="4.2"/><path d="M13 9h3.5"/><path d="M13 12h6.5"/><path d="M13 15h3.5"/>' +
      '<path d="M20 7.5h.01"/><path d="M20 16.5h.01"/>',
    throat:
      '<path d="M8 3v5.5c0 1.2.6 2 .6 3.5s-.6 2.3-.6 3.5V21"/><path d="M16 3v5.5c0 1.2-.6 2-.6 3.5s.6 2.3.6 3.5V21"/>' +
      '<path d="M12.8 8.5l-2.4 3.7h3.2l-2.4 3.7"/>',
    nose:
      '<path d="M12 3.5c3 3.8 5.5 6.6 5.5 10a5.5 5.5 0 0 1-11 0c0-3.4 2.5-6.2 5.5-10z"/><path d="M9.5 14a2.5 2.5 0 0 0 2.5 2.5"/>',
    wheeze:
      '<path d="M3 8c1.5-1.5 2.5 1.5 4 0s2.5 1.5 4 0 2.5 1.5 4 0 2.5 1.5 3 0"/>' +
      '<path d="M3 12.5c1.5-1.5 2.5 1.5 4 0s2.5 1.5 4 0 2.5 1.5 4 0 2.5 1.5 3 0"/>' +
      '<path d="M3 17c1.5-1.5 2.5 1.5 4 0s2.5 1.5 4 0"/>',
    dyspnea:
      PULMOES + '<circle cx="19" cy="5" r="3"/><path d="M19 3.8v1.4"/><path d="M19 6.4h.01"/>',
    eyes:
      '<path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>' +
      '<path d="M19.5 17c1 1.2 1.6 2 1.6 2.9a1.6 1.6 0 0 1-3.2 0c0-.9.6-1.7 1.6-2.9z"/>',
    chest:
      CORACAO + '<path d="M2.5 3.5l1.6 1.4"/><path d="M12 1.8v2"/><path d="M21.5 3.5l-1.6 1.4"/>',
    palpitation:
      CORACAO + '<path d="M7 12.5h2.5l1.5-2.5 2.5 5 1.5-2.5H17"/>',
    headache:
      '<path d="M6 10a6 6 0 0 1 12 0c0 2-.7 3-1.5 4.2-.5.8-.5 1.6-.5 2.8v1H9v-3c-1.8-1-3-2.7-3-5z"/>' +
      '<path d="M12.5 6.5L10 10h3l-2.5 3.5"/>',
    dizzy:
      '<path d="M12 11a1.5 1.5 0 0 1 3 0 3.5 3.5 0 0 1-7 0 5.5 5.5 0 0 1 11 0 7.5 7.5 0 0 1-15 0"/>',
    fatigue:
      '<rect x="2.5" y="7.5" width="16" height="9" rx="2"/><path d="M21.5 10.5v3"/><path d="M6 10.5v3"/>',

    // --- Contexto ---
    local:
      '<path d="M12 21s-6.5-5.8-6.5-11a6.5 6.5 0 0 1 13 0c0 5.2-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
    fumaca:
      '<path d="M6.5 18a4 4 0 0 1-.7-7.9 5.5 5.5 0 0 1 10.6-1.2A4.5 4.5 0 0 1 17 18z"/>' +
      '<path d="M9 13.5c1-1 1.5 1 2.5 0s1.5 1 2.5 0"/><path d="M8 21h8"/>',
    relogio:
      '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    mascara:
      '<path d="M6 7.5c4-1.5 8-1.5 12 0v7c0 2.6-2.7 4.5-6 4.5s-6-1.9-6-4.5z"/>' +
      '<path d="M8.5 11h7"/><path d="M8.5 14h7"/>' +
      '<path d="M6 9.5H4a2 2 0 0 0-2 2v1a2 2 0 0 0 2 2h2"/><path d="M18 9.5h2a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2h-2"/>',
    exercicio:
      '<path d="M6.5 6.5v11"/><path d="M17.5 6.5v11"/><path d="M3.5 9v6"/><path d="M20.5 9v6"/><path d="M6.5 12h11"/>',
    trabalho:
      '<path d="M5 16v-2a7 7 0 0 1 14 0v2"/><rect x="3" y="16" width="18" height="3" rx="1"/><path d="M12 7v6"/>',
    filtrado:
      '<path d="M3.5 11L12 4l8.5 7"/><path d="M5.5 10v9.5h13V10"/><path d="M9.5 14.5l2 2 3.5-3.5"/>',

    // --- Sobre você ---
    idoso:
      '<circle cx="10" cy="5.5" r="2.5"/><path d="M10 9v6l-1.5 5"/><path d="M10 15l2 5"/><path d="M10 11.5l-2.5 3"/>' +
      '<path d="M15 20v-8a2 2 0 0 1 4 0"/>',
    gestante:
      '<circle cx="10" cy="4.5" r="2.3"/><path d="M9.5 8.5C8 11 8.5 15 9 19.5v2"/>' +
      '<path d="M9.5 8.5c4.8-.2 7.7 2.8 7.2 6.4-.3 2.2-2 3.6-4.7 3.9"/><path d="M12.5 18.8l.3 2.7"/>',
    crianca:
      '<circle cx="12" cy="13" r="7"/><path d="M12 6c0-1.5 1-2.5 2.5-2.5"/><path d="M9.5 12.5h.01"/><path d="M14.5 12.5h.01"/>' +
      '<path d="M9.5 15.5c1.3 1.2 3.7 1.2 5 0"/>',
    doenca_respiratoria: PULMOES,
    doenca_cardiaca: CORACAO + '<path d="M12 11v4"/><path d="M10 13h4"/>',
    imunologica:
      '<path d="M12 3l7.5 2.8v5.4c0 4.6-3.2 8.2-7.5 9.8-4.3-1.6-7.5-5.2-7.5-9.8V5.8z"/><path d="M12 9.5v5"/><path d="M9.5 12h5"/>',
    medicacao_a_mao: CAPSULA,

    // --- Agora ---
    piorando:
      '<path d="M3.5 17l6-6 4 4 7-8"/><path d="M15 7h5.5v5.5"/>',
    medicacao_nao_alivia:
      CAPSULA + '<circle cx="18" cy="18" r="4.2"/><path d="M16.3 16.3l3.4 3.4"/><path d="M19.7 16.3l-3.4 3.4"/>',

    // --- Resultado, consentimento e botões ---
    nivel_low:
      '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16.3 9.5"/>',
    nivel_moderate:
      '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4.5"/><path d="M12 17.2h.01"/>',
    nivel_high:
      '<path d="M8.2 3h7.6L21 8.2v7.6L15.8 21H8.2L3 15.8V8.2z"/><path d="M12 7.5v5.5"/><path d="M12 16.5h.01"/>',
    nivel_emergency:
      '<path d="M5 4h3.5l1.8 4.5-2.2 1.4a11 11 0 0 0 5 5l1.4-2.2 4.5 1.8V18a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    cadeado:
      '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/><path d="M12 15v2"/>',
    enviar:
      '<path d="M21 3L10.5 13.5"/><path d="M21 3l-6.5 18-4-7.5L3 9.5z"/>',
    ok:
      '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16.3 9.5"/>',
    seta_dir:
      '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
    seta_esq:
      '<path d="M19 12H5"/><path d="M11 6l-6 6 6 6"/>',
    // Botão que leva ao questionário (também desenhado, igual, em publico.html).
    prancheta:
      '<rect x="5" y="4.5" width="14" height="16.5" rx="2.5"/><rect x="9" y="2.5" width="6" height="4" rx="1.5"/>' +
      '<path d="M8 14h2l1.4-3 2.2 6 1.4-3H17"/>'
  };

  /** Devolve um <svg> pronto (decorativo). `tamanho` em px; omitido = 24. */
  function icone(nome, tamanho) {
    if (!Object.prototype.hasOwnProperty.call(ICONES, nome)) return null;
    var s = document.createElementNS(NS, 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('width', String(tamanho || 24));
    s.setAttribute('height', String(tamanho || 24));
    s.setAttribute('fill', 'none');
    s.setAttribute('stroke', 'currentColor');
    s.setAttribute('stroke-width', '1.8');
    s.setAttribute('stroke-linecap', 'round');
    s.setAttribute('stroke-linejoin', 'round');
    s.setAttribute('aria-hidden', 'true');
    s.setAttribute('focusable', 'false');
    s.innerHTML = ICONES[nome];
    return s;
  }

  var api = { ICONES: ICONES, icone: icone };
  raiz.RespirarIcones = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
