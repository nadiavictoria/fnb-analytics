import React from 'react';
import './Dashboard.css';
import { formatChartValue, formatCurrency, formatPercent } from './display';
import { getAreaNarrative } from './insights';

const quadrantDescriptions = {
  Opportunity: 'Low retail rent and low F&B supply density.',
  Competitive: 'Low retail rent and high F&B supply density.',
  Niche: 'High retail rent and low F&B supply density.',
  Saturated: 'High retail rent and high F&B supply density.',
};

const formatDelta = (currentValue, averageValue, formatter) => {
  if (
    currentValue === null ||
    currentValue === undefined ||
    averageValue === null ||
    averageValue === undefined
  ) {
    return 'No shortlist benchmark';
  }

  const delta = currentValue - averageValue;
  if (delta === 0) return `At shortlist average (${formatter(averageValue)})`;

  const relative = averageValue === 0 ? 0 : Math.abs(delta / averageValue);
  const direction = delta > 0 ? 'above' : 'below';
  return `${Math.round(relative * 100)}% ${direction} shortlist avg`;
};

const DecisionHero = ({ areaDetails, selectedConcept, areas }) => {
  if (!areaDetails) return null;

  const getFieldAverage = (field) => {
    const values = areas
      .map((area) => area?.[field])
      .filter((value) => value !== null && value !== undefined && !Number.isNaN(Number(value)))
      .map(Number);

    if (values.length === 0) return null;

    return values.reduce((sum, value) => sum + value, 0) / values.length;
  };

  const footfallAvg = getFieldAverage('total_footfall');
  const rentAvg = getFieldAverage('rent_proxy_psm');
  const competitionAvg = getFieldAverage('competitor_count');
  const narrative = getAreaNarrative(areaDetails);
  const quadrant = areaDetails.market_quadrant || 'Data unavailable';
  const coreAudienceLabel = areaDetails.primary_demographic || 'Data unavailable';
  const coreAudienceShare =
    areaDetails.primary_demographic_share !== null &&
    areaDetails.primary_demographic_share !== undefined
      ? `${formatPercent(areaDetails.primary_demographic_share)} of demographic`
      : 'Data unavailable';

  return (
    <div className="dashboard-card selected-area-hero">
      <div className="selected-area-hero-top">
        <div>
          <div className="selected-area-name">{areaDetails.planning_area}</div>
          <p className="selected-area-subtitle">{narrative.idealFor}</p>
        </div>
        <div className="selected-area-rank-pill">
          Rank {areaDetails.rank} for {selectedConcept?.description || 'this concept'}
        </div>
      </div>

      <div className="decision-kpi-grid decision-kpi-grid-expanded">
        <div className="selected-area-meta-card">
          <span>Footfall</span>
          <strong>{formatChartValue(areaDetails.total_footfall)}</strong>
          <small>{formatDelta(areaDetails.total_footfall, footfallAvg, formatChartValue)}</small>
        </div>
        <div className="selected-area-meta-card">
          <span>Rent proxy</span>
          <strong>{formatCurrency(areaDetails.rent_proxy_psm)}</strong>
          <small>{formatDelta(areaDetails.rent_proxy_psm, rentAvg, formatCurrency)}</small>
        </div>
        <div className="selected-area-meta-card">
          <span>Competitors</span>
          <strong>{formatChartValue(areaDetails.competitor_count)}</strong>
          <small>{formatDelta(areaDetails.competitor_count, competitionAvg, formatChartValue)}</small>
        </div>
        <div className="selected-area-meta-card selected-area-meta-card-emphasis">
          <span>Core audience</span>
          <strong>{coreAudienceLabel}</strong>
          <small>{coreAudienceShare}</small>
        </div>
      </div>

      <div className="decision-story-grid decision-story-grid-top">
        <div className="decision-story-card">
          <span>Market quadrant</span>
          <strong>{quadrant}</strong>
          <p>{quadrantDescriptions[quadrant] || 'Quadrant explanation unavailable.'}</p>
        </div>
        <div className="decision-story-card">
          <span>Market story</span>
          <strong>{areaDetails.cluster_label || 'Data unavailable'}</strong>
          <p>{areaDetails.cluster_description || narrative.marketStory}</p>
        </div>
      </div>
    </div>
  );
};

export default DecisionHero;
