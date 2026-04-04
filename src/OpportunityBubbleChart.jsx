import React from 'react';
import { Bubble } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  Legend,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js';
import './Dashboard.css';
import { DATA_UNAVAILABLE, formatChartValue, formatCurrency } from './display';

ChartJS.register(LinearScale, PointElement, Title, Tooltip, Legend);

const bubblePalette = [
  { background: 'rgba(37, 99, 235, 0.55)', border: 'rgba(29, 78, 216, 1)' },
  { background: 'rgba(14, 165, 233, 0.45)', border: 'rgba(2, 132, 199, 1)' },
  { background: 'rgba(15, 118, 110, 0.45)', border: 'rgba(13, 148, 136, 1)' },
  { background: 'rgba(99, 102, 241, 0.42)', border: 'rgba(79, 70, 229, 1)' },
  { background: 'rgba(100, 116, 139, 0.4)', border: 'rgba(71, 85, 105, 1)' },
];

const OpportunityBubbleChart = ({ areas, selectedAreaName }) => {
  if (!areas || areas.length === 0) {
    return <div className="chart-empty">{DATA_UNAVAILABLE}</div>;
  }

  const data = {
    datasets: areas.map((area, index) => {
      const color = bubblePalette[index % bubblePalette.length];
      const isSelected = area.planning_area === selectedAreaName;

      return {
        label: area.planning_area,
        data: [
          {
            x: area.rent_proxy_psm ?? 0,
            y: area.total_footfall ?? 0,
            r: Math.max(8, Math.min(22, Math.sqrt(area.competitor_count ?? 0) * 1.2)),
          },
        ],
        backgroundColor: color.background,
        borderColor: color.border,
        borderWidth: isSelected ? 4 : 2,
        pointStyle: 'circle',
      };
    }),
  };

  const options = {
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          usePointStyle: true,
          boxWidth: 10,
        },
      },
      tooltip: {
        callbacks: {
          title: (items) => items[0]?.dataset?.label || DATA_UNAVAILABLE,
          label: (context) => {
            const point = context.raw || {};
            const area = areas.find((candidate) => candidate.planning_area === context.dataset.label);
            return [
              `Footfall: ${formatChartValue(point.y)}`,
              `Rent: ${formatCurrency(point.x)}`,
              `Competitors: ${formatChartValue(area?.competitor_count)}`,
              `Quadrant: ${area?.market_quadrant || DATA_UNAVAILABLE}`,
            ];
          },
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Rent proxy (SGD per sq m)',
        },
        ticks: {
          callback: (value) => Number(value).toFixed(0),
        },
      },
      y: {
        title: {
          display: true,
          text: 'Total footfall',
        },
        ticks: {
          callback: (value) => formatChartValue(value),
        },
      },
    },
  };

  return (
    <div className="dashboard-card bubble-chart-card">
      <div className="dashboard-section-head">
        <div>
          <h2>Footfall vs Rent</h2>
          <p>Bubble size shows competitor count, so you can compare throughput, cost, and rivalry in one view.</p>
        </div>
      </div>
      <div className="bubble-chart-wrap">
        <Bubble data={data} options={options} />
      </div>
    </div>
  );
};

export default OpportunityBubbleChart;
