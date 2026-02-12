# Parking-Stall

Ứng dụng web **PC Cá Nhân** để quản lý cấu hình máy tính trên trình duyệt, có backend API và database SQLite.

## Tính năng
- Thêm thông tin máy (tên máy, CPU, RAM, ổ cứng, mục đích, ghi chú) với kiểm tra dữ liệu thân thiện.
- Tìm kiếm nhanh trong danh sách máy.
- Thống kê tổng số máy, tổng RAM, tổng dung lượng lưu trữ.
- Lưu dữ liệu vào database SQLite (`data/pc_catalog.db`) qua API.

## Chạy dự án
Chạy server Python tích hợp API + static files:

```bash
python3 api_server.py
```

Sau đó truy cập `http://localhost:4173`.

## API chính
- `GET /api/pcs`: lấy danh sách cấu hình.
- `POST /api/pcs`: tạo cấu hình mới.
- `DELETE /api/pcs/:id`: xóa cấu hình.
