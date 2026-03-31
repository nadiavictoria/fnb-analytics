# Master Dataset Column Explanation

| Column name | data type | explanation |
| -------- | ------- | ----- |
| PLANNING_AREA | string | Name of the planning area (e.g., Ang Mo Kio, Bedok) |
| total_footfall | integer | Total number of people observed in the area |
| total_inflow | integer | Net movement of people entering minus leaving the area |
| weekday_volume | integer | Total foot traffic during weekdays |
| weekend_volume | integer | Total foot traffic during weekends |
| morning | integer | Foot traffic during morning hours |
| lunch | integer | Foot traffic during lunch hours |
| afternoon | integer | Foot traffic during afternoon hours |
| evening | integer | Foot traffic during evening hours |
| other | integer | Foot traffic outside standard time categories |
| low_income | float | Estimated number of low-income individuals in the area |
| mid_income | float | Estimated number of middle-income individuals |
| high_income | float | Estimated number of high-income individuals |
| children | integer | Number of children in the population |
| teens_youth | integer | Number of teenagers and youth |
| young_adults | integer | Number of young adults |
| mid_age_adults | integer | Number of middle-aged adults |
| older_adults | integer | Number of older adults |
| seniors | integer | Number of senior citizens |
| rent_proxy_psm | float | Estimated rent per square meter (proxy value) |
| competitor_count | integer | Total number of food competitors in the area |
| unique_competitor_names | integer | Number of unique competitor businesses |
| unique_category_count | integer | Number of different food categories available |
| mean_rating | float | Average rating of food establishments |
| median_rating | float | Median rating of food establishments |
| total_reviews | float | Total number of reviews across establishments |
| median_reviews | float | Median number of reviews per place |
| mean_price_mid | float | Average mid-range price level |
| rated_place_count | integer | Number of places with ratings available |
| priced_place_count | integer | Number of places with pricing data available |
| hawker_stall_count | integer | Number of hawker stalls |
| restaurant_count | integer | Number of restaurants |
| chinese_count | integer | Number of Chinese cuisine places |
| japanese_count | integer | Number of Japanese cuisine places |
| indian_count | integer | Number of Indian cuisine places |
| cafe_count | integer | Number of cafes |
| thai_count | integer | Number of Thai cuisine places |
| fast_food_count | integer | Number of fast food outlets |
| rating_coverage_ratio | float | Proportion of places with ratings data |
| price_coverage_ratio | float | Proportion of places with pricing data |
| income_missing | integer (0/1) | Indicator if income data is missing (1 = missing) |
| demo_missing | integer (0/1) | Indicator if demographic data is missing |
| rent_missing | integer (0/1) | Indicator if rent data is missing |
