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
          '#a259ec', // purple for Low
          '#2ecc40', // green for Mid
          '#ff9800'  // orange for High
        ],
        borderColor: [
          '#a259ec',
          '#2ecc40',
          '#ff9800'
        ],
        borderWidth: 1,
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Income Mix' },
    },
  };
  return <Pie data={data} options={options} />;
};

export default IncomeMixPieChart;
