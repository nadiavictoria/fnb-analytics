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
import { DATA_UNAVAILABLE, formatCurrency } from './display';
import { getBarColors } from './chartColors';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const rentChartColor = {
  background: 'rgba(59, 130, 246, 0.55)',
  border: 'rgba(37, 99, 235, 0.85)',
};

const RentProxyBarChart = ({ areas, selectedAreaName }) => {
  if (!areas || areas.length === 0) return <div className="chart-empty">{DATA_UNAVAILABLE}</div>;
  const barColors = getBarColors(areas, selectedAreaName, rentChartColor);

  const data = {
    labels: areas.map((area) => area.planning_area),
    datasets: [
      {
        label: 'Rent proxy PSM',
        data: areas.map((area) => area.rent_proxy_psm ?? null),
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
      title: { display: true, text: 'Rent Proxy PSM' },
      tooltip: {
        callbacks: {
          label: (context) => `Rent proxy: ${formatCurrency(context.raw)}`,
          afterLabel: (context) => {
            const area = areas[context.dataIndex];
            return `Rank ${area.rank}`;
          },
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'SGD per sq m' },
        ticks: {
          callback: (value) => Number(value).toFixed(0),
        },
      },
      y: {
        title: { display: true, text: 'Planning area' },
      },
    },
  };

  return <Bar data={data} options={options} />;
};

export default RentProxyBarChart;
