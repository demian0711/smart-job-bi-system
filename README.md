# 🎓 Smart Job BI System
### Hệ thống tìm kiếm thông tin việc làm thông minh cho sinh viên mới tốt nghiệp

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Tổng quan

**Smart Job BI System** là một hệ thống Kinh doanh Thông minh (Business Intelligence) được xây dựng trong khuôn khổ môn học **Hệ thống BI**, nhằm hỗ trợ **sinh viên mới tốt nghiệp** tìm kiếm việc làm phù hợp thông qua phân tích dữ liệu lớn về thị trường lao động.

Thay vì tìm kiếm thụ động, hệ thống cung cấp **cái nhìn toàn diện, trực quan và dựa trên dữ liệu** — giúp sinh viên ra quyết định chính xác hơn về hướng đi nghề nghiệp.

---

## 🎯 Mục tiêu hệ thống

| Mục tiêu | Mô tả |
|---|---|
| 🔍 **Tìm việc theo ngành nghề** | Lọc và gợi ý vị trí tuyển dụng theo lĩnh vực: CNTT, Tài chính, Marketing, Kỹ thuật, v.v. |
| 🛠️ **Tìm việc theo kỹ năng** | Phân tích mức độ phù hợp dựa trên kỹ năng của ứng viên (Python, Excel, Giao tiếp, v.v.) |
| 📍 **Tìm việc theo địa điểm** | Lọc theo tỉnh/thành phố, hỗ trợ làm việc từ xa (Remote) |
| 📊 **Hỗ trợ ra quyết định** | Biểu đồ xu hướng tuyển dụng, mức lương trung bình, kỹ năng được yêu cầu nhiều nhất |
| 🤖 **Gợi ý thông minh** | Áp dụng Machine Learning để đề xuất công việc phù hợp với hồ sơ ứng viên |

---

## 🏗️ Kiến trúc công nghệ

```
┌─────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                   │
│              Flask Web App  +  Apache Superset           │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    ANALYTICS LAYER                       │
│         Pandas · NumPy · Scikit-learn · Matplotlib       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                      DATA LAYER                          │
│              SQLAlchemy ORM  +  SQLite / PostgreSQL      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   DATA SOURCE LAYER                      │
│          CSV · Excel · Web Scraping · Faker (mock)       │
└─────────────────────────────────────────────────────────┘
```

### 🧰 Stack công nghệ chi tiết

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| **Backend** | [Flask](https://flask.palletsprojects.com/) | Web server, REST API, routing |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) | Xử lý, làm sạch, biến đổi dữ liệu |
| **Numerical Computing** | [NumPy](https://numpy.org/) | Tính toán ma trận, thống kê |
| **Visualization** | [Matplotlib](https://matplotlib.org/) | Vẽ biểu đồ phân tích |
| **BI Dashboard** | [Apache Superset](https://superset.apache.org/) | Dashboard tương tác, drill-down |
| **ORM / Database** | [SQLAlchemy](https://www.sqlalchemy.org/) | Quản lý CSDL, truy vấn dữ liệu |
| **Machine Learning** | [Scikit-learn](https://scikit-learn.org/) | Mô hình gợi ý, phân loại công việc |
| **Mock Data** | [Faker](https://faker.readthedocs.io/) | Sinh dữ liệu giả lập thực tế |

---

## 📁 Cấu trúc thư mục

```
smart-job-bi-system/
│
├── data/                   # Dữ liệu đầu vào (CSV, Excel, SQLite)
│   ├── sample_jobs.csv     # Dữ liệu mẫu tin tuyển dụng
│   └── sample_skills.csv   # Dữ liệu mẫu kỹ năng
│
├── src/                    # Mã nguồn Python
│   ├── models.py           # SQLAlchemy models
│   ├── data_generator.py   # Sinh dữ liệu với Faker
│   ├── analytics.py        # Phân tích dữ liệu với Pandas/NumPy
│   ├── ml_recommender.py   # Mô hình gợi ý việc làm
│   └── charts.py           # Vẽ biểu đồ với Matplotlib
│
├── templates/              # HTML templates (Jinja2)
│   ├── index.html
│   ├── search.html
│   └── dashboard.html
│
├── static/
│   └── charts/             # Biểu đồ được xuất ra (PNG/SVG)
│
├── app.py                  # Entry point Flask application
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt

### 1. Clone repository

```bash
git clone https://github.com/<your-username>/smart-job-bi-system.git
cd smart-job-bi-system
```

### 2. Tạo và kích hoạt môi trường ảo

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Sinh dữ liệu mẫu

```bash
python src/data_generator.py
```

### 5. Chạy ứng dụng

```bash
python app.py
```

Truy cập: [http://localhost:5000](http://localhost:5000)

---

## 📊 Tính năng phân tích BI

- **Top 10 kỹ năng được yêu cầu nhiều nhất** — Bar chart
- **Phân bố mức lương theo ngành nghề** — Box plot
- **Xu hướng tuyển dụng theo tháng** — Line chart
- **Tỉ lệ vị trí Remote vs. Onsite** — Pie chart
- **Ma trận tương quan kỹ năng ↔ mức lương** — Heatmap

---

## 👥 Nhóm thực hiện

> *Cập nhật thông tin thành viên nhóm tại đây*

| Họ và tên | MSSV | Vai trò |
|---|---|---|
| Nguyễn Văn A | 2100000 | Backend & ML |
| Trần Thị B | 2100001 | Data & Analytics |
| Lê Văn C | 2100002 | Frontend & Visualization |

---

## 📄 Giấy phép

Dự án được thực hiện cho mục đích học tập — Môn **Hệ thống Kinh doanh Thông minh**.

