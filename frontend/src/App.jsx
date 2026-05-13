import { useEffect, useMemo, useState } from 'react';
import { compareStrategies, getConfig, simulate } from './api/client.js';
import ConfigPanel from './components/ConfigPanel.jsx';
import MetricsPanel from './components/MetricsPanel.jsx';
import StrategyComparison from './components/StrategyComparison.jsx';
import PeerProgressTable from './components/PeerProgressTable.jsx';
import TransferLog from './components/TransferLog.jsx';
import PeerNetworkGraph from './components/PeerNetworkGraph.jsx';
import TimelineReplay from './components/TimelineReplay.jsx';

export default function App() {
  const [config, setConfig] = useState(null);
  const [form, setForm] = useState({
    seed: 9,
    bandwidthKbps: 512,
    latencyMs: 50,
    initialChunkProbability: 0.15,
  });
  const [strategy, setStrategy] = useState('rarestFirst');
  const [compareResult, setCompareResult] = useState(null);
  const [singleResult, setSingleResult] = useState(null);
  const [selectedView, setSelectedView] = useState('rarestFirst');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getConfig()
      .then((data) => {
        setConfig(data);
        setForm((prev) => ({
          ...prev,
          seed: data.seed,
          bandwidthKbps: data.bandwidth_kbps ?? data.bandwidthKbps ?? 512,
          latencyMs: data.latency_ms ?? data.latencyMs ?? 50,
          // initialChunkProbability: data.initial_chunk_probability ?? 0.28,
          initialChunkProbability: data.initial_chunk_probability ?? data.initialChunkProbability ?? 0.15,
        }));
      })
      .catch((err) => setError(err.message));
  }, []);

  const activeResult = useMemo(() => {
    if (compareResult) return compareResult[selectedView];
    return singleResult;
  }, [compareResult, selectedView, singleResult]);

  async function handleCompare() {
    setLoading(true);
    setError('');
    setSingleResult(null);
    try {
      const result = await compareStrategies(form);
      setCompareResult(result);
      setSelectedView(result.winner === 'randomFirst' ? 'randomFirst' : 'rarestFirst');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulate() {
    setLoading(true);
    setError('');
    setCompareResult(null);
    try {
      const result = await simulate({ ...form, strategy });
      setSingleResult(result);
      setSelectedView(strategy);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Distributed Systems Project</p>
          <h1>BitTorrent-style Chunking: Large File Distribution</h1>
          <p>
            Event-based virtual-time simulation with 10 peers, 40 chunks, Random-First and Rarest-First comparison.
          </p>
        </div>
      </header>

      <ConfigPanel
        config={config}
        form={form}
        setForm={setForm}
        strategy={strategy}
        setStrategy={setStrategy}
        onCompare={handleCompare}
        onSimulate={handleSimulate}
        loading={loading}
      />

      {error && <div className="alert">{error}</div>}

      {compareResult && (
        <StrategyComparison
          result={compareResult}
          selectedView={selectedView}
          setSelectedView={setSelectedView}
        />
      )}

      {activeResult && (
        <>
          <MetricsPanel result={activeResult} compareResult={compareResult} />
          <section className="grid-two">
            <PeerProgressTable peers={activeResult.finalPeers} totalChunks={activeResult.config.totalChunks} />
            <PeerNetworkGraph logs={activeResult.logs} peerCount={activeResult.config.peer_count || activeResult.config.peerCount || 10} />
          </section>
          <TimelineReplay timeline={activeResult.progressTimeline} totalChunks={activeResult.config.totalChunks} />
          <TransferLog logs={activeResult.logs} />
        </>
      )}
    </main>
  );
}
