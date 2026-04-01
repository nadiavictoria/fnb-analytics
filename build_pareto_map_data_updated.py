from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
MASTER_DATASET = ROOT / "master_dataset.csv"
OUTPUT_JSON = ROOT / "pareto_shortlists_updated.json"
OUTPUT_CSV = ROOT / "pareto_shortlists_updated.csv"

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

    context_df = df[["PLANNING_AREA", "total_footfall", "competitor_count", "rent_proxy_psm"]].copy()
    context_df = context_df.merge(
        analysis_df[["PLANNING_AREA", *income_ratio_cols]],
        on="PLANNING_AREA",
        how="left",
    )

    demo_df = analysis_df[["PLANNING_AREA", *demographic_cols]].copy()
    demo_values = demo_df[demographic_cols]
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

    context_df = context_df.merge(
        demo_df[["PLANNING_AREA", "primary_demographic", "primary_demographic_share"]],
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
            "primary_demographic": record["primary_demographic"],
            "primary_demographic_share": None
            if pd.isna(record["primary_demographic_share"])
            else round(float(record["primary_demographic_share"]), 3),
        }
    return lookup


def pareto_efficient_mask(values: np.ndarray) -> np.ndarray:
    n = values.shape[0]
    is_efficient = np.ones(n, dtype=bool)

    for i in range(n):
        if not is_efficient[i]:
            continue

        dominates_i = np.all(values >= values[i], axis=1) & np.any(values > values[i], axis=1)
        dominates_i[i] = False
        if np.any(dominates_i):
            is_efficient[i] = False

    return is_efficient


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


def build_cluster_lookup(analysis_df: pd.DataFrame) -> dict[str, dict[str, object]]:
    clustering_df = build_clustering_df(analysis_df)

    train_df = clustering_df[~clustering_df["PLANNING_AREA"].isin(SPECIAL_CASE_AREAS)].copy()
    pred_df = clustering_df.copy()

    train_names = train_df["PLANNING_AREA"].copy()
    x_train = train_df.drop(columns=["PLANNING_AREA"]).copy()
    x_all = pred_df.drop(columns=["PLANNING_AREA"]).copy()

    imputer = SimpleImputer(strategy="median")
    x_train_imputed = pd.DataFrame(imputer.fit_transform(x_train), columns=x_train.columns, index=x_train.index)
    x_all_imputed = pd.DataFrame(imputer.transform(x_all), columns=x_all.columns, index=x_all.index)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_imputed)
    x_all_scaled = scaler.transform(x_all_imputed)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=20)
    train_labels = kmeans.fit_predict(x_train_scaled)
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


def main() -> None:
    concepts = {
        "affordable_everyday_meal": {
            "description": "Affordable everyday dining",
            "maximize": [
                "log_footfall",
                "low_income_ratio",
                "mid_income_ratio",
                "hawker_stall_count_ratio",
            ],
            "minimize": ["mean_price_mid"],
        },
        "premium_cafe": {
            "description": "Premium cafe / specialty cafe",
            "maximize": [
                "mean_price_mid",
                "high_income_ratio",
                "unique_category_count",
                "mean_rating",
            ],
            "minimize": [],
        },
        "family_casual_dining": {
            "description": "Family-oriented casual dining",
            "maximize": [
                "children_ratio",
                "mid_age_adults_ratio",
                "weekend_ratio",
                "mid_income_ratio",
            ],
            "minimize": ["mean_price_mid", "log_competitor_count"],
        },
        "local_cuisine": {
            "description": "Local cuisine / traditional favorites",
            "maximize": [
                "chinese_count_ratio",
                "indian_count_ratio",
                "hawker_stall_count_ratio",
            ],
            "minimize": ["cafe_count_ratio"],
        },
        "fast_food_grab_go": {
            "description": "Fast-food / grab-and-go concept",
            "maximize": [
                "log_footfall",
                "weekday_ratio",
                "fast_food_count_ratio",
                "teens_youth_ratio",
            ],
            "minimize": ["mean_price_mid"],
        },
    }

    concept_sort_cols = {
        "affordable_everyday_meal": "log_footfall",
        "premium_cafe": "mean_price_mid",
        "family_casual_dining": "mid_income_ratio",
        "local_cuisine": "hawker_stall_count_ratio",
        "fast_food_grab_go": "log_footfall",
    }

    df = pd.read_csv(MASTER_DATASET)
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
        top5["criteria_used"] = ", ".join(relevant_cols)
        top5["criteria_snapshot"] = top5[relevant_cols].apply(
            lambda row: format_snapshot(row, relevant_cols),
            axis=1,
        )

        concepts_payload[concept_key] = {
            "description": concept_cfg["description"],
            "primary_metric": sort_col,
            "criteria_used": relevant_cols,
            "areas": [
                {
                    "rank": idx + 1,
                    "planning_area": record["PLANNING_AREA"],
                    "primary_metric": record["primary_metric"],
                    "primary_value": float(record["primary_value"]),
                    "criteria_used": record["criteria_used"],
                    "criteria_snapshot": record["criteria_snapshot"],
                    **cluster_lookup[record["PLANNING_AREA"]],
                    **area_context_lookup[record["PLANNING_AREA"]],
                    "recommendation_summary": build_recommendation_summary(
                        concept_cfg["description"],
                        cluster_lookup[record["PLANNING_AREA"]]["cluster_label"],
                        cluster_lookup[record["PLANNING_AREA"]]["cluster_description"],
                    ),
                }
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
                    "criteria_used": record["criteria_used"],
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
                    "low_income_ratio": area_context["income_mix"]["low"],
                    "mid_income_ratio": area_context["income_mix"]["mid"],
                    "high_income_ratio": area_context["income_mix"]["high"],
                    "primary_demographic": area_context["primary_demographic"],
                    "primary_demographic_share": area_context["primary_demographic_share"],
                }
            )

    payload = {
        "generated_from": str(MASTER_DATASET.name),
        "concepts": concepts_payload,
    }
    OUTPUT_JSON.write_text(json.dumps(sanitize_for_json(payload), indent=2, allow_nan=False))
    pd.DataFrame(csv_rows).to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
