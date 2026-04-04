import React from 'react';
import './Dashboard.css';

const CriteriaSummary = ({ areaDetails }) => {
  if (!areaDetails) return null;
  // Parse criteria_snapshot string into array of [metric, value]
  let criteriaRows = [];
  if (areaDetails.criteria_snapshot) {
    criteriaRows = areaDetails.criteria_snapshot.split(';').map(row => {
      const [metric, value] = row.split('=');
      return metric && value ? [metric.trim(), value.trim()] : null;
    }).filter(Boolean);
  }

  // Find the primary metric and value
  const primaryMetric = areaDetails.primary_metric;
  const primaryValue = areaDetails.primary_value !== undefined ? String(areaDetails.primary_value) : undefined;

  return (
    <div className="criteria-summary">
      <h4>Criteria & Recommendation</h4>
      <div>
        <strong>Criteria Used and Snapshot:</strong>
        {criteriaRows.length > 0 ? (
          <table style={{ width: '100%', fontSize: '0.95em', marginBottom: 4, borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '2px 6px', borderBottom: '1px solid #ddd' }}>Metric</th>
                <th style={{ textAlign: 'left', padding: '2px 6px', borderBottom: '1px solid #ddd' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {criteriaRows.map(([metric, value]) => {
                const isPrimary =
                  metric === primaryMetric &&
                  (primaryValue === undefined || value === primaryValue);
                return (
                  <tr
                    key={metric}
                    style={
                      isPrimary
                        ? {
                            background: '#e3ecf7', // shale blue
                          }
                        : {}
                    }
                  >
                    <td
                      style={{
                        padding: '2px 6px',
                        borderBottom: '1px solid #f0f0f0',
                        fontStyle: isPrimary ? 'italic' : 'normal',
                      }}
                    >
                      {metric}
                      {isPrimary && (
                        <span style={{ fontWeight: 'bold', color: '#2a3b4c' }}> (primary metric)</span>
                      )}
                    </td>
                    <td
                      style={{
                        padding: '2px 6px',
                        borderBottom: '1px solid #f0f0f0',
                        fontStyle: isPrimary ? 'italic' : 'normal',
                      }}
                    >
                      {value}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div style={{ fontSize: '0.95em', marginBottom: 4 }}>
            {areaDetails.criteria_snapshot || 'N/A'}
          </div>
        )}
      </div>
      <div>
        <strong>Recommendation:</strong>
        <div style={{ fontSize: '0.95em' }}>
          {areaDetails.recommendation_summary || 'N/A'}
        </div>
      </div>
    </div>
  );
};

export default CriteriaSummary;
