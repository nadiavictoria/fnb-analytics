import React from 'react';
import './Dashboard.css';
import { DATA_UNAVAILABLE, formatChartValue, formatCurrency } from './display';

const ShortlistList = ({ areas, selectedAreaName, onSelectArea }) => {
  if (!areas || areas.length === 0) {
    return null;
  }

  return (
    <div className="dashboard-card shortlist-card">
      <div className="dashboard-section-head">
        <div>
          <h2>Shortlist</h2>
          <p>Click a planning area to update the map, summary, and comparison charts.</p>
        </div>
      </div>

      <div className="shortlist-list">
        {areas.map((area) => {
          const metric = area.primary_metric_display;
          const isSelected = area.planning_area === selectedAreaName;

          return (
            <button
              key={area.planning_area}
              className={`shortlist-item ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectArea(area)}
              type="button"
            >
              <div className="shortlist-rank">#{area.rank}</div>
              <div className="shortlist-body">
                <div className="shortlist-title-row">
                  <div className="shortlist-area">{area.planning_area}</div>
                  <span className={`shortlist-quadrant-pill quadrant-${(area.market_quadrant || 'unknown').toLowerCase()}`}>
                    {area.market_quadrant || 'Data unavailable'}
                  </span>
                </div>
                <div className="shortlist-metric">
                  <span>{metric?.label || 'Primary metric'}</span>
                  <strong>{metric?.formatted_value || DATA_UNAVAILABLE}</strong>
                </div>
                <div className="shortlist-secondary-grid">
                  <div>
                    <span>Footfall</span>
                    <strong>{formatChartValue(area.total_footfall)}</strong>
                  </div>
                  <div>
                    <span>Rent</span>
                    <strong>{formatCurrency(area.rent_proxy_psm)}</strong>
                  </div>
                  <div>
                    <span>Competition</span>
                    <strong>{formatChartValue(area.competitor_count)}</strong>
                  </div>
                </div>
                <div className="shortlist-fit-note">
                  Best for: {area.primary_demographic || 'Broad audience'} in a {area.cluster_label || 'mixed'} market
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ShortlistList;
