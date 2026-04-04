import React from 'react';
import './Dashboard.css';
import { DATA_UNAVAILABLE, formatPercent } from './display';

const AudienceBars = ({ title, subtitle, rows }) => {
  const hasRows = Array.isArray(rows) && rows.length > 0;

  return (
    <div className="dashboard-card audience-bars-card">
      <div className="dashboard-section-head">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
      </div>

      {hasRows ? (
        <div className="audience-bars-list">
          {rows.map((row) => (
            <div className="audience-bar-row" key={row.key}>
              <div className="audience-bar-header">
                <span>{row.label}</span>
                <strong>{row.share === null ? DATA_UNAVAILABLE : formatPercent(row.share)}</strong>
              </div>
              <div className="audience-bar-track">
                <div
                  className="audience-bar-fill"
                  style={{
                    width: `${Math.max(0, Math.min(100, (row.share || 0) * 100))}%`,
                    backgroundColor: row.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="profile-empty">{DATA_UNAVAILABLE}</div>
      )}
    </div>
  );
};

export default AudienceBars;
