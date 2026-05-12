export default function ConfigPanel({
  config,
  form,
  setForm,
  strategy,
  setStrategy,
  onCompare,
  onSimulate,
  loading,
}) {
  function updateField(field, value) {
    const numericFields = new Set(['seed', 'bandwidthKbps', 'latencyMs', 'initialChunkProbability']);
    setForm((prev) => ({ ...prev, [field]: numericFields.has(field) ? Number(value) : value }));
  }

  return (
    <section className="card config-panel">
      <div>
        <h2>Simulation Config</h2>
        <p className="muted">
          Default: {config?.file_size_mb || 10}MB file, {config?.chunk_size_kb || 256}KB/chunk,
          {' '}{config?.totalChunks || 40} chunks, {config?.peer_count || 10} peers.
        </p>
      </div>

      <div className="form-grid">
        <label>
          Seed
          <input type="number" value={form.seed} onChange={(e) => updateField('seed', e.target.value)} />
        </label>
        <label>
          Bandwidth (KB/s)
          <input
            type="number"
            min="1"
            value={form.bandwidthKbps}
            onChange={(e) => updateField('bandwidthKbps', e.target.value)}
          />
        </label>
        <label>
          Latency (ms)
          <input
            type="number"
            min="0"
            value={form.latencyMs}
            onChange={(e) => updateField('latencyMs', e.target.value)}
          />
        </label>
        <label>
          Initial probability
          <input
            type="number"
            min="0.05"
            max="0.95"
            step="0.01"
            value={form.initialChunkProbability}
            onChange={(e) => updateField('initialChunkProbability', e.target.value)}
          />
        </label>
        <label>
          Single strategy
          <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
            <option value="randomFirst">Random-First</option>
            <option value="rarestFirst">Rarest-First</option>
          </select>
        </label>
      </div>

      <div className="button-row">
        <button onClick={onCompare} disabled={loading}>{loading ? 'Running...' : 'Compare strategies'}</button>
        <button className="secondary" onClick={onSimulate} disabled={loading}>Run selected strategy</button>
      </div>
    </section>
  );
}
