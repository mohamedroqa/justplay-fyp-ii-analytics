"""Run reproducible A/B tests for every treatment versus the default group."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


ROOT = Path(__file__).resolve().parents[2]
FEATURES_PATH = ROOT / "data" / "processed" / "user_features.parquet"
MARTS = ROOT / "data" / "marts"
LOGS = ROOT / "logs"
CONTROL = "default"
ALPHA = 0.05

CONTINUOUS_METRICS = {
    "gross_revenue_per_user": "total_revenue",
    "net_revenue_per_user": "net_revenue",
}

BINARY_METRICS = {
    "activation_rate": ("activated", None),
    "monetization_rate": ("is_monetized", None),
    "d1_exact_activity_rate": ("exact_activity_d1", "eligible_d1"),
    "d7_exact_activity_rate": ("exact_activity_d7", "eligible_d7"),
    "d30_exact_activity_rate": ("exact_activity_d30", "eligible_d30"),
    "d1_rolling_activity_rate": ("rolling_activity_d1_plus", "eligible_d1"),
    "d7_rolling_activity_rate": ("rolling_activity_d7_plus", "eligible_d7"),
    "d30_rolling_activity_rate": ("rolling_activity_d30_plus", "eligible_d30"),
}


def mean_difference_ci(treatment: np.ndarray, control: np.ndarray) -> tuple[float, float, float]:
    difference = float(treatment.mean() - control.mean())
    se2_t = treatment.var(ddof=1) / len(treatment)
    se2_c = control.var(ddof=1) / len(control)
    se = float(np.sqrt(se2_t + se2_c))
    if se == 0:
        return difference, difference, difference
    df = (se2_t + se2_c) ** 2 / (
        (se2_t**2 / (len(treatment) - 1)) + (se2_c**2 / (len(control) - 1))
    )
    margin = float(stats.t.ppf(1 - ALPHA / 2, df) * se)
    return difference, difference - margin, difference + margin


def cohens_d(treatment: np.ndarray, control: np.ndarray) -> float:
    numerator = float(treatment.mean() - control.mean())
    pooled_variance = (
        ((len(treatment) - 1) * treatment.var(ddof=1))
        + ((len(control) - 1) * control.var(ddof=1))
    ) / (len(treatment) + len(control) - 2)
    return numerator / np.sqrt(pooled_variance) if pooled_variance > 0 else 0.0


def proportion_test(treatment: np.ndarray, control: np.ndarray) -> dict:
    n_t, n_c = len(treatment), len(control)
    x_t, x_c = int(treatment.sum()), int(control.sum())
    p_t, p_c = x_t / n_t, x_c / n_c
    difference = p_t - p_c
    pooled = (x_t + x_c) / (n_t + n_c)
    pooled_se = np.sqrt(pooled * (1 - pooled) * (1 / n_t + 1 / n_c))
    z = difference / pooled_se if pooled_se else 0.0
    p_value = float(2 * stats.norm.sf(abs(z)))
    unpooled_se = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    margin = float(stats.norm.ppf(1 - ALPHA / 2) * unpooled_se)
    return {
        "control_n": n_c,
        "treatment_n": n_t,
        "control_value": p_c,
        "treatment_value": p_t,
        "absolute_difference": difference,
        "relative_lift": difference / p_c if p_c else np.nan,
        "ci_95_low": difference - margin,
        "ci_95_high": difference + margin,
        "test_statistic": z,
        "p_value": p_value,
        "effect_size": difference,
        "effect_size_name": "risk_difference",
    }


def build() -> dict:
    MARTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(FEATURES_PATH)
    variations = sorted(v for v in frame["variation"].dropna().unique() if v != CONTROL)
    if CONTROL not in set(frame["variation"]):
        raise ValueError(f"Control variation {CONTROL!r} was not found")

    descriptive_records = []
    for variation, group in frame.groupby("variation", observed=True):
        for metric, column in CONTINUOUS_METRICS.items():
            values = group[column].to_numpy(dtype=np.float64)
            descriptive_records.append({
                "variation": variation,
                "metric": metric,
                "n": len(values),
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)),
                "median": float(np.median(values)),
                "q25": float(np.quantile(values, 0.25)),
                "q75": float(np.quantile(values, 0.75)),
                "minimum": float(np.min(values)),
                "maximum": float(np.max(values)),
            })

    records = []
    control_frame = frame.loc[frame["variation"].eq(CONTROL)]
    for treatment_name in variations:
        treatment_frame = frame.loc[frame["variation"].eq(treatment_name)]
        for metric, column in CONTINUOUS_METRICS.items():
            treatment = treatment_frame[column].to_numpy(dtype=np.float64)
            control = control_frame[column].to_numpy(dtype=np.float64)
            difference, ci_low, ci_high = mean_difference_ci(treatment, control)
            control_mean = float(control.mean())
            treatment_mean = float(treatment.mean())
            welch = stats.ttest_ind(treatment, control, equal_var=False)
            common = {
                "metric": metric,
                "metric_type": "continuous",
                "control_variation": CONTROL,
                "treatment_variation": treatment_name,
                "control_n": len(control),
                "treatment_n": len(treatment),
                "control_value": control_mean,
                "treatment_value": treatment_mean,
                "absolute_difference": difference,
                "relative_lift": difference / control_mean if control_mean else np.nan,
                "ci_95_low": ci_low,
                "ci_95_high": ci_high,
            }
            records.append({
                **common,
                "test_name": "welch_t_test",
                "test_statistic": float(welch.statistic),
                "p_value": float(welch.pvalue),
                "effect_size": float(cohens_d(treatment, control)),
                "effect_size_name": "cohens_d",
            })
            mann = stats.mannwhitneyu(treatment, control, alternative="two-sided", method="asymptotic")
            rank_biserial = 2 * float(mann.statistic) / (len(treatment) * len(control)) - 1
            records.append({
                **common,
                "test_name": "mann_whitney_u",
                "test_statistic": float(mann.statistic),
                "p_value": float(mann.pvalue),
                "effect_size": rank_biserial,
                "effect_size_name": "rank_biserial_correlation",
            })

        for metric, (value_column, eligible_column) in BINARY_METRICS.items():
            control_subset = control_frame
            treatment_subset = treatment_frame
            if eligible_column:
                control_subset = control_subset.loc[control_subset[eligible_column].astype(bool)]
                treatment_subset = treatment_subset.loc[treatment_subset[eligible_column].astype(bool)]
            result = proportion_test(
                treatment_subset[value_column].astype(bool).to_numpy(),
                control_subset[value_column].astype(bool).to_numpy(),
            )
            records.append({
                "metric": metric,
                "metric_type": "binary",
                "control_variation": CONTROL,
                "treatment_variation": treatment_name,
                "test_name": "two_proportion_z_test",
                **result,
            })

    results = pd.DataFrame(records)
    results["p_value_holm"] = np.nan
    for _, indices in results.groupby(["metric", "test_name"], sort=False).groups.items():
        idx = list(indices)
        results.loc[idx, "p_value_holm"] = multipletests(
            results.loc[idx, "p_value"].to_numpy(), alpha=ALPHA, method="holm"
        )[1]
    results["significant_after_holm"] = results["p_value_holm"] < ALPHA
    results["alpha"] = ALPHA

    descriptive = pd.DataFrame(descriptive_records)
    results_path = MARTS / "statistical_tests.parquet"
    descriptive_path = MARTS / "variation_descriptive.parquet"
    results.to_parquet(results_path, index=False, compression="zstd")
    descriptive.to_parquet(descriptive_path, index=False, compression="zstd")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "control": CONTROL,
        "treatments": variations,
        "alpha": ALPHA,
        "correction": "Holm within each metric and test family",
        "tests": len(results),
        "significant_after_holm": int(results["significant_after_holm"].sum()),
        "outputs": {
            "statistical_tests": str(results_path),
            "variation_descriptive": str(descriptive_path),
        },
    }
    (LOGS / "statistical_analysis_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return report


if __name__ == "__main__":
    build()
