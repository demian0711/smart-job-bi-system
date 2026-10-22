"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         SMART JOB BI SYSTEM — ETL Data Pipeline                            ║
║         Hệ thống tìm kiếm việc làm cho sinh viên mới tốt nghiệp            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Chức năng:                                                                 ║
║   E — Extract  : Sinh 2.500 bản ghi tuyển dụng từ nhiều nguồn              ║
║   T — Transform: Làm sạch, chuẩn hóa và Feature Engineering                ║
║   L — Load     : Lưu vào SQLite (SQLAlchemy) + xuất CSV                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
import warnings
from datetime import datetime, timedelta
from pathlib import Path

# Đảm bảo console Windows hiển thị đúng Unicode (UTF-8)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text, inspect

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# CẤU HÌNH
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent   # Gốc dự án
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "jobs_bi.db"
CSV_PATH = DATA_DIR / "jobs_dataset.csv"

TOTAL_RECORDS = 2_500
RANDOM_SEED   = 42

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: LOG
# ─────────────────────────────────────────────────────────────────────────────

def _sep(char: str = "─", width: int = 70) -> None:
    print(char * width)

def log_step(step: int, total: int, title: str) -> None:
    _sep("═")
    print(f"  BƯỚC {step}/{total}  │  {title}")
    _sep("═")

def log_info(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] ℹ  {msg}")

def log_ok(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] ✔  {msg}")

def log_warn(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] ⚠  {msg}")

def log_metric(label: str, value) -> None:
    print(f"         {'·':>2} {label:<35} {value}")

# ─────────────────────────────────────────────────────────────────────────────
# DỮ LIỆU GỐC (LOOKUP TABLES)
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRIES = {
    "IT/Phần mềm": {
        "titles": [
            "Junior Software Engineer", "Backend Developer", "Frontend Developer",
            "Full-Stack Developer", "Mobile Developer (Flutter)", "DevOps Intern",
            "Software QA Tester", "Junior Java Developer", "React Developer",
            "Python Developer Intern",
        ],
        "skills_pool": [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Vue.js",
            "Node.js", "Spring Boot", "Flutter", "Docker", "Git", "REST API",
            "MySQL", "PostgreSQL", "Linux", "Agile/Scrum",
        ],
        "salary_range": (8, 25),
    },
    "Phân tích dữ liệu/BI": {
        "titles": [
            "Data Analyst Intern", "Junior BI Analyst", "Business Intelligence Intern",
            "Data Engineer Trainee", "Junior Data Scientist", "Analytics Associate",
            "Reporting Analyst", "ETL Developer Intern",
        ],
        "skills_pool": [
            "Python", "SQL", "Pandas", "NumPy", "Power BI", "Apache Superset",
            "Tableau", "Excel", "Google Data Studio", "Matplotlib", "Seaborn",
            "Scikit-learn", "PySpark", "BigQuery", "ETL", "Statistics",
        ],
        "salary_range": (9, 22),
    },
    "Marketing": {
        "titles": [
            "Digital Marketing Intern", "Content Marketing Executive",
            "SEO/SEM Specialist Trainee", "Social Media Intern",
            "Brand Marketing Associate", "Performance Marketing Intern",
            "Email Marketing Specialist", "Marketing Analytics Intern",
        ],
        "skills_pool": [
            "Google Analytics", "Facebook Ads", "SEO", "Content Writing",
            "Canva", "Photoshop", "Email Marketing", "CRM", "Excel",
            "Giao tiếp", "Sáng tạo nội dung", "TikTok Ads", "Copywriting",
        ],
        "salary_range": (6, 18),
    },
    "Tài chính/Kế toán": {
        "titles": [
            "Kế toán mới tốt nghiệp", "Junior Accountant", "Financial Analyst Intern",
            "Kiểm toán nội bộ Intern", "Tax Accountant Trainee",
            "Accounts Payable Intern", "Treasury Analyst Intern",
        ],
        "skills_pool": [
            "Excel", "SAP", "MISA", "Kế toán tài chính", "Thuế", "Kiểm toán",
            "PowerPoint", "Báo cáo tài chính", "IFRS", "VAS", "SQL",
            "Tư duy phân tích", "Giao tiếp",
        ],
        "salary_range": (7, 18),
    },
    "Quản trị kinh doanh": {
        "titles": [
            "Business Analyst Intern", "Operations Intern", "HR Trainee",
            "Project Coordinator Intern", "Supply Chain Intern",
            "Customer Success Intern", "Sales Executive Trainee",
            "Administrative Officer Intern",
        ],
        "skills_pool": [
            "Excel", "PowerPoint", "Giao tiếp", "Thuyết trình", "Quản lý dự án",
            "Tiếng Anh", "CRM", "ERP", "Tư duy chiến lược", "Leadership",
            "Problem Solving", "Trello", "Jira",
        ],
        "salary_range": (6, 16),
    },
    "Kỹ thuật": {
        "titles": [
            "Kỹ sư cơ khí mới ra trường", "Electrical Engineer Trainee",
            "Civil Engineer Intern", "AutoCAD Draftsman Intern",
            "Mechanical Design Intern", "Industrial Engineer Trainee",
            "Quality Control Inspector Intern",
        ],
        "skills_pool": [
            "AutoCAD", "SolidWorks", "MATLAB", "PLC", "Kỹ thuật điện",
            "Cơ khí chính xác", "Quản lý chất lượng", "ISO 9001",
            "Đọc bản vẽ kỹ thuật", "Excel", "Tiếng Anh chuyên ngành",
        ],
        "salary_range": (7, 20),
    },
}

LOCATIONS = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Remote"]
LOCATION_WEIGHTS = [0.35, 0.40, 0.15, 0.10]

EXPERIENCE_LEVELS = ["Thực tập sinh", "Mới tốt nghiệp", "Dưới 1 năm"]
EXPERIENCE_WEIGHTS = [0.30, 0.45, 0.25]

SOURCES = ["TopCV", "VietnamWorks", "ITViec", "LinkedIn"]
SOURCE_WEIGHTS_BY_INDUSTRY = {
    "IT/Phần mềm":           [0.20, 0.25, 0.45, 0.10],
    "Phân tích dữ liệu/BI":  [0.25, 0.25, 0.35, 0.15],
    "Marketing":              [0.35, 0.35, 0.10, 0.20],
    "Tài chính/Kế toán":     [0.40, 0.45, 0.05, 0.10],
    "Quản trị kinh doanh":   [0.35, 0.40, 0.05, 0.20],
    "Kỹ thuật":              [0.35, 0.45, 0.10, 0.10],
}

COMPANIES = [
    "FPT Software", "VNG Corporation", "Tiki", "Shopee Vietnam", "Grab Vietnam",
    "MoMo", "VinAI Research", "VNPT Technology", "CMC Technology", "Haravan",
    "Masan Group", "Vinamilk", "Techcombank", "MB Bank", "VPBank",
    "Deloitte Vietnam", "PwC Vietnam", "KPMG Vietnam", "Ernst & Young Vietnam",
    "Accenture Vietnam", "Nielsen Vietnam", "Unilever Vietnam", "P&G Vietnam",
    "Samsung Vietnam", "LG Electronics Vietnam", "Intel Products Vietnam",
    "Bosch Vietnam", "Siemens Vietnam", "ABB Vietnam", "Schneider Electric VN",
    "HĐBT Consulting", "KMS Technology", "Base.vn", "BKAV", "Viettel Digital",
    "Sacombank", "VietinBank", "Agribank", "HDBank", "OCB",
    "Got It Vietnam", "Cốc Cốc", "Zalo", "VCCorp", "Sendo",
    "Sendo Farm", "Logivan", "Ahamove", "GHN Express", "VNPost",
    "Rikkeisoft", "Global CyberSoft", "TMA Solutions", "KienlongBank", "Orient Software",
    "Vccorp Media", "Traphaco", "Vingroup IT", "VinBrain", "VinBigData",
]

# ─────────────────────────────────────────────────────────────────────────────
# BƯỚC E — EXTRACT: SINH DỮ LIỆU GIẢ LẬP
# ─────────────────────────────────────────────────────────────────────────────

def extract_generate_data(n: int = TOTAL_RECORDS) -> pd.DataFrame:
    """
    Sinh n bản ghi tuyển dụng tổng hợp từ nhiều ngành nghề và nguồn khác nhau.
    """
    log_step(1, 4, "EXTRACT — Sinh dữ liệu tuyển dụng tổng hợp")
    log_info(f"Tổng số bản ghi cần tạo   : {n:,}")
    log_info(f"Random seed               : {RANDOM_SEED}")

    industry_list  = list(INDUSTRIES.keys())
    # Phân bổ số bản ghi theo ngành (trọng số)
    industry_weights = [0.22, 0.18, 0.15, 0.15, 0.15, 0.15]
    industry_counts  = np.random.multinomial(n, industry_weights).tolist()

    log_info("Phân bổ bản ghi theo ngành:")
    for ind, cnt in zip(industry_list, industry_counts):
        log_metric(ind, f"{cnt:,} bản ghi")

    # Ngày đăng: rải đều 6 tháng gần nhất
    today     = datetime.now()
    start_day = today - timedelta(days=180)

    records = []

    for industry, count in zip(industry_list, industry_counts):
        cfg = INDUSTRIES[industry]
        src_weights = SOURCE_WEIGHTS_BY_INDUSTRY[industry]

        for i in range(count):
            # --- Cơ bản ---
            job_id   = f"JOB-{len(records) + 1:05d}"
            title    = random.choice(cfg["titles"])
            company  = random.choice(COMPANIES)
            location = random.choices(LOCATIONS, weights=LOCATION_WEIGHTS, k=1)[0]
            exp_lvl  = random.choices(EXPERIENCE_LEVELS, weights=EXPERIENCE_WEIGHTS, k=1)[0]
            source   = random.choices(SOURCES, weights=src_weights, k=1)[0]

            # --- Kỹ năng: chọn ngẫu nhiên 3–6 kỹ năng ---
            n_skills = random.randint(3, 6)
            skills   = ", ".join(
                random.sample(cfg["skills_pool"], min(n_skills, len(cfg["skills_pool"])))
            )

            # --- Mức lương ---
            sal_min_base, sal_max_base = cfg["salary_range"]
            # Điều chỉnh theo kinh nghiệm
            exp_factor = {"Thực tập sinh": 0.75, "Mới tốt nghiệp": 1.0, "Dưới 1 năm": 1.20}
            factor     = exp_factor[exp_lvl]
            sal_min    = round(
                np.random.uniform(sal_min_base * 0.7, sal_min_base) * factor, 1
            )
            sal_max    = round(
                np.random.uniform(sal_max_base * 0.85, sal_max_base) * factor, 1
            )
            if sal_max < sal_min:
                sal_min, sal_max = sal_max, sal_min

            # --- Điểm nhu cầu thị trường (NumPy) ---
            # Kết hợp mức lương tương đối, vị trí và số lượt kỹ năng
            skill_richness = n_skills / 6
            loc_bonus      = {"Hà Nội": 0.3, "TP.HCM": 0.4, "Đà Nẵng": 0.2, "Remote": 0.1}
            demand_raw     = (
                0.45 * ((sal_min + sal_max) / 2) / sal_max_base
                + 0.35 * skill_richness
                + 0.20 * loc_bonus[location]
                + np.random.normal(0, 0.05)          # nhiễu Gaussian
            )
            demand_score   = float(np.clip(round(demand_raw * 10, 2), 1.0, 10.0))

            # --- Ngày đăng: phân phối lệch về gần hiện tại (tuyển nhiều hơn) ---
            days_ago     = int(np.random.beta(2, 5) * 180)
            posted_date  = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            # --- Giá trị NULL ngẫu nhiên 2% để test cleaning ---
            if random.random() < 0.02:
                sal_min = np.nan
            if random.random() < 0.02:
                sal_max = np.nan

            records.append({
                "job_id":           job_id,
                "title":            title,
                "company":          company,
                "industry":         industry,
                "skills":           skills,
                "location":         location,
                "salary_min":       sal_min,
                "salary_max":       sal_max,
                "experience_level": exp_lvl,
                "demand_score":     demand_score,
                "posted_date":      posted_date,
                "source":           source,
            })

    df = pd.DataFrame(records)
    log_ok(f"Đã sinh xong {len(df):,} bản ghi.")
    log_metric("Các cột", list(df.columns))
    log_metric("Shape", df.shape)
    _sep()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# BƯỚC T — TRANSFORM: CLEANING + FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def transform_clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Data Cleaning & Feature Engineering:
      - Chuẩn hóa kiểu dữ liệu
      - Xử lý missing values
      - Tính salary_avg
      - Phân loại income_group
      - Thêm cột phụ trợ BI
    """
    log_step(2, 4, "TRANSFORM — Data Cleaning & Feature Engineering")

    df = df.copy()
    total = len(df)

    # ── 2.1 Kiểu dữ liệu ────────────────────────────────────────────────────
    log_info("2.1 Chuẩn hóa kiểu dữ liệu...")
    df["posted_date"]    = pd.to_datetime(df["posted_date"])
    df["salary_min"]     = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"]     = pd.to_numeric(df["salary_max"], errors="coerce")
    df["demand_score"]   = pd.to_numeric(df["demand_score"], errors="coerce")
    df["job_id"]         = df["job_id"].astype(str)
    log_ok("Kiểu dữ liệu đã được chuẩn hóa.")

    # ── 2.2 Missing values ───────────────────────────────────────────────────
    log_info("2.2 Phát hiện & xử lý giá trị thiếu...")
    null_before = df.isnull().sum()
    null_cols   = null_before[null_before > 0]
    if null_cols.empty:
        log_warn("Không tìm thấy giá trị NULL nào.")
    else:
        for col, cnt in null_cols.items():
            log_metric(f"Null tại '{col}'", f"{cnt} bản ghi ({cnt/total*100:.1f}%)")

    # Điền salary_min/max = median theo ngành x kinh nghiệm
    for col in ["salary_min", "salary_max"]:
        group_median = (
            df.groupby(["industry", "experience_level"])[col]
            .transform("median")
        )
        filled = df[col].isna().sum()
        df[col] = df[col].fillna(group_median)
        # Fallback: toàn cục nếu vẫn còn NaN
        df[col] = df[col].fillna(df[col].median())
        log_ok(f"Đã điền {filled} giá trị null tại '{col}' bằng median theo nhóm.")

    # demand_score null -> 5.0 (giữa thang)
    ds_null = df["demand_score"].isna().sum()
    if ds_null:
        df["demand_score"] = df["demand_score"].fillna(5.0)
        log_ok(f"Đã điền {ds_null} giá trị null tại 'demand_score' = 5.0.")

    log_ok(f"Tổng null sau xử lý: {df.isnull().sum().sum()}")

    # ── 2.3 Chuẩn hóa mức lương ─────────────────────────────────────────────
    log_info("2.3 Chuẩn hóa & ràng buộc mức lương...")

    # Đảm bảo salary_min <= salary_max
    mask = df["salary_min"] > df["salary_max"]
    df.loc[mask, ["salary_min", "salary_max"]] = (
        df.loc[mask, ["salary_max", "salary_min"]].values
    )
    log_metric("Bản ghi có min > max (đã đảo)", int(mask.sum()))

    # Làm tròn 1 chữ số thập phân
    df["salary_min"] = df["salary_min"].round(1)
    df["salary_max"] = df["salary_max"].round(1)

    # ── 2.4 Feature Engineering ──────────────────────────────────────────────
    log_info("2.4 Feature Engineering — tính các cột mới...")

    # salary_avg: trọng bình (min * 0.4 + max * 0.6) ~ sát thực tế hơn mean
    df["salary_avg"] = (
        df["salary_min"] * 0.4 + df["salary_max"] * 0.6
    ).round(1)
    log_ok("'salary_avg' đã được tính (weighted avg: 40% min + 60% max).")

    # salary_range_width: biên độ lương
    df["salary_range_width"] = (df["salary_max"] - df["salary_min"]).round(1)

    # income_group: phân nhóm thu nhập bằng NumPy digitize
    bins   = [0, 8, 13, 18, np.inf]
    labels = ["Thấp (<8M)", "Trung bình (8–13M)", "Khá (13–18M)", "Cao (>18M)"]
    indices = np.digitize(df["salary_avg"].values, bins) - 1
    indices = np.clip(indices, 0, len(labels) - 1)
    df["income_group"] = [labels[i] for i in indices]
    log_ok("'income_group' đã được phân loại (4 nhóm thu nhập).")

    # demand_tier: phân loại nhu cầu thị trường
    demand_conditions = [
        df["demand_score"] >= 8.0,
        (df["demand_score"] >= 6.0) & (df["demand_score"] < 8.0),
        (df["demand_score"] >= 4.0) & (df["demand_score"] < 6.0),
        df["demand_score"] < 4.0,
    ]
    demand_choices = ["Rất cao", "Cao", "Trung bình", "Thấp"]
    df["demand_tier"] = np.select(demand_conditions, demand_choices, default="Trung bình")
    log_ok("'demand_tier' đã được phân loại theo demand_score.")

    # posted_month, posted_week: cho phân tích xu hướng theo thời gian
    df["posted_month"]   = df["posted_date"].dt.to_period("M").astype(str)
    df["posted_week"]    = df["posted_date"].dt.isocalendar().week.astype(int)
    df["days_since_post"] = (pd.Timestamp.today() - df["posted_date"]).dt.days
    log_ok("Các cột thời gian (posted_month, posted_week, days_since_post) đã tạo.")

    # skill_count: số lượng kỹ năng yêu cầu
    df["skill_count"] = df["skills"].str.split(",").apply(len)
    log_ok("'skill_count' đã được tính.")

    # ── 2.5 Kiểm tra tính nhất quán ─────────────────────────────────────────
    log_info("2.5 Kiểm tra tính nhất quán dữ liệu...")
    assert df["salary_min"].le(df["salary_max"]).all(), "salary_min > salary_max!"
    assert df["demand_score"].between(1.0, 10.0).all(), "demand_score ngoài [1, 10]!"
    assert df["job_id"].is_unique, "job_id không duy nhất!"
    log_ok("Tất cả ràng buộc dữ liệu đã được thỏa mãn.")

    # ── 2.6 Sắp xếp lại cột cuối cùng ──────────────────────────────────────
    final_columns = [
        "job_id", "title", "company", "industry", "skills", "skill_count",
        "location", "salary_min", "salary_max", "salary_avg", "salary_range_width",
        "income_group", "experience_level", "demand_score", "demand_tier",
        "posted_date", "posted_month", "posted_week", "days_since_post", "source",
    ]
    df = df[final_columns]

    log_ok(f"Transform hoàn tất. Shape cuối: {df.shape}")
    _sep()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# BƯỚC L — LOAD: LƯU VÀO SQLite + XUẤT CSV
# ─────────────────────────────────────────────────────────────────────────────

def load_to_sqlite(df: pd.DataFrame) -> None:
    """
    Tải DataFrame vào SQLite thông qua SQLAlchemy.
    Bảng: jobs_data
    """
    log_step(3, 4, "LOAD — Lưu dữ liệu vào SQLite (SQLAlchemy)")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{DB_PATH}"
    log_info(f"Kết nối SQLAlchemy → {db_url}")

    engine = create_engine(db_url, echo=False)

    # Chuyển đổi posted_date sang string để SQLite lưu đúng
    df_to_load = df.copy()
    df_to_load["posted_date"] = df_to_load["posted_date"].dt.strftime("%Y-%m-%d")

    log_info("Ghi DataFrame vào bảng 'jobs_data' (if_exists=replace)...")
    t0 = time.perf_counter()
    df_to_load.to_sql(
        name="jobs_data",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=500,
        method="multi",
    )
    elapsed = time.perf_counter() - t0

    # Xác minh
    with engine.connect() as conn:
        row_count = conn.execute(text("SELECT COUNT(*) FROM jobs_data")).scalar()
        col_count = len(conn.execute(text("PRAGMA table_info(jobs_data)")).fetchall())

    log_ok(f"Đã ghi xong trong {elapsed:.2f}s.")
    log_metric("Đường dẫn DB",   str(DB_PATH))
    log_metric("Bảng",           "jobs_data")
    log_metric("Số hàng trong DB", f"{row_count:,}")
    log_metric("Số cột trong DB",  col_count)
    _sep()


def load_to_csv(df: pd.DataFrame) -> None:
    """
    Xuất DataFrame ra file CSV.
    """
    log_step(4, 4, "LOAD — Xuất file CSV")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_info(f"Xuất CSV → {CSV_PATH}")

    t0 = time.perf_counter()
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    elapsed = time.perf_counter() - t0
    file_size_kb = CSV_PATH.stat().st_size / 1024

    log_ok(f"Xuất CSV hoàn tất trong {elapsed:.2f}s.")
    log_metric("Đường dẫn", str(CSV_PATH))
    log_metric("Kích thước", f"{file_size_kb:.1f} KB")
    log_metric("Encoding",   "utf-8-sig (hỗ trợ Excel mở tiếng Việt)")
    _sep()


# ─────────────────────────────────────────────────────────────────────────────
# BÁO CÁO TỔNG KẾT
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame) -> None:
    """
    In báo cáo thống kê tóm tắt sau ETL để kiểm tra nhanh chất lượng dữ liệu.
    """
    _sep("═")
    print("  📊  BÁO CÁO TỔNG KẾT SAU ETL")
    _sep("═")

    print("\n  ► Phân bổ theo Ngành nghề:")
    industry_cnt = df["industry"].value_counts()
    for name, cnt in industry_cnt.items():
        bar = "█" * (cnt // 30)
        print(f"     {name:<30} {cnt:>4}  {bar}")

    print("\n  ► Phân bổ theo Địa điểm:")
    for loc, cnt in df["location"].value_counts().items():
        pct = cnt / len(df) * 100
        print(f"     {loc:<12} {cnt:>4}  ({pct:.1f}%)")

    print("\n  ► Phân bổ theo Nguồn tuyển dụng:")
    for src, cnt in df["source"].value_counts().items():
        print(f"     {src:<15} {cnt:>4}")

    print("\n  ► Phân bổ theo Nhóm thu nhập:")
    for grp, cnt in df["income_group"].value_counts().sort_index().items():
        print(f"     {grp:<25} {cnt:>4}")

    print("\n  ► Thống kê lương (triệu VNĐ):")
    sal_stats = df["salary_avg"].describe()
    print(f"     Min    : {sal_stats['min']:.1f}M")
    print(f"     Median : {df['salary_avg'].median():.1f}M")
    print(f"     Mean   : {sal_stats['mean']:.1f}M")
    print(f"     Max    : {sal_stats['max']:.1f}M")

    print("\n  ► Thống kê Demand Score:")
    ds_stats = df["demand_score"].describe()
    print(f"     Min    : {ds_stats['min']:.2f}")
    print(f"     Mean   : {ds_stats['mean']:.2f}")
    print(f"     Max    : {ds_stats['max']:.2f}")

    print("\n  ► Khoảng thời gian dữ liệu:")
    print(f"     Từ     : {df['posted_date'].min().date()}")
    print(f"     Đến    : {df['posted_date'].max().date()}")

    _sep("═")
    print("  ✅  ETL Pipeline hoàn tất thành công!")
    _sep("═")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline() -> pd.DataFrame:
    """
    Điều phối toàn bộ quá trình ETL:
      1. Extract  — Sinh dữ liệu
      2. Transform — Làm sạch + Feature Engineering
      3. Load DB  — Lưu vào SQLite
      4. Load CSV — Xuất CSV
      5. Summary  — Báo cáo thống kê
    """
    _sep("═")
    print()
    print("  ██████╗ ██╗    ███████╗ ██████╗ ██████╗      ██████╗ ██╗")
    print("  ██╔══██╗██║    ██╔════╝ ╚══██╔╝ ██╔══██╗     ██╔══██╗██║")
    print("  ██████╔╝██║    ███████╗   ██║   ██████╔╝     ██████╔╝██║")
    print("  ██╔══██╗██║    ╚════██║   ██║   ██╔══╝       ██╔══██╗██║")
    print("  ██████╔╝██║    ███████║ ██████╗ ██║          ██████╔╝███████╗")
    print("  ╚═════╝ ╚═╝    ╚══════╝ ╚═════╝ ╚═╝          ╚═════╝ ╚══════╝")
    print()
    print("       Smart Job BI System — ETL Data Pipeline v1.0")
    print(f"       Khởi chạy lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    _sep("═")

    pipeline_start = time.perf_counter()

    # E — Extract
    raw_df = extract_generate_data(TOTAL_RECORDS)

    # T — Transform
    clean_df = transform_clean_and_engineer(raw_df)

    # L — Load to SQLite
    load_to_sqlite(clean_df)

    # L — Load to CSV
    load_to_csv(clean_df)

    # Summary
    print_summary(clean_df)

    total_elapsed = time.perf_counter() - pipeline_start
    print(f"  ⏱  Tổng thời gian pipeline: {total_elapsed:.2f} giây")
    print()

    return clean_df


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = run_pipeline()
