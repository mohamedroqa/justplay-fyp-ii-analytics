"""Audit transaction duplicates and revenue outliers without mutating source data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
MARTS = ROOT / "data" / "marts"
LOGS = ROOT / "logs"
DOCS = ROOT / "docs"

REVENUE_PATH = PROCESSED / "revenue_experiment.parquet"
FEATURES_PATH = PROCESSED / "user_features.parquet"
REPORT_JSON = LOGS / "duplicates_outliers_audit.json"
REPORT_MD = DOCS / "data_cleaning_final_report.md"
SENSITIVITY_PATH = MARTS / "outlier_sensitivity.parquet"

# source_row_id is deliberately excluded: this definition detects repeated
# business events even when the source exported them under different row IDs.
DUPLICATE_KEY = [
    "user_id",
    "created_at",
    "revenue_amount",
    "cashout_amount",
    "earning_amount",
    "cashout_transactions",
    "ad_unit_format_clean",
    "revenue_type",
]


def py(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def duplicate_audit() -> dict:
    parquet = pq.ParquetFile(REVENUE_PATH)
    hashes = []
    row_count = 0
    for batch in parquet.iter_batches(columns=DUPLICATE_KEY, batch_size=300_000):
        frame = batch.to_pandas()
        hashes.append(pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype=np.uint64))
        row_count += len(frame)
        print(f"duplicate hash scan: {row_count:,} rows", flush=True)

    all_hashes = np.concatenate(hashes)
    unique_hashes, counts = np.unique(all_hashes, return_counts=True)
    repeated_hashes = unique_hashes[counts > 1]
    candidate_rows = int(counts[counts > 1].sum())
    del hashes, unique_hashes, counts

    if candidate_rows == 0:
        exact_duplicate_rows = 0
        duplicate_groups = 0
    else:
        candidates = []
        repeated_set = set(repeated_hashes.tolist())
        for batch in parquet.iter_batches(columns=DUPLICATE_KEY, batch_size=300_000):
            frame = batch.to_pandas()
            batch_hash = pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype=np.uint64)
            keep = np.fromiter((int(h) in repeated_set for h in batch_hash), dtype=bool, count=len(batch_hash))
            if keep.any():
                candidates.append(frame.loc[keep])
        candidate_frame = pd.concat(candidates, ignore_index=True)
        group_sizes = candidate_frame.groupby(DUPLICATE_KEY, dropna=False, observed=True).size()
        duplicate_sizes = group_sizes.loc[group_sizes > 1]
        duplicate_groups = int(len(duplicate_sizes))
        exact_duplicate_rows = int((duplicate_sizes - 1).sum())

    source_ids = pq.read_table(REVENUE_PATH, columns=["source_row_id"])["source_row_id"]
    distinct_source_ids = int(pc.count_distinct(source_ids).as_py())
    return {
        "rows": row_count,
        "definition": DUPLICATE_KEY,
        "candidate_rows_from_64bit_hash": candidate_rows,
        "exact_duplicate_groups": duplicate_groups,
        "exact_duplicate_rows_beyond_first": exact_duplicate_rows,
        "distinct_source_row_ids": distinct_source_ids,
        "duplicate_source_row_ids": row_count - distinct_source_ids,
        "action": "No rows removed automatically; exact duplicates require a documented business decision.",
    }


def distribution(values: pd.Series) -> dict:
    quantiles = values.quantile([0, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999, 1.0])
    q1, q3 = float(quantiles.loc[0.25]), float(quantiles.loc[0.75])
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr
    return {
        "minimum": float(quantiles.loc[0]),
        "q25": q1,
        "median": float(quantiles.loc[0.5]),
        "q75": q3,
        "p95": float(quantiles.loc[0.95]),
        "p99": float(quantiles.loc[0.99]),
        "p999": float(quantiles.loc[0.999]),
        "maximum": float(quantiles.loc[1.0]),
        "iqr_upper_fence": threshold,
        "above_iqr_fence_rows": int((values > threshold).sum()),
        "above_p99_rows": int((values > quantiles.loc[0.99]).sum()),
    }


def outlier_audit() -> tuple[dict, pd.DataFrame]:
    features = pd.read_parquet(
        FEATURES_PATH,
        columns=["variation", "total_revenue", "total_cashout", "net_revenue"],
    )
    p99_revenue = float(features["total_revenue"].quantile(0.99))
    p999_revenue = float(features["total_revenue"].quantile(0.999))
    total_gross = float(features["total_revenue"].sum())
    top_1 = features["total_revenue"] > p99_revenue
    top_01 = features["total_revenue"] > p999_revenue

    sensitivity_records = []
    for variation, group in features.groupby("variation", observed=True, sort=True):
        original_gross = group["total_revenue"]
        original_net = group["net_revenue"]
        trimmed = group.loc[group["total_revenue"] <= p99_revenue]
        sensitivity_records.extend([
            {
                "variation": variation,
                "method": "original",
                "users": len(group),
                "gross_revenue_per_user": float(original_gross.mean()),
                "net_revenue_per_user": float(original_net.mean()),
                "threshold": np.nan,
            },
            {
                "variation": variation,
                "method": "winsorized_global_p99",
                "users": len(group),
                "gross_revenue_per_user": float(original_gross.clip(upper=p99_revenue).mean()),
                "net_revenue_per_user": float(
                    (original_net - original_gross + original_gross.clip(upper=p99_revenue)).mean()
                ),
                "threshold": p99_revenue,
            },
            {
                "variation": variation,
                "method": "trimmed_global_p99",
                "users": len(trimmed),
                "gross_revenue_per_user": float(trimmed["total_revenue"].mean()),
                "net_revenue_per_user": float(trimmed["net_revenue"].mean()),
                "threshold": p99_revenue,
            },
        ])

    transaction_table = pq.read_table(
        REVENUE_PATH, columns=["revenue_amount", "cashout_amount", "earning_amount"]
    )
    transaction_frame = transaction_table.to_pandas()
    report = {
        "policy": (
            "Outliers are retained in the primary analysis because no verified business rule marks "
            "them invalid. Winsorized and trimmed results are sensitivity analyses only."
        ),
        "user_level": {
            "total_revenue": distribution(features["total_revenue"]),
            "total_cashout": distribution(features["total_cashout"]),
            "net_revenue": distribution(features["net_revenue"]),
            "global_revenue_p99": p99_revenue,
            "global_revenue_p999": p999_revenue,
            "top_1_percent_user_count": int(top_1.sum()),
            "top_1_percent_gross_share": float(features.loc[top_1, "total_revenue"].sum() / total_gross),
            "top_0_1_percent_user_count": int(top_01.sum()),
            "top_0_1_percent_gross_share": float(features.loc[top_01, "total_revenue"].sum() / total_gross),
        },
        "transaction_level": {
            column: distribution(transaction_frame[column])
            for column in ["revenue_amount", "cashout_amount", "earning_amount"]
        },
    }
    return report, pd.DataFrame(sensitivity_records)


def write_markdown(report: dict) -> None:
    duplicates = report["duplicates"]
    users = report["outliers"]["user_level"]
    transaction = report["outliers"]["transaction_level"]
    status = "لم تُكتشف صفوف مكررة" if duplicates["exact_duplicate_rows_beyond_first"] == 0 else "توجد صفوف مكررة تحتاج قراراً"
    text = f"""# التقرير النهائي لتنظيف البيانات

تاريخ التحقق: **13 أكتوبر 2026**

## نتيجة فحص التكرار

- نطاق الفحص: **{duplicates['rows']:,}** معاملة مؤهلة للتجربة.
- تعريف التكرار: تطابق المستخدم، التاريخ، القيم المالية، عدد Cashout، صيغة الإعلان ونوع الإيراد؛ مع استبعاد رقم صف المصدر من مفتاح المقارنة.
- مجموعات التكرار الدقيقة: **{duplicates['exact_duplicate_groups']:,}**.
- الصفوف الزائدة عن أول سجل: **{duplicates['exact_duplicate_rows_beyond_first']:,}**.
- أرقام صفوف المصدر المكررة: **{duplicates['duplicate_source_row_ids']:,}**.
- النتيجة: **{status}**.

لم يُحذف أي سجل تلقائياً. إذا ظهرت تكرارات، يجب اتخاذ قرار أعمال موثق قبل استبعادها.

## القيم المتطرفة على مستوى المستخدم

| المقياس | P99 | P99.9 | Maximum | أعلى من IQR Fence |
|---|---:|---:|---:|---:|
| Total Revenue | {users['total_revenue']['p99']:.6f} | {users['total_revenue']['p999']:.6f} | {users['total_revenue']['maximum']:.6f} | {users['total_revenue']['above_iqr_fence_rows']:,} |
| Total Cashout | {users['total_cashout']['p99']:.6f} | {users['total_cashout']['p999']:.6f} | {users['total_cashout']['maximum']:.6f} | {users['total_cashout']['above_iqr_fence_rows']:,} |
| Net Revenue | {users['net_revenue']['p99']:.6f} | {users['net_revenue']['p999']:.6f} | {users['net_revenue']['maximum']:.6f} | {users['net_revenue']['above_iqr_fence_rows']:,} |

- المستخدمون فوق P99 للإيراد: **{users['top_1_percent_user_count']:,}**.
- حصتهم من Gross Revenue: **{users['top_1_percent_gross_share']:.2%}**.
- المستخدمون فوق P99.9: **{users['top_0_1_percent_user_count']:,}**.
- حصتهم من Gross Revenue: **{users['top_0_1_percent_gross_share']:.2%}**.

## القيم المتطرفة على مستوى المعاملة

| المقياس | P99 | P99.9 | Maximum |
|---|---:|---:|---:|
| Revenue Amount | {transaction['revenue_amount']['p99']:.6f} | {transaction['revenue_amount']['p999']:.6f} | {transaction['revenue_amount']['maximum']:.6f} |
| Cashout Amount | {transaction['cashout_amount']['p99']:.6f} | {transaction['cashout_amount']['p999']:.6f} | {transaction['cashout_amount']['maximum']:.6f} |
| Earning Amount | {transaction['earning_amount']['p99']:.6f} | {transaction['earning_amount']['p999']:.6f} | {transaction['earning_amount']['maximum']:.6f} |

## القرار المعتمد

القيم المتطرفة **لم تُحذف** من التحليل الأساسي، لأن الفحص لم يقدم قاعدة أعمال تثبت أنها أخطاء. أنشئنا بدلاً من ذلك تحليلاً منفصلاً يقارن النتائج الأصلية مع Winsorization وTrimming عند P99 العالمي:

`data/marts/outlier_sensitivity.parquet`

بهذا نحافظ على النتائج الحقيقية، ونوضح مدى حساسيتها للمستخدمين مرتفعي الإيراد دون تغيير البيانات الخام.
"""
    REPORT_MD.write_text(text, encoding="utf-8")


def main() -> None:
    MARTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    duplicates = duplicate_audit()
    outliers, sensitivity = outlier_audit()
    sensitivity.to_parquet(SENSITIVITY_PATH, index=False, compression="zstd")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "duplicates": duplicates,
        "outliers": outliers,
        "outputs": {
            "sensitivity_mart": str(SENSITIVITY_PATH),
            "markdown_report": str(REPORT_MD),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=py), encoding="utf-8")
    write_markdown(report)
    print(json.dumps({
        "exact_duplicate_groups": duplicates["exact_duplicate_groups"],
        "exact_duplicate_rows_beyond_first": duplicates["exact_duplicate_rows_beyond_first"],
        "duplicate_source_row_ids": duplicates["duplicate_source_row_ids"],
        "top_1_percent_gross_share": outliers["user_level"]["top_1_percent_gross_share"],
        "sensitivity_rows": len(sensitivity),
    }, indent=2))


if __name__ == "__main__":
    main()
