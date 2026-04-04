import { formatChartValue, formatCurrency, formatPercent } from './display';

const THEME_ORDER = ['Demand', 'Audience', 'Affordability', 'Competition', 'Quality', 'Market mix'];

const THEME_BY_KEY = {
  log_footfall: 'Demand',
  weekday_ratio: 'Demand',
  weekend_ratio: 'Demand',
  morning_ratio: 'Demand',
  lunch_ratio: 'Demand',
  afternoon_ratio: 'Demand',
  evening_ratio: 'Demand',
  low_income_ratio: 'Audience',
  mid_income_ratio: 'Audience',
  high_income_ratio: 'Audience',
  children_ratio: 'Audience',
  teens_youth_ratio: 'Audience',
  young_adults_ratio: 'Audience',
  mid_age_adults_ratio: 'Audience',
  older_adults_ratio: 'Audience',
  seniors_ratio: 'Audience',
  mean_price_mid: 'Affordability',
  rent_proxy_psm: 'Affordability',
  competitor_count: 'Competition',
  log_competitor_count: 'Competition',
  unique_category_count: 'Quality',
  mean_rating: 'Quality',
  hawker_stall_count_ratio: 'Market mix',
  fast_food_count_ratio: 'Market mix',
  chinese_count_ratio: 'Market mix',
  indian_count_ratio: 'Market mix',
  cafe_count_ratio: 'Market mix',
  restaurant_count_ratio: 'Market mix',
};

const toNumber = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return null;
  }
  return Number(value);
};

export const formatMetricValue = (value, unit) => {
  const numericValue = toNumber(value);
  if (numericValue === null) return 'Data unavailable';
  if (unit === '%') return formatPercent(numericValue);
  if (unit === 'SGD') return formatCurrency(numericValue);
  if (unit === '/5') return `${numericValue.toFixed(2)}/5`;
  return formatChartValue(numericValue);
};

export const getMetricTheme = (metricKey) => THEME_BY_KEY[metricKey] || 'Other';

export const groupCriteriaByTheme = (criteriaRows = []) => {
  const groups = new Map();

  criteriaRows.forEach((row) => {
    const theme = getMetricTheme(row.key);
    if (!groups.has(theme)) groups.set(theme, []);
    groups.get(theme).push(row);
  });

  return [...groups.entries()]
    .sort((a, b) => {
      const aIndex = THEME_ORDER.indexOf(a[0]);
      const bIndex = THEME_ORDER.indexOf(b[0]);
      return (aIndex === -1 ? THEME_ORDER.length : aIndex) - (bIndex === -1 ? THEME_ORDER.length : bIndex);
    })
    .map(([theme, rows]) => ({ theme, rows }));
};

const getCriterion = (area, key) =>
  (area?.criteria_display || []).find((item) => item.key === key) || null;

export const getAverageForMetric = (areas, metricKey) => {
  const values = areas
    .map((area) => toNumber(getCriterion(area, metricKey)?.value))
    .filter((value) => value !== null);

  if (values.length === 0) return null;

  return values.reduce((sum, value) => sum + value, 0) / values.length;
};

const getFavorability = (value, average, direction) => {
  if (value === null || average === null || average === 0) return null;
  const delta = (value - average) / Math.abs(average);
  return direction === 'minimize' ? -delta : delta;
};

export const summarizeDelta = (value, average, direction, unit) => {
  if (value === null || average === null) return 'No shortlist comparison available.';

  const difference = value - average;
  const relative = average === 0 ? null : Math.abs(difference / average);
  const formattedAverage = formatMetricValue(average, unit);

  if (difference === 0 || relative === null) {
    return `In line with the shortlist average of ${formattedAverage}.`;
  }

  const favorability = getFavorability(value, average, direction);
  const relation = favorability >= 0 ? 'better' : 'weaker';
  const comparator = difference > 0 ? 'above' : 'below';

  return `${Math.round(relative * 100)}% ${comparator} the shortlist average (${formattedAverage}), which is ${relation} for this concept.`;
};

export const getMetricInsightRows = (areaDetails, areas, maximize = [], minimize = []) => {
  const rows = Array.isArray(areaDetails?.criteria_display) ? areaDetails.criteria_display : [];

  return rows.map((row) => {
    const direction = maximize.includes(row.key)
      ? 'maximize'
      : minimize.includes(row.key)
        ? 'minimize'
        : null;
    const value = toNumber(row.value);
    const average = getAverageForMetric(areas, row.key);
    const favorability = getFavorability(value, average, direction);

    return {
      ...row,
      direction,
      average,
      favorability,
      deltaSummary: summarizeDelta(value, average, direction, row.unit),
    };
  });
};

export const getStrengthsAndWatchouts = (areaDetails, areas, maximize = [], minimize = []) => {
  const insightRows = getMetricInsightRows(areaDetails, areas, maximize, minimize)
    .filter((row) => row.direction && row.favorability !== null);

  const strengths = [...insightRows]
    .sort((a, b) => b.favorability - a.favorability)
    .slice(0, 3);

  const watchouts = [...insightRows]
    .sort((a, b) => a.favorability - b.favorability)
    .slice(0, 2);

  return { strengths, watchouts, insightRows };
};

export const getAudienceRows = (incomeMix = {}) => [
  { key: 'low', label: 'Low income', share: toNumber(incomeMix.low), color: '#93c5fd' },
  { key: 'mid', label: 'Mid income', share: toNumber(incomeMix.mid), color: '#3b82f6' },
  { key: 'high', label: 'High income', share: toNumber(incomeMix.high), color: '#1d4ed8' },
].filter((row) => row.share !== null);

export const getTopAudienceLabel = (areaDetails) => {
  const primary = areaDetails?.primary_demographic;
  const share = toNumber(areaDetails?.primary_demographic_share);

  if (!primary || share === null) return 'Broad audience mix';

  return `${primary} (${formatPercent(share)})`;
};

export const getAreaNarrative = (areaDetails) => {
  const demographicLead = getTopAudienceLabel(areaDetails);
  const quadrant = areaDetails?.market_quadrant || 'Mixed opportunity';
  const cluster = areaDetails?.cluster_label || 'Unknown market context';

  return {
    idealFor: `${quadrant} play with strongest pull from ${demographicLead.toLowerCase()}.`,
    marketStory: `${cluster}: ${areaDetails?.cluster_description || 'market context unavailable.'}`,
  };
};
