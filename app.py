"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         SMART JOB BI SYSTEM — Flask Web Application                        ║
║         Routes: /  │  /matching  │  /analytics  │  /superset               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

from flask import Flask, render_template, request, jsonify
import pandas as pd
from sqlalchemy import create_engine

# ── Path setup ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from smart_engine import recommend_jobs, generate_bi_charts  # noqa: E402

# ── App config ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "smart-job-bi-secret-2024"

DB_PATH    = BASE_DIR / "data" / "jobs_bi.db"
CHARTS_DIR = BASE_DIR / "static" / "charts"

# ── Reference data ─────────────────────────────────────────────────────────────
INDUSTRIES = [
    "IT/Phần mềm", "Phân tích dữ liệu/BI", "Marketing",
    "Tài chính/Kế toán", "Quản trị kinh doanh", "Kỹ thuật",
]
LOCATIONS = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Remote"]
SOURCES   = ["TopCV", "VietnamWorks", "ITViec", "LinkedIn"]


def _get_skill_lists() -> tuple[list[str], list[str]]:
    """
    Trích xuất từ DB: danh sách kỹ năng duy nhất (sorted) và Top-10 kỹ năng phổ biến.
    Kết quả được cache tại module-level để tránh truy vấn lặp.
    """
    with _engine().connect() as conn:
        df_skills = pd.read_sql("SELECT skills FROM jobs_data", conn)
    raw: list[str] = []
    for cell in df_skills["skills"].dropna():
        raw.extend(s.strip() for s in str(cell).split(",") if s.strip())
    counts   = Counter(raw)
    all_sk   = sorted({s.title() for s in raw})          # duy nhất, sorted A-Z
    top10_sk = [s.title() for s, _ in counts.most_common(10)]
    return all_sk, top10_sk

COMMON_SKILLS = [
    "Python", "SQL", "Excel", "Pandas", "NumPy", "Power BI", "Tableau",
    "Apache Superset", "Matplotlib", "Scikit-learn", "ETL", "Statistics",
    "Java", "JavaScript", "React", "Vue.js", "Node.js", "TypeScript",
    "Git", "Docker", "Linux", "REST API", "Agile/Scrum",
    "Google Analytics", "Facebook Ads", "SEO", "Content Writing", "CRM",
    "SAP", "MISA", "Kế toán tài chính", "Thuế", "Kiểm toán", "IFRS",
    "AutoCAD", "SolidWorks", "MATLAB", "PLC",
    "Giao tiếp", "Thuyết trình", "Tiếng Anh", "Quản lý dự án", "Trello",
]

INDUSTRY_BADGE = {
    "IT/Phần mềm":           {"color": "blue",   "icon": "fa-laptop-code"},
    "Phân tích dữ liệu/BI":  {"color": "purple", "icon": "fa-chart-pie"},
    "Marketing":              {"color": "pink",   "icon": "fa-bullhorn"},
    "Tài chính/Kế toán":     {"color": "green",  "icon": "fa-coins"},
    "Quản trị kinh doanh":   {"color": "orange", "icon": "fa-briefcase"},
    "Kỹ thuật":              {"color": "slate",  "icon": "fa-gears"},
}

LOCATION_ICON = {
    "Hà Nội":  "fa-map-marker-alt",
    "TP.HCM":  "fa-map-marker-alt",
    "Đà Nẵng": "fa-map-marker-alt",
    "Remote":  "fa-wifi",
}

# ── DB helpers ─────────────────────────────────────────────────────────────────

def _engine():
    return create_engine(f"sqlite:///{DB_PATH}", echo=False)


def _load_df() -> pd.DataFrame:
    with _engine().connect() as conn:
        df = pd.read_sql("SELECT * FROM jobs_data", conn)
    df["posted_date"] = pd.to_datetime(df["posted_date"])
    return df


def _compute_kpis(df: pd.DataFrame) -> dict:
    top_ind    = df["industry"].value_counts()
    top_source = df["source"].value_counts()
    return {
        "total_jobs":         f"{len(df):,}",
        "avg_salary":         f"{df['salary_avg'].mean():.1f}M",
        "top_industry":       top_ind.idxmax(),
        "top_industry_count": int(top_ind.max()),
        "total_sources":      df["source"].nunique(),
        "top_source":         top_source.idxmax(),
        "remote_pct":         f"{len(df[df['location']=='Remote'])/len(df)*100:.0f}%",
        "high_demand_jobs":   int(len(df[df["demand_tier"].isin(["Cao", "Rất cao"])])),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE 1 — HOME / SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    df   = _load_df()
    kpis = _compute_kpis(df)

    # Filters — thêm 'skill'
    industry = request.args.get("industry", "").strip()
    skill    = request.args.get("skill",    "").strip()
    location = request.args.get("location", "").strip()
    source   = request.args.get("source",   "").strip()
    keyword  = request.args.get("keyword",  "").strip()

    filt = df.copy()
    if industry:
        filt = filt[filt["industry"] == industry]
    if skill:
        filt = filt[filt["skills"].str.contains(skill, case=False, na=False)]
    if location:
        filt = filt[filt["location"] == location]
    if source:
        filt = filt[filt["source"] == source]
    if keyword:
        mask = (
            filt["title"].str.contains(keyword,   case=False, na=False) |
            filt["company"].str.contains(keyword, case=False, na=False) |
            filt["skills"].str.contains(keyword,  case=False, na=False)
        )
        filt = filt[mask]

    total_filtered = len(filt)
    jobs = (
        filt.sort_values("demand_score", ascending=False)
            .head(24)
            .to_dict("records")
    )

    # Lấy danh sách kỹ năng để hiển thị bộ lọc
    all_skills, top_skills = _get_skill_lists()

    # Enrich job records with badge metadata
    for job in jobs:
        badge = INDUSTRY_BADGE.get(job["industry"], {"color": "gray", "icon": "fa-building"})
        job["badge_color"] = badge["color"]
        job["badge_icon"]  = badge["icon"]
        job["loc_icon"]    = LOCATION_ICON.get(job["location"], "fa-map-marker-alt")
        skills_list = [s.strip() for s in str(job["skills"]).split(",")]
        job["skills_preview"] = skills_list[:4]
        job["skills_extra"]   = max(0, len(skills_list) - 4)

    any_filter = bool(industry or skill or location or source or keyword)

    return render_template(
        "index.html",
        kpis=kpis,
        jobs=jobs,
        total_filtered=total_filtered,
        industries=INDUSTRIES,
        all_skills=all_skills,
        top_skills=top_skills,
        locations=LOCATIONS,
        sources=SOURCES,
        selected_industry=industry,
        selected_skill=skill,
        selected_location=location,
        selected_source=source,
        keyword=keyword,
        any_filter=any_filter,
        active_page="home",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE 2 — AI SMART MATCHING
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/matching", methods=["GET", "POST"])
def matching():
    results   = None
    skill_gap = []
    stats     = {}
    error     = None
    form_data = {"industry": "", "skills": "", "location": "", "salary": 12.0}

    if request.method == "POST":
        industry   = request.form.get("industry", "").strip()
        skills_raw = request.form.get("skills",   "").strip()
        location   = request.form.get("location", "").strip()
        salary     = float(request.form.get("salary", 12.0) or 12.0)

        form_data = {
            "industry": industry,
            "skills":   skills_raw,
            "location": location,
            "salary":   salary,
        }
        student_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

        try:
            out       = recommend_jobs(
                preferred_industry = industry,
                student_skills     = student_skills,
                preferred_location = location,
                expected_salary    = salary,
            )
            results   = out["results"]
            skill_gap = out["skill_gap"]
            stats     = out["stats"]
            # Enrich results
            for r in results:
                badge = INDUSTRY_BADGE.get(r["industry"], {"color": "gray", "icon": "fa-building"})
                r["badge_color"] = badge["color"]
                r["badge_icon"]  = badge["icon"]
                r["loc_icon"]    = LOCATION_ICON.get(r["location"], "fa-map-marker-alt")
                # Color for match %
                mp = r["match_percentage"]
                r["match_color"] = (
                    "green"  if mp >= 80 else
                    "blue"   if mp >= 60 else
                    "yellow" if mp >= 40 else "red"
                )
        except Exception as exc:
            error = str(exc)

    return render_template(
        "matching.html",
        results=results,
        skill_gap=skill_gap,
        stats=stats,
        error=error,
        form_data=form_data,
        industries=INDUSTRIES,
        locations=LOCATIONS,
        common_skills=COMMON_SKILLS,
        active_page="matching",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE 3 — BI ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/analytics")
def analytics():
    df = _load_df()

    all_skills: list[str] = []
    for s in df["skills"].dropna():
        all_skills.extend(x.strip().title() for x in s.split(",") if x.strip())
    skill_counts = Counter(all_skills)
    top_skill, top_skill_n = (
        skill_counts.most_common(1)[0] if skill_counts else ("N/A", 0)
    )

    monthly    = df.groupby("posted_month")["job_id"].count().sort_index()
    best_month = monthly.idxmax()  if not monthly.empty else "N/A"
    best_m_cnt = int(monthly.max()) if not monthly.empty else 0

    ind_salary = df.groupby("industry")["salary_avg"].mean().sort_values(ascending=False)

    insights = {
        "top_industry":     df["industry"].value_counts().idxmax(),
        "top_industry_pct": round(df["industry"].value_counts().max() / len(df) * 100, 1),
        "avg_salary_it":    round(df[df["industry"] == "IT/Phần mềm"]["salary_avg"].mean(), 1),
        "avg_salary_all":   round(df["salary_avg"].mean(), 1),
        "top_skill":        top_skill,
        "top_skill_count":  top_skill_n,
        "best_month":       best_month,
        "best_month_count": best_m_cnt,
        "remote_pct":       round(len(df[df["location"] == "Remote"]) / len(df) * 100, 1),
        "high_demand_jobs": len(df[df["demand_tier"].isin(["Cao", "Rất cao"])]),
        "highest_sal_ind":  ind_salary.idxmax()     if not ind_salary.empty else "N/A",
        "highest_sal_val":  round(ind_salary.max(), 1) if not ind_salary.empty else 0,
    }

    ts = int(datetime.now().timestamp())  # cache-buster
    charts_exist = all(
        (CHARTS_DIR / f).exists()
        for f in ["chart_industry.png", "chart_trend.png", "chart_skills.png"]
    )

    return render_template(
        "analytics.html",
        insights=insights,
        charts_exist=charts_exist,
        ts=ts,
        active_page="analytics",
    )


@app.route("/api/regenerate-charts", methods=["POST"])
def regenerate_charts():
    try:
        generate_bi_charts()
        return jsonify({"ok": True, "message": "Đã tạo lại 3 biểu đồ thành công!"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTE 4 — APACHE SUPERSET INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/superset")
def superset():
    db_uri = f"sqlite:///{DB_PATH}"
    preview_path = CHARTS_DIR / "superset_preview.png"
    preview_exists = preview_path.exists()
    ts = int(datetime.now().timestamp())
    return render_template(
        "superset.html",
        db_uri=db_uri,
        db_path=str(DB_PATH),
        preview_exists=preview_exists,
        ts=ts,
        active_page="superset",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  🚀  Smart Job BI System — Flask Web App")
    print("  🌐  http://localhost:5000")
    print(f"  🗄️   DB: {DB_PATH.name}")
    print("═" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)

