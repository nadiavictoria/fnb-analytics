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
| population_total | float | Total resident population (sum of all age groups) |
| working_age_pct | float | Percentage of population aged approximately 20–64 (young_adults + mid_age_adults) |
| pct_high_income | float | Percentage of households classified as high-income |
| competitor_per_1k | float | Number of Google Maps F&B competitors per 1,000 residents |
| inflow_ratio | float | Ratio of total_inflow to total_footfall, positive values indicate net inflow (commercial/hub areas), negative indicate net outflow (residential areas)|
| lunch_share | float | Percentage of total daily footfall occurring during the lunch time band|
| evening_share | float | Percentage of total daily footfall occurring during the evening time band|
| weekend_share | float | Percentage of total weekly footfall occurring on weekends and public holidays|
| sfa_active_count | integer | Number of active government-licensed F&B establishments, broader than competitor_count as it includes all licensed outlets including unlisted hawker stalls |
| sfa_per_1k | float | Active SFA-licensed F&B establishments per 1,000 residents |
