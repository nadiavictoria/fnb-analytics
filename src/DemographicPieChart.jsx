import React from 'react';
import { Pie } from 'react-chartjs-2';
import {
  ArcElement,
  Chart as ChartJS,
  Legend,
  Tooltip,
} from 'chart.js';
import './Dashboard.css';
import { DATA_UNAVAILABLE } from './display';

ChartJS.register(ArcElement, Tooltip, Legend);

const demographicPalette = [
  '#1d4ed8',
  '#2563eb',
  '#0f766e',
  '#38bdf8',
  '#64748b',
  '#94a3b8',
];

const demographicOrder = [
  'children',
  'teens_youth',
  'young_adults',
  'mid_age_adults',
  'older_adults',
  'seniors',
];

const DemographicPieChart = ({ demographicBreakdown }) => {
  const rows = Array.isArray(demographicBreakdown)
    ? [...demographicBreakdown].sort(
        (a, b) => demographicOrder.indexOf(a.key) - demographicOrder.indexOf(b.key),
      )
    : [];
  const hasData = rows.length > 0;
  const numericValues = rows.map((row) =>
    row?.share !== null && row?.share !== undefined && !Number.isNaN(Number(row.share))
      ? Number(row.share)
      : 0,
  );
  const maxValue = Math.max(...numericValues, 0);

  const data = {
    labels: rows.map((row, index) => row?.label || `Segment ${index + 1}`),
    datasets: [
      {
        data: numericValues,
        backgroundColor: rows.map((_, index) => demographicPalette[index] || '#94a3b8'),
        borderColor: '#ffffff',
        borderWidth: 4,
        hoverOffset: 8,
        offset: numericValues.map((value) => (value === maxValue && value > 0 ? 16 : 0)),
      },
    ],
  };

  const options = {
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) =>
            `${context.label}: ${rows[context.dataIndex]?.share_formatted || DATA_UNAVAILABLE}`,
        },
      },
    },
  };

  return (
    <div className="dashboard-card compact-info-card">
      <div className="dashboard-section-head">
        <div>
          <h2>Demographics</h2>
          <p>Demographic composition in the selected planning area.</p>
        </div>
      </div>

      {hasData ? (
        <div className="profile-side-by-side">
          <div className="profile-pie-wrap profile-pie-wrap-large">
            <Pie data={data} options={options} />
          </div>

          <div className="profile-legend-list profile-legend-list-side">
            {rows.map((row, index) => {
              const isHighest = numericValues[index] === maxValue && maxValue > 0;
              return (
                <div
                  className={`profile-legend-item profile-legend-item-large ${isHighest ? 'profile-legend-item-accent' : ''}`}
                  key={row.key || index}
                >
                  <div className="profile-legend-left">
                    <span
                      className="profile-legend-swatch profile-legend-swatch-large"
                      style={{ backgroundColor: demographicPalette[index] || '#94a3b8' }}
                    />
                    <div className="profile-legend-copy">
                      <span>{row.label || DATA_UNAVAILABLE}</span>
                    </div>
                  </div>
                  <strong>{row.share_formatted || DATA_UNAVAILABLE}</strong>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="profile-empty">{DATA_UNAVAILABLE}</div>
      )}
    </div>
  );
};

export default DemographicPieChart;
