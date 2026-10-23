# BẢN ĐỀ XUẤT Ý TƯỞNG HỆ THỐNG VÀ CHIẾN LƯỢC THU THẬP DỮ LIỆU
**Dự án:** Hệ thống Kinh doanh Thông minh (BI) Tìm kiếm Thông tin Việc làm Dành cho Sinh viên Mới Tốt nghiệp  
**Tên hệ thống:** Smart Job BI System  
**Vai trò xây dựng:** Chuyên viên Phân tích Hệ thống (System Analyst)  
**Tài liệu:** Đề xuất Kỹ thuật & Đặc tả Kiến trúc Dữ liệu  

---

## TỔNG QUAN VÀ ĐẶT VẤN ĐỀ

Thị trường tuyển dụng lao động trẻ tại Việt Nam hiện đang đối mặt với hai thách thức cốt lõi:
1. **Sự phân mảnh thông tin tuyển dụng (Information Fragmentation):** Dữ liệu việc làm nằm rải rác trên nhiều nền tảng độc lập (TopCV, VietnamWorks, ITViec, LinkedIn) với quy chuẩn mô tả, cấu trúc mức lương và phân loại kỹ năng không đồng nhất.
2. **Bất cân xứng thông tin và Khoảng trống kỹ năng (Skill Gap):** Sinh viên mới tốt nghiệp thường gặp khó khăn trong việc định vị năng lực bản thân so với kỳ vọng thực tế của doanh nghiệp, dẫn đến tình trạng rải hồ sơ thụ động, thiếu định hướng bổ sung kỹ năng trọng yếu và tỉ lệ ứng tuyển thành công thấp.

**Smart Job BI System** được thiết kế như một **Hệ thống Hỗ trợ Ra quyết định (Decision Support System - DSS)** ứng dụng kiến trúc **Business Intelligence (BI)** hiện đại. Thay vì dừng lại ở việc tìm kiếm từ khóa thuần túy, hệ thống chuyển hóa dữ liệu tuyển dụng lớn thành tri thức có cấu trúc, cung cấp cơ chế so khớp hồ sơ thông minh và định lượng chính xác khoảng trống kỹ năng cần cải thiện cho ứng viên.

---

## PHẦN 1: ĐỐI TƯỢNG NGHIÊN CỨU VÀ TÍNH NĂNG THÔNG MINH CỐT LÕI

### 1.1. Phân khúc đối tượng mục tiêu (Target Persona)
Hệ thống tập trung chuyên biệt vào nhóm **ứng viên gia nhập thị trường lao động lần đầu (Entry-level / Fresh Graduates)** bao gồm:
* Sinh viên năm cuối chuẩn bị thực tập hoặc sinh viên vừa tốt nghiệp đại học/cao đẳng (kinh nghiệm dưới 1 năm).
* Đặc thù nhân khẩu học: Sở hữu nền tảng lý thuyết vững nhưng thiếu kinh nghiệm thực chiến; bộ kỹ năng chưa hoàn chỉnh; nhạy cảm cao với địa điểm làm việc (Hà Nội, TP.HCM, Đà Nẵng, mô hình Remote/Hybrid); có kỳ vọng thu nhập chưa thực sự bám sát biến động thị trường.

### 1.2. Thuật toán gợi ý việc làm thông minh (AI Smart Matching Engine)
Khác với các hệ thống tìm kiếm việc làm truyền thống dựa trên lọc chuỗi đơn giản (string matching), hệ thống triển khai mô hình **Weighted Scoring kết hợp Độ tương đồng Cosine (Cosine Similarity)** trên không gian vector đa chiều:

$$\text{Match Score} = \sum_{i=1}^{4} W_i \cdot S_i = 0.50 \cdot S_{\text{Skill}} + 0.25 \cdot S_{\text{Industry}} + 0.15 \cdot S_{\text{Location}} + 0.10 \cdot S_{\text{Salary}}$$

Trong đó, cơ cấu trọng số được tính toán tối ưu dựa trên mức độ ảnh hưởng đến quyết định tuyển dụng:

* **Trọng số Kỹ năng ($W_{\text{Skill}} = 50\%$ - Nhân tố quyết định):**  
  Tập kỹ năng của sinh viên ($A$) và tập yêu cầu kỹ năng của tin tuyển dụng ($B$) được vector hóa nhị phân trong không gian từ điển kỹ năng chuẩn hóa. Độ phù hợp được tính bằng độ đo Cosine:
  $$S_{\text{Skill}} = \frac{|A \cap B|}{\sqrt{|A|} \cdot \sqrt{|B|}}$$
  Phương pháp này triệt tiêu độ lệch khi số lượng kỹ năng liệt kê quá dài hoặc quá ngắn, phản ánh chính xác tỷ lệ trùng khớp thực chất.

* **Trọng số Ngành nghề ($W_{\text{Industry}} = 25\%$):**  
  Áp dụng hàm khớp chính xác (Exact match = $1.0$), khớp miền phụ (Partial domain match = $0.6$) và điểm phạt nền đối với ngành không tương thích ($0.05$).

* **Trọng số Địa điểm ($W_{\text{Location}} = 15\%$):**  
  Ưu tiên địa phương mong muốn ($1.0$). Đặc biệt, các vị trí làm việc từ xa (**Remote**) được gán hệ số linh hoạt ($0.75$) nhằm khuyến khích sinh viên tiếp cận việc làm không biên giới địa lý.

* **Trọng số Mức lương ($W_{\text{Salary}} = 10\%$):**  
  Chấm điểm thông qua hàm suy giảm tuyến tính (Linear Decay Function). Nếu lương trung bình của vị trí tuyển dụng đáp ứng hoặc vượt mức kỳ vọng ($R \ge 1.0$), điểm đạt cực đại ($1.0$). Khi lương thấp hơn kỳ vọng trong ngưỡng chấp nhận được ($0.6 \le R < 1.0$), điểm giảm dần theo tỷ lệ; nếu thấp hơn $40\%$ mức kỳ vọng thì điểm về $0$.

### 1.3. Mô đun Định lượng Khoảng trống Kỹ năng (Skill Gap Analysis)
Sau khi xếp hạng và trích xuất **Top 15 công việc phù hợp nhất**, hệ thống tự động thực hiện phép trừ tập hợp:

$$\Delta_{\text{Gap}} = B_{\text{Job}} \setminus A_{\text{Student}}$$

Thuật toán tổng hợp tần suất xuất hiện của các kỹ năng còn thiếu trên toàn bộ danh sách đề xuất, từ đó xuất ra **Báo cáo Top 10 Kỹ năng Cần Bổ sung (Skill Gap Alert)**. Tính năng này giải quyết triệt để bài toán mù mờ về năng lực của sinh viên: thay vì bị từ chối mà không rõ nguyên nhân, sinh viên nhận được một bản đồ chỉ dẫn học tập (Upskilling Roadmap) định lượng cụ thể để đáp ứng đúng nhu cầu doanh nghiệp.

---

## PHẦN 2: CHIẾN LƯỢC VÀ ĐẶC TẢ NGUỒN DỮ LIỆU ĐẦU VÀO

Hệ thống kết hợp hai luồng thông tin: dữ liệu thị trường khách quan (Supply-side Data) và hồ sơ ứng viên cá nhân hóa (Demand-side Data).

```
                      NGUỒN DỮ LIỆU ĐẦU VÀO
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
DỮ LIỆU THỊ TRƯỜNG                               HỒ SƠ ỨNG VIÊN
(2.500 tin tuyển dụng)                          (Đầu vào cá nhân)
 ├── TopCV (Tổng hợp, Entry-level)               ├── Ngành học mục tiêu
 ├── VietnamWorks (Doanh nghiệp lớn/FDI)         ├── Kỹ năng hiện có
 ├── ITViec (Công nghệ / BI / Data)              ├── Địa điểm mong muốn
 └── LinkedIn (Đa quốc gia, Remote)              └── Mức lương kỳ vọng
```

### 2.1. Nguồn dữ liệu thị trường (External Market Ingestion)
Quy mô dữ liệu thử nghiệm chuẩn đạt **2.500 bản ghi tin tuyển dụng** được tổng hợp từ 4 kênh tuyển dụng hàng đầu tại Việt Nam:
1. **TopCV:** Chiếm tỷ trọng cao về các vị trí thực tập sinh, nhân sự mới tốt nghiệp thuộc các khối ngành Kinh tế, Marketing, Kế toán.
2. **VietnamWorks:** Nguồn tin tuyển dụng tiêu chuẩn từ các tập đoàn lớn, doanh nghiệp FDI với yêu cầu quy chuẩn về bằng cấp và phúc lợi.
3. **ITViec:** Cung cấp dữ liệu chuyên sâu cho khối ngành IT/Phần mềm và Phân tích Dữ liệu/BI với bảng kỹ năng kỹ thuật (Tech-stack) phân hóa rõ ràng.
4. **LinkedIn:** Bổ sung các việc làm mang tính toàn cầu, vị trí làm việc từ xa (Remote) và các chứng chỉ quốc tế.

Dữ liệu bao phủ **6 nhóm ngành kinh tế mũi nhọn**: *IT/Phần mềm*, *Phân tích dữ liệu/BI*, *Marketing*, *Tài chính/Kế toán*, *Quản trị kinh doanh*, và *Kỹ thuật*.

### 2.2. Hồ sơ tương tác người dùng (User Input Profile)
Hệ thống thiết kế giao diện tương tác thu thập 4 tham số động từ ứng viên:
* **Ngành nghề mong muốn (`preferred_industry`):** Định hướng lĩnh vực nghề nghiệp chính.
* **Danh sách kỹ năng sở hữu (`student_skills`):** Chuỗi kỹ năng chuyên môn và kỹ năng mềm ứng viên đã tích lũy (hỗ trợ nhập tự do kết hợp chọn nhanh từ ngân hàng kỹ năng).
* **Địa bàn mong muốn (`preferred_location`):** Phân vùng địa lý (Hà Nội, TP.HCM, Đà Nẵng, Remote).
* **Mức lương kỳ vọng (`expected_salary`):** Giá trị số liên tục tính theo đơn vị triệu VNĐ/tháng.

---

## PHẦN 3: QUY TRÌNH ETL VÀ KIẾN TRÚC LƯU TRỮ TỔNG THỂ

Quy trình ETL (Extract - Transform - Load) được thiết kế tối ưu bằng ngôn ngữ Python, bảo đảm chuẩn hóa dòng chảy dữ liệu từ dữ liệu thô đến lớp hiển thị báo cáo.

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. EXTRACT: Thu thập dữ liệu từ 4 sàn (TopCV, VNWorks, ITViec, Linked) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Raw Data
┌───────────────────────────────────▼────────────────────────────────────┐
│ 2. TRANSFORM (Pandas & NumPy Engine):                                  │
│    • Xử lý khuyết thiếu (Group Median Imputation)                      │
│    • Chuẩn hóa dải lương & tính salary_avg = min*0.4 + max*0.6         │
│    • Tính Demand Score theo phân phối chuẩn & Feature Engineering      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Clean Dataframe
┌───────────────────────────────────▼────────────────────────────────────┐
│ 3. LOAD (SQLAlchemy Engine):                                           │
│    • Database: data/jobs_bi.db (Bảng jobs_data)                        │
│    • Export: data/jobs_dataset.csv (phục vụ đối soát & Excel)          │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
      WEBSITE FLASK APPLICATION             APACHE SUPERSET DASHBOARD
   (AI Matching & Realtime Filter)         (Interactive BI Visualization)
```

### 3.1. Giai đoạn Extract (Trích xuất dữ liệu)
* Dữ liệu thô thu thập từ các cổng việc làm được tiền xử lý cấu trúc thành các trường thống nhất: tiêu đề vị trí, tên công ty, phân loại ngành, chuỗi kỹ năng, địa điểm, dải lương ban đầu, cấp bậc kinh nghiệm và ngày đăng tuyển (rải đều trong phạm vi 6 tháng gần nhất để phục vụ phân tích chuỗi thời gian).

### 3.2. Giai đoạn Transform (Làm sạch & Kỹ nghệ Tính năng - Feature Engineering)
Sử dụng thư viện **Pandas** và **NumPy** để triển khai chuỗi xử lý:
* **Khử nhiễu và xử lý giá trị khuyết thiếu (Missing Data Imputation):** Các vị trí thiếu giá trị `salary_min` hoặc `salary_max` được điền khuyết tự động bằng giá trị trung vị (**Median**) theo từng nhóm phân cấp `[industry x experience_level]`, tránh làm sai lệch phân phối tổng thể.
* **Chuẩn hóa mức lương (`salary_avg`):** Mức lương thực tế được tính bằng trung bình có trọng số thay vì trung bình cộng giản đơn:
  $$\text{salary\_avg} = \text{salary\_min} \times 0.4 + \text{salary\_max} \times 0.6$$
  *(Trọng số 0.6 cho cận trên phản ánh xu hướng thương lượng lương thực tế của ứng viên).*
* **Xây dựng Điểm số Nhu cầu Thị trường (`demand_score`):**
  Nhúng chỉ báo định lượng từ 1.0 đến 10.0 thông qua tính toán đa nhân tố bằng NumPy:
  $$\text{Demand Raw} = 0.45 \cdot \left(\frac{\text{Lương TB}}{\text{Lương Max Ngành}}\right) + 0.35 \cdot \left(\frac{\text{Số Kỹ năng}}{6}\right) + 0.20 \cdot \text{Bonus Địa phương} + \mathcal{N}(0, 0.05)$$
* **Phân lớp chỉ số BI phục vụ phân tích:**
  * `income_group`: Phân 4 nhóm thu nhập bằng `np.digitize` (Thấp $<8M$, Trung bình $8-13M$, Khá $13-18M$, Cao $>18M$).
  * `demand_tier`: Phân tầng mức độ nóng (Thấp, Trung bình, Cao, Rất cao).
  * `posted_month`, `posted_week`: Phân rã trục thời gian phục vụ phân tích xu hướng tuyển dụng (Time-series Analysis).

### 3.3. Giai đoạn Load (Lưu trữ và Tích hợp Kiến trúc Kép)
Dữ liệu hoàn thiện (gồm 20 cột chuẩn hóa) được nạp thông qua **SQLAlchemy Engine**:
1. **Lưu trữ cục bộ hiệu năng cao:** Bảng `jobs_data` trong cơ sở dữ liệu SQLite tại `data/jobs_bi.db` và xuất đồng thời ra `data/jobs_dataset.csv` (UTF-8-SIG).
2. **Khả năng phục vụ kép (Dual-layer Serving):**
   * **Lớp Ứng dụng Trực tuyến (Flask Web Application):** Kết nối trực tiếp vào SQLite để thực thi thuật toán so khớp AI Smart Matching tức thì (thời gian phản hồi $< 0.1$ giây) và cung cấp bộ lọc tương tác đa chiều.
   * **Lớp Phân tích BI Chuyên sâu (Apache Superset):** Kết nối trực tiếp qua SQLAlchemy URI hoặc thông qua Dataset `student_jobs_bi` để xuất bản hệ thống Dashboard BI trực quan hóa 4 chiều: Phân bố Địa bàn (Donut Chart), Lương theo Ngành nghề (Bar Chart), Xu hướng Tuyển dụng 6 tháng (Line Chart) và Ma trận Nhu cầu theo Nguồn tuyển dụng (Treemap Chart).

---

## KẾT LUẬN VÀ GIÁ TRỊ MANG LẠI

Bản đề xuất đã thiết lập một nền tảng vững chắc cho hệ thống **Smart Job BI System**, kết hợp hài hòa giữa **Kỹ thuật Dữ liệu (Data Engineering)**, **Khoa học Dữ liệu (Data Science - Matching Engine)** và **Kinh doanh Thông minh (Business Intelligence - Superset)**. 

Bằng cách loại bỏ sự phân mảnh thông tin từ 4 nền tảng lớn và định lượng hóa độ khớp kỹ năng cùng khoảng trống năng lực, hệ thống không chỉ là công cụ tìm kiếm việc làm mà còn đóng vai trò là một **trợ lý định hướng nghề nghiệp thông minh**, giúp sinh viên mới tốt nghiệp đưa ra quyết định dựa trên dữ liệu thực tế thay vì cảm tính.

