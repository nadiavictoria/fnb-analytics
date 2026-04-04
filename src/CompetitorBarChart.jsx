import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js';
import { DATA_UNAVAILABLE, formatChartValue } from './display';
import { getBarColors } from './chartColors';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const competitorChartColor = {
  background: 'rgba(59, 130, 246, 0.55)',
  border: 'rgba(37, 99, 235, 0.85)',
};

const CompetitorBarChart = ({ areas, selectedAreaName }) => {
  if (!areas || areas.length === 0) return <div className="chart-empty">{DATA_UNAVAILABLE}</div>;
  const barColors = getBarColors(areas, selectedAreaName, competitorChartColor);

  const data = {
    labels: areas.map((area) => area.planning_area),
    datasets: [
      {
        label: 'Competitor count',
        data: areas.map((area) => area.competitor_count ?? null),
        backgroundColor: barColors.backgroundColor,
        borderColor: barColors.borderColor,
        borderWidth: 1.5,
        borderRadius: 6,
        barThickness: 18,
        maxBarThickness: 22,
        categoryPercentage: 0.72,
        barPercentage: 0.86,
      },
    ],
  };

  const options = {
    indexAxis: 'y',
    maintainAspectRatio: false,
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: true, text: 'Competitor Count' },
      tooltip: {
        callbacks: {
          label: (context) => `Competitors: ${formatChartValue(context.raw)}`,
          afterLabel: (context) => {
            const area = areas[context.dataIndex];
            return `Rank ${area.rank}`;
          },
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Competitors' },
        ticks: {
          callback: (value) => formatChartValue(value),
        },
      },
      y: {
        title: { display: true, text: 'Planning area' },
      },
    },
  };

  return <Bar data={data} options={options} />;
};

export default CompetitorBarChart;
