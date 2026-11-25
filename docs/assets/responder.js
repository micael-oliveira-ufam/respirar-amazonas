/*
 * Formulário do questionário no site. Perguntas, ordem e textos espelham o app Flutter
 * (lib/screens/questionnaire_screen.dart). Cálculo e JSON: responder_logica.js.
 * Termo de consentimento: responder_termo.js (gerado de lib/data/lgpd_terms.dart).
 */
(function () {
  'use strict';

  var L = window.RespirarResponder;
  var T = window.RESPIRAR_TERMO;
  var FB = window.RESPIRAR_FIREBASE_WEB;
  var VERSAO_SDK = '13.3.0'; // Firebase JS SDK (gstatic). Ver tool/test_responder_site.py.
  var BASE_SDK = 'https://www.gstatic.com/firebasejs/' + VERSAO_SDK + '/';
  var PRAZO_ENVIO_MS = 20000;
  // Texto copiado do app (lib/data/references.dart, `scoringNotice`). Testado em tool/test_responder_site.py.
  var TEXTO_PONTUACAO = 'A classificação em baixo, moderado, alto e emergência usa pontos por sintoma, tempo de ' +
    'exposição e perfil, com limiares (8 e 15 pontos) definidos pelo projeto. Eles NÃO vêm ' +
    'de uma escala clínica validada nem das fontes acima e não foram testados com pacientes. ' +
    'Trate o resultado como orientação educativa, não como diagnóstico.';

  var EXPOSICOES = [
    { v: 'under1h', r: 'Menos de 1 h' },
    { v: 'between1and4h', r: '1 a 4 h' },
    { v: 'over4h', r: 'Mais de 4 h' }
  ];

  var PERFIS = [
    { k: 'idoso', r: 'Tenho 60 anos ou mais' },
    { k: 'gestante', r: 'Estou grávida' },
    { k: 'crianca', r: 'Sou criança (menos de 12 anos)' },
    { k: 'doenca_respiratoria', r: 'Asma, DPOC ou outra doença respiratória crônica' },
    { k: 'doenca_cardiaca', r: 'Doença cardíaca crônica' }
  ];

  var LOCAIS = [
    { v: 'ar_livre', r: 'Ao ar livre' },
    { v: 'casa_janelas_abertas', r: 'Dentro, janelas abertas' },
    { v: 'casa_janelas_fechadas', r: 'Dentro, janelas fechadas' }
  ];

  var MASCARAS = [
    { v: 'nao_saiu', r: 'Não saí' },
    { v: 'nao', r: 'Sem máscara' },
    { v: 'cirurgica_pano', r: 'Cirúrgica ou pano' },
    { v: 'pff2_n95', r: 'PFF2 / N95' }
  ];

  // Perguntas de contexto sim/não (não entram na pontuação). `campo` = chave do contexto.
  var SIM_NAO = {
    visivel: { campo: 'fumaca_visivel', r: 'Dá para ver ou sentir cheiro de fumaça?' },
    exercicio: { campo: 'atividade_fisica_ar_livre', r: 'Fez exercício intenso ao ar livre hoje?' },
    trabalho: { campo: 'trabalho_ar_livre', r: 'Seu trabalho é ao ar livre?' },
    filtrado: { campo: 'ar_filtrado', r: 'Você tem ar filtrado ou um cômodo protegido para ficar?', ajuda: 'Ar-condicionado com filtro, purificador de ar ou um cômodo fechado com menos fumaça.' },
    imunidade: { campo: 'imunologica', r: 'Tem doença ou usa remédio que reduz a imunidade?' },
    medicacao: { campo: 'medicacao_a_mao', r: 'Se usa medicação para o pulmão ou o coração, ela está à mão?', ajuda: 'Se não usa nenhuma, escolha "Não sei" ou pule.' },
    piorando: { campo: 'piorando', r: 'Os sintomas estão piorando?' },
    naoAlivia: { campo: 'medicacao_nao_alivia', r: 'Você tomou o seu remédio de costume e os sintomas continuam?', ajuda: 'Pense no remédio que você já usa para falta de ar, asma, bronquite ou coração. Responda "Sim" se tomou e não melhorou. Se você não usa nenhum desses remédios, escolha "Não sei".' }
  };

  var estado = {
    etapa: 0,
    gravidades: {},
    exposicao: 'under1h',
    perfil: {},
    contexto: {},
    resultado: null,
    submissionId: null,
    payload: null,
    enviando: false,
    enviado: false
  };
  var ETAPAS = 4;

  function $(id) { return document.getElementById(id); }

  function el(tag, attrs, filhos) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (filhos || []).forEach(function (f) { if (f) n.appendChild(f); });
    return n;
  }

  var contadorGrupo = 0;

  /** Grupo de rádios; `valorInicial` pode ser null ("Não sei" é a opção de valor null). */
  function grupoRadio(rotulo, opcoes, valorAtual, aoMudar, ajuda) {
    var nome = 'g' + (++contadorGrupo);
    var linha = el('div', { class: 'resp-linha', role: 'radiogroup', 'aria-label': rotulo });
    opcoes.forEach(function (o) {
      var id = nome + '_' + String(o.v);
      var input = el('input', { type: 'radio', name: nome, id: id, value: String(o.v) });
      if (valorAtual === o.v) input.checked = true;
      input.addEventListener('change', function () { aoMudar(o.v); });
      linha.appendChild(el('label', { for: id }, [input, document.createTextNode(o.r)]));
    });
    return el('div', null, [
      el('h2', { text: rotulo }),
      ajuda ? el('p', { class: 'ajuda', text: ajuda }) : null,
      linha
    ]);
  }

  function simNao(rotulo, campo, ajuda) {
    var atual = estado.contexto[campo];
    var opcoes = [
      { v: 'sim', r: 'Sim' }, { v: 'nao', r: 'Não' }, { v: 'nsei', r: 'Não sei' }
    ];
    var valor = atual === true ? 'sim' : atual === false ? 'nao' : (atual === null ? 'nsei' : undefined);
    return grupoRadio(rotulo, opcoes, valor, function (v) {
      estado.contexto[campo] = v === 'sim' ? true : v === 'nao' ? false : null;
    }, ajuda);
  }

  function construirSintomas() {
    var secao = $('etapa-0');
    secao.innerHTML = '';
    secao.appendChild(el('h2', { text: 'O que você sente agora?' }));
    secao.appendChild(el('p', { class: 'ajuda', text: 'Escolha a intensidade de cada sintoma. Sem marcar, vale "Nenhum".' }));
    L.SINTOMAS.forEach(function (item) {
      var fieldset = el('fieldset', { class: 'resp-sintoma' });
      fieldset.appendChild(el('legend', { text: item.rotulo }));
      var linha = el('div', { class: 'resp-linha' });
      L.ROTULOS_GRAVIDADE.forEach(function (rot, valor) {
        var id = 's_' + item.id + '_' + valor;
        var input = el('input', { type: 'radio', name: 's_' + item.id, id: id, value: String(valor) });
        if ((estado.gravidades[item.id] || 0) === valor) input.checked = true;
        input.addEventListener('change', function () { estado.gravidades[item.id] = valor; });
        linha.appendChild(el('label', { for: id }, [input, document.createTextNode(rot)]));
      });
      fieldset.appendChild(linha);
      secao.appendChild(fieldset);
    });
  }

  function construirExposicao() {
    var secao = $('etapa-1');
    secao.innerHTML = '';
    secao.appendChild(grupoRadio('Onde você está agora?', LOCAIS, estado.contexto.local || null, function (v) { estado.contexto.local = v; }));
    secao.appendChild(simNao('Dá para ver ou sentir cheiro de fumaça?', SIM_NAO.visivel.campo));
    secao.appendChild(grupoRadio('Quanto tempo ficou ao ar livre hoje?', EXPOSICOES, estado.exposicao, function (v) { estado.exposicao = v; },
      'Soma do dia todo. Os cortes de 1 h e 4 h são escolha do projeto.'));
    secao.appendChild(grupoRadio('Que proteção usou ao sair hoje?', MASCARAS, estado.contexto.mascara || null, function (v) { estado.contexto.mascara = v; }));
    secao.appendChild(simNao(SIM_NAO.exercicio.r, SIM_NAO.exercicio.campo));
    secao.appendChild(simNao(SIM_NAO.trabalho.r, SIM_NAO.trabalho.campo));
    secao.appendChild(simNao(SIM_NAO.filtrado.r, SIM_NAO.filtrado.campo, SIM_NAO.filtrado.ajuda));
  }

  function construirSobreVoce() {
    var secao = $('etapa-2');
    secao.innerHTML = '';
    secao.appendChild(el('h2', { text: 'Algum destes se aplica a você?' }));
    secao.appendChild(el('p', { class: 'ajuda', text: 'Esses grupos têm maior risco com a fumaça. Toque para marcar.' }));
    var linha = el('div', { class: 'resp-linha' });
    PERFIS.forEach(function (p) {
      var id = 'p_' + p.k;
      var input = el('input', { type: 'checkbox', id: id });
      input.checked = !!estado.perfil[p.k];
      input.addEventListener('change', function () { estado.perfil[p.k] = input.checked; });
      linha.appendChild(el('label', { for: id }, [input, document.createTextNode(p.r)]));
    });
    secao.appendChild(linha);
    secao.appendChild(simNao(SIM_NAO.imunidade.r, SIM_NAO.imunidade.campo));
    secao.appendChild(simNao(SIM_NAO.medicacao.r, SIM_NAO.medicacao.campo, SIM_NAO.medicacao.ajuda));
  }

  function construirAgora() {
    var secao = $('etapa-3');
    secao.innerHTML = '';
    secao.appendChild(simNao(SIM_NAO.piorando.r, SIM_NAO.piorando.campo));
    secao.appendChild(simNao(SIM_NAO.naoAlivia.r, SIM_NAO.naoAlivia.campo, SIM_NAO.naoAlivia.ajuda));
  }

  function mostrarEtapa() {
    for (var i = 0; i < ETAPAS; i++) $('etapa-' + i).hidden = i !== estado.etapa;
    $('voltar').hidden = estado.etapa === 0;
    $('continuar').textContent = estado.etapa === ETAPAS - 1 ? 'Ver minha orientação' : 'Continuar';
    $('progresso').textContent = 'Etapa ' + (estado.etapa + 1) + ' de ' + ETAPAS;
    window.scrollTo(0, 0);
  }

  function ir(etapa) {
    estado.etapa = etapa;
    mostrarEtapa();
  }

  function calcularResultado() {
    var resposta = {
      submissionId: L.novoSubmissionId(),
      registradoEm: new Date(),
      gravidades: estado.gravidades,
      exposicao: estado.exposicao,
      perfil: estado.perfil,
      contexto: estado.contexto,
      localizacao: null,
      appVersion: 'site'
    };
    var montado = L.montarPayload(resposta);
    estado.resultado = montado.resultado;
    estado.payload = montado.payload;
    estado.submissionId = resposta.submissionId;
    estado.registradoEm = resposta.registradoEm;
    mostrarResultado();
  }

  function mostrarResultado() {
    var r = estado.resultado;
    var secao = $('resultado');
    secao.hidden = false;
    secao.innerHTML = '';
    secao.appendChild(el('h2', { text: 'Sua orientação' }));
    var emergencia = r.nivel === 'emergency';
    secao.appendChild(el('div', { class: 'resp-aviso' + (emergencia ? ' emergencia' : ''), text: L.ROTULOS_NIVEL[r.nivel] }));
    if (emergencia) {
      secao.appendChild(el('p', { class: 'resp-aviso emergencia' }, [
        el('a', { href: 'tel:192', text: 'Ligar SAMU 192' })
      ]));
    }
    secao.appendChild(el('p', { class: 'ajuda', text: 'Pontuação: ' + r.pontos + '. ' + TEXTO_PONTUACAO }));
    secao.appendChild(el('p', { class: 'ajuda', text: 'O app RespirAR Amazonas traz as orientações completas para cada nível de risco.' }));
    $('consentimento').hidden = false;
    $('consentimento').scrollIntoView({ behavior: 'smooth', block: 'start' });
    ocultarNavegacao();
  }

  function ocultarNavegacao() {
    $('formulario').hidden = true;
    $('navegacao').hidden = true;
  }

  function montarTermo() {
    $('resumo-termo').textContent = T.resumo;
    $('versao-termo').textContent = T.versao;
    $('rotulo-caixa').textContent = T.rotuloCaixa;
    var corpo = $('texto-termo');
    corpo.innerHTML = '';
    T.secoes.forEach(function (s) {
      corpo.appendChild(el('h3', { text: s.titulo }));
      s.paragrafos.forEach(function (p) { corpo.appendChild(el('p', { text: p })); });
    });
    if (!FB) {
      $('status').textContent = 'Envio indisponível no momento. As respostas não foram enviadas.';
      $('enviar').disabled = true;
    }
  }

  function atualizarBotaoEnviar() {
    $('enviar').disabled = !$('aceite-termo').checked || !FB || estado.enviando;
  }

  function pedirLocalizacao() {
    return new Promise(function (resolve) {
      if (!navigator.geolocation) return resolve(null);
      navigator.geolocation.getCurrentPosition(
        function (p) { resolve({ lat: p.coords.latitude, lon: p.coords.longitude }); },
        function () { resolve(null); },
        { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 }
      );
    });
  }

  var promessaFirebase = null;
  function carregarFirestore() {
    if (!promessaFirebase) {
      promessaFirebase = Promise.all([
        import(BASE_SDK + 'firebase-app.js'),
        import(BASE_SDK + 'firebase-firestore.js')
      ]).then(function (mods) {
        var app = mods[0].initializeApp(FB, 'respirar-site');
        var db = mods[1].getFirestore(app);
        return { db: db, doc: mods[1].doc, setDoc: mods[1].setDoc, serverTimestamp: mods[1].serverTimestamp };
      });
    }
    return promessaFirebase;
  }

  function prazo(promessa, ms) {
    return new Promise(function (resolve, reject) {
      var t = setTimeout(function () { reject(new Error('prazo')); }, ms);
      promessa.then(function (v) { clearTimeout(t); resolve(v); }, function (e) { clearTimeout(t); reject(e); });
    });
  }

  function mensagemDeErro(e) {
    if (e && e.message === 'prazo') return 'Sem resposta do servidor agora. Tente de novo em instantes.';
    if (e && e.code === 'permission-denied') {
      return 'O servidor não confirmou o envio. Se você já enviou antes, não precisa repetir.';
    }
    return 'Não foi possível enviar agora. Tente de novo em instantes.';
  }

  async function enviar() {
    if (estado.enviando || estado.enviado) return;
    estado.enviando = true;
    atualizarBotaoEnviar();
    $('status').textContent = 'Enviando suas respostas…';
    try {
      var payload = Object.assign({}, estado.payload);
      if ($('aceite-localizacao').checked) {
        var loc = await pedirLocalizacao();
        if (loc) {
          payload.lat = L.arredondar2(loc.lat);
          payload.lon = L.arredondar2(loc.lon);
        }
      }
      var fb = await prazo(carregarFirestore(), PRAZO_ENVIO_MS);
      var dados = Object.assign({}, payload, { recebido_em: fb.serverTimestamp() });
      await prazo(fb.setDoc(fb.doc(fb.db, 'respostas', estado.submissionId), dados), PRAZO_ENVIO_MS);
      estado.enviado = true;
      ocultarConsentimento();
      $('mensagem-final').textContent = 'Obrigado! Suas respostas foram enviadas, sem identificação.';
      $('concluido').hidden = false;
    } catch (e) {
      $('status').textContent = mensagemDeErro(e);
    } finally {
      estado.enviando = false;
      atualizarBotaoEnviar();
    }
  }

  function ocultarConsentimento() {
    $('consentimento').hidden = true;
  }

  function naoEnviar() {
    ocultarConsentimento();
    $('mensagem-final').textContent = 'Tudo bem. Suas respostas não foram enviadas.';
    $('concluido').hidden = false;
  }

  function iniciar() {
    if (!L || !T) {
      $('status').textContent = 'Não foi possível carregar o questionário. Recarregue a página.';
      return;
    }
    construirSintomas();
    construirExposicao();
    construirSobreVoce();
    construirAgora();
    montarTermo();
    mostrarEtapa();

    $('voltar').addEventListener('click', function () { if (estado.etapa > 0) ir(estado.etapa - 1); });
    $('continuar').addEventListener('click', function () {
      if (estado.etapa < ETAPAS - 1) {
        ir(estado.etapa + 1);
      } else {
        calcularResultado();
      }
    });
    $('aceite-termo').addEventListener('change', atualizarBotaoEnviar);
    $('enviar').addEventListener('click', enviar);
    $('nao-enviar').addEventListener('click', naoEnviar);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
