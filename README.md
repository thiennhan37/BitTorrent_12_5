# BitTorrent-style Chunking: Large File Distribution

Đồ án mô phỏng cơ chế phân phối file lớn theo phong cách BitTorrent cho môn **Cơ sở dữ liệu phân tán / Hệ phân tán**.

Project này đã chuyển mô phỏng sang hướng **event-based virtual time**: mỗi peer là một process độc lập, peer rảnh sẽ tự chọn chunk còn thiếu, chọn source peer đang có chunk đó, chờ thời gian truyền ảo rồi cập nhật trạng thái ngay tại thời điểm event kết thúc.

## Tính năng chính

- File master cố định: **10MB**.
- Chunk size: **256KB**.
- Tổng số chunk: **40**.
- Số peer: **10**.
- Sinh initial state ngẫu nhiên theo seed, nhưng bảo đảm mỗi chunk có ít nhất một peer sở hữu.
- So sánh công bằng hai chiến lược:
  - **Random-First**
  - **Rarest-First**
- Backend Flask API.
- Core simulation viết theo kiểu SimPy process/event.
- Frontend React dashboard.
- Có log START/END kèm timestamp, source peer, destination peer, chunk id.
- Có progress timeline, chunk grid, metrics và network graph.

## Cấu trúc thư mục

```text
bittorrent_style_chunking_complete/
  backend/
    app.py
    run_compare.py
    requirements.txt
    simulation/
      config.py
      initial_state.py
      models.py
      network.py
      service.py
      simpy_compat.py
      simulator.py
      strategies.py
    tests/
      test_simulator.py
  frontend/
    package.json
    index.html
    src/
      App.jsx
      api/client.js
      components/
      styles.css
  README.md
  REPORT.md
```

## Cài đặt backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Chạy API:

```bash
python app.py
```

API chạy mặc định tại:

```text
http://localhost:5000
```

Chạy thử so sánh ở terminal:

```bash
python run_compare.py
```

Chạy test:

```bash
python -m pytest -q
```

## Cài đặt frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy mặc định tại:

```text
http://localhost:5173
```

Nếu backend chạy ở host khác, tạo file `.env` trong `frontend/`:

```text
VITE_API_BASE=http://localhost:5000
```

## API

### GET `/api/config`

Trả về cấu hình mặc định của mô phỏng.

### POST `/api/simulate`

Chạy một strategy cụ thể.

Request mẫu:

```json
{
  "strategy": "rarestFirst",
  "seed": 9,
  "bandwidthKbps": 512,
  "latencyMs": 50,
  "initialChunkProbability": 0.15
}
```

Response gồm:

```text
totalTime, logs, transfers, progressTimeline, finalPeers, chunkAvailability, config
```

### POST `/api/simulate/compare`

Chạy cả Random-First và Rarest-First trên cùng initial state.

Request mẫu:

```json
{
  "seed": 9,
  "bandwidthKbps": 512,
  "latencyMs": 50,
  "initialChunkProbability": 0.15
}
```

Response mẫu rút gọn:

```json
{
  "randomFirst": { "totalTime": 18.25, "logs": [], "progressTimeline": [], "finalPeers": [] },
  "rarestFirst": { "totalTime": 16.2, "logs": [], "progressTimeline": [], "finalPeers": [] },
  "winner": "rarestFirst"
}
```

## Công thức thời gian truyền

```text
download_time = latency + chunk_size / bandwidth
```

Trong code:

```text
latency = latency_ms / 1000
chunk_size = 256 KB
bandwidth = min(source_upload_bandwidth, destination_download_bandwidth)
```

Đơn vị bandwidth trong project là **KB/s** để công thức trực tiếp và dễ trình bày.

## Ý nghĩa thuật toán

### Random-First

Mỗi peer lấy danh sách chunk còn thiếu, lọc các chunk có ít nhất một peer khác đang upload được, rồi chọn ngẫu nhiên.

Ưu điểm: đơn giản, dễ cài đặt.

Nhược điểm: có thể bỏ qua chunk hiếm, làm một số chunk bị lan truyền chậm.

### Rarest-First

Mỗi peer đếm số bản sao của các chunk còn thiếu trong swarm, chọn nhóm chunk có số bản sao ít nhất, sau đó chọn ngẫu nhiên trong nhóm đó.

Ưu điểm: ưu tiên nhân bản chunk hiếm, giảm nguy cơ nghẽn ở cuối mô phỏng.

Nhược điểm: cần thống kê availability toàn mạng nên phức tạp hơn Random-First.

## Ghi chú triển khai

File `backend/simulation/simpy_compat.py` có fallback rất nhỏ để test trong môi trường không cài được package ngoài. Khi cài `requirements.txt`, simulator sẽ dùng **SimPy thật**.
