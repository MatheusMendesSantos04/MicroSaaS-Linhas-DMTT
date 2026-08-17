// Dashboards do Power BI publicados pelo GEPOT.
// tipo: "publico" (link de "Publicar na Web", sem login) ou "interno" (compartilhamento
// autenticado do Power BI — só quem tem conta na organização acessa).
// imagem: import de um screenshot do dashboard (opcional) — mostrado como capa do card.
// indicadores: lista curta do que o dashboard permite identificar (opcional).

import detalhamentoPorLinha from "./assets/dashboards/detalhamento-por-linha.png";
import passeLivreEstudantil from "./assets/dashboards/passe-livre-estudantil.png";
import domingoLivreCidadao from "./assets/dashboards/domingo-livre-cidadao.png";
import onibusDaMulher from "./assets/dashboards/onibus-da-mulher.png";

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
  {
    titulo: "PASSE LIVRE ESTUDANTIL",
    descricao: "Acompanhamento da gratuidade no transporte público de Maceió.",
    indicadores: [
      "Total de gratuidade",
      "Custo total",
      "Média mensal de gratuidade",
      "Média mensal de custo",
      "Mês com maior/menor gratuidade",
      "Gratuidade e custo por empresa",
    ],
    imagem: passeLivreEstudantil,
    link: "https://app.powerbi.com/view?r=eyJrIjoiNmM2ZmM3YTYtNjM4ZS00OTI2LThlZTctNDg0Nzk1NmI2ZTU3IiwidCI6IjEzOWMwYTg0LWI0ZTQtNGU0ZS04NWU5LWZjZGU3YTBhMjk3MCJ9",
    tipo: "publico",
  },
  {
    titulo: "DOMINGO LIVRE CIDADÃO",
    descricao: "Acompanhamento de usuários e custo do programa Domingo Livre no transporte público de Maceió.",
    indicadores: [
      "Total de cidadãos atendidos",
      "Custo total",
      "Média mensal de cidadãos",
      "Média mensal de custo",
      "Mês com maior/menor uso",
      "Cidadãos e custo por ano",
    ],
    imagem: domingoLivreCidadao,
    link: "https://app.powerbi.com/view?r=eyJrIjoiODUxY2E5MjctODIzNC00YTc5LWExZDQtMTVkMWI5NDE1NTA2IiwidCI6IjEzOWMwYTg0LWI0ZTQtNGU0ZS04NWU5LWZjZGU3YTBhMjk3MCJ9",
    tipo: "publico",
  },
  {
    titulo: "ÔNIBUS DA MULHER",
    descricao: "Prioridade e segurança para mulheres no transporte público de Maceió.",
    indicadores: [
      "Viagens realizadas",
      "Passageiros ida e volta",
      "Total de passageiros",
      "Ida vs volta por linha",
      "Participação por empresa",
    ],
    imagem: onibusDaMulher,
    link: "https://app.powerbi.com/view?r=eyJrIjoiOTNkMTBhMTMtZGIxNC00OWYzLWJmOWYtN2QxNjExMWM4MjRhIiwidCI6IjEzOWMwYTg0LWI0ZTQtNGU0ZS04NWU5LWZjZGU3YTBhMjk3MCJ9",
    tipo: "publico",
  },
];
