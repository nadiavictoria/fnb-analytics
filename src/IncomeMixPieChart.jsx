import React from 'react';
import { Pie } from 'react-chartjs-2';
import {
  ArcElement,
  Chart as ChartJS,
  Legend,
  Tooltip,
} from 'chart.js';
import './Dashboard.css';
import { DATA_UNAVAILABLE, formatPercent } from './display';

ChartJS.register(ArcElement, Tooltip, Legend);

const rows = [
  { key: 'low', label: 'Low', color: '#ff7417' },
  { key: 'mid', label: 'Mid', color: '#f8a308' },
  { key: 'high', label: 'High', color: '#1f7f78' },
];

const IncomeMixPieChart = ({ incomeMix }) => {
  const values = rows.map((row) => {
    const value = incomeMix?.[row.key];
    return value !== null && value !== undefined && !Number.isNaN(Number(value))
      ? Number(value)
      : null;
  });

  const hasData = values.some((value) => value !== null);
  const numericValues = values.map((value) => (value === null ? 0 : value));
  const maxValue = Math.max(...numericValues, 0);

  const data = {
    labels: rows.map((row) => row.label),
    datasets: [
      {
        data: numericValues,
        backgroundColor: rows.map((row) => row.color),
        borderColor: '#ffffff',
        borderWidth: 6,
        hoverOffset: 8,
        offset: numericValues.map((value) => (value === maxValue && value > 0 ? 18 : 0)),
      },
    ],
  };

  const options = {
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => `${context.label}: ${formatPercent(context.raw)}`,
        },
      },
    },
  };

  return (
    <div className="dashboard-card compact-info-card">
      <div className="dashboard-section-head">
        <div>
          <h2>Income Mix</h2>
          <p>Household income composition in the selected planning area.</p>
        </div>
      </div>

      {hasData ? (
        <div className="profile-side-by-side">
          <div className="profile-pie-wrap profile-pie-wrap-large">
            <Pie data={data} options={options} />
          </div>
          <div className="profile-legend-list profile-legend-list-side">
            {rows.map((row, index) => (
              <div
                className={`profile-legend-item profile-legend-item-large ${
                  numericValues[index] === maxValue && maxValue > 0 ? 'profile-legend-item-accent' : ''
                }`}
                key={row.key}
              >
                <div className="profile-legend-left">
                  <span
                    className="profile-legend-swatch profile-legend-swatch-large"
                    style={{ backgroundColor: row.color }}
                  />
                  <span>{row.label}</span>
                </div>
                <strong>
                  {values[index] === null ? DATA_UNAVAILABLE : formatPercent(values[index])}
                </strong>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="profile-empty">{DATA_UNAVAILABLE}</div>
      )}
    </div>
  );
};

export default IncomeMixPieChart;
