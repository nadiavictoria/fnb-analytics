import { Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const IncomeMixPieChart = ({ incomeMix }) => {
  if (!incomeMix || [incomeMix.low, incomeMix.mid, incomeMix.high].every(v => v == null)) {
    return <div style={{ textAlign: 'center', color: '#999', fontSize: '0.9em' }}>Income Mix<br/>No data available</div>;
  }
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
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' },
      title: { display: true, text: 'Income Mix' },
    },
  };
  return (
    <div style={{ width: '100%', height: 200 }}>
      <Pie data={data} options={options} />
    </div>
  );
};

export default IncomeMixPieChart;
