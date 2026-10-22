"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        SMART JOB BI SYSTEM — Smart Engine v1.0                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Module 1 │ recommend_jobs()      — Smart Matching Algorithm               ║
║             Weighted Cosine Scoring: Skills(50%) + Industry(25%)           ║
║             + Location(15%) + Salary(10%)  →  Top-15 + Skill Gap          ║
║                                                                             ║
║  Module 2 │ generate_bi_charts()  — BI Visualization (Matplotlib)         ║
║             chart_industry.png  — Jobs count & avg salary by industry      ║
║             chart_trend.png     — Monthly hiring trend (line chart)        ║
║             chart_skills.png    — Top-10 most-demanded skills              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import warnings
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from sqlalchemy import create_engine, text

# ── Môi trường ────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

matplotlib.use("Agg")          # Non-interactive backend (safe for servers)
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DB_PATH     = BASE_DIR / "data"  / "jobs_bi.db"
CHARTS_DIR  = BASE_DIR / "static" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Matplotlib Global Style ───────────────────────────────────────────────────
FONT_VI       = "Segoe UI"          # Hỗ trợ tiếng Việt có dấu trên Windows
COLOR_PRIMARY = "#2563EB"           # Xanh dương chuyên nghiệp
COLOR_ACCENT  = "#F59E0B"           # Vàng accent
COLOR_BG      = "#F8FAFC"           # Nền sáng nhẹ
COLOR_GRID    = "#E2E8F0"           # Grid nhạt
COLOR_TEXT    = "#1E293B"           # Chữ tối

PALETTE_INDUSTRIES = [
    "#2563EB", "#7C3AED", "#059669", "#DC2626",
    "#D97706", "#0891B2",
]

plt.rcParams.update({
    "font.family":           FONT_VI,
    "font.size":             10,
    "axes.titlesize":        13,
    "axes.titleweight":      "bold",
    "axes.labelsize":        10,
    "axes.spines.top":       False,
    "axes.spines.right":     False,
    "axes.facecolor":        COLOR_BG,
    "figure.facecolor":      "white",
    "grid.color":            COLOR_GRID,
    "grid.linewidth":        0.8,
    "xtick.labelsize":       9,
    "ytick.labelsize":       9,
    "legend.fontsize":       9,
    "legend.framealpha":     0.8,
    "savefig.dpi":           150,
    "savefig.bbox":          "tight",
    "savefig.facecolor":     "white",
})


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _load_dataframe() -> pd.DataFrame:
    """Đọc toàn bộ bảng jobs_data từ SQLite vào Pandas DataFrame."""
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM jobs_data", conn)
    df["posted_date"] = pd.to_datetime(df["posted_date"])
    return df


def _parse_skills(skills_str: str) -> list[str]:
    """Chuyển chuỗi kỹ năng CSV thành danh sách đã chuẩn hóa."""
    if not isinstance(skills_str, str) or not skills_str.strip():
        return []
    return [s.strip().lower() for s in skills_str.split(",") if s.strip()]


def _cosine_similarity_sets(set_a: set, set_b: set) -> float:
    """
    Cosine similarity đơn giản giữa 2 tập hợp từ khoá (binary vectors).
    Công thức: |A ∩ B| / (sqrt(|A|) * sqrt(|B|))
    """
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    denominator  = np.sqrt(len(set_a)) * np.sqrt(len(set_b))
    return float(intersection / denominator) if denominator > 0 else 0.0


def _salary_score(job_sal_avg: float, expected_salary: float) -> float:
    """
    Chấm điểm lương [0, 1].
    - Nếu job_sal_avg >= expected: 1.0 (hoàn toàn phù hợp)
    - Nếu thấp hơn: suy giảm tuyến tính tới ngưỡng -40%
    """
    if expected_salary <= 0:
        return 0.5        # Không có kỳ vọng → điểm trung bình
    ratio = job_sal_avg / expected_salary
    if ratio >= 1.0:
        return 1.0
    elif ratio >= 0.6:
        return float((ratio - 0.6) / 0.4)
    else:
        return 0.0


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — SMART MATCHING ALGORITHM
# ══════════════════════════════════════════════════════════════════════════════

def recommend_jobs(
    preferred_industry: str,
    student_skills:     list[str],
    preferred_location: str,
    expected_salary:    float,
    top_n:              int = 15,
) -> dict:
    """
    Smart Job Matching Engine dựa trên Weighted Scoring + Cosine Similarity.

    Trọng số:
        Kỹ năng  (50%) — Cosine Similarity giữa kỹ năng sinh viên & yêu cầu
        Ngành    (25%) — Exact-match + partial-match boost
        Địa điểm (15%) — Exact-match; Remote luôn cho thêm điểm
        Mức lương(10%) — So sánh salary_avg với expected_salary

    Parameters
    ----------
    preferred_industry : str   — Ngành nghề sinh viên muốn (vd: "IT/Phần mềm")
    student_skills     : list  — Danh sách kỹ năng sinh viên (vd: ["Python","SQL"])
    preferred_location : str   — Địa điểm mong muốn (vd: "Hà Nội" / "Remote")
    expected_salary    : float — Lương kỳ vọng (triệu VNĐ, vd: 12.0)
    top_n              : int   — Số kết quả trả về (mặc định 15)

    Returns
    -------
    dict với các key:
        "results"        : list[dict] — Top-N công việc, mỗi dict kèm match_%
        "skill_gap"      : list[str]  — Kỹ năng còn thiếu (tổng hợp từ Top-N)
        "query_summary"  : dict       — Tóm tắt thông tin đầu vào
        "stats"          : dict       — Thống kê nhanh về kết quả
    """
    print("\n" + "═" * 68)
    print("  MODULE 1 │ SMART MATCHING ALGORITHM")
    print("═" * 68)
    print(f"  Ngành nghề      : {preferred_industry}")
    print(f"  Kỹ năng SV      : {', '.join(student_skills) if student_skills else '(chưa nhập)'}")
    print(f"  Địa điểm        : {preferred_location}")
    print(f"  Lương kỳ vọng   : {expected_salary:,.1f} triệu VNĐ")
    print("─" * 68)

    # ── Tải dữ liệu ──────────────────────────────────────────────────────────
    print("  [1/4] Đọc dữ liệu từ SQLite...")
    df = _load_dataframe()
    print(f"        Tổng bản ghi trong DB: {len(df):,}")

    # ── Chuẩn hóa đầu vào ────────────────────────────────────────────────────
    student_skill_set = set(s.strip().lower() for s in student_skills if s.strip())
    pref_industry_lc  = preferred_industry.strip().lower()
    pref_location_lc  = preferred_location.strip().lower()

    # ── Tính điểm từng bản ghi ───────────────────────────────────────────────
    print("  [2/4] Tính điểm Weighted Cosine Similarity cho 2.500 công việc...")

    scores_skill    = np.zeros(len(df), dtype=float)
    scores_industry = np.zeros(len(df), dtype=float)
    scores_location = np.zeros(len(df), dtype=float)
    scores_salary   = np.zeros(len(df), dtype=float)
    skill_gaps_all  = []   # Thu thập skill gap từ Top-N

    for idx, row in enumerate(df.itertuples(index=False)):
        # --- Điểm KỸ NĂNG (Cosine Similarity, w=0.50) ----------------------
        job_skill_set  = set(_parse_skills(str(row.skills)))
        cos_sim        = _cosine_similarity_sets(student_skill_set, job_skill_set)
        scores_skill[idx] = cos_sim

        # --- Điểm NGÀNH NGHỀ (w=0.25) --------------------------------------
        job_industry_lc = str(row.industry).lower()
        if pref_industry_lc == job_industry_lc:
            ind_score = 1.0
        elif pref_industry_lc in job_industry_lc or job_industry_lc in pref_industry_lc:
            ind_score = 0.6        # Partial match
        else:
            ind_score = 0.05       # Khác ngành hoàn toàn → điểm nền nhỏ
        scores_industry[idx] = ind_score

        # --- Điểm ĐỊA ĐIỂM (w=0.15) ----------------------------------------
        job_location_lc = str(row.location).lower()
        if pref_location_lc == job_location_lc:
            loc_score = 1.0
        elif job_location_lc == "remote":
            loc_score = 0.75       # Remote luôn linh hoạt
        elif pref_location_lc == "remote":
            loc_score = 0.60
        else:
            loc_score = 0.10       # Khác địa điểm
        scores_location[idx] = loc_score

        # --- Điểm LƯƠNG (w=0.10) --------------------------------------------
        scores_salary[idx] = _salary_score(float(row.salary_avg), expected_salary)

    # ── Weighted Total Score (numpy vector ops) ───────────────────────────────
    W_SKILL    = 0.50
    W_INDUSTRY = 0.25
    W_LOCATION = 0.15
    W_SALARY   = 0.10

    total_scores = (
        W_SKILL    * scores_skill    +
        W_INDUSTRY * scores_industry +
        W_LOCATION * scores_location +
        W_SALARY   * scores_salary
    )

    # Chuyển sang phần trăm [0, 100]
    # Chuẩn hóa: max lý thuyết = 1.0 (tất cả đều hoàn hảo)
    match_pct = np.clip(total_scores * 100, 0, 100).round(1)

    # ── Chọn Top-N ───────────────────────────────────────────────────────────
    print(f"  [3/4] Xếp hạng và chọn Top {top_n} công việc phù hợp nhất...")
    top_indices = np.argsort(total_scores)[::-1][:top_n]

    results = []
    skill_gap_counter = Counter()

    for rank, idx in enumerate(top_indices, start=1):
        row = df.iloc[idx]
        job_skills_set = set(_parse_skills(str(row["skills"])))
        missing_skills = sorted(job_skills_set - student_skill_set)

        # Cập nhật skill gap counter
        for sk in missing_skills:
            skill_gap_counter[sk] += 1

        results.append({
            "rank":             rank,
            "job_id":           row["job_id"],
            "title":            row["title"],
            "company":          row["company"],
            "industry":         row["industry"],
            "location":         row["location"],
            "skills_required":  row["skills"],
            "skill_gap":        missing_skills,
            "salary_min":       float(row["salary_min"]),
            "salary_max":       float(row["salary_max"]),
            "salary_avg":       float(row["salary_avg"]),
            "experience_level": row["experience_level"],
            "demand_score":     float(row["demand_score"]),
            "demand_tier":      row["demand_tier"],
            "source":           row["source"],
            "posted_date":      str(row["posted_date"])[:10],
            "match_percentage": float(match_pct[idx]),
            "score_breakdown": {
                "skill_score":    round(float(scores_skill[idx])    * 100, 1),
                "industry_score": round(float(scores_industry[idx]) * 100, 1),
                "location_score": round(float(scores_location[idx]) * 100, 1),
                "salary_score":   round(float(scores_salary[idx])   * 100, 1),
            },
        })

    # ── Tổng hợp Skill Gap ────────────────────────────────────────────────────
    # Lấy kỹ năng xuất hiện nhiều nhất trong Top-N (sinh viên cần học thêm)
    top_skill_gaps = [sk for sk, _ in skill_gap_counter.most_common(10)]

    # ── Thống kê nhanh ────────────────────────────────────────────────────────
    match_percentages = [r["match_percentage"] for r in results]
    stats = {
        "total_jobs_scanned":     len(df),
        "top_n_returned":         len(results),
        "avg_match_pct":          round(float(np.mean(match_percentages)), 1),
        "max_match_pct":          round(float(np.max(match_percentages)), 1),
        "min_match_pct":          round(float(np.min(match_percentages)), 1),
        "avg_salary_top_n":       round(float(np.mean([r["salary_avg"] for r in results])), 1),
        "skill_coverage_pct":     round(
            len(student_skill_set & set(_parse_skills(results[0]["skills_required"])))
            / max(len(set(_parse_skills(results[0]["skills_required"]))), 1) * 100, 1
        ) if results else 0.0,
    }

    print(f"  [4/4] Hoàn tất. Kết quả Top {top_n}:")
    print(f"        Match cao nhất : {stats['max_match_pct']:.1f}%")
    print(f"        Match trung bình: {stats['avg_match_pct']:.1f}%")
    print(f"        Lương TB Top-{top_n} : {stats['avg_salary_top_n']:.1f}M VNĐ")
    print(f"        Kỹ năng cần học: {', '.join(top_skill_gaps[:5]) if top_skill_gaps else 'Không có'}")

    print("\n  ┌─ TOP 5 KẾT QUẢ PHÙ HỢP NHẤT ─────────────────────────────────")
    for r in results[:5]:
        print(f"  │ #{r['rank']:>2} [{r['match_percentage']:>5.1f}%] "
              f"{r['title']:<35} │ {r['salary_avg']:.1f}M │ {r['location']}")
    print("  └" + "─" * 65)
    print()

    return {
        "results":       results,
        "skill_gap":     top_skill_gaps,
        "query_summary": {
            "preferred_industry": preferred_industry,
            "student_skills":     list(student_skills),
            "preferred_location": preferred_location,
            "expected_salary":    expected_salary,
        },
        "stats": stats,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — BI VISUALIZATION
# ══════════════════════════════════════════════════════════════════════════════

def _add_watermark(fig: plt.Figure) -> None:
    """Thêm watermark nhẹ 'Smart Job BI System' vào góc biểu đồ."""
    fig.text(
        0.99, 0.01, "Smart Job BI System",
        ha="right", va="bottom",
        fontsize=7, color="#94A3B8", style="italic",
        transform=fig.transFigure,
    )


def _chart_industry(df: pd.DataFrame, out_path: Path) -> None:
    """
    Biểu đồ cột kép:
    - Cột xanh : Số lượng tin tuyển dụng theo ngành
    - Đường cam: Mức lương trung bình (triệu VNĐ) [trục Y phụ]
    """
    agg = (
        df.groupby("industry", sort=False)
        .agg(job_count=("job_id", "count"), avg_salary=("salary_avg", "mean"))
        .sort_values("job_count", ascending=False)
        .reset_index()
    )

    fig, ax1 = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("white")
    ax1.set_facecolor(COLOR_BG)

    x     = np.arange(len(agg))
    width = 0.55

    # ── Cột số lượng việc làm ─────────────────────────────────────────────
    bars = ax1.bar(
        x, agg["job_count"],
        width=width,
        color=PALETTE_INDUSTRIES[: len(agg)],
        alpha=0.88,
        zorder=3,
        edgecolor="white",
        linewidth=0.6,
    )

    # Label trên đầu cột
    for bar, cnt in zip(bars, agg["job_count"]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5,
            f"{int(cnt):,}",
            ha="center", va="bottom",
            fontsize=9, fontweight="bold",
            color=COLOR_TEXT,
        )

    ax1.set_xlabel("Ngành nghề", fontsize=11, labelpad=8, color=COLOR_TEXT)
    ax1.set_ylabel("Số lượng tin tuyển dụng", fontsize=11, color=COLOR_PRIMARY, labelpad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(agg["industry"], rotation=15, ha="right", fontsize=9)
    ax1.tick_params(axis="y", colors=COLOR_PRIMARY)
    ax1.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax1.grid(axis="y", zorder=0, linestyle="--", alpha=0.6)
    ax1.set_ylim(0, agg["job_count"].max() * 1.18)

    # ── Đường lương trung bình (trục Y phụ) ──────────────────────────────
    ax2 = ax1.twinx()
    ax2.plot(
        x, agg["avg_salary"],
        color=COLOR_ACCENT,
        marker="D",
        markersize=7,
        linewidth=2.5,
        zorder=4,
        markerfacecolor="white",
        markeredgewidth=2,
    )
    for xi, sal in zip(x, agg["avg_salary"]):
        ax2.text(
            xi, sal + 0.25, f"{sal:.1f}M",
            ha="center", va="bottom",
            fontsize=8.5, color=COLOR_ACCENT, fontweight="bold",
        )
    ax2.set_ylabel("Lương trung bình (triệu VNĐ)", fontsize=11,
                   color=COLOR_ACCENT, labelpad=8)
    ax2.tick_params(axis="y", colors=COLOR_ACCENT)
    ax2.spines["right"].set_color(COLOR_ACCENT)
    ax2.spines["top"].set_visible(False)
    ax2.set_ylim(agg["avg_salary"].min() * 0.85, agg["avg_salary"].max() * 1.15)

    # ── Legend & Title ────────────────────────────────────────────────────
    patch_jobs = mpatches.Patch(color=COLOR_PRIMARY, alpha=0.88, label="Số lượng tin tuyển dụng")
    line_sal   = plt.Line2D([0], [0], color=COLOR_ACCENT, marker="D",
                             linewidth=2, label="Lương trung bình")
    ax1.legend(handles=[patch_jobs, line_sal], loc="upper right",
               framealpha=0.9, edgecolor="#CBD5E1")

    fig.suptitle(
        "Thống kê Việc làm & Mức lương Trung bình theo Ngành nghề",
        fontsize=14, fontweight="bold", color=COLOR_TEXT, y=1.01,
    )
    ax1.set_title(
        "Dữ liệu tổng hợp từ TopCV · VietnamWorks · ITViec · LinkedIn",
        fontsize=9, color="#64748B", pad=4,
    )

    _add_watermark(fig)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔  chart_industry.png  → {out_path}")


def _chart_trend(df: pd.DataFrame, out_path: Path) -> None:
    """
    Biểu đồ đường xu hướng tuyển dụng theo tháng.
    - Đường tổng + đường riêng từng ngành (mờ hơn)
    - Kèm fill_between để làm nổi xu hướng chính
    """
    # Đảm bảo posted_date là datetime
    df = df.copy()
    df["posted_date"] = pd.to_datetime(df["posted_date"])
    df["month_label"] = df["posted_date"].dt.to_period("M").astype(str)

    # Tổng hợp theo tháng × ngành
    monthly_total = (
        df.groupby("month_label")["job_id"].count()
        .reset_index(name="count")
        .sort_values("month_label")
    )
    monthly_by_ind = (
        df.groupby(["month_label", "industry"])["job_id"].count()
        .reset_index(name="count")
        .sort_values("month_label")
    )

    months  = monthly_total["month_label"].tolist()
    x_ticks = range(len(months))

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BG)

    # ── Đường từng ngành (background, mờ) ────────────────────────────────
    industries = df["industry"].unique()
    # Pivot: index=month_label, columns=industry, values=count (0 nếu thiếu)
    pivot_ind = (
        monthly_by_ind
        .pivot_table(index="month_label", columns="industry",
                     values="count", aggfunc="sum", fill_value=0)
        .reindex(months, fill_value=0)
    )
    for i, ind in enumerate(pivot_ind.columns):
        ax.plot(
            x_ticks, pivot_ind[ind].values,
            color=PALETTE_INDUSTRIES[i % len(PALETTE_INDUSTRIES)],
            linewidth=1.2, alpha=0.45, linestyle="--",
            label=ind,
        )
    # ── Đường tổng (nổi bật) ─────────────────────────────────────────────
    total_vals = monthly_total["count"].values
    ax.plot(
        x_ticks, total_vals,
        color=COLOR_PRIMARY, linewidth=3, zorder=5,
        marker="o", markersize=6,
        markerfacecolor="white", markeredgewidth=2,
        label="Tổng tất cả ngành",
    )
    ax.fill_between(
        x_ticks, total_vals,
        alpha=0.12, color=COLOR_PRIMARY, zorder=2,
    )

    # Nhãn giá trị tổng
    for xi, val in zip(x_ticks, total_vals):
        ax.annotate(
            str(val),
            xy=(xi, val),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center", fontsize=8,
            fontweight="bold", color=COLOR_PRIMARY,
        )

    # ── Axes ──────────────────────────────────────────────────────────────
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(
        [m.replace("-", "/") for m in months],
        rotation=20, ha="right", fontsize=9,
    )
    ax.set_xlabel("Tháng", fontsize=11, labelpad=8)
    ax.set_ylabel("Số lượng tin tuyển dụng", fontsize=11, labelpad=8)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.set_ylim(0, total_vals.max() * 1.25)

    # Trendline (Linear regression với NumPy)
    z   = np.polyfit(list(x_ticks), total_vals, 1)
    p   = np.poly1d(z)
    ax.plot(
        x_ticks, p(list(x_ticks)),
        color="#EF4444", linewidth=1.5,
        linestyle=":", alpha=0.7,
        label="Xu hướng (Linear Trend)",
        zorder=3,
    )

    # ── Legend & Title ────────────────────────────────────────────────────
    handles, labels = ax.get_legend_handles_labels()
    # Đẩy "Tổng" và "Xu hướng" lên đầu legend
    priority = ["Tổng tất cả ngành", "Xu hướng (Linear Trend)"]
    ordered  = [(h, l) for h, l in zip(handles, labels) if l in priority]
    others   = [(h, l) for h, l in zip(handles, labels) if l not in priority]
    all_h, all_l = zip(*(ordered + others))
    ax.legend(all_h, all_l, loc="upper left", ncol=2,
              framealpha=0.9, edgecolor="#CBD5E1", fontsize=8.5)

    fig.suptitle(
        "Xu hướng Tuyển dụng theo Tháng — 6 Tháng Gần Nhất",
        fontsize=14, fontweight="bold", color=COLOR_TEXT, y=1.01,
    )
    ax.set_title(
        "Đường đứt = từng ngành  │  Đường liền đậm = tổng  │  Đường chấm đỏ = Linear Trend",
        fontsize=8.5, color="#64748B", pad=4,
    )

    _add_watermark(fig)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔  chart_trend.png     → {out_path}")


def _chart_skills(df: pd.DataFrame, out_path: Path) -> None:
    """
    Biểu đồ ngang Top 10 kỹ năng được yêu cầu nhiều nhất.
    - Màu gradient từ đậm → nhạt theo thứ hạng
    - Nhãn tần suất + % hiển thị ngay trên cột
    """
    # Tách & đếm kỹ năng
    all_skills: list[str] = []
    for skills_str in df["skills"].dropna():
        all_skills.extend(_parse_skills(str(skills_str)))

    skill_counts = Counter(all_skills)
    top_skills   = skill_counts.most_common(10)
    labels       = [s.title() for s, _ in top_skills]     # Viết hoa đầu từ
    counts       = np.array([c for _, c in top_skills], dtype=float)
    pcts         = counts / counts.sum() * 100

    # Đảo chiều để skill cao nhất ở trên cùng
    labels  = labels[::-1]
    counts  = counts[::-1]
    pcts    = pcts[::-1]

    # Gradient màu (đậm → nhạt)
    cmap   = plt.cm.Blues
    colors = [cmap(0.4 + 0.6 * i / (len(labels) - 1)) for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor(COLOR_BG)

    bars = ax.barh(
        labels, counts,
        color=colors,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.5,
        height=0.62,
        zorder=3,
    )

    # Nhãn: count + %
    max_val = counts.max()
    for bar, cnt, pct in zip(bars, counts, pcts):
        w = bar.get_width()
        # Số lượng bên trong (trắng nếu đủ rộng)
        if w > max_val * 0.25:
            ax.text(
                w - max_val * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{int(cnt):,}",
                ha="right", va="center",
                fontsize=9.5, fontweight="bold",
                color="white",
            )
        # Phần trăm bên ngoài
        ax.text(
            w + max_val * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.1f}%",
            ha="left", va="center",
            fontsize=8.5, color=COLOR_TEXT,
        )

    # Đường tham chiếu trung bình
    avg_count = counts.mean()
    ax.axvline(
        avg_count, color="#EF4444", linewidth=1.5,
        linestyle="--", alpha=0.75, zorder=4,
        label=f"Trung bình ({avg_count:.0f} lượt)",
    )

    ax.set_xlabel("Số lượt xuất hiện trong tin tuyển dụng", fontsize=11, labelpad=8)
    ax.set_xlim(0, max_val * 1.18)
    ax.grid(axis="x", linestyle="--", alpha=0.5, zorder=0)
    ax.legend(loc="lower right", framealpha=0.9, edgecolor="#CBD5E1")

    # Huy hiệu hạng
    for i, (bar, rank) in enumerate(zip(bars, range(len(labels), 0, -1))):
        if rank <= 3:
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            ax.text(
                -max_val * 0.04,
                bar.get_y() + bar.get_height() / 2,
                medals[rank],
                ha="center", va="center", fontsize=11,
            )

    fig.suptitle(
        "Top 10 Kỹ năng Được Nhà Tuyển Dụng Săn Đón Nhất",
        fontsize=14, fontweight="bold", color=COLOR_TEXT, y=1.01,
    )
    ax.set_title(
        "Dành cho sinh viên mới tốt nghiệp  ·  Tổng hợp 2.500 tin tuyển dụng",
        fontsize=9, color="#64748B", pad=4,
    )

    _add_watermark(fig)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔  chart_skills.png    → {out_path}")


def generate_bi_charts() -> dict[str, Path]:
    """
    Tạo và lưu 3 biểu đồ BI chất lượng cao vào static/charts/.

    Returns
    -------
    dict: {"industry": Path, "trend": Path, "skills": Path}
    """
    print("\n" + "═" * 68)
    print("  MODULE 2 │ BI VISUALIZATION — Matplotlib")
    print("═" * 68)
    print(f"  Thư mục output : {CHARTS_DIR}")
    print("  DPI            : 150  │  Font: Segoe UI (hỗ trợ tiếng Việt)")
    print("─" * 68)

    # Tải dữ liệu
    print("  [*] Đọc dữ liệu từ SQLite...")
    df = _load_dataframe()
    print(f"       {len(df):,} bản ghi sẵn sàng.\n")

    out_industry = CHARTS_DIR / "chart_industry.png"
    out_trend    = CHARTS_DIR / "chart_trend.png"
    out_skills   = CHARTS_DIR / "chart_skills.png"

    _chart_industry(df, out_industry)
    _chart_trend(df,    out_trend)
    _chart_skills(df,   out_skills)

    print(f"\n  ✅  Đã tạo xong 3 biểu đồ BI trong: {CHARTS_DIR}")
    print("═" * 68 + "\n")

    return {
        "industry": out_industry,
        "trend":    out_trend,
        "skills":   out_skills,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  DEMO / ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "╔" + "═" * 66 + "╗")
    print("║   SMART JOB BI SYSTEM — Smart Engine Demo                     ║")
    print("╚" + "═" * 66 + "╝")

    # ── Demo Module 1: Smart Matching ─────────────────────────────────────────
    result = recommend_jobs(
        preferred_industry = "Phân tích dữ liệu/BI",
        student_skills     = ["Python", "SQL", "Pandas", "Excel", "Power BI"],
        preferred_location = "Hà Nội",
        expected_salary    = 12.0,
        top_n              = 15,
    )

    print("\n  ── SKILL GAP (Kỹ năng cần học thêm) ──")
    if result["skill_gap"]:
        for i, sk in enumerate(result["skill_gap"], 1):
            print(f"   {i:>2}. {sk.title()}")
    else:
        print("   Bạn đã đáp ứng đủ kỹ năng cho Top-15 việc làm này!")

    print("\n  ── THỐNG KÊ ──")
    for k, v in result["stats"].items():
        print(f"   {k:<30} : {v}")

    # ── Demo Module 2: BI Charts ──────────────────────────────────────────────
    chart_paths = generate_bi_charts()
    print("  Các file biểu đồ đã tạo:")
    for name, path in chart_paths.items():
        size_kb = path.stat().st_size / 1024
        print(f"   [{name:<10}] {path.name}  ({size_kb:.1f} KB)")
