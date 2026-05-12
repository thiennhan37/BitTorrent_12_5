# Báo cáo đồ án: BitTorrent-style Chunking - Large File Distribution

## 1. Giới thiệu đề tài

Đề tài mô phỏng quá trình phân phối một file lớn theo phong cách BitTorrent. Thay vì một server trung tâm gửi toàn bộ file cho từng client, file được chia thành nhiều chunk nhỏ. Các peer trong mạng có thể vừa tải chunk còn thiếu, vừa upload chunk đã có cho peer khác.

Mục tiêu chính của đồ án là so sánh hai chiến lược chọn chunk:

1. **Random-First**: chọn ngẫu nhiên một chunk còn thiếu có thể tải được.
2. **Rarest-First**: ưu tiên chunk hiếm nhất trong toàn mạng.

## 2. Bối cảnh bài toán

Thông số mô phỏng mặc định:

| Thông số | Giá trị |
|---|---:|
| File master | 10MB |
| Chunk size | 256KB |
| Tổng số chunk | 40 |
| Số peer | 10 |
| Điều kiện dừng | Tất cả peer đạt 100% completion |
| Metric chính | Virtual time hoàn thành toàn mạng |

Mỗi peer ban đầu sở hữu một tập chunk ngẫu nhiên. Initial state được sinh theo seed để có thể tái lập thí nghiệm. Hệ thống bảo đảm mỗi chunk xuất hiện ở ít nhất một peer, vì nếu một chunk không tồn tại trong swarm thì không peer nào có thể tải chunk đó.

## 3. Kiến trúc hệ thống

Project gồm hai phần chính:

```text
Frontend React  --->  Flask API  --->  Simulation Core
```

### 3.1 Backend

Backend gồm các module:

| Module | Vai trò |
|---|---|
| `config.py` | Lưu cấu hình mô phỏng |
| `models.py` | Mô hình Peer và TransferRecord |
| `initial_state.py` | Sinh trạng thái ban đầu theo seed |
| `network.py` | Tính thời gian truyền chunk |
| `strategies.py` | Cài Random-First và Rarest-First |
| `simulator.py` | Event-based simulator |
| `service.py` | Hàm chạy single simulation và compare |
| `app.py` | Flask REST API |

### 3.2 Frontend

Frontend gồm các component:

| Component | Vai trò |
|---|---|
| `ConfigPanel` | Nhập seed, bandwidth, latency, strategy |
| `MetricsPanel` | Hiển thị tổng thời gian, số transfer, winner |
| `StrategyComparison` | So sánh Random-First và Rarest-First |
| `PeerProgressTable` | Hiển thị completion từng peer |
| `ChunkGrid` | Hiển thị 40 ô chunk của mỗi peer |
| `TransferLog` | Hiển thị event START/END |
| `PeerNetworkGraph` | Hiển thị hướng truyền chunk giữa peer |
| `TimelineReplay` | Replay trạng thái theo progress timeline |

## 4. Mô hình dữ liệu

### 4.1 Peer

Mỗi peer lưu các thông tin:

- `peerId`
- `ownedChunks`
- `downloadBandwidthKbps`
- `uploadBandwidthKbps`
- `latencyMs`
- `activeDownloads`
- `activeUploads`

Peer có thể download nếu:

1. Peer chưa có chunk đó.
2. Peer còn download slot trống.
3. Chunk đó không nằm trong active download.

Peer có thể upload nếu:

1. Peer đang sở hữu chunk.
2. Peer còn upload slot trống.
3. Source peer khác destination peer.

### 4.2 Transfer log

Mỗi transfer tạo hai log event:

- `START`: thời điểm bắt đầu truyền.
- `END`: thời điểm truyền hoàn tất và destination peer nhận chunk.

Mỗi log gồm:

```text
time, event, sourcePeer, destinationPeer, chunkId, duration, bandwidthKbps, latencyMs
```

## 5. Event-based simulation

Đồ án không dùng mô phỏng theo round đồng bộ. Thay vào đó, mỗi peer là một process độc lập.

Luồng hoạt động của một peer:

```text
while peer chưa đủ 40 chunk:
    chọn chunk còn thiếu theo strategy
    chọn source peer đang sở hữu chunk đó
    khóa download slot và upload slot
    ghi log START
    yield env.timeout(download_time)
    thêm chunk vào peer nhận
    giải phóng slot
    ghi log END
    cập nhật progress timeline
```

Công thức thời gian truyền:

```text
download_time = latency + chunk_size / bandwidth
```

Trong đó:

```text
latency = latency_ms / 1000
bandwidth = min(source upload bandwidth, destination download bandwidth)
chunk_size = 256KB
```

Vì dùng virtual time, chương trình không cần chờ thời gian thật. Simulation có thể mô phỏng nhiều transfer bất đồng bộ trong cùng một timeline ảo.

## 6. Chiến lược Random-First

Với mỗi peer:

1. Lấy danh sách chunk còn thiếu.
2. Lọc ra các chunk có ít nhất một source peer đang upload được.
3. Chọn ngẫu nhiên một chunk.
4. Chọn ngẫu nhiên source peer sở hữu chunk đó.
5. Bắt đầu transfer.

Ưu điểm của Random-First là đơn giản. Tuy nhiên, do chọn ngẫu nhiên, thuật toán có thể không nhân bản kịp các chunk hiếm. Điều này thường làm giai đoạn cuối chậm hơn vì nhiều peer cùng cần một chunk có ít bản sao.

## 7. Chiến lược Rarest-First

Với mỗi peer:

1. Lấy danh sách chunk còn thiếu.
2. Đếm số peer đang sở hữu từng chunk còn thiếu.
3. Chỉ xét các chunk hiện có thể tải được.
4. Chọn chunk có số bản sao ít nhất.
5. Nếu nhiều chunk cùng độ hiếm, chọn ngẫu nhiên trong nhóm đó.
6. Chọn source peer và truyền chunk.

Rarest-First thường hiệu quả hơn vì ưu tiên lan truyền chunk hiếm ra nhiều peer sớm hơn. Khi chunk hiếm được nhân bản, swarm giảm nguy cơ bị nghẽn ở cuối quá trình phân phối.

## 8. So sánh công bằng

Để so sánh công bằng, project bảo đảm:

- Hai strategy dùng cùng seed.
- Hai strategy chạy trên cùng initial state.
- Hai strategy dùng cùng file size, chunk size, peer count.
- Hai strategy dùng cùng bandwidth và latency.
- Metric chính là `totalTime`, tức virtual time khi peer cuối cùng đạt 100% completion.

Endpoint `/api/simulate/compare` sinh initial state một lần rồi clone sang hai lượt chạy.

## 9. API

### GET `/api/config`

Trả về cấu hình mặc định.

### POST `/api/simulate`

Chạy một strategy.

Input:

```json
{
  "strategy": "rarestFirst",
  "seed": 9,
  "bandwidthKbps": 512,
  "latencyMs": 50,
  "initialChunkProbability": 0.15
}
```

### POST `/api/simulate/compare`

Chạy cả Random-First và Rarest-First trên cùng initial state.

Output chính:

```json
{
  "randomFirst": { "totalTime": 18.25 },
  "rarestFirst": { "totalTime": 16.2 },
  "winner": "rarestFirst"
}
```

## 10. Kết luận

Project đã mô phỏng được quá trình phân phối chunk theo kiểu BitTorrent bằng event-based virtual time. Backend cung cấp API để chạy từng strategy hoặc so sánh hai strategy. Frontend hiển thị metrics, completion của từng peer, chunk grid, transfer log, timeline replay và network graph.

Kết quả kỳ vọng là Rarest-First thường có xu hướng ổn định hơn Random-First trong các trường hợp chunk phân phối không đều, vì chiến lược này ưu tiên nhân bản chunk hiếm, giúp giảm bottleneck ở cuối quá trình tải file.

## 11. Hướng phát triển

Có thể mở rộng project theo các hướng:

1. Thêm bandwidth khác nhau cho từng peer.
2. Thêm churn: peer online/offline ngẫu nhiên.
3. Thêm tracker service thật.
4. Thêm optimistic unchoking / choking giống BitTorrent.
5. Thêm file splitter và file assembler để xử lý file thật.
6. Lưu kết quả thí nghiệm vào database để phân tích nhiều lần chạy.
