"""Separate raw revenue into experiment-matched and external scopes.

This check is intentionally separate from the generic source audit. It proves
which transaction totals are eligible for the A/B analysis without modifying
either raw CSV.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
USERS_PATH = ROOT / "data" / "raw" / "users_data_final_case_study.csv"
REVENUE_PATH = ROOT / "data" / "raw" / "revenue_data_final_case_study.csv"
JSON_PATH = ROOT / "logs" / "experiment_scope_audit.json"
SUMMARY_PATH = ROOT / "docs" / "experiment_scope_summary.md"
CHUNK_SIZE = 250_000
NUMERIC_COLUMNS = [
    "revenue_amount",
    "cashout_amount",
    "earning_amount",
    "cashout_transactions",
]


def as_plain(counter: Counter) -> dict[str, float]:
    return {key: float(counter[key]) for key in NUMERIC_COLUMNS}


def main() -> None:
    users = pd.read_csv(USERS_PATH, usecols=["user_id"], dtype={"user_id": "string"})
    known_ids = set(users["user_id"].dropna())

    matched_ids: set[str] = set()
    external_ids: set[str] = set()
    matched_rows = 0
    external_rows = 0
    null_user_rows = 0
    matched_sums: Counter = Counter()
    external_sums: Counter = Counter()

    usecols = ["user_id", *NUMERIC_COLUMNS]
    for chunk in pd.read_csv(
        REVENUE_PATH,
        usecols=usecols,
        dtype={"user_id": "string"},
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        matched_mask = chunk["user_id"].isin(known_ids)
        external_mask = chunk["user_id"].notna() & ~matched_mask
        null_mask = chunk["user_id"].isna()

        matched_rows += int(matched_mask.sum())
        external_rows += int(external_mask.sum())
        null_user_rows += int(null_mask.sum())
        matched_ids.update(chunk.loc[matched_mask, "user_id"].dropna().unique())
        external_ids.update(chunk.loc[external_mask, "user_id"].dropna().unique())

        for column in NUMERIC_COLUMNS:
            values = pd.to_numeric(chunk[column], errors="coerce").fillna(0)
            matched_sums[column] += float(values.loc[matched_mask].sum())
            external_sums[column] += float(values.loc[external_mask].sum())

    matched = as_plain(matched_sums)
    external = as_plain(external_sums)
    matched["net_revenue"] = matched["revenue_amount"] - matched["cashout_amount"]
    external["net_revenue"] = external["revenue_amount"] - external["cashout_amount"]

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_users": len(known_ids),
        "experiment_users_with_transactions": len(matched_ids),
        "experiment_users_without_transactions": len(known_ids) - len(matched_ids),
        "external_users_with_transactions": len(external_ids),
        "matched_transaction_rows": matched_rows,
        "external_transaction_rows": external_rows,
        "null_user_id_rows": null_user_rows,
        "experiment_totals": matched,
        "external_totals": external,
        "analysis_rule": "Only matched transactions enter A/B KPIs; external transactions remain audit-only.",
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def money(value: float) -> str:
        return f"{value:,.6f}"

    summary = f"""# تدقيق نطاق معاملات تجربة A/B

تاريخ التشغيل: `{report['generated_at_utc']}`

## قاعدة التحليل

تدخل في نتائج المشروع معاملات المستخدمين الموجودين في ملف `users` فقط. تحفظ المعاملات الخارجية لأغراض التدقيق ولا تدخل في KPIs أو المقارنات الإحصائية.

## التغطية

| البند | القيمة |
|---|---:|
| جميع مستخدمي التجربة | {report['experiment_users']:,} |
| مستخدمو التجربة الذين لديهم معاملات | {report['experiment_users_with_transactions']:,} |
| مستخدمو التجربة دون معاملات | {report['experiment_users_without_transactions']:,} |
| مستخدمون خارجيون لديهم معاملات | {report['external_users_with_transactions']:,} |
| صفوف معاملات التجربة | {report['matched_transaction_rows']:,} |
| صفوف معاملات خارجية | {report['external_transaction_rows']:,} |
| صفوف دون user_id | {report['null_user_id_rows']:,} |

## المجاميع المؤهلة لتجربة A/B

| المؤشر | القيمة |
|---|---:|
| Gross Revenue | {money(matched['revenue_amount'])} |
| Cashout | {money(matched['cashout_amount'])} |
| Net Revenue | {money(matched['net_revenue'])} |
| Earning Amount | {money(matched['earning_amount'])} |
| Cashout Transactions | {matched['cashout_transactions']:,.0f} |

## المجاميع الخارجية المستبعدة من التحليل

| المؤشر | القيمة |
|---|---:|
| Gross Revenue | {money(external['revenue_amount'])} |
| Cashout | {money(external['cashout_amount'])} |
| Net Revenue | {money(external['net_revenue'])} |
| Earning Amount | {money(external['earning_amount'])} |
| Cashout Transactions | {external['cashout_transactions']:,.0f} |
"""
    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    print(f"Scope audit JSON: {JSON_PATH}")
    print(f"Scope audit summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
