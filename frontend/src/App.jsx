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
    seed: 1,
    download_bandwidth: 128,
    upload_bandwidth: 128,
    latencyMs: 50,
    initialChunkProbability: 0.3,
    max_download_slots: 2,
    max_upload_slots: 3,
  });
  const [strategy, setStrategy] = useState('rarestFirst');
  const [compareResult, setCompareResult] = useState(null);
  const [singleResult, setSingleResult] = useState(null);
<<<<<<< HEAD
=======
  const [churnRecommendation, setChurnRecommendation] = useState(null);
  const [churnScenario, setChurnScenario] = useState(null);
>>>>>>> parent of dc85ae4 (Fix churn event timing across timeline snapshots)
  const [selectedView, setSelectedView] = useState('rarestFirst');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timelineIndex, setTimelineIndex] = useState(0);

  useEffect(() => {
    getConfig()
      .then((data) => {
        setConfig(data);
        setForm((prev) => ({
          ...prev,
          seed: data.seed,
          download_bandwidth:
            data.download_bandwidth ?? data.downloadBandwidthKbps ?? data.bandwidth_kbps ?? data.bandwidthKbps ?? 128,
          upload_bandwidth:
            data.upload_bandwidth ??
            data.uploadBandwidthKbps ??
            data.upload_bandwidth_kbps ??
            data.effectiveUploadBandwidthKbps ??
            128,
          latencyMs: data.latency_ms ?? data.latencyMs ?? 50,
          initialChunkProbability: data.initial_chunk_probability ?? data.initialChunkProbability ?? 0.3,
          max_download_slots: data.max_download_slots ?? data.maxDownloadSlots ?? 2,
          max_upload_slots: data.max_upload_slots ?? data.maxUploadSlots ?? 3,
        }));
      })
      .catch((err) => setError(err.message));
  }, []);

  const activeResult = useMemo(() => {
    if (compareResult) return compareResult[selectedView];
    return singleResult;
  }, [compareResult, selectedView, singleResult]);

  const activeSnapshotTime = useMemo(() => {
    const timeline = activeResult?.progressTimeline || [];
    if (!timeline.length) return null;
    const safeIndex = Math.min(timelineIndex, timeline.length - 1);
    return timeline[safeIndex]?.time ?? null;
  }, [activeResult, timelineIndex]);

<<<<<<< HEAD
=======
  const activeSnapshot = useMemo(() => {
    const timeline = activeResult?.progressTimeline || [];
    if (!timeline.length) return null;
    const safeIndex = Math.min(timelineIndex, timeline.length - 1);
    return timeline[safeIndex] || null;
  }, [activeResult, timelineIndex]);

>>>>>>> parent of dc85ae4 (Fix churn event timing across timeline snapshots)
  async function handleCompare() {
    setLoading(true);
    setError('');
    setSingleResult(null);
    setTimelineIndex(0);
    try {
      const result = await compareStrategies(form);
      setCompareResult(result);
<<<<<<< HEAD
=======
      setBaselineCompareResult(result);
      setChurnRecommendation(null);
      setChurnScenario(null);
>>>>>>> parent of dc85ae4 (Fix churn event timing across timeline snapshots)
      setSelectedView(result.winner === 'randomFirst' ? 'randomFirst' : 'rarestFirst');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
<<<<<<< HEAD
  }

  async function handleSimulate() {
    setLoading(true);
    setError('');
    setCompareResult(null);
    setTimelineIndex(0);
    try {
      const result = await simulate({ ...form, strategy });
      setSingleResult(result);
      setSelectedView(strategy);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
=======
  }

  async function handleSimulate() {
    setLoading(true);
    setError('');
    setCompareResult(null);
    setBaselineCompareResult(null);
    setChurnRecommendation(null);
    setChurnScenario(null);
    setTimelineIndex(0);
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

  async function handleRecommendChurn() {
    const baseline = baselineCompareResult || compareResult;
    if (!baseline || activeSnapshotTime == null) return;

    setLoading(true);
    setError('');
    try {
      const result = await recommendChurn({
        ...form,
        initialState: baseline.initialState,
        time: activeSnapshotTime,
      });
      setChurnRecommendation(result.recommendation);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleApplyChurn(peerId, time = activeSnapshotTime) {
    const baseline = baselineCompareResult || compareResult;
    if (!baseline || time == null || peerId == null) return;

    const event = { time, peerId, online: false };
    setLoading(true);
    setError('');
    try {
      const result = await compareStrategies({
        ...form,
        initialState: baseline.initialState,
        churnEvents: [event],
      });
      setCompareResult(result);
      setChurnScenario(event);
      setSelectedView(result.winner === 'rarestFirst' ? 'rarestFirst' : 'randomFirst');
      setTimelineIndex(0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleResetChurn() {
    if (!baselineCompareResult) return;
    setCompareResult(baselineCompareResult);
    setChurnRecommendation(null);
    setChurnScenario(null);
    setTimelineIndex(0);
>>>>>>> parent of dc85ae4 (Fix churn event timing across timeline snapshots)
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

<<<<<<< HEAD
=======
      {compareResult && (
        <ChurnPanel
          snapshotTime={activeSnapshotTime}
          recommendation={churnRecommendation}
          churnScenario={churnScenario}
          loading={loading}
          onRecommend={handleRecommendChurn}
          onApply={handleApplyChurn}
          onReset={handleResetChurn}
        />
      )}

>>>>>>> parent of dc85ae4 (Fix churn event timing across timeline snapshots)
      {activeResult && (
        <>
          <MetricsPanel result={activeResult} compareResult={compareResult} />
          <section className="grid-two">
            <PeerProgressTable peers={activeResult.finalPeers} totalChunks={activeResult.config.totalChunks} />
            <PeerNetworkGraph
              logs={activeResult.logs}
              peerCount={activeResult.config.peer_count || activeResult.config.peerCount || 10}
              maxTime={activeSnapshotTime}
<<<<<<< HEAD
=======
              peers={activeSnapshot?.peers || activeResult.finalPeers}
              recommendedPeerId={churnRecommendation?.peerId}
              onPeerClick={compareResult ? handleApplyChurn : null}
>>>>>>> parent of dc85ae4 (Fix churn event timing across timeline snapshots)
            />
          </section>
          <TimelineReplay
            timeline={activeResult.progressTimeline}
            totalChunks={activeResult.config.totalChunks}
            index={timelineIndex}
            onIndexChange={setTimelineIndex}
          />
          <TransferLog logs={activeResult.logs} />
        </>
      )}
    </main>
  );
}
