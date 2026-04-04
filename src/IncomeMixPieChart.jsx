import React from 'react';
import { Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const IncomeMixPieChart = ({ incomeMix }) => {
  if (!incomeMix) return <div>No data</div>;
  const data = {
    labels: ['Low', 'Mid', 'High'],
    datasets: [
      {
        data: [incomeMix.low, incomeMix.mid, incomeMix.high],
        backgroundColor: [
          '#EC6B56',
          '#FFC154',
          '#47B39C'
        ],
        borderColor: [
          '#EC6B56',
          '#FFC154',
          '#47B39C'
        ],
        borderWidth: 1,
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'bottom' },
      title: { display: true, text: 'Income Mix' },
    },
  };
  return <Pie data={data} options={options} />;
};

export default IncomeMixPieChart;
