export default function ChurnPanel({
  snapshotTime,
  recommendation,
  churnScenario,
  loading,
  onRecommend,
  onApply,
  onReset,
}) {
  const recommendedPeer = recommendation?.peerId;
  const rareChunks = recommendation?.rareChunks || [];

  return (
    <section className="card churn-panel">
      <div className="section-header">
        <div>
          <h2>Peer churn what-if</h2>
          <p className="muted">Current timeline point: t = {snapshotTime == null ? '0' : snapshotTime}s</p>
        </div>
        {churnScenario && (
          <span className="churn-badge">
            Peer {churnScenario.peerId} offline at {churnScenario.time}s
          </span>
        )}
      </div>

      <div className="button-row">
        <button onClick={onRecommend} disabled={loading || snapshotTime == null}>
          {loading ? 'Searching...' : 'Find best peer to drop'}
        </button>
        {recommendation && (
          <button className="secondary" onClick={() => onApply(recommendedPeer, recommendation.event?.time)} disabled={loading}>
            Apply Peer {recommendedPeer} offline
          </button>
        )}
        {churnScenario && (
          <button className="ghost" onClick={onReset} disabled={loading}>
            Back to baseline
          </button>
        )}
      </div>

      {recommendation && (
        <div className={`churn-recommendation ${recommendation.desired ? 'strong' : ''}`}>
          <strong>{recommendation.message}</strong>
          <div className="churn-facts">
            <span>Random: {recommendation.randomCompleted ? `${recommendation.randomTotalTime}s` : 'incomplete'}</span>
            <span>Rarest: {recommendation.rarestCompleted ? `${recommendation.rarestTotalTime}s` : 'incomplete'}</span>
            <span>Rare chunks: {rareChunks.length ? rareChunks.slice(0, 8).join(', ') : 'none'}</span>
          </div>
        </div>
      )}
    </section>
  );
}
