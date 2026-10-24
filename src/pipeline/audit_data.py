"""Full, read-only audit of the FYP II raw CSV files.

The script reads both files in chunks, never edits raw data, and writes a
machine-readable JSON report plus a concise Markdown summary.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
LOG_DIR = ROOT / "logs"
DOCS_DIR = ROOT / "docs"
USERS_PATH = RAW_DIR / "users_data_final_case_study.csv"
REVENUE_PATH = RAW_DIR / "revenue_data_final_case_study.csv"
CHUNK_SIZE = 250_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def update_date_range(current_min, current_max, series: pd.Series):
    values = pd.to_datetime(series, errors="coerce")
    chunk_min = values.min()
    chunk_max = values.max()
    if pd.notna(chunk_min):
        current_min = chunk_min if current_min is None else min(current_min, chunk_min)
    if pd.notna(chunk_max):
        current_max = chunk_max if current_max is None else max(current_max, chunk_max)
    return current_min, current_max, int(values.isna().sum())


def counter_to_dict(counter: Counter, limit: int | None = None) -> dict[str, int]:
    items = counter.most_common(limit)
    return {str(key): int(value) for key, value in items}


def audit_users(path: Path) -> tuple[dict[str, Any], set[str]]:
    rows = 0
    columns: list[str] | None = None
    null_counts: Counter = Counter()
    sentinel_missing: Counter = Counter()
    categories = {name: Counter() for name in ["variation", "country_code", "platform", "channel", "os_version"]}
    numeric_sums = Counter()
    numeric_invalid = Counter()
    date_ranges = {"assignment_dt": [None, None, 0], "install_dt": [None, None, 0]}
    user_ids: set[str] = set()
    duplicate_user_ids = 0

    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, low_memory=False):
        if columns is None:
            columns = list(chunk.columns)
        rows += len(chunk)
        null_counts.update({column: int(value) for column, value in chunk.isna().sum().items()})

        for column in chunk.select_dtypes(include=["object", "string"]).columns:
            sentinel_missing[column] += int(chunk[column].astype("string").str.strip().str.lower().eq("missing").sum())

        for column, counter in categories.items():
            if column in chunk.columns:
                counter.update(chunk[column].fillna("<NULL>").astype(str).tolist())

        for column in ["assigned", "activated"]:
            numeric = pd.to_numeric(chunk[column], errors="coerce")
            numeric_sums[column] += float(numeric.fillna(0).sum())
            numeric_invalid[column] += int(numeric.isna().sum())

        for column in date_ranges:
            minimum, maximum, invalid = update_date_range(
                date_ranges[column][0], date_ranges[column][1], chunk[column]
            )
            date_ranges[column] = [minimum, maximum, date_ranges[column][2] + invalid]

        for value in chunk["user_id"].dropna().astype(str):
            if value in user_ids:
                duplicate_user_ids += 1
            else:
                user_ids.add(value)

    report = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "rows": rows,
        "columns": columns or [],
        "column_count": len(columns or []),
        "unique_user_ids": len(user_ids),
        "duplicate_user_ids": duplicate_user_ids,
        "null_counts": counter_to_dict(null_counts),
        "sentinel_missing_counts": counter_to_dict(sentinel_missing),
        "numeric_sums": {key: value for key, value in numeric_sums.items()},
        "numeric_invalid_counts": counter_to_dict(numeric_invalid),
        "date_ranges": {
            column: {
                "min": values[0].date().isoformat() if values[0] is not None else None,
                "max": values[1].date().isoformat() if values[1] is not None else None,
                "invalid_or_null": int(values[2]),
            }
            for column, values in date_ranges.items()
        },
        "categories": {
            column: counter_to_dict(counter, 50) for column, counter in categories.items()
        },
    }
    return report, user_ids


def audit_revenue(path: Path, known_user_ids: set[str]) -> dict[str, Any]:
    rows = 0
    columns: list[str] | None = None
    null_counts: Counter = Counter()
    sentinel_missing: Counter = Counter()
    revenue_types: Counter = Counter()
    ad_formats: Counter = Counter()
    numeric_sums = Counter()
    numeric_invalid = Counter()
    numeric_negative = Counter()
    date_min = None
    date_max = None
    date_invalid = 0
    revenue_user_ids: set[str] = set()
    orphan_user_ids: set[str] = set()

    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, low_memory=False):
        if columns is None:
            columns = list(chunk.columns)
        rows += len(chunk)
        null_counts.update({column: int(value) for column, value in chunk.isna().sum().items()})

        for column in chunk.select_dtypes(include=["object", "string"]).columns:
            sentinel_missing[column] += int(chunk[column].astype("string").str.strip().str.lower().eq("missing").sum())

        revenue_types.update(chunk["revenue_type"].fillna("<NULL>").astype(str).tolist())
        ad_formats.update(chunk["ad_unit_format"].fillna("<NULL>").astype(str).tolist())

        for column in ["revenue_amount", "cashout_amount", "earning_amount", "cashout_transactions"]:
            numeric = pd.to_numeric(chunk[column], errors="coerce")
            numeric_sums[column] += float(numeric.fillna(0).sum())
            numeric_invalid[column] += int(numeric.isna().sum())
            numeric_negative[column] += int((numeric < 0).sum())

        date_min, date_max, invalid = update_date_range(date_min, date_max, chunk["created_at"])
        date_invalid += invalid

        ids = set(chunk["user_id"].dropna().astype(str).unique())
        revenue_user_ids.update(ids)
        orphan_user_ids.update(ids.difference(known_user_ids))

    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "rows": rows,
        "columns": columns or [],
        "column_count": len(columns or []),
        "unique_user_ids": len(revenue_user_ids),
        "orphan_user_ids": len(orphan_user_ids),
        "null_counts": counter_to_dict(null_counts),
        "sentinel_missing_counts": counter_to_dict(sentinel_missing),
        "numeric_sums": {key: value for key, value in numeric_sums.items()},
        "numeric_invalid_counts": counter_to_dict(numeric_invalid),
        "numeric_negative_counts": counter_to_dict(numeric_negative),
        "created_at_range": {
            "min": date_min.date().isoformat() if date_min is not None else None,
            "max": date_max.date().isoformat() if date_max is not None else None,
            "invalid_or_null": date_invalid,
        },
        "revenue_type_counts": counter_to_dict(revenue_types),
        "ad_unit_format_counts": counter_to_dict(ad_formats),
        "duplicate_row_check": "Deferred to DuckDB full-row grouping in the transformation phase.",
    }


def markdown_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| البند | القيمة |", "|---|---:|"]
    lines.extend(f"| {label} | {value} |" for label, value in rows)
    return "\n".join(lines)


def write_summary(report: dict[str, Any], path: Path) -> None:
    users = report["users"]
    revenue = report["revenue"]
    revenue_sums = revenue["numeric_sums"]
    net_revenue = revenue_sums["revenue_amount"] - revenue_sums["cashout_amount"]

    lines = [
        "# تقرير التدقيق الأولي للبيانات الكاملة",
        "",
        f"تاريخ التشغيل: `{report['generated_at_utc']}`",
        "",
        "## ملخص المصدر",
        "",
        markdown_table([
            ("صفوف المستخدمين", f"{users['rows']:,}"),
            ("المستخدمون الفريدون", f"{users['unique_user_ids']:,}"),
            ("تكرار user_id", f"{users['duplicate_user_ids']:,}"),
            ("صفوف معاملات الإيرادات", f"{revenue['rows']:,}"),
            ("مستخدمون لديهم معاملات", f"{revenue['unique_user_ids']:,}"),
            ("معرفات معاملات غير موجودة في users", f"{revenue['orphan_user_ids']:,}"),
        ]),
        "",
        "## النطاق الزمني",
        "",
        markdown_table([
            ("assignment_dt", f"{users['date_ranges']['assignment_dt']['min']} → {users['date_ranges']['assignment_dt']['max']}"),
            ("install_dt", f"{users['date_ranges']['install_dt']['min']} → {users['date_ranges']['install_dt']['max']}"),
            ("created_at", f"{revenue['created_at_range']['min']} → {revenue['created_at_range']['max']}"),
        ]),
        "",
        "## المجاميع المالية الخام",
        "",
        markdown_table([
            ("Gross Revenue", f"{revenue_sums['revenue_amount']:,.6f}"),
            ("Cashout", f"{revenue_sums['cashout_amount']:,.6f}"),
            ("Net Revenue", f"{net_revenue:,.6f}"),
            ("Earning Amount", f"{revenue_sums['earning_amount']:,.6f}"),
            ("Cashout Transactions", f"{revenue_sums['cashout_transactions']:,.0f}"),
        ]),
        "",
        "## توزيع Variations",
        "",
        markdown_table(list(users["categories"]["variation"].items())),
        "",
        "## توزيع الدول",
        "",
        markdown_table(list(users["categories"]["country_code"].items())),
        "",
        "## أكبر قنوات الاستحواذ",
        "",
        markdown_table(list(users["categories"]["channel"].items())[:15]),
        "",
        "## أنواع معاملات الإيرادات",
        "",
        markdown_table(list(revenue["revenue_type_counts"].items())),
        "",
        "## ملاحظات المرحلة التالية",
        "",
        "- تثبيت تعريف القيم النصية `missing` قبل التحويل.",
        "- تنفيذ فحص التكرار الكامل للمعاملات داخل DuckDB.",
        "- بناء أهلية D1/D3/D7/D14/D30 بناءً على تاريخ نهاية الرصد.",
        "- عدم نشر أي ملف يحتوي على `user_id`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    for path in [USERS_PATH, REVENUE_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Missing raw input: {path}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    users_report, user_ids = audit_users(USERS_PATH)
    revenue_report = audit_revenue(REVENUE_PATH, user_ids)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "chunk_size": CHUNK_SIZE,
        "users": users_report,
        "revenue": revenue_report,
    }

    json_path = LOG_DIR / "data_audit.json"
    summary_path = DOCS_DIR / "data_audit_summary.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(report, summary_path)
    print(f"Audit JSON: {json_path}")
    print(f"Audit summary: {summary_path}")


if __name__ == "__main__":
    main()
