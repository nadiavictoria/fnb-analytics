import React from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart, ArcElement, Tooltip, Legend } from 'chart.js';

Chart.register(ArcElement, Tooltip, Legend);

const DemographicPieChart = ({ primaryDemographic, primaryShare }) => {
  if (!primaryDemographic || primaryShare == null) return <div>No demographic data</div>;
  const share = Number(primaryShare);
  const data = {
    labels: [primaryDemographic, 'Others'],
    datasets: [
      {
        data: [share, 1 - share],
        backgroundColor: ['#4e79a7', '#e0e4ea'],
        borderWidth: 1,
      },
    ],
  };
  const options = {
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
      },
      title: { display: true, text: 'Primary Demographic' },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.raw;
            return `${label}: ${(value * 100).toFixed(1)}%`;
          },
        },
      },
    },
    cutout: '0%',
    responsive: true,
    maintainAspectRatio: false,
  };
  return (
    <div style={{ width: '100%', height: 200 }}>
      <Pie data={data} options={options} />
    </div>
  );
};

export default DemographicPieChart;
