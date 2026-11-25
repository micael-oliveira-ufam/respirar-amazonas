/*
 * Lógica do questionário no site (sem DOM, testável em Node).
 *
 * Espelha, campo a campo, o app Flutter:
 *   - pontuação e níveis: lib/logic/risk_assessment.dart (função `assess`);
 *   - JSON enviado ao Firestore: lib/services/api_client.dart (`buildAnswerPayload`);
 *   - valores de contexto: lib/models/smoke_context.dart (`toPayload`).
 * Se algo mudar no app, mude aqui também: o teste tool/test_responder_site.py compara
 * os valores com o gabarito do Dart e com as listas de campos de firebase/firestore.rules.
 *
 * ATENÇÃO (mesma ressalva do app): pesos e limiares são PROVISÓRIOS, escolha do projeto,
 * sem validação clínica. Não é diagnóstico.
 */
(function (raiz) {
  'use strict';

  var SINTOMAS = [
    { id: 'cough', rotulo: 'Tosse', consequencia: 'respiratory' },
    { id: 'throat', rotulo: 'Irritação ou dor na garganta', consequencia: 'respiratory' },
    { id: 'nose', rotulo: 'Coriza ou nariz irritado', consequencia: 'respiratory' },
    { id: 'wheeze', rotulo: 'Chiado no peito', consequencia: 'respiratory' },
    { id: 'dyspnea', rotulo: 'Falta de ar', consequencia: 'respiratory', sinalAlerta: true },
    { id: 'eyes', rotulo: 'Olhos ardendo, vermelhos ou lacrimejando', consequencia: 'ocular' },
    { id: 'chest', rotulo: 'Aperto ou dor no peito', consequencia: 'cardiovascular', sinalAlerta: true },
    { id: 'palpitation', rotulo: 'Palpitações ou batimentos irregulares', consequencia: 'cardiovascular' },
    { id: 'headache', rotulo: 'Dor de cabeça', consequencia: 'neurological' },
    { id: 'dizzy', rotulo: 'Tontura ou confusão', consequencia: 'neurological', sinalAlerta: true },
    { id: 'fatigue', rotulo: 'Cansaço fora do normal', consequencia: 'general' }
  ];

  var PONTOS_EXPOSICAO = { under1h: 0, between1and4h: 2, over4h: 4 };
  var PONTOS_VULNERAVEL = 3;
  var LIMIAR_MODERADO = 8;
  var LIMIAR_ALTO = 15;

  var ROTULOS_GRAVIDADE = ['Nenhum', 'Leve', 'Moderado', 'Intenso'];
  var ROTULOS_NIVEL = {
    low: 'Risco baixo',
    moderate: 'Risco moderado',
    high: 'Risco alto',
    emergency: 'Procure atendimento agora'
  };

  /**
   * Avalia o risco (mesma regra do Dart). `gravidades` = { id: 0..3 } para os 11 sintomas;
   * ausente = 0. `exposicao` = 'under1h' | 'between1and4h' | 'over4h'.
   * `perfil` = { idoso, gestante, crianca, doenca_respiratoria, doenca_cardiaca } (booleanos).
   */
  function avaliar(gravidades, exposicao, perfil) {
    var p = perfil || {};
    var soma = 0;
    var sinalGravePresente = false;
    var totais = {};
    SINTOMAS.forEach(function (item) {
      var s = gravidades && gravidades[item.id] !== undefined ? gravidades[item.id] : 0;
      if (typeof s !== 'number' || s < 0 || s > 3 || Math.floor(s) !== s) {
        throw new RangeError('Gravidade de ' + item.id + ' deve ser 0, 1, 2 ou 3.');
      }
      soma += s;
      totais[item.consequencia] = (totais[item.consequencia] || 0) + s;
      if (item.sinalAlerta && s === 3) sinalGravePresente = true;
    });

    var faltaDeArCronica = (gravidades && (gravidades.dyspnea || 0)) >= 2 &&
      (!!p.doenca_respiratoria || !!p.doenca_cardiaca);
    var emergencia = sinalGravePresente || faltaDeArCronica;

    var vulneravel = !!(p.idoso || p.gestante || p.crianca || p.doenca_respiratoria || p.doenca_cardiaca);
    if (!(exposicao in PONTOS_EXPOSICAO)) {
      throw new RangeError('Exposição desconhecida: ' + exposicao);
    }
    var pontos = soma + PONTOS_EXPOSICAO[exposicao] + (vulneravel ? PONTOS_VULNERAVEL : 0);

    var nivel = emergencia ? 'emergency'
      : pontos >= LIMIAR_ALTO ? 'high'
      : pontos >= LIMIAR_MODERADO ? 'moderate'
      : 'low';

    var efeitos = Object.keys(totais).filter(function (k) { return totais[k] >= 2; });
    return { nivel: nivel, pontos: pontos, efeitos: efeitos };
  }

  /** Arredonda a 2 casas como o Dart (`(v * 100).round() / 100`: meio arredonda para longe de zero). */
  function arredondar2(v) {
    return Math.sign(v) * Math.round(Math.abs(v) * 100) / 100;
  }

  /** Converte as respostas de contexto no formato `contexto` da API (só o que foi respondido). */
  function contextoParaPayload(ctx) {
    var c = ctx || {};
    var out = {};
    if (c.local) out.local = c.local;
    if (typeof c.fumaca_visivel === 'boolean') out.fumaca_visivel = c.fumaca_visivel;
    if (c.mascara) out.mascara = c.mascara;
    if (typeof c.atividade_fisica_ar_livre === 'boolean') out.atividade_fisica_ar_livre = c.atividade_fisica_ar_livre;
    if (typeof c.ar_filtrado === 'boolean') out.ar_filtrado = c.ar_filtrado;
    if (typeof c.trabalho_ar_livre === 'boolean') out.trabalho_ar_livre = c.trabalho_ar_livre;
    if (typeof c.imunologica === 'boolean') out.imunologica = c.imunologica;
    if (typeof c.medicacao_a_mao === 'boolean') out.medicacao_a_mao = c.medicacao_a_mao;
    if (typeof c.medicacao_nao_alivia === 'boolean') out.medicacao_nao_alivia = c.medicacao_nao_alivia;
    if (typeof c.piorando === 'boolean') out.piorando = c.piorando;
    return out;
  }

  /**
   * Monta o documento que vai para `respostas/{submission_id}` (sem `recebido_em`, que é
   * acrescentado com a hora do servidor do Firebase na hora da gravação).
   * `resposta` = { submissionId, registradoEm (Date), gravidades, exposicao, perfil,
   *                contexto, localizacao: {lat, lon} | null, appVersion }
   */
  function montarPayload(resposta) {
    var r = avaliar(resposta.gravidades, resposta.exposicao, resposta.perfil);
    var gravidades = resposta.gravidades || {};
    var sintomas = {};
    SINTOMAS.forEach(function (item) {
      sintomas[item.id] = gravidades[item.id] !== undefined ? gravidades[item.id] : 0;
    });
    var perfil = resposta.perfil || {};
    var payload = {
      submission_id: resposta.submissionId,
      registrado_em: resposta.registradoEm.toISOString(),
      nivel: r.nivel,
      pontos: r.pontos,
      exposicao: resposta.exposicao,
      perfil: {
        idoso: !!perfil.idoso,
        gestante: !!perfil.gestante,
        crianca: !!perfil.crianca,
        doenca_respiratoria: !!perfil.doenca_respiratoria,
        doenca_cardiaca: !!perfil.doenca_cardiaca
      },
      sintomas: sintomas,
      app_version: resposta.appVersion || 'site'
    };
    var loc = resposta.localizacao;
    if (loc && isFinite(loc.lat) && isFinite(loc.lon) &&
        Math.abs(loc.lat) <= 90 && Math.abs(loc.lon) <= 180) {
      payload.lat = arredondar2(loc.lat);
      payload.lon = arredondar2(loc.lon);
    }
    var contexto = contextoParaPayload(resposta.contexto);
    if (Object.keys(contexto).length > 0) payload.contexto = contexto;
    return { payload: payload, resultado: r };
  }

  /** UUID v4 (36 caracteres), como o `newSubmissionId` do app. */
  function novoSubmissionId(cripto) {
    var c = cripto || (typeof crypto !== 'undefined' ? crypto : null);
    if (c && typeof c.randomUUID === 'function') return c.randomUUID();
    var b = new Uint8Array(16);
    c.getRandomValues(b);
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    var h = Array.prototype.map.call(b, function (x) { return ('0' + x.toString(16)).slice(-2); }).join('');
    return h.slice(0, 8) + '-' + h.slice(8, 12) + '-' + h.slice(12, 16) + '-' + h.slice(16, 20) + '-' + h.slice(20);
  }

  var api = {
    SINTOMAS: SINTOMAS,
    ROTULOS_GRAVIDADE: ROTULOS_GRAVIDADE,
    ROTULOS_NIVEL: ROTULOS_NIVEL,
    PONTOS_EXPOSICAO: PONTOS_EXPOSICAO,
    PONTOS_VULNERAVEL: PONTOS_VULNERAVEL,
    LIMIAR_MODERADO: LIMIAR_MODERADO,
    LIMIAR_ALTO: LIMIAR_ALTO,
    avaliar: avaliar,
    arredondar2: arredondar2,
    contextoParaPayload: contextoParaPayload,
    montarPayload: montarPayload,
    novoSubmissionId: novoSubmissionId
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  raiz.RespirarResponder = api;
})(typeof window !== 'undefined' ? window : globalThis);
