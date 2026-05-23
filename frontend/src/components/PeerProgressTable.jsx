import ChunkGrid from './ChunkGrid.jsx';

export default function PeerProgressTable({ peers = [], totalChunks = 40 }) {
  return (
    <section className="card scroll-card">
      <h2>Peer completion and chunk grid</h2>
      <div className="peer-list">
        {peers.map((peer) => (
          <div className="peer-row" key={peer.peerId}>
            <div className="peer-row-header">
              <strong>Peer {peer.peerId}</strong>
              <span>{peer.ownedChunkCount}/{totalChunks} chunks · {peer.completion}%</span>
            </div>
            <div className="progress-bar">
              <div style={{ width: `${peer.completion}%` }} />
            </div>
            <ChunkGrid ownedChunks={peer.ownedChunks} totalChunks={totalChunks} />
          </div>
        ))}
      </div>
    </section>
  );
}
