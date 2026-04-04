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

const CompetitorBarChart = ({ areas }) => {
  if (!areas || areas.length === 0) return <div>No data</div>;
  const data = {
    labels: areas.map(a => `Rank ${a.rank}`),
    datasets: [
      {
        label: 'Competitor Count',
        data: areas.map(a => a.competitor_count),
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Competitor Count vs Rank' },
    },
    scales: {
      x: { title: { display: true, text: 'Rank' } },
      y: { title: { display: true, text: 'Competitor Count' } },
    },
  };
  return <Bar data={data} options={options} />;
};

export default CompetitorBarChart;
