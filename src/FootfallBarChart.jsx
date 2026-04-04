import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const FootfallBarChart = ({ areas }) => {
  if (!areas || areas.length === 0) return <div>No data</div>;
  const data = {
    labels: areas.map(a => `Rank ${a.rank}`),
    datasets: [
      {
        label: 'Total Footfall',
        data: areas.map(a => a.total_footfall),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Total Footfall vs Rank' },
    },
    scales: {
      x: { title: { display: true, text: 'Rank' } },
      y: { title: { display: true, text: 'Total Footfall' } },
    },
  };
  return <Bar data={data} options={options} />;
};

export default FootfallBarChart;
