# F&B Pareto Map

This folder contains the updated planning-area recommendation map for the F&B location analysis.

The app combines:

- KMeans clustering to group planning areas into broad market archetypes
- Pareto analysis to shortlist planning areas for different F&B concepts
- A small web UI to explore the top 5 shortlisted planning areas for each concept on a map

## Files

- `clustering_and_pareto_processing.ipynb`: notebook where the clustering and Pareto logic was developed
- `build_pareto_map_data_updated.py`: Python script that recreates the analysis outputs needed by the UI
- `pareto_shortlists_updated.json`: generated JSON used by the HTML page
- `pareto_map_updated.html`: map UI
- `master_dataset.csv`: planning-area feature dataset used by the script
- `SubzoneBoundary.geojson`: planning-area geometry used for the map

## Cluster Archetypes

The updated map uses the 3-cluster KMeans interpretation from the notebook.

### Cluster 0: Mainstream Urban / Heartland

This cluster supports stronger everyday demand, denser competition, and a more mass-market, affordable environment.

### Cluster 1: Peripheral / Low-Intensity

This cluster points to sparser commercial ecosystems and weaker overall F&B density.

### Cluster 2: Premium Central / Lifestyle

This cluster supports higher price points, stronger ratings, and greater category diversity.

## Pareto Concepts

Each concept uses a concept-specific set of maximize and minimize metrics. Pareto-efficient areas are then shortlisted, and the top 5 are shown in the UI.

### 1. Affordable Everyday Dining

Description: mainstream, price-sensitive, repeat everyday demand.

Metrics used:

- Maximize `log_footfall`
- Maximize `low_income_ratio`
- Maximize `mid_income_ratio`
- Maximize `hawker_stall_count_ratio`
- Minimize `mean_price_mid`

Primary metric used to sort the shortlist:

- `log_footfall`

### 2. Premium Cafe / Specialty Cafe

Description: upscale, lifestyle-oriented, higher-spending environments.

Metrics used:

- Maximize `mean_price_mid`
- Maximize `high_income_ratio`
- Maximize `unique_category_count`
- Maximize `mean_rating`

Primary metric used to sort the shortlist:

- `mean_price_mid`

### 3. Family-Oriented Casual Dining

Description: residential family demand and evening / weekend dining.

Metrics used:

- Maximize `children_ratio`
- Maximize `mid_age_adults_ratio`
- Maximize `weekend_ratio`
- Maximize `mid_income_ratio`
- Minimize `mean_price_mid`
- Minimize `log_competitor_count`

Primary metric used to sort the shortlist:

- `mid_income_ratio`

### 4. Local Cuisine / Traditional Favorites

Description: areas that look more suitable for local food environments.

Metrics used:

- Maximize `chinese_count_ratio`
- Maximize `indian_count_ratio`
- Maximize `hawker_stall_count_ratio`
- Minimize `cafe_count_ratio`

Primary metric used to sort the shortlist:

- `hawker_stall_count_ratio`

### 5. Fast-Food / Grab-and-Go Concept

Description: high-throughput, convenience-oriented food demand.

Metrics used:

- Maximize `log_footfall`
- Maximize `weekday_ratio`
- Maximize `fast_food_count_ratio`
- Maximize `teens_youth_ratio`
- Minimize `mean_price_mid`

Primary metric used to sort the shortlist:

- `log_footfall`

## Derived Metrics Used In The Pareto Analysis

The script builds transformed metrics from `master_dataset.csv` before running Pareto analysis.

Examples include:

- `log_footfall`: `log1p(total_footfall)`
- `inflow_ratio`: `total_inflow / total_footfall`
- `weekday_ratio`, `weekend_ratio`
- time-band ratios such as `morning_ratio`, `lunch_ratio`, `afternoon_ratio`, `evening_ratio`
- household income ratios such as `low_income_ratio`, `mid_income_ratio`, `high_income_ratio`
- demographic ratios such as `children_ratio`, `teens_youth_ratio`, `young_adults_ratio`, `mid_age_adults_ratio`, `older_adults_ratio`, `seniors_ratio`
- `log_competitor_count`: `log1p(competitor_count)`
- competition mix ratios such as `hawker_stall_count_ratio`, `restaurant_count_ratio`, `cafe_count_ratio`, `fast_food_count_ratio`, `chinese_count_ratio`, `indian_count_ratio`

## What The UI Shows

For each shortlisted planning area, the updated HTML page shows:

- planning area name
- cluster id and cluster label
- cluster explanation
- recommendation summary linking Pareto fit and cluster fit
- total footfall
- income mix across low / mid / high income households
- competitor count
- rent approximation from `rent_proxy_psm`
- primary demographic and its share

## Regenerating The JSON

If you change the analysis logic or the source data, regenerate the JSON with:

```bash
python build_pareto_map_data_updated.py
```

This will refresh:

- `pareto_shortlists_updated.json`

## Running The Local Server

From inside the `fnb-analytics` folder:

```bash
python -m http.server
```

By default, this starts a local server on port `8000`.

## Accessing The HTML

After the server starts, open:

```text
http://localhost:8000/pareto_map_updated.html
```

If you change the JSON or HTML and do not see the update immediately, do a hard refresh in the browser.
