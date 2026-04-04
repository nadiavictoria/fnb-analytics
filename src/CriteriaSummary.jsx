import React from 'react';
import './Dashboard.css';

const CriteriaSummary = ({ areaDetails }) => {
  if (!areaDetails) return null;
  // Use criteria_display array if available
  const criteriaRows = Array.isArray(areaDetails.criteria_display)
    ? areaDetails.criteria_display
    : [];

  // Find the primary metric key
  const primaryMetric = areaDetails.primary_metric;

  return (
    <div className="criteria-summary">
      <h3>Criteria & Recommendation</h3>
      {areaDetails.planning_area && (
        <div style={{ marginBottom: 8 }}>
          <strong>Planning Area:</strong> {areaDetails.planning_area}
        </div>
      )}
      <div>
        <strong>Criteria Used and Snapshot Value:</strong>
        {criteriaRows.length > 0 ? (
          <>
            <table style={{ width: '100%', fontSize: '0.95em', marginBottom: 4, borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '2px 6px', borderBottom: '1px solid #ddd' }}>Metric</th>
                  <th style={{ textAlign: 'left', padding: '2px 6px', borderBottom: '1px solid #ddd' }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {criteriaRows.map((row) => {
                  const isPrimary = row.key === primaryMetric;
                  return (
                    <tr
                      key={row.key}
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
                        {row.label}
                        {isPrimary && (
                          <span style={{ fontWeight: 'bold', color: '#2a3b4c' }}> (primary metric)</span>
                        )}
                      </td>
                      <td
                        style={{
                          padding: '2px 6px',
                          borderBottom: '1px solid #f0f0f0',
                          fontWeight: isPrimary ? 'bold' : 'normal',
                        }}
                      >
                        {row.formatted_value}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {areaDetails.cluster_label && (
              <div style={{ marginTop: 8 }}>
                <strong>{areaDetails.cluster_label}</strong>
                {areaDetails.cluster_description && (
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.97em', color: '#444' }}>Area {areaDetails.cluster_description}</p>
                )}
              </div>
            )}
          </>
        ) : (
          <div style={{ fontSize: '0.95em', marginTop: 4 }}>
            {areaDetails.criteria_snapshot || 'N/A'}
          </div>
        )}
      </div>
      <div style={{ marginTop: 8 }}>
        <strong>Recommendation</strong>
        <div style={{ fontSize: '0.95em', marginTop: 4 }}>
          {areaDetails.recommendation_summary || 'N/A'}
        </div>
      </div>
    </div>
  );
};

export default CriteriaSummary;
