# Streamlit Delivery Dashboard

Dashboard Streamlit nội bộ để xem tình trạng giao hàng từ Google Sheet. App chỉ đọc dữ liệu qua Google Sheets API với service account và scope read-only.

## Chạy local

```powershell
.\.venv-streamlit\Scripts\python.exe -m streamlit run .\streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Hoặc dùng script:

```powershell
.\run-streamlit.ps1
```

Mở:

- Máy hiện tại: http://localhost:8501
- Thiết bị cùng mạng: dùng URL Network mà Streamlit in ra.

## Biến môi trường

App đọc trực tiếp `.env.local` hiện có:

- `GOOGLE_SHEET_ID`
- `GOOGLE_SHEET_GID`
- `GOOGLE_CLIENT_EMAIL`
- `GOOGLE_PRIVATE_KEY`
- `AUTH_USERS`

`GOOGLE_SHEET_GID` hiện đang dùng tab `GIAO HÀNG`.

## Đăng nhập

User được cấu hình trong `AUTH_USERS`, ví dụ:

```env
AUTH_USERS=[{"email":"admin@example.com","password":"change-me","name":"Admin","role":"admin"}]
```

Vai trò:

- `admin`: xem toàn bộ dữ liệu.
- `viewer`: xem toàn bộ dữ liệu.
- `driver`: lọc theo email NVGH hoặc tên NVGH nếu sheet có dữ liệu tương ứng.

## Read-only

Code không có hàm update, append, delete hoặc batchUpdate Google Sheet. Scope sử dụng:

```text
https://www.googleapis.com/auth/spreadsheets.readonly
```

## Báo cáo đơn hàng tỉnh

Tab `Báo cáo` dùng cùng bộ lọc sidebar và tính:

- Báo cáo theo `NVGH thực hiện`.
- Báo cáo theo `Tỉnh / Tuyến`, lấy từ cột `Tuyến`.
- `Nhà xe` lấy từ cột `Nhà Xe`.
- `Đơn hàng tỉnh` được xác định bằng `Zone = Ngoại thành`.
- `Tỉ lệ tiền gửi đơn hàng tỉnh` = `Chi phí vận chuyển đơn hàng tỉnh / Giá trị đơn hàng tỉnh`.
