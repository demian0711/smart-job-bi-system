# 🚀 HƯỚNG DẪN THỰC HÀNH TÍCH HỢP APACHE SUPERSET TỪ A ĐẾN Z
### Dự án: Hệ thống Kinh doanh Thông minh (BI) - Tìm kiếm Thông tin Việc làm Sinh viên
**Đường dẫn dự án:** `D:\Workspace\Project\smart-job-bi-system`  
**Cơ sở dữ liệu:** `data/jobs_dataset.csv` (2.500 dòng) và `data/jobs_bi.db` (SQLite)

---

## 📑 MỤC LỤC
1. [Giai đoạn 1: Khởi động Docker Desktop & Apache Superset trên Windows](#giai-đoạn-1-khởi-động-docker-desktop--apache-superset-trên-windows)
2. [Giai đoạn 2: Đăng nhập & Đưa dữ liệu vào Superset (Upload CSV & SQLAlchemy)](#giai-đoạn-2-đăng-nhập--đưa-dữ-liệu-vào-superset)
3. [Giai đoạn 3: Tạo 4 Biểu đồ (Charts) chuẩn BI với đúng tên cột thực tế](#giai-đoạn-3-tạo-4-biểu-đồ-charts-chuẩn-bi)
4. [Giai đoạn 4: Ghép thành Dashboard hoàn chỉnh & Đưa lên Web Flask](#giai-đoạn-4-ghép-thành-dashboard-hoàn-chỉnh--đưa-lên-web-flask)

---

## GIAI ĐOẠN 1: KHỞI ĐỘNG DOCKER DESKTOP & APACHE SUPERSET TRÊN WINDOWS

### Bước 1.1: Mở Docker Desktop và kiểm tra trạng thái
1. Nhấn phím **Windows** trên bàn phím, gõ tìm kiếm `Docker Desktop` và bấm mở ứng dụng.
2. Nhìn xuống góc dưới cùng bên trái của cửa sổ Docker Desktop:
   - Khi thấy biểu tượng **con cá voi** và chữ **Engine running** (hoặc dấu chấm màu xanh lá cây) là Docker đã sẵn sàng hoạt động.
   - *(Nếu hiển thị "Engine starting...", hãy chờ khoảng 30–60 giây để Docker nạp xong).*

---

### Bước 1.2: Khởi động Container Superset có sẵn trên máy tính
Máy tính của bạn **đã có sẵn container Superset và PostgreSQL** từ trước:
- Tên container Superset: `vietnam-news-bi-superset-1` (Image: `apache/superset:5.0.0-dev`)
- Tên container Database: `vietnam-news-bi-postgres-1` (Image: `postgres:16-alpine`)

**Cách thực hiện (Chọn 1 trong 2 cách):**

* **Cách A (Bấm chuột trên giao diện Docker Desktop):**
  1. Trong menu bên trái của Docker Desktop, chọn mục **Containers**.
  2. Tìm container `vietnam-news-bi-postgres-1` -> Nhấn nút **Play (Start)** ở cột Actions.
  3. Tìm container `vietnam-news-bi-superset-1` -> Nhấn nút **Play (Start)** ở cột Actions.
  4. Quan sát thấy cột **Status** chuyển sang màu xanh lá **Running (Port 8088)** là thành công.

* **Cách B (Gõ 1 lệnh PowerShell / CMD cực nhanh):**
  Mở terminal tại máy tính và chạy:
  ```powershell
  docker start vietnam-news-bi-postgres-1 vietnam-news-bi-superset-1
  ```

> 💡 **Trường hợp máy mới hoặc chưa có container:**  
> Trong thư mục dự án đã có sẵn file `docker-compose.yml`. Bạn chỉ cần mở PowerShell tại thư mục `D:\Workspace\Project\smart-job-bi-system` và chạy:
> ```powershell
> docker compose up -d
> ```

---

## GIAI ĐOẠN 2: ĐĂNG NHẬP & ĐƯA DỮ LIỆU VÀO SUPERSET

### Bước 2.1: Truy cập và đăng nhập Superset
1. Mở trình duyệt web (Chrome, Edge hoặc Cốc Cốc).
2. Truy cập vào địa chỉ: **[http://localhost:8088](http://localhost:8088)**
3. Nhập thông tin tài khoản quản trị mặc định:
   - **Username:** `admin`
   - **Password:** `admin`
4. Bấm nút **Sign In**.

---

### Bước 2.2: Đưa dữ liệu vào Superset

Dự án hỗ trợ 2 cách. **Bạn hãy dùng CÁCH 1 (Upload CSV) vì đây là cách chuẩn nhất, nhanh nhất và không bao giờ gặp lỗi đường dẫn:**

---

### 🌟 CÁCH 1 (ƯU TIÊN): UPLOAD FILE CSV `jobs_dataset.csv`

#### Bước 2.2.1: Cho phép tính năng Upload File trong Database của Superset
*(Mặc định Superset tắt tính năng upload file để bảo mật, bạn chỉ cần bật 1 lần duy nhất)*
1. Tại góc trên cùng bên phải màn hình Superset, bấm vào biểu tượng bánh răng **Settings**.
2. Chọn dòng **Database Connections**.
3. Trong danh sách cơ sở dữ liệu hiển thị, tìm database đang dùng (thường có tên là **examples** hoặc **PostgreSQL**).
4. Ở cột cuối cùng bên phải của database đó, bấm vào biểu tượng **cây bút (Edit)**.
5. Cửa sổ sửa hiện ra:
   - Bấm chuyển sang tab **Advanced** (ở phía trên).
   - Bấm vào mục **Security** (mở rộng danh sách tuỳ chọn bảo mật).
   - Tìm dòng **Allow file uploads to database** và **TÍCH CHỌN** vào ô vuông này.
6. Bấm nút **Finish** (hoặc **Save**) ở góc dưới cửa sổ để lưu lại.

#### Bước 2.2.2: Tải file dữ liệu `jobs_dataset.csv` lên
1. Trên thanh điều hướng chính phía trên của Superset, di chuột vào menu **Data**.
2. Chọn mục **Upload a CSV** (hoặc *Upload file to database* -> *Upload CSV*).
3. Điền các trường chính xác như sau:
   - **CSV File:** Nhấn nút **Choose File** (hoặc *Browse*), dẫn đến thư mục dự án và chọn file:  
     `D:\Workspace\Project\smart-job-bi-system\data\jobs_dataset.csv`
   - **Table Name:** Gõ chính xác: `student_jobs_bi`
   - **Database:** Chọn database bạn vừa cho phép upload ở Bước 2.2.1 (ví dụ: `examples` hoặc `PostgreSQL`).
   - **Schema:** Để trống (hoặc gõ `public`).
   - **Parse Dates:** Gõ tên cột: `posted_date` (để Superset tự động nhận diện thời gian cho biểu đồ xu hướng).
   - **If Table Already Exists:** Chọn `Replace` (để ghi đè nếu đã tồn tại).
4. Kéo xuống góc dưới cùng và bấm nút **Save**.
5. Màn hình thông báo thành công và chuyển sang danh sách **Datasets**, bạn sẽ thấy bảng `student_jobs_bi` đã sẵn sàng với **2.500 bản ghi**!

---

### 📖 CÁCH 2 (DÀNH CHO THUYẾT TRÌNH): KẾT NỐI QUA SQLALCHEMY URI
Khi quay video demo hoặc thuyết trình, bạn có thể mở tab Superset trên Web Flask để giải thích cho giảng viên:
- **Nguyên lý:** Superset tích hợp sẵn thư viện SQLAlchemy giống như Flask. Nó sử dụng chuỗi kết nối URI dạng:
  ```text
  sqlite:////D:/Workspace/Project/smart-job-bi-system/data/jobs_bi.db
  ```
- **Ý nghĩa:** Python xử lý ETL xong xuất ra SQLite, Superset kết nối trực tiếp vào file SQLite đó thông qua SQLAlchemy để vẽ biểu đồ theo thời gian thực (Zero-code Dashboard).

---

## GIAI ĐOẠN 3: TẠO 4 BIỂU ĐỒ (CHARTS) CHUẨN BI

Nhấn vào menu **Charts** trên thanh điều hướng -> Bấm nút **+ Chart** màu xanh ở góc trên bên phải để bắt đầu tạo từng biểu đồ:

---

### 📊 BIỂU ĐỒ 1: Phân bố Việc làm theo Địa điểm (Pie / Donut Chart)
*Mục đích: Giúp sinh viên nắm tỷ lệ việc làm tại Hà Nội, TP.HCM, Đà Nẵng và cơ hội làm việc từ xa (Remote).*

1. Tại ô **Choose a Dataset**: Chọn `student_jobs_bi`.
2. Tại ô **Choose Chart Type**: Tìm và chọn loại **Pie Chart** (biểu đồ tròn).
3. Bấm nút **Create New Chart**.
4. Cấu hình bên cột bên trái (tab **Query**):
   - **Dimensions:** Chọn cột `location`.
   - **Metric:** Mặc định là `COUNT(*)` (hoặc bấm chọn `COUNT(*)`).
5. Chuyển sang tab **Customize** (bên cạnh tab Query):
   - Tích chọn ô **Donut** (để tạo lỗ rỗng ở giữa theo phong cách SaaS hiện đại).
   - **Label Type:** Chọn `Category and Percentage` (hiển thị tên địa điểm và % tỷ lệ).
6. Bấm nút **Update Chart** để xem trước biểu đồ hiển thị.
7. Đổi tên biểu đồ (click vào chữ *[Untitled]* ở góc trên cùng bên trái):  
   Sửa thành: `1. Phân bố Việc làm theo Địa điểm`
8. Bấm nút **Save** ở góc trên bên phải -> Chọn **Save only** -> Bấm **Save**.

---

### 📊 BIỂU ĐỒ 2: Số lượng Việc làm & Mức lương theo Ngành nghề (Bar Chart)
*Mục đích: So sánh ngành nào tuyển dụng nhiều nhất và ngành nào có mức lương trung bình cao nhất (IT, BI, Marketing, Tài chính...).*

1. Bấm vào menu **Charts** -> Bấm **+ Chart**.
2. Chọn Dataset `student_jobs_bi` -> Chọn Chart Type: **Bar Chart** (hoặc *Time-series Bar Chart*).
3. Bấm **Create New Chart**.
4. Cấu hình tab **Query**:
   - **X-Axis / Dimensions:** Chọn cột `industry`.
   - **Metrics:** Chọn 2 chỉ số:
     - Metric 1: Chọn `COUNT(*)` -> Bấm vào nhãn sửa chữ thành `Số lượng tin tuyển dụng`.
     - Metric 2: Bấm dấu `+` thêm Metric -> Chọn tab `SIMPLE` -> Cột chọn `salary_avg`, hàm chọn `AVG` -> Đặt nhãn: `Lương Trung Bình (Triệu VNĐ)`.
5. Tab **Customize**:
   - Tích chọn **Show Value** (hiển thị số liệu trực tiếp trên đầu cột).
   - **Sort Axis By:** Chọn theo `Metric` giảm dần.
6. Bấm **Update Chart**.
7. Đổi tên biểu đồ: `2. Số lượng Việc làm & Lương TB theo Ngành nghề`.
8. Bấm **Save** -> **Save only** -> **Save**.

---

### 📊 BIỂU ĐỒ 3: Xu hướng Tuyển dụng theo Thời gian (Line Chart)
*Mục đích: Phân tích đỉnh tuyển dụng theo tháng trong 6 tháng gần nhất để sinh viên biết thời điểm "vàng" nộp CV.*

1. Bấm vào menu **Charts** -> Bấm **+ Chart**.
2. Chọn Dataset `student_jobs_bi` -> Chọn Chart Type: **Line Chart** (hoặc *Time-series Line Chart*).
3. Bấm **Create New Chart**.
4. Cấu hình tab **Query**:
   - **Time Column:** Chọn `posted_date`.
   - **Time Grain:** Chọn `Month` (gom nhóm theo từng tháng).
   - **Time Range:** Chọn `No filter` (để lấy toàn bộ dữ liệu 6 tháng).
   - **Metrics:** Chọn `COUNT(*)` (Số lượng tin đăng).
   - **Dimensions (Tuỳ chọn):** Có thể chọn thêm `industry` nếu muốn tách thành nhiều đường cho từng ngành.
5. Tab **Customize**:
   - Tích chọn **Show Markers** (hiển thị các điểm chấm trên đường vẽ).
   - Tích chọn **Smooth Line** (làm mượt đường cong).
6. Bấm **Update Chart**.
7. Đổi tên biểu đồ: `3. Xu hướng Tuyển dụng theo Thời gian`.
8. Bấm **Save** -> **Save only** -> **Save**.

---

### 📊 BIỂU ĐỒ 4: Nhu cầu Thị trường theo Kỹ năng & Nguồn Tuyển dụng (Treemap / Bar)
*Mục đích: Đánh giá độ nóng (Demand Score) của thị trường dựa trên nguồn tuyển dụng (TopCV, VietnamWorks, ITViec, LinkedIn) và nhóm thu nhập.*

1. Bấm vào menu **Charts** -> Bấm **+ Chart**.
2. Chọn Dataset `student_jobs_bi` -> Chọn Chart Type: **Treemap** (hoặc *Bar Chart*).
3. Bấm **Create New Chart**.
4. Cấu hình tab **Query**:
   - **Dimensions:** Chọn 2 cột: `source` (Nguồn tuyển dụng) và `demand_tier` (Cấp độ nhu cầu).
   - **Metric:** Bấm tab `SIMPLE` -> Chọn cột `demand_score`, hàm `AVG` (Điểm nhu cầu trung bình).
5. Bấm **Update Chart**.
6. Đổi tên biểu đồ: `4. Nhu cầu Thị trường & Nguồn Tuyển dụng`.
7. Bấm **Save** -> **Save only** -> **Save**.

---

## GIAI ĐOẠN 4: GHÉP THÀNH DASHBOARD HOÀN CHỈNH & ĐƯA LÊN WEB FLASK

### Bước 4.1: Tạo Dashboard mới
1. Trên thanh điều hướng của Superset, bấm vào menu **Dashboards**.
2. Bấm nút **+ Dashboard** ở góc trên bên phải.
3. Đặt tiêu đề cho Dashboard (nhấp vào ô *[Untitled]*):  
   Nhập: `Hệ thống BI - Phân tích Việc làm Sinh viên`

---

### Bước 4.2: Kéo thả 4 biểu đồ vào bố cục 2x2
1. Ở thanh menu bên phải màn hình (cột **Charts**), bạn sẽ thấy danh sách 4 biểu đồ vừa tạo:
   - `1. Phân bố Việc làm theo Địa điểm`
   - `2. Số lượng Việc làm & Lương TB theo Ngành nghề`
   - `3. Xu hướng Tuyển dụng theo Thời gian`
   - `4. Nhu cầu Thị trường & Nguồn Tuyển dụng`
2. Kéo thả từng biểu đồ vào vùng làm việc chính ở giữa màn hình:
   - **Hàng 1:** Kéo Biểu đồ 1 vào góc trái, Biểu đồ 2 vào góc phải.
   - **Hàng 2:** Kéo Biểu đồ 3 vào góc trái, Biểu đồ 4 vào góc phải.
3. Dùng chuột điều chỉnh độ rộng (resize) các ô biểu đồ cho cân đối và vuông vắn.

---

### Bước 4.3: Thêm bộ lọc tương tác (Native Filter)
1. Ở mép trái màn hình Dashboard, bấm vào biểu tượng **chiếc phễu (Filters)** -> Chọn **+ Add Filter**.
2. Cấu hình bộ lọc:
   - **Filter Type:** `Value`
   - **Filter name:** `Ngành nghề`
   - **Dataset:** `student_jobs_bi`
   - **Column:** `industry`
   - Bấm **Save**.
3. Bạn có thể bấm thêm bộ lọc thứ 2 cho `location` (Địa điểm).
4. Bấm nút **Save** ở góc trên bên phải để lưu Dashboard.
5. Chuyển trạng thái góc trên bên phải từ **Draft** sang **Published** (màu xanh lá cây).

---

### Bước 4.4: Chụp màn hình và lưu vào dự án để hiển thị lên Web Flask
1. Giữ nguyên màn hình Dashboard Superset vừa hoàn thiện (thu nhỏ thanh menu bên cạnh để dashboard chiếm trọn màn hình).
2. Nhấn tổ hợp phím trên Windows:  
   👉 **`Windows + Shift + S`**
3. Kéo chuột chọn toàn bộ khung Dashboard thật đẹp và rõ nét.
4. Mở ứng dụng **Paint** (nhấn phím Windows -> gõ Paint -> nhấn `Ctrl + V` để dán ảnh vào).
5. Nhấn `Ctrl + S` (Lưu file), chọn định dạng **PNG**, lưu chính xác vào đường dẫn sau:
   ```text
   D:\Workspace\Project\smart-job-bi-system\static\charts\superset_preview.png
   ```
6. **Kiểm tra thành quả:**
   - Mở trình duyệt web truy cập trang Flask: **[http://localhost:5000/superset](http://localhost:5000/superset)**
   - Nhấn **F5 (Reload)** trang:
   - 🎉 **Mục "Ảnh chụp Báo cáo Dashboard Thực tế" sẽ tự động phát hiện file ảnh và hiển thị Dashboard Superset tuyệt đẹp ngay trên ứng dụng web của bạn!**

---

## 🎯 DANH SÁCH KIỂM TRA (CHECKLIST BẢO VỆ MÔN HỌC)
- [x] Đã khởi động Docker & Apache Superset trên cổng 8088.
- [x] Đã import 2.500 bản ghi dữ liệu sinh viên vào bảng `student_jobs_bi`.
- [x] Đã tạo 4 biểu đồ: Địa điểm, Ngành nghề/Lương, Xu hướng thời gian, Nhu cầu thị trường.
- [x] Đã ghép Dashboard có bộ lọc tương tác (Native Filters) và xuất bản (Published).
- [x] Đã lưu ảnh `superset_preview.png` vào thư mục `static/charts/` và hiển thị trên tab Superset của Web Flask.
- [x] Nắm rõ cấu hình SQLAlchemy Connection URI để trình bày kiến trúc tích hợp hệ thống.

