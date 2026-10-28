/* Painel SEM relatos, para o site estático (GitHub Pages) enquanto nenhum retrato foi publicado.
 * A página aparece completa (gráficos e mapa zerados, em vez de ficar cinza como desativada) e diz que os
 * relatos serão atualizados ao longo do tempo. Mantido em paridade com publico.montar() de um banco vazio:
 * server/tests/test_painel_vazio_js.py compara os dois (todos os períodos). */
(function (raiz) {
  'use strict';
  raiz.RespirarPainelVazio = function (dias) {
    return {
      gerado_em: null,
      periodo_dias: dias,
      total_respostas: 0,
      suficiente: true,
      minimo_para_divulgar: 0,
      minimo_por_area: 1,
      niveis: { low: 0, moderate: 0, high: 0, emergency: 0 },
      sintomas: [],
      serie_diaria: [],
      bairros: {
        periodo_dias: dias,
        minimo_por_bairro: 1,
        bairros: [],
        areas_em_consulta: 0,
        fonte: 'Bairro obtido do OpenStreetMap (Nominatim) pelo centro de cada área de ~1 km; aproximação, pois uma área pode cruzar divisas de bairros.'
      },
      perfil: { idoso: 0, gestante: 0, crianca: 0, doenca_respiratoria: 0, doenca_cardiaca: 0 },
      exposicao: { under1h: 0, between1and4h: 0, over4h: 0 },
      contexto: {},
      mapa: { horas: Math.min(dias * 24, 720), celulas: [] },
      vazio: true   // só no site estático: a página mostra a mensagem "ainda não há relatos"
    };
  };
})(typeof window !== 'undefined' ? window : globalThis);
