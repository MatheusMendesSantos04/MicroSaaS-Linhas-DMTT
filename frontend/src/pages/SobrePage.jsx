export default function SobrePage() {
  return (
    <div className="page-content">
      <h1 className="page-title">Sobre o sistema</h1>

      <p className="page-text">
        O <strong>Linhas DMTT</strong> é um sistema da DMTT (Diretoria de Mobilidade e Trânsito
        de Maceió/AL) para consulta de itinerários de ônibus, criado pelo setor GEPOT.
      </p>

      <h2 className="page-subheading">O que ele resolve</h2>
      <p className="page-text">
        Quando o setor recebe uma reclamação sobre um ônibus, é preciso descobrir qual linha
        passava por determinada rua em determinado horário. Este sistema permite:
      </p>
      <ul className="page-list">
        <li>Visualizar o traçado de qualquer linha no mapa, com os sentidos IDA e VOLTA.</li>
        <li>Ver o itinerário completo (ruas atendidas) e o quadro de horários por linha.</li>
        <li>Buscar por nome de rua e listar todas as linhas que passam ali.</li>
        <li>Filtrar essa busca por horário (janela de ±20 min) para identificar o ônibus provável.</li>
        <li>Clicar em qualquer ponto do mapa para descobrir automaticamente a rua e as linhas que a atendem.</li>
      </ul>

      <h2 className="page-subheading">Dashboards</h2>
      <p className="page-text">
        A seção <strong>Dashboards</strong> reúne os relatórios e indicadores do GEPOT publicados
        no Power BI, centralizando o acesso num único lugar.
      </p>

      <h2 className="page-subheading">Como os dados funcionam</h2>
      <p className="page-text">
        O sistema é totalmente estático — sem servidor rodando em produção. Os dados de linhas,
        itinerários e horários são gerados a partir da base oficial do setor e publicados junto
        com o site.
      </p>
    </div>
  );
}
