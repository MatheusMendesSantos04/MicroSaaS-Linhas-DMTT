// Adicione aqui os dashboards do Power BI conforme forem publicados.
// tipo: "publico" (link de "Publicar na Web", sem login) ou "interno" (compartilhamento
// autenticado do Power BI — só quem tem conta na organização acessa).
//
// Exemplo:
// {
//   titulo: "Frota e Quilometragem",
//   descricao: "Acompanhamento mensal de quilometragem rodada por linha.",
//   link: "https://app.powerbi.com/view?r=...",
//   tipo: "interno",
// },

// EXEMPLOS — substituir pelos dashboards reais assim que forem publicados no Power BI.
export const DASHBOARDS = [
  {
    titulo: "Frota e Quilometragem",
    descricao: "Acompanhamento mensal de quilometragem rodada por linha e por motorista.",
    link: "https://app.powerbi.com/view?r=EXEMPLO-frota-km",
    tipo: "interno",
  },
  {
    titulo: "Itinerários e Pontos de Parada",
    descricao: "Visão consolidada de linhas, ruas atendidas e pontos de parada por bairro.",
    link: "https://app.powerbi.com/view?r=EXEMPLO-itinerarios",
    tipo: "publico",
  },
  {
    titulo: "Indicadores Mensais GEPOT",
    descricao: "Painel de indicadores do setor: relatórios entregues, prazos e pendências.",
    link: "https://app.powerbi.com/view?r=EXEMPLO-indicadores",
    tipo: "interno",
  },
];
