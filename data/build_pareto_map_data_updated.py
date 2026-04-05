from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


DATA_ROOT = Path(__file__).resolve().parent
MASTER_DATASET = DATA_ROOT / "master_dataset.csv"
OUTPUT_JSON = DATA_ROOT / "pareto_shortlists_updated.json"
OUTPUT_CSV = DATA_ROOT / "pareto_shortlists_updated.csv"
CLUSTER_CACHE = DATA_ROOT / ".cluster_cache.joblib"

# Columns actually consumed by the pipeline, avoids loading unused fields
MASTER_DATASET_COLS = [
    "PLANNING_AREA",
    "total_footfall",
    "weekday_volume", "weekend_volume",
    "morning", "lunch", "evening", "afternoon", "other",
    "low_income", "mid_income", "high_income",
    "children", "teens_youth", "young_adults", "mid_age_adults", "older_adults", "seniors",
    "competitor_count", "unique_category_count",
    "mean_rating", "mean_price_mid",
    "hawker_stall_count", "restaurant_count",
    "chinese_count", "japanese_count", "indian_count", "cafe_count", "thai_count", "fast_food_count",
    "rent_proxy_psm",
    "inflow_ratio",
    "market_quadrant",
]

SPECIAL_CASE_AREAS = {
    "CENTRAL WATER CATCHMENT",
    "LIM CHU KANG",
    "MARINA SOUTH",
    "SOUTHERN ISLANDS",
    "STRAITS VIEW",
}

CLUSTER_METADATA = {
    0: {
        "label": "Mainstream Urban / Heartland",
        "description": (
            "supports stronger everyday demand, denser competition, and a more "
            "mass-market, affordable environment."
        ),
    },
    1: {
        "label": "Peripheral / Low-Intensity",
        "description": (
            "points to sparser commercial ecosystems and weaker overall F&B density."
        ),
    },
    2: {
        "label": "Premium Central / Lifestyle",
        "description": (
            "supports higher price points, stronger ratings, and greater category diversity."
        ),
    },
}

METRIC_DISPLAY_MAP = {
    "log_footfall": {"label": "Total footfall", "source": "total_footfall"},
    "low_income_ratio": {"label": "Lower-income households", "source": "income_mix.low"},
    "mid_income_ratio": {"label": "Middle-income households", "source": "income_mix.mid"},
    "high_income_ratio": {"label": "Higher-income households", "source": "income_mix.high"},
    "hawker_stall_count_ratio": {"label": "Hawker presence", "source": None},
    "mean_price_mid": {"label": "Typical price level", "source": None},
    "unique_category_count": {"label": "Category diversity", "source": None},
    "mean_rating": {"label": "Average rating", "source": None},
    "children_ratio": {"label": "Families with children", "source": None},
    "mid_age_adults_ratio": {"label": "Mid-age adults", "source": None},
    "weekend_ratio": {"label": "Weekend activity share", "source": None},
    "weekday_ratio": {"label": "Weekday activity share", "source": None},
    "log_competitor_count": {"label": "Nearby competitors", "source": "competitor_count"},
    "chinese_count_ratio": {"label": "Chinese cuisine presence", "source": None},
    "indian_count_ratio": {"label": "Indian cuisine presence", "source": None},
    "cafe_count_ratio": {"label": "Cafe presence", "source": None},
    "fast_food_count_ratio": {"label": "Fast-food presence", "source": None},
    "teens_youth_ratio": {"label": "Teens and youth presence", "source": None},
}


def build_analysis_df(df: pd.DataFrame) -> pd.DataFrame:
    analysis_df = df.copy()

    analysis_df["log_footfall"] = np.log1p(analysis_df["total_footfall"])

    total_day_volume = analysis_df["weekday_volume"] + analysis_df["weekend_volume"]
    analysis_df["weekday_ratio"] = analysis_df["weekday_volume"] / total_day_volume
    analysis_df["weekend_ratio"] = analysis_df["weekend_volume"] / total_day_volume

    time_cols = ["morning", "lunch", "evening", "afternoon", "other"]
    analysis_df[[f"{col}_ratio" for col in time_cols]] = analysis_df[time_cols].div(
        analysis_df[time_cols].sum(axis=1),
        axis=0,
    )

    income_cols = ["low_income", "mid_income", "high_income"]
    analysis_df["income_total"] = analysis_df[income_cols].sum(axis=1, min_count=1)
    for col in income_cols:
        analysis_df[f"{col}_ratio"] = analysis_df[col] / analysis_df["income_total"]

    demo_cols = [
        "children",
        "teens_youth",
        "young_adults",
        "mid_age_adults",
        "older_adults",
        "seniors",
    ]
    analysis_df["demo_total"] = analysis_df[demo_cols].sum(axis=1, min_count=1)
    for col in demo_cols:
        analysis_df[f"{col}_ratio"] = analysis_df[col] / analysis_df["demo_total"]

    analysis_df["log_competitor_count"] = np.log1p(analysis_df["competitor_count"])

    competition_count_cols = [
        "hawker_stall_count",
        "restaurant_count",
        "chinese_count",
        "japanese_count",
        "indian_count",
        "cafe_count",
        "thai_count",
        "fast_food_count",
    ]
    for col in competition_count_cols:
        analysis_df[f"{col}_ratio"] = analysis_df[col] / analysis_df["competitor_count"]

    return analysis_df


def build_area_context_lookup(df: pd.DataFrame, analysis_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    income_ratio_cols = ["low_income_ratio", "mid_income_ratio", "high_income_ratio"]
    demographic_cols = [
        "children",
        "teens_youth",
        "young_adults",
        "mid_age_adults",
        "older_adults",
        "seniors",
    ]
    demographic_labels = {
        "children": "Children",
        "teens_youth": "Teens / Youth",
        "young_adults": "Young Adults",
        "mid_age_adults": "Mid-Age Adults",
        "older_adults": "Older Adults",
        "seniors": "Seniors",
    }

    demo_ratio_cols = [f"{col}_ratio" for col in demographic_cols]
    overall_demo_totals = analysis_df[demographic_cols].sum(axis=0, min_count=1)
    overall_demo_total = overall_demo_totals.sum(min_count=1)
    overall_demo_mix = {
        col: np.nan if pd.isna(overall_demo_total) or overall_demo_total == 0 else overall_demo_totals[col] / overall_demo_total
        for col in demographic_cols
    }

    context_df = df[["PLANNING_AREA", "total_footfall", "competitor_count", "rent_proxy_psm", "market_quadrant"]].copy()
    context_df = context_df.merge(
        analysis_df[["PLANNING_AREA", *income_ratio_cols]],
        on="PLANNING_AREA",
        how="left",
    )

    demo_df = analysis_df[["PLANNING_AREA", *demographic_cols, *demo_ratio_cols]].copy()
    demo_values = demo_df[demographic_cols]
    demo_ratio_values = demo_df[demo_ratio_cols]
    demo_total = demo_values.sum(axis=1, min_count=1)
    has_demo = demo_values.notna().any(axis=1)

    primary_demo_col = pd.Series(pd.NA, index=demo_df.index, dtype="object")
    primary_demo_value = pd.Series(np.nan, index=demo_df.index, dtype="float64")

    if has_demo.any():
        primary_demo_col.loc[has_demo] = demo_values.loc[has_demo].idxmax(axis=1)
        primary_demo_value.loc[has_demo] = demo_values.loc[has_demo].max(axis=1)

    primary_demo_share = primary_demo_value / demo_total

    demo_df["primary_demographic"] = primary_demo_col.map(demographic_labels)
    demo_df["primary_demographic_share"] = primary_demo_share

    demographic_breakdown_list: list[list[dict[str, object]] | None] = []
    top_demographics_list: list[list[dict[str, object]] | None] = []
    demographic_emphasis_list: list[dict[str, object] | None] = []

    for _, row in demo_df.iterrows():
        ratio_map = {col: row[f"{col}_ratio"] for col in demographic_cols}
        valid_items = [
            (col, ratio)
            for col, ratio in ratio_map.items()
            if not pd.isna(ratio)
        ]

        if not valid_items:
            demographic_breakdown_list.append(None)
            top_demographics_list.append(None)
            demographic_emphasis_list.append(None)
            continue

        ranked_items = sorted(valid_items, key=lambda item: item[1], reverse=True)
        demographic_breakdown_list.append(
            [
                {
                    "key": col,
                    "label": demographic_labels[col],
                    "share": round(float(share), 3),
                    "share_formatted": f"{float(share) * 100:.1f}%",
                }
                for col, share in ranked_items
            ]
        )
        top_demographics_list.append(
            [
                {
                    "key": col,
                    "label": demographic_labels[col],
                    "share": round(float(share), 3),
                    "share_formatted": f"{float(share) * 100:.1f}%",
                }
                for col, share in ranked_items[:2]
            ]
        )

        best_col = None
        best_delta = None
        for col, share in valid_items:
            baseline = overall_demo_mix[col]
            if pd.isna(baseline):
                continue
            delta_pp = (float(share) - float(baseline)) * 100
            if best_delta is None or delta_pp > best_delta:
                best_col = col
                best_delta = delta_pp

        if best_col is None or best_delta is None:
            demographic_emphasis_list.append(None)
        else:
            share = ratio_map[best_col]
            demographic_emphasis_list.append(
                {
                    "key": best_col,
                    "label": demographic_labels[best_col],
                    "share": round(float(share), 3),
                    "share_formatted": f"{float(share) * 100:.1f}%",
                    "vs_overall_pp": round(float(best_delta), 1),
                    "vs_overall_formatted": f"{float(best_delta):+.1f} pp",
                }
            )

    demo_df["demographic_breakdown"] = demographic_breakdown_list
    demo_df["top_demographics"] = top_demographics_list
    demo_df["demographic_emphasis"] = demographic_emphasis_list

    context_df = context_df.merge(
        demo_df[
            [
                "PLANNING_AREA",
                "primary_demographic",
                "primary_demographic_share",
                "demographic_breakdown",
                "top_demographics",
                "demographic_emphasis",
            ]
        ],
        on="PLANNING_AREA",
        how="left",
    )

    lookup: dict[str, dict[str, object]] = {}
    for record in context_df.to_dict(orient="records"):
        lookup[record["PLANNING_AREA"]] = {
            "total_footfall": None if pd.isna(record["total_footfall"]) else int(record["total_footfall"]),
            "income_mix": {
                "low": None if pd.isna(record["low_income_ratio"]) else round(float(record["low_income_ratio"]), 3),
                "mid": None if pd.isna(record["mid_income_ratio"]) else round(float(record["mid_income_ratio"]), 3),
                "high": None if pd.isna(record["high_income_ratio"]) else round(float(record["high_income_ratio"]), 3),
            },
            "competitor_count": None if pd.isna(record["competitor_count"]) else int(record["competitor_count"]),
            "rent_proxy_psm": None if pd.isna(record["rent_proxy_psm"]) else round(float(record["rent_proxy_psm"]), 2),
            "market_quadrant": None if pd.isna(record["market_quadrant"]) else record["market_quadrant"],
            "primary_demographic": record["primary_demographic"],
            "primary_demographic_share": None
            if pd.isna(record["primary_demographic_share"])
            else round(float(record["primary_demographic_share"]), 3),
            "demographic_breakdown": record["demographic_breakdown"],
            "top_demographics": record["top_demographics"],
            "demographic_emphasis": record["demographic_emphasis"],
        }
    return lookup


def get_metric_display_meta(metric_key: str) -> dict[str, object]:
    default_label = metric_key.replace("_", " ").title()
    return METRIC_DISPLAY_MAP.get(metric_key, {"label": default_label, "source": None})


def resolve_nested_value(data: dict[str, object], path: str):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def resolve_metric_display_value(metric_key: str, area_record: dict[str, object], area_context: dict[str, object]):
    source = get_metric_display_meta(metric_key)["source"]
    if source:
        return resolve_nested_value(area_context, source)
    return area_record.get(metric_key)


def metric_display_unit(metric_key: str) -> str | None:
    if metric_key == "log_footfall":
        return "visits"
    if metric_key == "log_competitor_count":
        return "competitors"
    if metric_key.endswith("_ratio"):
        return "%"
    if metric_key.endswith("_count") or metric_key == "unique_category_count":
        return "count"
    if "rating" in metric_key:
        return "/5"
    if "price" in metric_key:
        return "SGD"
    return None


def format_metric_value(metric_key: str, value) -> str | None:
    if value is None or pd.isna(value):
        return "Data unavailable"
    numeric_value = float(value)
    if metric_key.endswith("_ratio"):
        return f"{numeric_value * 100:.1f}%"
    if metric_key == "log_footfall":
        return f"{int(round(numeric_value)):,}"
    if metric_key == "log_competitor_count":
        return f"{int(round(numeric_value))}"
    if metric_key.endswith("_count") or metric_key == "unique_category_count":
        return f"{int(round(numeric_value))}"
    if "rating" in metric_key:
        return f"{numeric_value:.2f}/5"
    if "price" in metric_key:
        return f"{numeric_value:.2f}"
    return f"{numeric_value:.3f}"


def build_metric_display(metric_key: str, area_record: dict[str, object], area_context: dict[str, object]) -> dict[str, object]:
    meta = get_metric_display_meta(metric_key)
    value = resolve_metric_display_value(metric_key, area_record, area_context)
    if value is not None and not pd.isna(value):
        value = int(value) if isinstance(value, (int, np.integer)) else float(value)
    else:
        value = None
    return {
        "key": metric_key,
        "label": meta["label"],
        "value": value,
        "formatted_value": format_metric_value(metric_key, value),
        "unit": metric_display_unit(metric_key),
    }


def pareto_efficient_mask(values: np.ndarray) -> np.ndarray:
    v = values[:, np.newaxis, :]       # (n, 1, d)
    u = values[np.newaxis, :, :]       # (1, n, d)
    dominated = np.all(u >= v, axis=2) & np.any(u > v, axis=2)
    np.fill_diagonal(dominated, False)
    return ~dominated.any(axis=1)


def build_clustering_df(analysis_df: pd.DataFrame) -> pd.DataFrame:
    analysis_cols = [
        "PLANNING_AREA",
        "log_footfall",
        "inflow_ratio",
        "weekday_ratio",
        "morning_ratio",
        "lunch_ratio",
        "afternoon_ratio",
        "evening_ratio",
        "mid_income_ratio",
        "high_income_ratio",
        "children_ratio",
        "young_adults_ratio",
        "mid_age_adults_ratio",
        "seniors_ratio",
        "log_competitor_count",
        "unique_category_count",
        "mean_rating",
        "mean_price_mid",
        "hawker_stall_count_ratio",
        "restaurant_count_ratio",
        "cafe_count_ratio",
        "fast_food_count_ratio",
    ]
    return analysis_df[analysis_cols].copy()


def _dataset_hash() -> str:
    """Return a SHA-256 hex digest of master_dataset.csv for cache invalidation."""
    h = hashlib.sha256()
    h.update(MASTER_DATASET.read_bytes())
    return h.hexdigest()


def _fit_clustering_models(x_train: pd.DataFrame) -> tuple[SimpleImputer, StandardScaler, KMeans]:
    imputer = SimpleImputer(strategy="median")
    x_train_imputed = pd.DataFrame(imputer.fit_transform(x_train), columns=x_train.columns, index=x_train.index)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_imputed)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=20)
    kmeans.fit(x_train_scaled)

    return imputer, scaler, kmeans


def build_cluster_lookup(analysis_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    clustering_df = build_clustering_df(analysis_df)

    train_df = clustering_df[~clustering_df["PLANNING_AREA"].isin(SPECIAL_CASE_AREAS)].copy()
    pred_df = clustering_df.copy()

    train_names = train_df["PLANNING_AREA"].copy()
    x_train = train_df.drop(columns=["PLANNING_AREA"]).copy()
    x_all = pred_df.drop(columns=["PLANNING_AREA"]).copy()

    current_hash = _dataset_hash()

    if CLUSTER_CACHE.exists():
        cached = joblib.load(CLUSTER_CACHE)
        if cached.get("dataset_hash") == current_hash:
            imputer = cached["imputer"]
            scaler = cached["scaler"]
            kmeans = cached["kmeans"]
        else:
            imputer, scaler, kmeans = _fit_clustering_models(x_train)
            joblib.dump(
                {"dataset_hash": current_hash, "imputer": imputer, "scaler": scaler, "kmeans": kmeans},
                CLUSTER_CACHE,
            )
    else:
        imputer, scaler, kmeans = _fit_clustering_models(x_train)
        joblib.dump(
            {"dataset_hash": current_hash, "imputer": imputer, "scaler": scaler, "kmeans": kmeans},
            CLUSTER_CACHE,
        )

    x_train_imputed = pd.DataFrame(imputer.transform(x_train), columns=x_train.columns, index=x_train.index)
    x_all_imputed = pd.DataFrame(imputer.transform(x_all), columns=x_all.columns, index=x_all.index)

    x_train_scaled = scaler.transform(x_train_imputed)
    x_all_scaled = scaler.transform(x_all_imputed)

    train_labels = kmeans.predict(x_train_scaled)
    all_labels = kmeans.predict(x_all_scaled)

    train_lookup = dict(zip(train_names, train_labels))
    cluster_lookup: dict[str, dict[str, object]] = {}

    for area_name, cluster_id in zip(pred_df["PLANNING_AREA"], all_labels):
        cluster_meta = CLUSTER_METADATA[int(cluster_id)]
        cluster_lookup[area_name] = {
            "kmeans_cluster": int(cluster_id),
            "cluster_label": cluster_meta["label"],
            "cluster_description": cluster_meta["description"],
            "cluster_assignment_method": "fit" if area_name in train_lookup else "predicted",
        }

    return cluster_lookup


def run_pareto(df: pd.DataFrame, concept_config: dict[str, object]) -> pd.DataFrame:
    maximize_cols = concept_config["maximize"]
    minimize_cols = concept_config["minimize"]

    needed_cols = ["PLANNING_AREA", *maximize_cols, *minimize_cols]
    concept_df = df[needed_cols].copy()
    concept_df = concept_df.dropna(subset=maximize_cols + minimize_cols).reset_index(drop=True)

    for col in minimize_cols:
        concept_df[f"neg_{col}"] = -concept_df[col]

    pareto_cols = maximize_cols + [f"neg_{col}" for col in minimize_cols]
    mask = pareto_efficient_mask(concept_df[pareto_cols].to_numpy())
    concept_df["pareto_efficient"] = mask
    return concept_df[concept_df["pareto_efficient"]].copy()


def format_snapshot(row: pd.Series, columns: list[str]) -> str:
    return "; ".join(f"{col}={row[col]:.3f}" for col in columns)


def sanitize_for_json(value):
    if isinstance(value, dict):
        return {key: sanitize_for_json(val) for key, val in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(item) for item in value]
    if pd.isna(value):
        return None
    return value


def build_recommendation_summary(concept_description: str, cluster_label: str, cluster_description: str) -> str:
    concept_text = concept_description.rstrip(".")
    concept_text = concept_text[0].lower() + concept_text[1:]
    article = "an" if concept_text[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
    return (
        f"This area is shortlisted for {article} {concept_text} and belongs to the "
        f"{cluster_label} cluster, which {cluster_description}"
    )


def build_area_payload(
    area_record: dict[str, object],
    rank: int,
    concept_cfg: dict[str, object],
    cluster_info: dict[str, object],
    area_context: dict[str, object],
) -> dict[str, object]:
    criteria_used = list(area_record["criteria_used"])
    return {
        "rank": rank,
        "planning_area": area_record["PLANNING_AREA"],
        "primary_metric": area_record["primary_metric"],
        "primary_value": float(area_record["primary_value"]),
        "primary_metric_display": build_metric_display(area_record["primary_metric"], area_record, area_context),
        "criteria_used": criteria_used,
        "criteria_display": [
            build_metric_display(metric_key, area_record, area_context)
            for metric_key in criteria_used
        ],
        "criteria_snapshot": area_record["criteria_snapshot"],
        **cluster_info,
        **area_context,
        "recommendation_summary": build_recommendation_summary(
            concept_cfg["description"],
            cluster_info["cluster_label"],
            cluster_info["cluster_description"],
        ),
    }


def main() -> None:
    with open(Path(__file__).resolve().parent / "archetypes.json") as f:
        concepts = json.load(f)

    concept_sort_cols = {key: cfg["sort_col"] for key, cfg in concepts.items()}

    df = pd.read_csv(MASTER_DATASET, usecols=MASTER_DATASET_COLS)
    analysis_df = build_analysis_df(df)
    cluster_lookup = build_cluster_lookup(analysis_df)
    area_context_lookup = build_area_context_lookup(df, analysis_df)

    concepts_payload: dict[str, dict[str, object]] = {}
    csv_rows: list[dict[str, object]] = []

    for concept_key, concept_cfg in concepts.items():
        shortlist = run_pareto(analysis_df, concept_cfg)
        sort_col = concept_sort_cols[concept_key]
        relevant_cols = concept_cfg["maximize"] + concept_cfg["minimize"]

        top5 = shortlist.sort_values(sort_col, ascending=False).head(5).copy()
        top5["primary_metric"] = sort_col
        top5["primary_value"] = top5[sort_col].round(3)
        top5["criteria_used"] = [list(relevant_cols) for _ in range(len(top5))]
        top5["criteria_snapshot"] = top5[relevant_cols].apply(
            lambda row: format_snapshot(row, relevant_cols),
            axis=1,
        )

        concepts_payload[concept_key] = {
            "description": concept_cfg["description"],
            "primary_metric": sort_col,
            "criteria_used": relevant_cols,
            "maximize": concept_cfg["maximize"],
            "minimize": concept_cfg["minimize"],
            "areas": [
                build_area_payload(
                    record,
                    idx + 1,
                    concept_cfg,
                    cluster_lookup[record["PLANNING_AREA"]],
                    area_context_lookup[record["PLANNING_AREA"]],
                )
                for idx, record in enumerate(top5.to_dict(orient="records"))
            ],
        }

        for idx, record in enumerate(top5.to_dict(orient="records")):
            area_name = record["PLANNING_AREA"]
            cluster_info = cluster_lookup[area_name]
            area_context = area_context_lookup[area_name]

            csv_rows.append(
                {
                    "concept_key": concept_key,
                    "concept_description": concept_cfg["description"],
                    "rank": idx + 1,
                    "planning_area": area_name,
                    "primary_metric": record["primary_metric"],
                    "primary_value": float(record["primary_value"]),
                    "criteria_used": ", ".join(record["criteria_used"]),
                    "criteria_snapshot": record["criteria_snapshot"],
                    "kmeans_cluster": cluster_info["kmeans_cluster"],
                    "cluster_label": cluster_info["cluster_label"],
                    "cluster_description": cluster_info["cluster_description"],
                    "cluster_assignment_method": cluster_info["cluster_assignment_method"],
                    "recommendation_summary": build_recommendation_summary(
                        concept_cfg["description"],
                        cluster_info["cluster_label"],
                        cluster_info["cluster_description"],
                    ),
                    "total_footfall": area_context["total_footfall"],
                    "competitor_count": area_context["competitor_count"],
                    "rent_proxy_psm": area_context["rent_proxy_psm"],
                    "market_quadrant": area_context["market_quadrant"],
                    "low_income_ratio": area_context["income_mix"]["low"],
                    "mid_income_ratio": area_context["income_mix"]["mid"],
                    "high_income_ratio": area_context["income_mix"]["high"],
                    "primary_demographic": area_context["primary_demographic"],
                    "primary_demographic_share": area_context["primary_demographic_share"],
                    "demographic_emphasis": None
                    if not area_context["demographic_emphasis"]
                    else area_context["demographic_emphasis"]["label"],
                    "demographic_emphasis_share": None
                    if not area_context["demographic_emphasis"]
                    else area_context["demographic_emphasis"]["share"],
                    "demographic_emphasis_vs_overall_pp": None
                    if not area_context["demographic_emphasis"]
                    else area_context["demographic_emphasis"]["vs_overall_pp"],
                }
            )

    payload = {
        "generated_from": str(MASTER_DATASET.name),
        "concepts": concepts_payload,
    }
    payload_json = json.dumps(sanitize_for_json(payload), indent=2, allow_nan=False)
    OUTPUT_JSON.write_text(payload_json)
    pd.DataFrame(csv_rows).to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
