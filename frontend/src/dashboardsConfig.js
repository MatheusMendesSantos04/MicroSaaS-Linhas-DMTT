// Dashboards do Power BI publicados pelo GEPOT.
// tipo: "publico" (link de "Publicar na Web", sem login) ou "interno" (compartilhamento
// autenticado do Power BI — só quem tem conta na organização acessa).
// imagem: import de um screenshot do dashboard (opcional) — mostrado como capa do card.
// indicadores: lista curta do que o dashboard permite identificar (opcional).

import detalhamentoPorLinha from "./assets/dashboards/detalhamento-por-linha.png";

export const DASHBOARDS = [
  {
    titulo: "DETALHAMENTO POR LINHA",
    descricao: "Cumprimento de itinerário e transporte de passageiros, por linha.",
    indicadores: [
      "Índice de partidas realizadas",
      "Índice de partidas não realizadas",
      "Índice de partidas pontuais",
      "Índice de partidas atrasadas",
      "Total de passageiros",
      "Passageiro por viagem",
    ],
    imagem: detalhamentoPorLinha,
    link: "https://app.powerbi.com/view?r=eyJrIjoiOGM2NzAwNDEtNmY5MC00NmRlLWE3ZDctOWM4NzU1MTdmNTdmIiwidCI6IjEzOWMwYTg0LWI0ZTQtNGU0ZS04NWU5LWZjZGU3YTBhMjk3MCJ9",
    tipo: "publico",
  },
];
