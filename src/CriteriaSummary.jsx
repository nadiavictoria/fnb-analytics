import React from 'react';
import './Dashboard.css';
import DirectionChip from './DirectionChip';
import { DATA_UNAVAILABLE, displayText } from './display';
import { getAreaNarrative, getStrengthsAndWatchouts } from './insights';

const formatValueWithUnit = (row) => {
  const formattedValue = row.formatted_value || DATA_UNAVAILABLE;
  if (!row.unit || row.unit === '%' || row.unit === '/5') {
    return formattedValue;
  }
  return `${formattedValue} ${row.unit}`;
};

const CriteriaSummary = ({
  areaDetails,
  areas = [],
  conceptDescription,
  maximize = [],
  minimize = [],
  debug = false,
}) => {
  if (!areaDetails) return null;

  const { strengths, watchouts, insightRows } = getStrengthsAndWatchouts(
    areaDetails,
    areas,
    maximize,
    minimize,
  );
  const primaryMetric = areaDetails.primary_metric;
  const narrative = getAreaNarrative(areaDetails);
  const orderedInsightRows = [...insightRows].sort((a, b) => {
    if (a.key === primaryMetric) return -1;
    if (b.key === primaryMetric) return 1;
    return 0;
  });

  return (
    <div className="dashboard-card criteria-summary">
      <div className="dashboard-section-head">
        <div>
          <h2>Why This Area Is Recommended</h2>
          <p>Decision-ready summary with the main advantages, tradeoffs, and shortlist-relative deltas.</p>
        </div>
      </div>

      <div className="criteria-text-block">
        <p>{displayText(areaDetails.recommendation_summary)}</p>
      </div>

      <div className="insight-grid">
        <div className="insight-card">
          <h3>Strongest advantages</h3>
          <div className="insight-list">
            {strengths.map((row) => (
              <div className="insight-item" key={row.key}>
                <div className="insight-item-top">
                  <strong>{displayText(row.label)}</strong>
                  <DirectionChip direction={row.direction} />
                </div>
                <span>{row.deltaSummary}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="insight-card">
          <h3>Main tradeoffs</h3>
          <div className="insight-list">
            {watchouts.map((row) => (
              <div className="insight-item" key={row.key}>
                <div className="insight-item-top">
                  <strong>{displayText(row.label)}</strong>
                  <DirectionChip direction={row.direction} />
                </div>
                <span>{row.deltaSummary}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="insight-card">
          <h3>Who this area suits best</h3>
          <div className="insight-list">
            <div className="insight-item">
              <div className="insight-item-top">
                <strong>{displayText(conceptDescription)}</strong>
              </div>
              <span>{narrative.idealFor}</span>
            </div>
            <div className="insight-item">
              <div className="insight-item-top">
                <strong>Market context</strong>
              </div>
              <span>{narrative.marketStory}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="criteria-table-wrap">
        <h3>Shortlist Criteria With Deltas</h3>
        <table className="criteria-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Direction</th>
              <th>Value</th>
              <th>Compared with shortlist</th>
            </tr>
          </thead>
          <tbody>
            {orderedInsightRows.map((row) => {
              const isPrimary = row.key === primaryMetric;
              return (
                <tr
                  key={row.key}
                  className={isPrimary ? 'criteria-row-primary' : ''}
                >
                  <td>
                    <div className="criteria-label-line">
                      <span>{displayText(row.label)}</span>
                      {isPrimary && <span className="criteria-primary-pill">Primary metric</span>}
                    </div>
                  </td>
                  <td><DirectionChip direction={row.direction} /></td>
                  <td>{formatValueWithUnit(row)}</td>
                  <td>{row.deltaSummary}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {debug && (
        <div className="criteria-debug">
          <h3>Debug</h3>
          <p><strong>Primary metric key:</strong> {displayText(areaDetails.primary_metric)}</p>
          <p><strong>Primary raw value:</strong> {displayText(areaDetails.primary_value)}</p>
          <p><strong>Criteria snapshot:</strong> {displayText(areaDetails.criteria_snapshot)}</p>
        </div>
      )}
    </div>
  );
};

export default CriteriaSummary;
