export default function ChurnPanel({
  snapshotTime,
  recommendation,
  churnEvents,
  effectivePeerStates,
  loading,
  onRecommend,
  onApply,
  onReset,
}) {
  const recommendedPeer = recommendation?.peerId;
  const rareChunks = recommendation?.rareChunks || [];

  const hasAnyChurnEvent = (churnEvents || []).length > 0;
  const hasActiveChurnState = Array.from(effectivePeerStates?.entries?.() || []).length > 0;

  return (
    <section className="card churn-panel">
      <div className="section-header">
        <div>
          <h2>Peer churn what-if</h2>
          <p className="muted">Current timeline point: t = {snapshotTime == null ? '0' : snapshotTime}s</p>
        </div>
        {hasActiveChurnState && (
          <div className="churn-badge-list">
            {Array.from(effectivePeerStates.entries()).map(([peerId, online]) => (
              <span key={`active-${peerId}`} className={`churn-badge ${online ? 'online' : 'offline'}`}>
                Peer {peerId} {online ? 'online' : 'offline'} @ t={snapshotTime}s
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="button-row">
        <button onClick={onRecommend} disabled={loading || snapshotTime == null}>
          {loading ? 'Searching...' : 'Find best peer to drop'}
        </button>
        {recommendation && (
          <button className="secondary" onClick={() => onApply(recommendedPeer)} disabled={loading}>
            Apply Peer {recommendedPeer} offline
          </button>
        )}
        {hasAnyChurnEvent && (
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
