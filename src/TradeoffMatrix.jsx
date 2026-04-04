import React from 'react';
import './Dashboard.css';
import DirectionChip from './DirectionChip';
import { DATA_UNAVAILABLE } from './display';
import { formatMetricValue, groupCriteriaByTheme } from './insights';

const TradeoffMatrix = ({
  areas,
  selectedAreaName,
  maximize = [],
  minimize = [],
}) => {
  if (!areas || areas.length === 0) return null;

  const criteriaRows = areas[0]?.criteria_display || [];
  const groupedRows = groupCriteriaByTheme(criteriaRows);

  const getCellState = (metricKey, area) => {
    const metricValues = areas.map((candidate) => {
      const row = (candidate.criteria_display || []).find((item) => item.key === metricKey);
      return row?.value ?? null;
    });
    const numericValues = metricValues.filter((value) => value !== null && value !== undefined);
    if (numericValues.length === 0) return '';

    const currentValue = (area.criteria_display || []).find((item) => item.key === metricKey)?.value;
    if (currentValue === null || currentValue === undefined) return '';

    const isMaximize = maximize.includes(metricKey);
    const bestValue = isMaximize ? Math.max(...numericValues) : Math.min(...numericValues);
    const worstValue = isMaximize ? Math.min(...numericValues) : Math.max(...numericValues);

    if (currentValue === bestValue) return 'best';
    if (currentValue === worstValue) return 'watchout';
    return '';
  };

  return (
    <div className="dashboard-card tradeoff-matrix-card">
      <div className="dashboard-section-head">
        <div>
          <h2>Shortlist Tradeoff Matrix</h2>
          <p>See how each shortlisted area performs across the decision criteria, grouped by business theme.</p>
        </div>
        <div className="tradeoff-legend" aria-label="Tradeoff matrix legend">
          <span><i className="tradeoff-legend-swatch tradeoff-legend-best" /> Best performing</span>
          <span><i className="tradeoff-legend-swatch tradeoff-legend-watchout" /> Worst performing</span>
        </div>
      </div>

      <div className="tradeoff-matrix-wrap">
        <table className="tradeoff-matrix">
          <thead>
            <tr>
              <th>Metric</th>
              {areas.map((area) => (
                <th
                  key={area.planning_area}
                  className={area.planning_area === selectedAreaName ? 'selected-column' : ''}
                >
                  <div className="tradeoff-area-head">
                    <strong>#{area.rank}</strong>
                    <span>{area.planning_area}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {groupedRows.map((group) => (
              <React.Fragment key={group.theme}>
                <tr className="tradeoff-theme-row">
                  <td colSpan={areas.length + 1}>{group.theme}</td>
                </tr>
                {group.rows.map((row) => {
                  const direction = maximize.includes(row.key)
                    ? 'maximize'
                    : minimize.includes(row.key)
                      ? 'minimize'
                      : null;

                  return (
                    <tr key={row.key}>
                      <td className="tradeoff-metric-cell">
                        <div className="tradeoff-metric-head">
                          <span>{row.label}</span>
                        </div>
                        <DirectionChip direction={direction} />
                      </td>
                      {areas.map((area) => {
                        const areaMetric = (area.criteria_display || []).find((item) => item.key === row.key);
                        const cellState = getCellState(row.key, area);
                        const isSelected = area.planning_area === selectedAreaName;

                        return (
                          <td
                            key={`${area.planning_area}-${row.key}`}
                            className={[
                              isSelected ? 'selected-column' : '',
                              cellState ? `metric-${cellState}` : '',
                            ].join(' ').trim()}
                          >
                            <span className="tradeoff-cell-value">
                              {areaMetric
                                ? formatMetricValue(areaMetric.value, areaMetric.unit)
                                : DATA_UNAVAILABLE}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TradeoffMatrix;
