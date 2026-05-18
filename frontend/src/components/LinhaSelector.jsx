export default function LinhaSelector({ linhas, selectedLinhaId, selectedSentido, onSelectLinha, onSelectSentido }) {
  return (
    <div className="controls">
      <label className="control-group">
        <span className="control-label">Linha</span>
        <select
          value={selectedLinhaId}
          onChange={(e) => onSelectLinha(e.target.value)}
          className="control-select"
        >
          <option value="">Todas as linhas</option>
          {linhas.map((linha) => (
            <option key={linha.id} value={linha.id}>
              {linha.nome}
            </option>
          ))}
        </select>
      </label>

      <label className="control-group">
        <span className="control-label">Sentido</span>
        <select
          value={selectedSentido}
          onChange={(e) => onSelectSentido(e.target.value)}
          className="control-select"
        >
          <option value="ambos">Ida e Volta</option>
          <option value="ida">Somente Ida</option>
          <option value="volta">Somente Volta</option>
        </select>
      </label>
    </div>
  );
}
